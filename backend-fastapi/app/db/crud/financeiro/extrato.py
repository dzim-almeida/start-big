# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/financeiro/extrato.py
# DESCRICAO: Financeiro (banco) - extrato: o livro do dinheiro linha a linha.
# ---------------------------------------------------------------------------

from typing import Optional, Sequence, Tuple
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload
from app.core.enum import (
    MovimentacaoFinanceiraTipo,
)
from app.db.models.conta_bancaria import ContaBancaria
from app.db.models.funcionario import Funcionario
from app.db.models.movimentacao_financeira import MovimentacaoFinanceira
from app.db.models.ordem_servico import OrdemServico
from app.db.models.ordem_servico_pagamento import OrdemServicoPagamento
from app.db.models.venda import Venda
from app.db.models.venda_pagamento import PagamentoVenda


# ===========================================================================
# EXTRATO — o livro do dinheiro, linha a linha
# ===========================================================================

def _query_extrato(
    db: Session,
    empresa_id: int,
    *,
    inicio=None,
    fim=None,
    tipo: Optional[str] = None,
    origem: Optional[str] = None,
):
    """Base do extrato, com o recorte de empresa feito à mão.

    `movimentacoes_financeiras` NÃO TEM `empresa_id` -- ela nasceu para o
    fechamento de caixa, onde a sessão já dizia de quem era. Aqui a empresa é
    alcançada pelo funcionário ou pela conta bancária da linha.

    A linha SEM funcionário E SEM conta bancária entra assim mesmo, e isso é
    deliberado: uma instalação atende UMA loja (a licença é por máquina), e
    esconder dinheiro de um extrato é pior do que o risco teórico de mostrar
    dinheiro de outra empresa num banco que nunca vai existir em campo. Um
    extrato que omite linha em silêncio não serve para auditoria nenhuma.
    """
    q = (
        db.query(MovimentacaoFinanceira)
        .outerjoin(
            Funcionario, Funcionario.id == MovimentacaoFinanceira.funcionario_id
        )
        .outerjoin(
            ContaBancaria,
            ContaBancaria.id == MovimentacaoFinanceira.conta_bancaria_id,
        )
        .filter(
            or_(
                Funcionario.empresa_id == empresa_id,
                ContaBancaria.empresa_id == empresa_id,
                and_(
                    MovimentacaoFinanceira.funcionario_id.is_(None),
                    MovimentacaoFinanceira.conta_bancaria_id.is_(None),
                ),
            )
        )
    )

    # Filtra por `criado_em`, que é o instante em que o dinheiro ANDOU. O
    # extrato não tem "vencimento": aqui tudo já aconteceu.
    if inicio is not None:
        q = q.filter(MovimentacaoFinanceira.criado_em >= inicio)
    if fim is not None:
        q = q.filter(MovimentacaoFinanceira.criado_em <= fim)
    if tipo:
        q = q.filter(MovimentacaoFinanceira.tipo == tipo)
    if origem:
        q = q.filter(MovimentacaoFinanceira.origem == origem)

    return q


def listar_extrato(
    db: Session,
    empresa_id: int,
    *,
    inicio=None,
    fim=None,
    tipo: Optional[str] = None,
    origem: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
) -> Tuple[Sequence[MovimentacaoFinanceira], int]:
    q = _query_extrato(db, empresa_id, inicio=inicio, fim=fim, tipo=tipo, origem=origem)
    total = q.count()
    itens = (
        q.options(joinedload(MovimentacaoFinanceira.forma_pagamento))
        # Mais recente primeiro: quem abre um extrato quer ver o que acabou de
        # acontecer. O `id` desempata o mesmo instante, que é comum num lote.
        .order_by(
            MovimentacaoFinanceira.criado_em.desc(), MovimentacaoFinanceira.id.desc()
        )
        .limit(limit)
        .offset(offset)
        .all()
    )
    return itens, total


def totais_extrato(
    db: Session,
    empresa_id: int,
    *,
    inicio=None,
    fim=None,
    tipo: Optional[str] = None,
    origem: Optional[str] = None,
) -> Tuple[int, int]:
    """(entradas, saidas) do MESMO filtro da lista, pela mesma query base."""
    def _soma(valor_tipo: str) -> int:
        return int(
            _query_extrato(
                db, empresa_id, inicio=inicio, fim=fim, tipo=tipo, origem=origem
            )
            .filter(MovimentacaoFinanceira.tipo == valor_tipo)
            .with_entities(func.coalesce(func.sum(MovimentacaoFinanceira.valor), 0))
            .scalar()
            or 0
        )

    return _soma(MovimentacaoFinanceiraTipo.ENTRADA.value), _soma(
        MovimentacaoFinanceiraTipo.SAIDA.value
    )


def documentos_de_origem(
    db: Session, *, venda_pagamento_ids: Sequence[int], os_pagamento_ids: Sequence[int]
) -> Tuple[dict, dict]:
    """Numero da venda / da OS que originou cada movimento, em duas consultas.

    "Entrou R$ 25" nao serve para auditoria; "entrou R$ 25 da venda 3" serve.
    """
    por_venda: dict = {}
    por_os: dict = {}

    if venda_pagamento_ids:
        linhas = (
            db.query(PagamentoVenda.id, Venda.numero_venda)
            .join(Venda, Venda.id == PagamentoVenda.venda_id)
            .filter(PagamentoVenda.id.in_(venda_pagamento_ids))
            .all()
        )
        por_venda = {pid: numero for pid, numero in linhas}

    if os_pagamento_ids:
        linhas = (
            db.query(OrdemServicoPagamento.id, OrdemServico.numero_os)
            .join(
                OrdemServico,
                OrdemServico.id == OrdemServicoPagamento.ordem_servico_id,
            )
            .filter(OrdemServicoPagamento.id.in_(os_pagamento_ids))
            .all()
        )
        por_os = {pid: numero for pid, numero in linhas}

    return por_venda, por_os
