# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/ordem_servico/escrita.py
# DESCRICAO: Ordem de servico (crud) - criar e atualizar OS, item, pagamento e foto.
# Usa flush() + refresh(), sem commit (o commit e do endpoint).
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.db.models.ordem_servico import OrdemServico as OSModel
from app.db.models.ordem_servico_item import OrdemServicoItem as OSItemModel
from app.db.models.ordem_servico_pagamento import OrdemServicoPagamento as OSPagamentoModel
from app.db.models.ordem_servico_foto import OrdemServicoFoto as OSFotoModel


# ===========================================================================
# ESCRITA (CREATE / UPDATE) — Ordem de Serviço
# ===========================================================================

def create_ordem_servico(db: Session, os_to_add: OSModel) -> OSModel:
    """Adiciona e persiste uma nova OS no banco."""
    db.add(os_to_add)
    db.flush()
    db.refresh(os_to_add)
    return os_to_add


def update_ordem_servico(db: Session, os_to_update: OSModel) -> OSModel:
    """Persiste alterações em uma OS existente."""
    db.flush()
    db.refresh(os_to_update)
    return os_to_update


# ===========================================================================
# ESCRITA (CREATE / UPDATE / DELETE) — Itens
# ===========================================================================

def create_os_item(db: Session, item_to_add: OSItemModel) -> OSItemModel:
    """Adiciona um novo item a uma OS."""
    db.add(item_to_add)
    db.flush()
    db.refresh(item_to_add)
    return item_to_add


def update_os_item(db: Session, item_to_update: OSItemModel) -> OSItemModel:
    """Persiste alterações em um item de OS."""
    db.flush()
    db.refresh(item_to_update)
    return item_to_update


def delete_os_item(db: Session, item_to_delete: OSItemModel) -> None:
    """Remove um item de OS do banco."""
    db.delete(item_to_delete)
    db.flush()


# ===========================================================================
# ESCRITA (CREATE) — Pagamentos
# ===========================================================================

def create_os_pagamento(db: Session, pagamento_to_add: OSPagamentoModel) -> OSPagamentoModel:
    """
    Adiciona um pagamento à OS.
    Pagamentos são criados exclusivamente no fluxo de finalização.
    """
    db.add(pagamento_to_add)
    db.flush()
    db.refresh(pagamento_to_add)
    return pagamento_to_add


# ===========================================================================
# ESCRITA (CREATE / DELETE) — Fotos
# ===========================================================================

def create_os_foto(db: Session, foto_to_add: OSFotoModel) -> OSFotoModel:
    """Registra uma nova foto de OS no banco."""
    db.add(foto_to_add)
    db.flush()
    db.refresh(foto_to_add)
    return foto_to_add


def delete_os_foto(db: Session, foto_to_delete: OSFotoModel) -> None:
    """Remove o registro de uma foto de OS do banco."""
    db.delete(foto_to_delete)
    db.flush()
