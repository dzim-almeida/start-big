# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/financeiro/contas_receber.py
# DESCRICAO: Financeiro (banco) - contas a receber: consulta, totais,
#            pendentes, criacao e o elo com o pagamento da venda/OS.
# ---------------------------------------------------------------------------

"""(Texto de quando era db/crud/financeiro_receber.py; desde 12/10/2026 o financeiro e o pacote services/financeiro/.)

Separado de `crud/financeiro.py` em 02/09/2026, pelo MESMO motivo que ja tinha
quebrado o service em quatro tres dias antes: o PyArmor da licenca trial recusa
ofuscar modulo acima de um teto de bytecode, e o crud passou dele.

O teto foi MEDIDO, nao chutado: `ordem_servico.py` (53 KB, 17.900 bytes de
bytecode) passa; o crud com 41 KB e 22.300 de bytecode e recusado com "out of
license". Ou seja, a conta nao e o tamanho do arquivo -- e quanto codigo ele
tem. Comentario e docstring nao contam.

Quando o PyArmor virar licenca paga, nada disto precisa voltar: a divisao
segue a mesma costura dos services (pagar de um lado, receber e leitura do
outro) e continua fazendo sentido sozinha.
"""

from datetime import date
from typing import Optional, Sequence, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.core.enum import (
    ContaPagarStatus,
    ContaReceberStatus,
)
from app.db.models.conta_pagar import ContaPagar
from app.db.models.conta_receber import ContaReceber
from app.db.crud.financeiro.contas_pagar import _query_contas


# ===========================================================================
# CONTAS A RECEBER
#
# Espelho do contas a pagar. As consultas sao deliberadamente as mesmas, com os
# nomes trocados: quem ler uma entende a outra, e o dia em que a regra do
# "vencido" mudar, muda igual dos dois lados.
# ===========================================================================

