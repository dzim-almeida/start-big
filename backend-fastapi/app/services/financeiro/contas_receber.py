# ---------------------------------------------------------------------------
# ARQUIVO: services/financeiro/contas_receber.py
# DESCRICAO: Financeiro - contas a receber: leitura, criacao, edicao, baixa,
#            estorno e historico.
# ---------------------------------------------------------------------------

"""(Texto de quando era services/financeiro_receber.py; desde 12/10/2026 o financeiro e o pacote services/financeiro/.)

O dinheiro que a loja tem A RECEBER, e o dia em que ele chega.

A conciliação mora aqui, e não num arquivo próprio, porque ela é uma baixa em
lote: reusa `receber_conta` uma vez por cobrança, e é isso que garante que o
lote gere o mesmo movimento, a mesma trilha e o mesmo estorno da baixa manual.

Separado de `services/financeiro.py` em 29/08/2026 por um limite de ferramenta:
o arquivo original passou de 79 KB e o PyArmor (licença trial) recusa ofuscar
acima de ~55 KB, quebrando a geração do sidecar. O corte seguiu as seções que
já existiam no arquivo — nenhuma regra mudou de lugar dentro delas.
"""

from datetime import date
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.core.enum import (
    ContaReceberStatus,
    MovimentacaoFinanceiraOrigem,
    MovimentacaoFinanceiraTipo,
)
from app.core.tempo import hoje_local, inicio_do_dia_utc
from app.db.crud import financeiro as financeiro_crud
from app.db.crud import sessao_caixa as caixa_crud
from app.db.models.conta_receber import ContaReceber
from app.helpers.exceptions import BadRequestException, NotFoundException
from app.services.financeiro.comum import ENTIDADE_CONTA_RECEBER, _funcionario_do_token, _nome_do_cliente
from app.services.financeiro.contas_bancarias import _conta_padrao_id


# ===========================================================================
# CONTAS A RECEBER — leitura, baixa e estorno
#
# Espelho do contas a pagar. Onde a regra é a mesma, o código é o mesmo com os
# nomes trocados -- de propósito: quem entende um lado entende o outro, e o dia
# em que a regra mudar, muda igual nos dois.
# ===========================================================================

def _serializar_receber(conta: ContaReceber, hoje: date) -> Dict[str, Any]:
    pendente = conta.status == ContaReceberStatus.PENDENTE.value
    return {
        "id": conta.id,
        "descricao": conta.descricao,
        "valor": conta.valor,
        "taxa": conta.taxa,
        "juros": conta.juros,
        "juros_destino": conta.juros_destino,
        "vencimento": conta.vencimento,
        "status": conta.status,
        "cliente_id": conta.cliente_id,
        "cliente_nome": _nome_do_cliente(conta.cliente),
        "valor_recebido": conta.valor_recebido,
        "recebido_em": conta.recebido_em,
        "conta_bancaria_id": conta.conta_bancaria_id,
        "conta_bancaria_nome": conta.conta_bancaria.nome if conta.conta_bancaria else None,
        "forma_pagamento_id": conta.forma_pagamento_id,
        "venda_pagamento_id": conta.venda_pagamento_id,
        "ordem_servico_pagamento_id": conta.ordem_servico_pagamento_id,
        # "Automática" = reflexo de um documento fechado. A tela usa para não
        # oferecer edição livre de algo que a venda ou a OS já decidiu.
        "automatica": bool(conta.venda_pagamento_id or conta.ordem_servico_pagamento_id),
        "observacao": conta.observacao,
        "criado_em": conta.criado_em,
        "vencida": bool(pendente and conta.vencimento < hoje),
        "dias_para_vencer": (conta.vencimento - hoje).days if pendente else None,
    }


