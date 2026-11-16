# ---------------------------------------------------------------------------
# ARQUIVO: services/financeiro/conciliacao.py
# DESCRICAO: Financeiro - baixa automatica do dinheiro da maquininha no dia e
#            conciliacao em lote (reusa receber_conta, uma vez por cobranca).
# ---------------------------------------------------------------------------

import logging
from datetime import date
from typing import Any, Dict, List, Optional, Sequence
from sqlalchemy.orm import Session
from app.core.enum import (
    ContaReceberStatus,
)
from app.core.tempo import hoje_local
from app.db.crud import financeiro as financeiro_crud
from app.db.models.conta_receber import ContaReceber
from app.helpers.exceptions import BadRequestException
from app.schemas.financeiro import ContaReceberBaixa
from app.schemas.financeiro import (
    Conciliacao,
    ConciliacaoDia,
    ConciliacaoItem,
    ConciliacaoResultado,
)
from app.services.financeiro.comum import _nome_do_cliente
from app.services.financeiro.contas_receber import receber_conta

logger = logging.getLogger(__name__)


# ===========================================================================
# CONCILIAÇÃO (Onda 4)
# ===========================================================================

# ===========================================================================
# BAIXA AUTOMÁTICA — o dinheiro da maquininha entrando no dia
# ===========================================================================

def baixar_automaticas(db: Session, hoje: Optional[date] = None) -> int:
    """Dá baixa nas cobranças que o dono declarou que caem sozinhas. Devolve quantas.

    SÓ ALCANÇA O QUE NASCEU MARCADO (`baixa_automatica`), e a marca só é posta
    quando a FORMA de pagamento tem prazo declarado -- ou seja, dinheiro de
    operadora. Fiado nunca entra aqui, e essa é a linha que separa "o dono
    declarou que a maquininha deposita em D+1" de "inventar que o cliente
    pagou".

    VENCIMENTO <= HOJE, e não "= hoje". É o que faz a tarefa se recuperar
    sozinha: a loja fecha na sexta e só abre na segunda, e as trêss cobranças do
    fim de semana entram todas de uma vez no boot de segunda. Uma tarefa que
    olhasse só o dia de hoje perderia todo dia em que a máquina ficou desligada
    -- que é o defeito clássico de agendamento em máquina de loja.

    IDEMPOTENTE por construção: a baixa muda o status para RECEBIDA e a consulta
    só pega PENDENTE. Rodar duas vezes no mesmo minuto não duplica nada.

    UMA FALHA NÃO DERRUBA AS OUTRAS. Cada cobrança é uma transação: se a
    terceira tiver um problema, a primeira e a segunda já entraram e a quarta
    ainda entra. O contrário deixaria o caixa do dia inteiro travado por causa
    de uma linha ruim.
    """
    hoje = hoje or hoje_local()
    pendentes = financeiro_crud.listar_baixas_automaticas_vencidas(db, hoje=hoje)
    if not pendentes:
        return 0

    formas = financeiro_crud.formas_de_origem_completas(
        db,
        venda_pagamento_ids=[c.venda_pagamento_id for c in pendentes if c.venda_pagamento_id],
        os_pagamento_ids=[
            c.ordem_servico_pagamento_id for c in pendentes if c.ordem_servico_pagamento_id
        ],
    )

    baixadas = 0
    for conta in pendentes:
        forma = formas.get(
            conta.venda_pagamento_id or -1
        ) or formas.get(conta.ordem_servico_pagamento_id or -1)
        try:
            receber_conta(
                db,
                conta.empresa_id,
                conta.id,
                ContaReceberBaixa(
                    # O valor PREVISTO, sem juros. A taxa da maquininha só se
                    # conhece no extrato, e inventá-la aqui seria pior que
                    # deixar o dono acertar na Conciliação -- que existe
                    # exatamente para isso e já rateia a diferença.
                    valor_recebido=int(conta.valor or 0),
                    recebido_em=conta.vencimento,
                    forma_pagamento_id=getattr(forma, "id", None),
                    # A conta que a forma declarou; NULL cai na principal.
                    conta_bancaria_id=getattr(forma, "conta_bancaria_id", None),
                    observacao="Baixa automática: prazo declarado na forma de pagamento.",
                ),
                # Sem funcionário: não houve gente. O rastro fica na observação
                # e no histórico, e um nome inventado aqui seria pior que o vazio.
                {},
            )
            db.commit()
            baixadas += 1
        except Exception:
            db.rollback()
            logger.exception(
                "Falha na baixa automática da cobrança %s", conta.id
            )

    return baixadas


def _formas_de_origem(db: Session, contas: Sequence[ContaReceber]) -> Dict[int, Optional[str]]:
    """Mapa conta_id -> nome da forma que originou a cobrança."""
    por_venda, por_os = financeiro_crud.formas_de_origem(
        db,
        venda_pagamento_ids=[c.venda_pagamento_id for c in contas if c.venda_pagamento_id],
        os_pagamento_ids=[
            c.ordem_servico_pagamento_id for c in contas if c.ordem_servico_pagamento_id
        ],
    )
    return {
        c.id: (
            por_venda.get(c.venda_pagamento_id)
            if c.venda_pagamento_id
            else por_os.get(c.ordem_servico_pagamento_id)
            if c.ordem_servico_pagamento_id
            else None
        )
        for c in contas
    }