def _query_receber(
    db: Session,
    empresa_id: int,
    *,
    status: Optional[str] = None,
    inicio: Optional[date] = None,
    fim: Optional[date] = None,
    cliente_id: Optional[int] = None,
    busca: Optional[str] = None,
    vencidas: bool = False,
    hoje: Optional[date] = None,
):
    q = db.query(ContaReceber).filter(ContaReceber.empresa_id == empresa_id)
    if status:
        q = q.filter(ContaReceber.status == status)
    if inicio:
        q = q.filter(ContaReceber.vencimento >= inicio)
    if fim:
        q = q.filter(ContaReceber.vencimento <= fim)
    if cliente_id:
        q = q.filter(ContaReceber.cliente_id == cliente_id)
    if busca:
        q = q.filter(ContaReceber.descricao.ilike(f"%{busca.strip()}%"))
    # O mesmo recorte do a pagar, para o alerta de fiado atrasado cair na lista
    # de quem realmente está devendo.
    if vencidas:
        q = q.filter(
            ContaReceber.status == ContaReceberStatus.PENDENTE.value,
            ContaReceber.vencimento < (hoje or date.today()),
        )
    return q


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
) -> Tuple[Sequence[ContaReceber], int]:
    q = _query_receber(
        db, empresa_id, status=status, inicio=inicio, fim=fim,
        cliente_id=cliente_id, busca=busca, vencidas=vencidas,
    )
    total = q.count()
    itens = (
        q.options(joinedload(ContaReceber.cliente), joinedload(ContaReceber.conta_bancaria))
        .order_by(ContaReceber.vencimento.asc(), ContaReceber.id.asc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return itens, total


def totais_contas_receber(
    db: Session,
    empresa_id: int,
    *,
    hoje: date,
    inicio: Optional[date] = None,
    fim: Optional[date] = None,
    cliente_id: Optional[int] = None,
    busca: Optional[str] = None,
    vencidas: bool = False,
) -> Tuple[int, int, int]:
    """(pendente, recebido, vencido) — sem o recorte de status, como no pagar."""
    def _soma(coluna, *extra):
        q = _query_receber(
            db, empresa_id, inicio=inicio, fim=fim, cliente_id=cliente_id, busca=busca,
            vencidas=vencidas, hoje=hoje,
        )
        for condicao in extra:
            q = q.filter(condicao)
        return q.with_entities(func.coalesce(func.sum(coluna), 0)).scalar() or 0

    pendente = _soma(ContaReceber.valor, ContaReceber.status == ContaReceberStatus.PENDENTE.value)
    recebido = _soma(
        ContaReceber.valor_recebido, ContaReceber.status == ContaReceberStatus.RECEBIDA.value
    )
    vencido = _soma(
        ContaReceber.valor,
        ContaReceber.status == ContaReceberStatus.PENDENTE.value,
        ContaReceber.vencimento < hoje,
    )
    return int(pendente), int(recebido), int(vencido)


def pendentes_por_vencimento(
    db: Session, empresa_id: int, *, inicio: date, fim: date
) -> Tuple[Sequence[ContaPagar], Sequence[ContaReceber]]:
    """As duas pontas do fluxo no mesmo recorte de vencimento, já ordenadas.

    Sai das MESMAS queries base da listagem e dos totais (`_query_contas` e
    `_query_receber`): se o fluxo filtrasse por conta própria, um documento
    poderia aparecer na tela de Contas a Pagar e sumir da projeção — e um fluxo
    de caixa que discorda da lista não serve para decidir nada.
    """
    pagar = (
        _query_contas(db, empresa_id, status=ContaPagarStatus.PENDENTE.value,
                      inicio=inicio, fim=fim)
        .order_by(ContaPagar.vencimento.asc(), ContaPagar.id.asc())
        .all()
    )
    receber = (
        _query_receber(db, empresa_id, status=ContaReceberStatus.PENDENTE.value,
                       inicio=inicio, fim=fim)
        .order_by(ContaReceber.vencimento.asc(), ContaReceber.id.asc())
        .all()
    )
    return pagar, receber


def get_conta_receber(db: Session, empresa_id: int, conta_id: int) -> Optional[ContaReceber]:
    return (
        db.query(ContaReceber)
        .options(joinedload(ContaReceber.cliente), joinedload(ContaReceber.conta_bancaria))
        .filter(ContaReceber.id == conta_id, ContaReceber.empresa_id == empresa_id)
        .first()
    )


def criar_conta_receber(db: Session, conta: ContaReceber) -> ContaReceber:
    db.add(conta)
    db.flush()
    return conta


def get_receber_do_pagamento(
    db: Session,
    empresa_id: int,
    *,
    venda_pagamento_id: Optional[int] = None,
    ordem_servico_pagamento_id: Optional[int] = None,
) -> Optional[ContaReceber]:
    """A conta a receber que este pagamento ja originou, se houver.

    E o que torna a geracao IDEMPOTENTE: uma OS reaberta e refinalizada passa de
    novo pelos mesmos pagamentos, e sem esta checagem a divida do cliente
    dobraria a cada refinalizacao.
    """
    q = db.query(ContaReceber).filter(ContaReceber.empresa_id == empresa_id)
    if venda_pagamento_id is not None:
        q = q.filter(ContaReceber.venda_pagamento_id == venda_pagamento_id)
    elif ordem_servico_pagamento_id is not None:
        q = q.filter(ContaReceber.ordem_servico_pagamento_id == ordem_servico_pagamento_id)
    else:
        return None
    return q.first()


def total_recebido(db: Session, empresa_id: int, inicio, fim) -> int:
    total = (
        db.query(func.coalesce(func.sum(ContaReceber.valor_recebido), 0))
        .filter(
            ContaReceber.empresa_id == empresa_id,
            ContaReceber.status == ContaReceberStatus.RECEBIDA.value,
            ContaReceber.recebido_em >= inicio,
            ContaReceber.recebido_em <= fim,
        )
        .scalar()
    )
    return int(total or 0)


def listar_receber_pendentes_do_documento(
    db: Session,
    empresa_id: int,
    *,
    venda_pagamento_ids: Optional[Sequence[int]] = None,
    ordem_servico_pagamento_ids: Optional[Sequence[int]] = None,
) -> Sequence[ContaReceber]:
    """As promessas AINDA EM ABERTO geradas por estes pagamentos.

    Serve ao cancelamento do documento que as criou. So PENDENTE de proposito:
    cobranca ja RECEBIDA virou dinheiro no livro, e apaga-la faria o caixa
    fechar com falta -- para desfazer aquela existe o estorno.
    """
    ids = list(venda_pagamento_ids or ordem_servico_pagamento_ids or [])
    if not ids:
        return []

    coluna = (
        ContaReceber.venda_pagamento_id
        if venda_pagamento_ids
        else ContaReceber.ordem_servico_pagamento_id
    )
    return (
        db.query(ContaReceber)
        .filter(
            ContaReceber.empresa_id == empresa_id,
            coluna.in_(ids),
            ContaReceber.status == ContaReceberStatus.PENDENTE.value,
        )
        .all()
    )
