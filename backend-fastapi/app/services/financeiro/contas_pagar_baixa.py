# ---------------------------------------------------------------------------
# ARQUIVO: services/financeiro/contas_pagar_baixa.py
# DESCRICAO: Financeiro - pagar e estornar conta a pagar: onde o documento
#            vira lancamento (e a recorrencia gera a proxima).
# ---------------------------------------------------------------------------

from datetime import date
from typing import Any, Dict
from sqlalchemy.orm import Session
from app.core.enum import (
    ContaPagarStatus,
    MovimentacaoFinanceiraOrigem,
    MovimentacaoFinanceiraTipo,
)
from app.core.tempo import hoje_local, inicio_do_dia_utc
from app.db.crud import financeiro as financeiro_crud
from app.db.crud import sessao_caixa as caixa_crud
from app.db.models.conta_pagar import ContaPagar
from app.helpers.exceptions import BadRequestException, NotFoundException
from app.schemas.financeiro import (
    ContaPagarBaixa,
    ContaPagarEstorno,
)
from app.services.financeiro.comum import _funcionario_do_token, _somar_meses
from app.services.financeiro.contas_bancarias import _conta_padrao_id
from app.services.financeiro.contas_pagar import ENTIDADE_CONTA_PAGAR, _serializar_conta


def _proximo_vencimento(vencimento: date) -> date:
    """O mês seguinte, para a RECORRÊNCIA.

    Aqui a âncora é mesmo a conta anterior, e não há outra: a recorrência não
    tem começo guardado -- cada ocorrência nasce da baixa da anterior. A
    consequência é que uma conta de dia 31 encolhe para 28 em fevereiro e assim
    permanece. É uma imprecisão conhecida e aceita: acertá-la exigiria guardar o
    dia original numa coluna, e ninguém contratou aluguel para o dia 31.

    No PARCELAMENTO isso não acontece -- lá existe a primeira parcela como
    âncora, e `_somar_meses` a usa.
    """
    return _somar_meses(vencimento, 1)


def pagar_conta(
    db: Session,
    empresa_id: int,
    conta_id: int,
    dados: ContaPagarBaixa,
    usuario_token: Dict[str, Any],
) -> Dict[str, Any]:
    """Dá baixa: marca a conta como PAGA e escreve no livro do dinheiro.

    As duas coisas na MESMA transação. Uma conta marcada como paga sem o
    lançamento correspondente deixaria o resultado do mês mentindo, e um
    lançamento sem a conta deixaria a despesa órfã no livro.
    """
    conta = financeiro_crud.get_conta_pagar(db, empresa_id, conta_id)
    if not conta:
        raise NotFoundException(detail="Conta não encontrada")
    if conta.status == ContaPagarStatus.PAGA.value:
        raise BadRequestException(detail="Esta conta já está paga.")
    if conta.status == ContaPagarStatus.CANCELADA.value:
        raise BadRequestException(detail="Esta conta foi cancelada e não pode ser paga.")

    valor_pago = dados.valor_pago if dados.valor_pago is not None else conta.valor
    dia_pagamento = dados.pago_em or hoje_local()

    if dados.conta_bancaria_id is not None:
        if not financeiro_crud.get_conta_bancaria(db, empresa_id, dados.conta_bancaria_id):
            raise BadRequestException(detail="Conta bancária não encontrada")

    func_id, func_nome = _funcionario_do_token(usuario_token)

    # O LANÇAMENTO. Passa pelo mesmo `registrar_movimento` que a venda e a
    # sangria usam: é o único lugar que escreve no livro, e concentrar a escrita
    # é o que impede uma linha de dinheiro nascer sem origem.
    #
    # `sessao_caixa_id` fica NULO de propósito, mesmo quando há caixa aberto:
    # pagar fornecedor não é sangria. Se o dinheiro saiu fisicamente da gaveta, a
    # sangria é lançada à parte pelo operador, e contar as duas coisas faria a
    # gaveta fechar com falta.
    conta_origem_id = dados.conta_bancaria_id or _conta_padrao_id(db, empresa_id)

    movimento = caixa_crud.registrar_movimento(
        db,
        tipo=MovimentacaoFinanceiraTipo.SAIDA,
        origem=MovimentacaoFinanceiraOrigem.DESPESA,
        valor=valor_pago,
        conta_bancaria_id=conta_origem_id,
        forma_pagamento_id=dados.forma_pagamento_id,
        funcionario_id=func_id,
        funcionario_nome=func_nome,
        motivo=f"Pagamento: {conta.descricao}",
    )

    conta.status = ContaPagarStatus.PAGA.value
    conta.valor_pago = valor_pago
    # Guardado como início do dia em UTC: é timestamp de evento e converte
    # (ver core/tempo.py), diferente de `vencimento`, que é data pura.
    conta.pago_em = inicio_do_dia_utc(dia_pagamento)
    # A conta RESOLVIDA, e nao a escolha crua do usuario: o movimento caiu
    # nela, e deixar aqui um NULL faria o estorno procurar de onde o dinheiro
    # saiu e nao achar.
    conta.conta_bancaria_id = conta_origem_id
    conta.forma_pagamento_id = dados.forma_pagamento_id
    conta.movimentacao_financeira_id = movimento.id
    if dados.observacao:
        conta.observacao = dados.observacao

    financeiro_crud.registrar_historico(
        db, empresa_id=empresa_id, entidade=ENTIDADE_CONTA_PAGAR, entidade_id=conta.id,
        campo="baixa", valor_antigo=ContaPagarStatus.PENDENTE.value,
        valor_novo=f"PAGA {valor_pago}",
        funcionario_id=func_id, funcionario_nome=func_nome,
    )

    # Recorrência: a próxima nasce agora, com o valor ORIGINAL da conta e não o
    # pago. A luz veio R$ 80 mais cara este mês por causa do calor; repetir esse
    # valor viraria previsão errada todo mês seguinte.
    #
    # IDEMPOTENTE. Sem a checagem, estornar e pagar de novo criava uma SEGUNDA
    # ocorrência do mês seguinte, e a dívida se multiplicava a cada repetição do
    # ciclo. `gerada_por_id` é o que permite perguntar "já gerei a partir desta?".
    if conta.recorrente and not financeiro_crud.get_ocorrencia_gerada(
        db, empresa_id, conta.id
    ):
        financeiro_crud.criar_conta_pagar(
            db,
            ContaPagar(
                empresa_id=empresa_id,
                descricao=conta.descricao,
                valor=conta.valor,
                vencimento=_proximo_vencimento(conta.vencimento),
                plano_conta_id=conta.plano_conta_id,
                fornecedor_id=conta.fornecedor_id,
                recorrente=True,
                status=ContaPagarStatus.PENDENTE.value,
                gerada_por_id=conta.id,
            ),
        )

    db.flush()
    db.refresh(conta)
    return _serializar_conta(conta, hoje_local())


