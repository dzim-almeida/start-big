# ---------------------------------------------------------------------------
# ARQUIVO: crud/forma_pagamento.py
# DESCRICAO: Queries SQL via SQLAlchemy para o catálogo de Formas de Pagamento.
#
# FormaPagamento é um catálogo global do sistema, independente de OS.
# As funções aqui são usadas tanto pelo endpoint de FormaPagamento quanto
# pelo service de OS ao validar pagamentos na finalização.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Sequence

from app.db.models.forma_pagamento import FormaPagamento as FormaPagamentoModel


# ===========================================================================
# LEITURA (READ)
# ===========================================================================

def get_forma_pagamento_by_id(db: Session, fp_id: int) -> FormaPagamentoModel | None:
    """Busca uma forma de pagamento pelo ID. Retorna None se não encontrada."""
    return db.scalar(select(FormaPagamentoModel).where(FormaPagamentoModel.id == fp_id))


def get_forma_pagamento_by_nome(db: Session, nome: str) -> FormaPagamentoModel | None:
    """Busca uma forma de pagamento pelo nome (case-insensitive). Usado para verificar duplicatas."""
    return db.scalar(
        select(FormaPagamentoModel).where(FormaPagamentoModel.nome.ilike(nome))
    )


def get_formas_pagamento(db: Session) -> Sequence[FormaPagamentoModel]:
    """Retorna todas as formas de pagamento (ativas e inativas) ordenadas por nome."""
    return db.scalars(
        select(FormaPagamentoModel).order_by(FormaPagamentoModel.nome)
    ).all()


# ===========================================================================
# ESCRITA (CREATE / UPDATE)
# ===========================================================================

def create_forma_pagamento(db: Session, fp_to_add: FormaPagamentoModel) -> FormaPagamentoModel:
    """Persiste uma nova forma de pagamento no banco."""
    db.add(fp_to_add)
    db.flush()
    db.refresh(fp_to_add)
    return fp_to_add


def update_forma_pagamento(db: Session, fp_to_update: FormaPagamentoModel) -> FormaPagamentoModel:
    """Persiste alterações em uma forma de pagamento existente."""
    db.flush()
    db.refresh(fp_to_update)
    return fp_to_update