def listar_contas_receber(
    db: Session,
    empresa_id: int,
    *,
    status: Optional[str] = None,
    inicio: Optional[date] = None,
    fim: Optional[date] = None,
    cliente_id: Optional[int] = None,
    busca: Optional[str] = None,
    vencidas: bool = False,
    limit: int = 200,
    offset: int = 0,
) -> Dict[str, Any]:
    hoje = hoje_local()

    # Mesma regra do a pagar: fiado atrasado é de mês anterior quase por
    # definição, então o recorte de vencidas ignora o mês visto.
    if vencidas:
        inicio = fim = None

    itens, total_itens = financeiro_crud.listar_contas_receber(
        db, empresa_id, status=status, inicio=inicio, fim=fim,
        cliente_id=cliente_id, busca=busca, vencidas=vencidas,
        limit=limit, offset=offset,
    )
    pendente, recebido, vencido = financeiro_crud.totais_contas_receber(
        db, empresa_id, hoje=hoje, inicio=inicio, fim=fim,
        cliente_id=cliente_id, busca=busca, vencidas=vencidas,
    )
    return {
        "itens": [_serializar_receber(c, hoje) for c in itens],
        "total_itens": total_itens,
        "total_pendente": pendente,
        "total_recebido": recebido,
        "total_vencido": vencido,
    }


def get_conta_receber(db: Session, empresa_id: int, conta_id: int) -> Dict[str, Any]:
    conta = financeiro_crud.get_conta_receber(db, empresa_id, conta_id)
    if not conta:
        raise NotFoundException(detail="Conta não encontrada")
    return _serializar_receber(conta, hoje_local())


def criar_conta_receber(
    db: Session, empresa_id: int, dados, usuario_token: Dict[str, Any]
) -> Dict[str, Any]:
    """Lançamento manual — o que não passou pela venda nem pela OS.

    A maioria das contas a receber nasce sozinha, do fecho. Esta porta existe
    para o cliente que já devia antes do módulo existir, ou para um acerto
    combinado fora do balcão.
    """
    conta = financeiro_crud.criar_conta_receber(
        db,
        ContaReceber(
            empresa_id=empresa_id,
            descricao=dados.descricao.strip(),
            valor=dados.valor,
            taxa=dados.taxa,
            vencimento=dados.vencimento,
            cliente_id=dados.cliente_id,
            observacao=dados.observacao,
            status=ContaReceberStatus.PENDENTE.value,
        ),
    )
    func_id, func_nome = _funcionario_do_token(usuario_token)
    financeiro_crud.registrar_historico(
        db, empresa_id=empresa_id, entidade=ENTIDADE_CONTA_RECEBER, entidade_id=conta.id,
        campo="criacao", valor_antigo=None, valor_novo=conta.descricao,
        funcionario_id=func_id, funcionario_nome=func_nome,
    )
    db.refresh(conta)
    return _serializar_receber(conta, hoje_local())


CAMPOS_AUDITADOS_RECEBER = ("valor", "vencimento", "cliente_id", "taxa")


def atualizar_conta_receber(
    db: Session, empresa_id: int, conta_id: int, dados, usuario_token: Dict[str, Any]
) -> Dict[str, Any]:
    conta = financeiro_crud.get_conta_receber(db, empresa_id, conta_id)
    if not conta:
        raise NotFoundException(detail="Conta não encontrada")
    if conta.status == ContaReceberStatus.RECEBIDA.value:
        raise BadRequestException(
            detail="Esta conta já foi recebida. Estorne o recebimento antes de alterá-la."
        )

    func_id, func_nome = _funcionario_do_token(usuario_token)
    for campo, novo in dados.model_dump(exclude_unset=True).items():
        antigo = getattr(conta, campo)
        if antigo == novo:
            continue
        if campo in CAMPOS_AUDITADOS_RECEBER:
            financeiro_crud.registrar_historico(
                db, empresa_id=empresa_id, entidade=ENTIDADE_CONTA_RECEBER,
                entidade_id=conta.id, campo=campo,
                valor_antigo=str(antigo) if antigo is not None else None,
                valor_novo=str(novo) if novo is not None else None,
                funcionario_id=func_id, funcionario_nome=func_nome,
            )
        setattr(conta, campo, novo.strip() if isinstance(novo, str) else novo)

    db.flush()
    db.refresh(conta)
    return _serializar_receber(conta, hoje_local())