def estornar_pagamento(
    db: Session,
    empresa_id: int,
    conta_id: int,
    dados: ContaPagarEstorno,
    usuario_token: Dict[str, Any],
) -> Dict[str, Any]:
    """Desfaz a baixa sem apagar nada do livro.

    O movimento de estorno é lançado com a data de HOJE, jamais na data original.
    `sessao_caixa` PERSISTE `saldo_final_esperado` e `saldo_final_informado`: um
    lançamento retroativo faria a quebra de caixa gravada discordar da
    recalculada, e aí nenhum dos dois números serve para nada.
    """
    conta = financeiro_crud.get_conta_pagar(db, empresa_id, conta_id)
    if not conta:
        raise NotFoundException(detail="Conta não encontrada")
    if conta.status != ContaPagarStatus.PAGA.value:
        raise BadRequestException(detail="Só é possível estornar uma conta paga.")

    func_id, func_nome = _funcionario_do_token(usuario_token)
    valor_estornado = conta.valor_pago or conta.valor

    # ENTRADA, o espelho da SAIDA original. Origem segue DESPESA: o par
    # saída + entrada com o mesmo motivo é o que a auditoria lê como estorno,
    # e uma origem própria faria o total de despesas do período ignorá-lo.
    caixa_crud.registrar_movimento(
        db,
        tipo=MovimentacaoFinanceiraTipo.ENTRADA,
        origem=MovimentacaoFinanceiraOrigem.DESPESA,
        valor=valor_estornado,
        # A MESMA conta de onde o dinheiro saiu -- lido ANTES de a baixa ser
        # limpa, mais abaixo. Devolver noutra conta deixaria uma com sobra e a
        # outra com falta, e a soma esconderia o erro.
        conta_bancaria_id=conta.conta_bancaria_id or _conta_padrao_id(db, empresa_id),
        forma_pagamento_id=conta.forma_pagamento_id,
        funcionario_id=func_id,
        funcionario_nome=func_nome,
        motivo=f"Estorno de pagamento: {conta.descricao} — {dados.motivo}",
    )

    financeiro_crud.registrar_historico(
        db, empresa_id=empresa_id, entidade=ENTIDADE_CONTA_PAGAR, entidade_id=conta.id,
        campo="estorno", valor_antigo=f"PAGA {valor_estornado}",
        valor_novo=f"PENDENTE — {dados.motivo}",
        funcionario_id=func_id, funcionario_nome=func_nome,
    )

    # Desfaz também a CONSEQUÊNCIA do pagamento: a ocorrência do mês seguinte
    # que a recorrência criou ao dar a baixa.
    #
    # Sem isto, estornar deixava a loja aparentando dever duas contas de
    # internet -- a de setembro, de volta a pendente, e a de outubro, que só
    # existia por causa do pagamento que acabou de ser desfeito.
    #
    # Apaga em vez de cancelar, e é a única exceção à regra da casa: a linha foi
    # criada pelo SISTEMA, nunca teve dinheiro andando, e some ao desfazer
    # exatamente o que a criou. Um fantasma "Cancelada" por estorno seria ruído
    # de uma conta que ninguém lançou.
    #
    # Se a ocorrência JÁ FOI PAGA ou cancelada, fica onde está: aí houve decisão
    # de gente no meio, e apagá-la levaria junto um pagamento de verdade.
    gerada = financeiro_crud.get_ocorrencia_gerada(db, empresa_id, conta.id)
    if gerada is not None and gerada.status == ContaPagarStatus.PENDENTE.value:
        financeiro_crud.apagar_conta(db, gerada)

    # Volta a PENDENTE e limpa a baixa. A CHECK do banco exige coerência: conta
    # não-PAGA não pode carregar `pago_em` nem `valor_pago`.
    conta.status = ContaPagarStatus.PENDENTE.value
    conta.valor_pago = None
    conta.pago_em = None
    conta.conta_bancaria_id = None
    conta.forma_pagamento_id = None
    conta.movimentacao_financeira_id = None

    db.flush()
    db.refresh(conta)
    return _serializar_conta(conta, hoje_local())