def get_conciliacao(
    db: Session, empresa_id: int, inicio: date, fim: date
) -> Conciliacao:
    """O que a loja espera receber, agrupado por DIA.

    O agrupamento por dia não é estética: é o formato em que o dinheiro chega.
    A operadora não deposita venda a venda -- deposita o lote do dia, um valor
    só. Conferir item a item contra o extrato é exatamente o trabalho que esta
    tela existe para evitar.

    Só PENDENTES: o que já foi recebido saiu da fila de conferência.
    """
    itens, _total = financeiro_crud.listar_contas_receber(
        db, empresa_id, status=ContaReceberStatus.PENDENTE.value,
        inicio=inicio, fim=fim, limit=1000,
    )
    formas = _formas_de_origem(db, itens)

    por_dia: Dict[date, List[ContaReceber]] = {}
    for conta in itens:
        por_dia.setdefault(conta.vencimento, []).append(conta)

    dias = [
        ConciliacaoDia(
            data=dia,
            quantidade=len(contas),
            total_previsto=sum(int(c.valor or 0) for c in contas),
            itens=[
                ConciliacaoItem(
                    conta_id=c.id,
                    descricao=c.descricao,
                    valor=int(c.valor or 0),
                    cliente_nome=_nome_do_cliente(c.cliente),
                    forma_origem=formas.get(c.id),
                )
                for c in contas
            ],
        )
        for dia, contas in sorted(por_dia.items())
    ]

    return Conciliacao(
        inicio=inicio,
        fim=fim,
        total_previsto=sum(d.total_previsto for d in dias),
        dias=dias,
    )


def baixar_lote(
    db: Session, empresa_id: int, dados, usuario_token: Dict[str, Any]
) -> ConciliacaoResultado:
    """Confere o depósito do dia e dá baixa em TODAS as cobranças daquele lote.

    O depósito é um valor só; as cobranças são várias. O rateio é
    PROPORCIONAL ao previsto de cada uma, e o CENTAVO QUE SOBRA do arredondamento
    vai para a última -- assim a soma das baixas é exatamente o que caiu no
    banco. Dividir igual entre as contas faria uma venda de R$ 20 e outra de
    R$ 400 absorverem a mesma taxa, e o histórico de cada uma mentiria.

    A diferença NÃO vira lançamento à parte: cada conta fica com
    `valor_recebido` menor que o previsto, que é o mesmo mecanismo do
    recebimento parcial já existente ("o cliente devia 200 e trouxe 150"). É o
    que mantém o livro do dinheiro igual ao extrato do banco -- inventar uma
    despesa de taxa por cima faria o sistema mostrar entrada e saída que a
    conta bancária nunca viu.

    Reusa `receber_conta` uma vez por cobrança, e não um caminho próprio: é o
    que garante que o lote gere o mesmo movimento, a mesma trilha de auditoria
    e o mesmo estorno que a baixa feita à mão.
    """
    itens, _total = financeiro_crud.listar_contas_receber(
        db, empresa_id, status=ContaReceberStatus.PENDENTE.value,
        inicio=dados.data, fim=dados.data, limit=1000,
    )
    if not itens:
        raise BadRequestException(
            detail="Não há cobranças pendentes com vencimento nesse dia."
        )

    total_previsto = sum(int(c.valor or 0) for c in itens)
    if total_previsto <= 0:
        raise BadRequestException(detail="O lote deste dia não tem valor a conferir.")

    partes: List[int] = []
    restante = int(dados.valor_recebido)
    for conta in itens[:-1]:
        parte = round(dados.valor_recebido * int(conta.valor or 0) / total_previsto)
        partes.append(parte)
        restante -= parte
    partes.append(restante)

    if any(parte <= 0 for parte in partes):
        raise BadRequestException(
            detail=(
                "O valor informado é pequeno demais para o lote deste dia: alguma "
                "cobrança ficaria com zero. Confira o depósito ou dê baixa nas contas "
                "uma a uma."
            )
        )

    for conta, parte in zip(itens, partes):
        receber_conta(
            db, empresa_id, conta.id,
            ContaReceberBaixa(
                valor_recebido=parte,
                # A data do LOTE, não a de hoje: o dinheiro caiu no dia do
                # repasse, e conciliar com atraso não muda quando ele entrou.
                recebido_em=dados.data,
                conta_bancaria_id=dados.conta_bancaria_id,
                forma_pagamento_id=dados.forma_pagamento_id,
            ),
            usuario_token,
        )

    return ConciliacaoResultado(
        data=dados.data,
        quantidade=len(itens),
        total_previsto=total_previsto,
        total_recebido=int(dados.valor_recebido),
        diferenca=int(dados.valor_recebido) - total_previsto,
    )