def cancelar_conta_receber(
    db: Session, empresa_id: int, conta_id: int, usuario_token: Dict[str, Any]
) -> Dict[str, Any]:
    """Cancela em vez de excluir. Dívida perdoada continua sendo história."""
    conta = financeiro_crud.get_conta_receber(db, empresa_id, conta_id)
    if not conta:
        raise NotFoundException(detail="Conta não encontrada")
    if conta.status == ContaReceberStatus.RECEBIDA.value:
        raise BadRequestException(
            detail="Esta conta já foi recebida. Estorne o recebimento antes de cancelá-la."
        )

    func_id, func_nome = _funcionario_do_token(usuario_token)
    financeiro_crud.registrar_historico(
        db, empresa_id=empresa_id, entidade=ENTIDADE_CONTA_RECEBER, entidade_id=conta.id,
        campo="status", valor_antigo=conta.status,
        valor_novo=ContaReceberStatus.CANCELADA.value,
        funcionario_id=func_id, funcionario_nome=func_nome,
    )
    conta.status = ContaReceberStatus.CANCELADA.value
    db.flush()
    db.refresh(conta)
    return _serializar_receber(conta, hoje_local())


def receber_conta(
    db: Session, empresa_id: int, conta_id: int, dados, usuario_token: Dict[str, Any]
) -> Dict[str, Any]:
    """Dá baixa: a promessa vira dinheiro, e o livro registra a ENTRADA.

    É o momento que o fecho da venda já deixava marcado no código -- "o
    movimento nasce no dia em que o cliente pagar". Origem RECEBIMENTO,
    reservada para isto desde a primeira versão do enum.

    `sessao_caixa_id` fica NULO, como no pagamento de conta a pagar: quitar uma
    dívida antiga não é venda no PDV. Se o dinheiro entrou na gaveta, o operador
    lança um suprimento -- contar as duas coisas faria a gaveta fechar com sobra.
    """
    conta = financeiro_crud.get_conta_receber(db, empresa_id, conta_id)
    if not conta:
        raise NotFoundException(detail="Conta não encontrada")
    if conta.status == ContaReceberStatus.RECEBIDA.value:
        raise BadRequestException(detail="Esta conta já foi recebida.")
    if conta.status == ContaReceberStatus.CANCELADA.value:
        raise BadRequestException(detail="Esta conta foi cancelada e não pode ser recebida.")

    # O padrão já soma os juros: quem cobrou multa quer receber o total, e
    # obrigar a redigitar a soma convida ao erro de conta na hora do balcão.
    juros = dados.juros or 0
    destino = getattr(dados.juros_destino, "value", dados.juros_destino) or "LOJA"
    valor_recebido = (
        dados.valor_recebido if dados.valor_recebido is not None else conta.valor + juros
    )
    dia = dados.recebido_em or hoje_local()

    # QUANTO ENTROU DE FATO NA LOJA. Quando o juros é da maquininha, o cliente
    # desembolsa o total mas esse pedaço vai para a operadora -- lançar tudo
    # faria o sistema mostrar saldo que a conta bancária não tem, e o caixa
    # fecharia com sobra todo dia em que houvesse parcelamento.
    valor_para_a_loja = (
        valor_recebido - juros if destino == "OPERADORA" else valor_recebido
    )

    if dados.conta_bancaria_id is not None:
        if not financeiro_crud.get_conta_bancaria(db, empresa_id, dados.conta_bancaria_id):
            raise BadRequestException(detail="Conta bancária não encontrada")

    func_id, func_nome = _funcionario_do_token(usuario_token)

    # A conta escolhida, ou a principal da loja. NUNCA nenhuma: desde que o saldo
    # passou a ser derivado do livro, movimento sem conta é dinheiro que entrou e
    # não aparece em saldo nenhum.
    conta_destino_id = dados.conta_bancaria_id or _conta_padrao_id(db, empresa_id)

    movimento = caixa_crud.registrar_movimento(
        db,
        tipo=MovimentacaoFinanceiraTipo.ENTRADA,
        origem=MovimentacaoFinanceiraOrigem.RECEBIMENTO,
        valor=valor_para_a_loja,
        conta_bancaria_id=conta_destino_id,
        forma_pagamento_id=dados.forma_pagamento_id,
        funcionario_id=func_id,
        funcionario_nome=func_nome,
        motivo=(
            f"Recebimento: {conta.descricao}"
            + (f" (juros de {juros} retido pela operadora)" if destino == "OPERADORA" else "")
        ),
    )

    conta.status = ContaReceberStatus.RECEBIDA.value
    # `valor_recebido` é o que o CLIENTE desembolsou; o livro guarda o que
    # entrou na loja. Os dois só divergem quando o juros é da operadora, e
    # guardar os dois é o que permite explicar a diferença depois.
    conta.valor_recebido = valor_recebido
    conta.juros = juros
    conta.juros_destino = destino
    conta.recebido_em = inicio_do_dia_utc(dia)
    # A conta RESOLVIDA, pela mesma razao do gemeo em contas a pagar.
    conta.conta_bancaria_id = conta_destino_id
    conta.forma_pagamento_id = dados.forma_pagamento_id
    conta.movimentacao_financeira_id = movimento.id
    if dados.observacao:
        conta.observacao = dados.observacao

    financeiro_crud.registrar_historico(
        db, empresa_id=empresa_id, entidade=ENTIDADE_CONTA_RECEBER, entidade_id=conta.id,
        campo="baixa", valor_antigo=ContaReceberStatus.PENDENTE.value,
        valor_novo=f"RECEBIDA {valor_recebido}",
        funcionario_id=func_id, funcionario_nome=func_nome,
    )

    db.flush()
    db.refresh(conta)
    return _serializar_receber(conta, hoje_local())


