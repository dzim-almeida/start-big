# ---------------------------------------------------------------------------
# ARQUIVO: services/financeiro/promessas.py
# DESCRICAO: Financeiro - venda/OS com vencimento futuro vira conta a receber
#            (chamado por venda.py e ordem_servico.py), e o cancelamento delas.
# ---------------------------------------------------------------------------

from datetime import date, timedelta
from typing import Any, Optional, Sequence
from sqlalchemy.orm import Session
from app.core.enum import (
    ContaReceberStatus,
)
from app.core.tempo import hoje_local
from app.db.crud import financeiro as financeiro_crud
from app.db.models.conta_receber import ContaReceber
from app.services import sessao_caixa as caixa_service
from app.services.financeiro.comum import ENTIDADE_CONTA_RECEBER, _nome_do_cliente


def _prazo_da_forma(pagamento) -> int:
    forma = getattr(pagamento, "forma_pagamento", None)
    return int(getattr(forma, "dias_para_receber", 0) or 0)


def _juros_da_operadora(pagamento) -> int:
    """Quanto do valor cobrado a operadora fica -- o complemento exato de
    `caixa_service.valor_que_entra`, para `bruto = valor + taxa` fechar.

    Derivado da outra em vez de recalculado: se um dia a regra de "quanto
    chega na loja" mudar, as duas mudam juntas e a conta continua fechando.
    """
    return (pagamento.valor or 0) - caixa_service.valor_que_entra(pagamento)


def aplicar_prazo_de_recebimento(db: Session, pagamentos) -> None:
    """Carimba no pagamento o vencimento que a FORMA declarou.

    Dinheiro de cartao nao esta na conta no dia da venda -- a maquininha
    deposita depois. Quem sabe em quantos dias e o dono, e ele declara isso uma
    vez na forma de pagamento em vez de digitar a data em toda venda.

    RODA ANTES de tudo que lanca, e e por isso que ela existe como passo
    separado: `registrar_pagamentos_de_*` e `registrar_promessas_de_*` ja sabem
    ler `pagamento.vencimento` ("promessa: e conta a receber, nao gaveta"), e as
    duas continuam sem saber que prazo existe. O carimbo so preenche a data que
    o operador nao digitou.

    NAO SOBRESCREVE DATA DIGITADA. Se alguem combinou um vencimento especifico
    com o cliente, quem manda e ele -- a forma so diz o padrao.

    Prazo zero (o padrao de toda forma) nao carimba nada, e nada muda: o
    dinheiro entra na hora, como sempre entrou.
    """
    hoje = hoje_local()
    carimbou = False
    for pagamento in pagamentos or []:
        if pagamento.vencimento:
            continue
        dias = _prazo_da_forma(pagamento)
        if dias <= 0:
            continue
        pagamento.vencimento = hoje + timedelta(days=dias)
        carimbou = True

    if carimbou:
        db.flush()


def _criar_promessa(
    db: Session,
    empresa_id: int,
    *,
    descricao: str,
    cliente_id: Optional[int],
    valor: int,
    vencimento: date,
    taxa: int = 0,
    venda_pagamento_id: Optional[int] = None,
    ordem_servico_pagamento_id: Optional[int] = None,
    baixa_automatica: bool = False,
) -> Optional[ContaReceber]:
    """Cria a conta a receber de UM pagamento prometido.

    IDEMPOTENTE. Uma OS reaberta e refinalizada passa de novo pelos mesmos
    pagamentos; sem a checagem, a dívida do cliente dobraria a cada
    refinalização. Mesma lição do `gerada_por_id` na recorrência.

    `baixa_automatica` separa o CARTAO do FIADO. As duas coisas chegam aqui pelo
    mesmo caminho, e só a primeira pode entrar sozinha no vencimento: o dono
    declarou que a operadora deposita em D+n. Cliente não paga por agendamento.
    """
    if financeiro_crud.get_receber_do_pagamento(
        db,
        empresa_id,
        venda_pagamento_id=venda_pagamento_id,
        ordem_servico_pagamento_id=ordem_servico_pagamento_id,
    ):
        return None

    return financeiro_crud.criar_conta_receber(
        db,
        ContaReceber(
            empresa_id=empresa_id,
            descricao=descricao,
            cliente_id=cliente_id,
            valor=valor,
            taxa=taxa,
            vencimento=vencimento,
            status=ContaReceberStatus.PENDENTE.value,
            venda_pagamento_id=venda_pagamento_id,
            ordem_servico_pagamento_id=ordem_servico_pagamento_id,
            baixa_automatica=baixa_automatica,
        ),
    )


