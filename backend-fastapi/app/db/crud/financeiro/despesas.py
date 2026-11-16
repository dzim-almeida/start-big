# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/financeiro/despesas.py
# DESCRICAO: Financeiro (banco) - totais de despesa (por categoria, pagas,
#            compras de estoque), usados pela visao geral e pela analise.
# ---------------------------------------------------------------------------

from datetime import date
from typing import List, Optional, Tuple
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from app.core.enum import (
    ContaPagarStatus,
    PlanoContaTipo,
)
from app.db.models.conta_pagar import ContaPagar
from app.db.models.plano_conta import PlanoConta


def despesas_por_categoria(
    db: Session, empresa_id: int, inicio: date, fim: date
) -> List[Tuple[Optional[int], Optional[str], int]]:
    """(plano_conta_id, nome, total) do que foi PAGO no período.

    Agrupa pela data de PAGAMENTO e não de vencimento: a pergunta é "para onde
    o dinheiro foi neste mês", e uma conta de março paga em abril saiu do caixa
    em abril.
    """
    linhas = (
        db.query(
            ContaPagar.plano_conta_id,
            PlanoConta.nome,
            func.coalesce(func.sum(ContaPagar.valor_pago), 0),
        )
        .outerjoin(PlanoConta, PlanoConta.id == ContaPagar.plano_conta_id)
        .filter(
            ContaPagar.empresa_id == empresa_id,
            ContaPagar.status == ContaPagarStatus.PAGA.value,
            ContaPagar.pago_em >= inicio,
            ContaPagar.pago_em <= fim,
        )
        .group_by(ContaPagar.plano_conta_id, PlanoConta.nome)
        .all()
    )
    return [(linha[0], linha[1], int(linha[2] or 0)) for linha in linhas]


def _total_pago(db: Session, empresa_id: int, inicio, fim, *, mercadoria: bool) -> int:
    """Soma das contas PAGAS no período, separadas por natureza da categoria.

    A separação é a regra contábil que o módulo passou a respeitar em
    02/09/2026: comprar mercadoria não é despesa, é o dinheiro virando estoque.
    Ela sai do CAIXA (e continua no Fluxo de Caixa e no gráfico de para onde o
    dinheiro foi), mas só sai do LUCRO no dia em que a peça é vendida, pelo CMV.
    Sem isso a mesma peça era descontada duas vezes.

    CONTA SEM CATEGORIA CONTA COMO DESPESA. É o lado seguro do erro: uma compra
    de mercadoria não classificada some do lucro no mês da compra, o que
    subestima o lucro; classificá-la como custo por engano inventaria lucro que
    não existe. Melhor o dono ver lucro menor e ir categorizar.
    """
    q = (
        db.query(func.coalesce(func.sum(ContaPagar.valor_pago), 0))
        .outerjoin(PlanoConta, PlanoConta.id == ContaPagar.plano_conta_id)
        .filter(
            ContaPagar.empresa_id == empresa_id,
            ContaPagar.status == ContaPagarStatus.PAGA.value,
            ContaPagar.pago_em >= inicio,
            ContaPagar.pago_em <= fim,
        )
    )
    e_custo = PlanoConta.tipo == PlanoContaTipo.CUSTO.value
    q = q.filter(e_custo if mercadoria else or_(~e_custo, PlanoConta.id.is_(None)))
    return int(q.scalar() or 0)


def total_despesas_pagas(db: Session, empresa_id: int, inicio, fim) -> int:
    """O que saiu e É despesa: tudo menos compra de mercadoria."""
    return _total_pago(db, empresa_id, inicio, fim, mercadoria=False)


def total_compras_estoque(db: Session, empresa_id: int, inicio, fim) -> int:
    """O que saiu para COMPRAR mercadoria — dinheiro que virou estoque."""
    return _total_pago(db, empresa_id, inicio, fim, mercadoria=True)