def estornar_recebimento(
    db: Session, empresa_id: int, conta_id: int, dados, usuario_token: Dict[str, Any]
) -> Dict[str, Any]:
    """Desfaz a baixa sem apagar o lançamento. Ver o gêmeo em contas a pagar."""
    conta = financeiro_crud.get_conta_receber(db, empresa_id, conta_id)
    if not conta:
        raise NotFoundException(detail="Conta não encontrada")
    if conta.status != ContaReceberStatus.RECEBIDA.value:
        raise BadRequestException(detail="Só é possível estornar uma conta recebida.")

    func_id, func_nome = _funcionario_do_token(usuario_token)
    # Devolve o que ENTROU na loja, não o que o cliente desembolsou: o juros da
    # operadora nunca virou movimento, então estorná-lo tiraria do caixa
    # dinheiro que nunca esteve lá.
    valor = conta.valor_recebido or conta.valor
    if conta.juros_destino == "OPERADORA":
        valor -= conta.juros

    caixa_crud.registrar_movimento(
        db,
        tipo=MovimentacaoFinanceiraTipo.SAIDA,
        origem=MovimentacaoFinanceiraOrigem.RECEBIMENTO,
        valor=valor,
        # A MESMA conta da baixa: devolver noutra deixaria uma com sobra e a
        # outra com falta, e a soma até fecharia -- o erro só apareceria no dia
        # em que o dono conferisse conta por conta.
        conta_bancaria_id=conta.conta_bancaria_id or _conta_padrao_id(db, empresa_id),
        forma_pagamento_id=conta.forma_pagamento_id,
        funcionario_id=func_id,
        funcionario_nome=func_nome,
        motivo=f"Estorno de recebimento: {conta.descricao} — {dados.motivo}",
    )

    financeiro_crud.registrar_historico(
        db, empresa_id=empresa_id, entidade=ENTIDADE_CONTA_RECEBER, entidade_id=conta.id,
        campo="estorno", valor_antigo=f"RECEBIDA {valor}",
        valor_novo=f"PENDENTE — {dados.motivo}",
        funcionario_id=func_id, funcionario_nome=func_nome,
    )

    conta.status = ContaReceberStatus.PENDENTE.value
    conta.valor_recebido = None
    # O juros some junto: ele foi cobrado por causa daquele recebimento, e
    # deixá-lo para trás faria a próxima baixa somar multa duas vezes.
    conta.juros = 0
    conta.juros_destino = "LOJA"
    conta.recebido_em = None
    conta.conta_bancaria_id = None
    conta.forma_pagamento_id = None
    conta.movimentacao_financeira_id = None

    db.flush()
    db.refresh(conta)
    return _serializar_receber(conta, hoje_local())


def listar_historico_do_recebimento(db: Session, empresa_id: int, conta_id: int):
    conta = financeiro_crud.get_conta_receber(db, empresa_id, conta_id)
    if not conta:
        raise NotFoundException(detail="Conta não encontrada")
    return financeiro_crud.listar_historico(db, empresa_id, ENTIDADE_CONTA_RECEBER, conta_id)