def registrar_promessas_de_venda(db: Session, venda) -> None:
    """Transforma em conta a receber cada pagamento de venda com vencimento futuro.

    NÃO decide o que é promessa — só registra. Quem decide já existia:
    `registrar_pagamentos_de_venda` pula o pagamento com vencimento futuro no
    livro do dinheiro, com a regra escrita lá ("promessa: é conta a receber, não
    gaveta"). Esta função é o outro lado dessa frase, que faltava.

    Roda com o caixa LIGADO OU DESLIGADO, ao contrário da irmã do livro: fiado é
    fiado em qualquer loja, e amarrar o contas a receber ao controle de caixa
    esconderia a dívida de quem não usa gaveta.
    """
    funcionario = getattr(venda, "funcionario", None)
    empresa_id = getattr(funcionario, "empresa_id", None)
    if not empresa_id:
        return

    hoje = hoje_local()
    cliente = getattr(venda, "cliente", None)
    nome = _nome_do_cliente(cliente)
    referencia = venda.numero_venda or venda.id

    for pagamento in venda.pagamentos:
        if not pagamento.vencimento or pagamento.vencimento <= hoje:
            continue
        _criar_promessa(
            db,
            empresa_id,
            descricao=f"Venda {referencia}" + (f" — {nome}" if nome else ""),
            cliente_id=venda.cliente_id,
            # LIQUIDO, com o juros da operadora em `taxa`. É o contrato que o
            # model sempre pediu ("`valor` é o que a operadora repassa, já sem a
            # taxa dela"; `bruto = valor + taxa`) e que ninguém cumpria: até
            # 05/09/2026 gravava-se o bruto aqui, e o Fluxo de Caixa prometia em
            # "Vai entrar" um dinheiro que a operadora nunca ia depositar.
            valor=caixa_service.valor_que_entra(pagamento),
            taxa=_juros_da_operadora(pagamento),
            vencimento=pagamento.vencimento,
            venda_pagamento_id=pagamento.id,
            # Prazo declarado na forma = dinheiro de operadora, que cai sozinho.
            # Sem prazo, a data veio de um acordo com o cliente: é fiado, e
            # fiado nunca entra sem alguém confirmar.
            baixa_automatica=_prazo_da_forma(pagamento) > 0,
        )


def registrar_promessas_de_os(db: Session, ordem_servico, pagamentos) -> None:
    """Gêmea da de venda, para a OS.

    `pagamentos` são os desta finalização. A idempotência cobre a refinalização
    de qualquer forma, mas passar só os novos evita consulta à toa.
    """
    funcionario = getattr(ordem_servico, "funcionario", None)
    empresa_id = getattr(funcionario, "empresa_id", None)
    if not empresa_id:
        return

    hoje = hoje_local()
    objeto = getattr(ordem_servico, "equipamento", None)
    cliente = getattr(objeto, "cliente", None)
    nome = _nome_do_cliente(cliente)
    cliente_id = getattr(cliente, "id", None)

    for pagamento in pagamentos:
        if not pagamento.vencimento or pagamento.vencimento <= hoje:
            continue
        _criar_promessa(
            db,
            empresa_id,
            descricao=f"OS {ordem_servico.numero_os}" + (f" — {nome}" if nome else ""),
            cliente_id=cliente_id,
            # Líquido + taxa, igual à gêmea da venda. Ver o comentário de lá.
            valor=caixa_service.valor_que_entra(pagamento),
            taxa=_juros_da_operadora(pagamento),
            vencimento=pagamento.vencimento,
            ordem_servico_pagamento_id=pagamento.id,
            baixa_automatica=_prazo_da_forma(pagamento) > 0,
        )


def cancelar_promessas_do_documento(
    db: Session,
    *,
    empresa_id: Optional[int],
    venda_pagamentos: Optional[Sequence[Any]] = None,
    ordem_servico_pagamentos: Optional[Sequence[Any]] = None,
) -> int:
    """Derruba as cobrancas em aberto que este documento tinha gerado.

    O BURACO QUE ELA FECHA (achado pelo dono em 05/09/2026, na loja): cancelar
    uma OS ou reabri-la sem pagamento mexia no estoque e no livro do dinheiro,
    mas NAO no contas a receber. A promessa ficava PENDENTE para sempre.

    O sintoma na tela foi uma OS cancelada e refeita: a Conciliacao passou a
    prometer os dois valores no mesmo dia, e o "a receber em aberto" somou uma
    divida que nao existia. Pior, na reabertura os pagamentos sao apagados e a
    FK e `ondelete=SET NULL` -- a cobranca perdia ate o vinculo com a origem e
    passava a aparecer como "lancada a mao", sem forma de rastrear de onde veio.

    ⚠️ CHAMAR ANTES DE `pagamentos.clear()`. Depois do clear o vinculo ja foi a
    zero e nao ha mais como achar as linhas.

    SO PENDENTE. Cobranca ja RECEBIDA virou dinheiro no livro: cancela-la faria
    o caixa fechar com falta. Para desfazer aquela existe o estorno.

    CANCELA, nao apaga -- mesma regra do resto do modulo. "Sumiu uma cobranca de
    R$ 290" precisa ter resposta, e a linha cancelada continua no historico.
    """
    if not empresa_id:
        return 0

    ids = [p.id for p in (venda_pagamentos or ordem_servico_pagamentos or []) if p.id]
    if not ids:
        return 0

    contas = financeiro_crud.listar_receber_pendentes_do_documento(
        db,
        empresa_id,
        venda_pagamento_ids=ids if venda_pagamentos else None,
        ordem_servico_pagamento_ids=ids if ordem_servico_pagamentos else None,
    )
    for conta in contas:
        financeiro_crud.registrar_historico(
            db, empresa_id=empresa_id, entidade=ENTIDADE_CONTA_RECEBER,
            entidade_id=conta.id, campo="status",
            valor_antigo=conta.status, valor_novo=ContaReceberStatus.CANCELADA.value,
            funcionario_id=None, funcionario_nome=None,
        )
        conta.status = ContaReceberStatus.CANCELADA.value

    if contas:
        db.flush()
    return len(contas)
