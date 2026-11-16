# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/cliente/historico.py
# DESCRICAO: Clientes - objetos/equipamentos ligados ao cliente.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Sequence

from app.db.models.objeto_servico import ObjetoServico


# ===========================================================================
# OBJETOS DO CLIENTE
# ===========================================================================

def get_objetos_by_cliente_id(
    db: Session, cliente_id: int
) -> Sequence[ObjetoServico]:
    """Retorna todos os objetos ativos de um cliente, ordenados do mais recente ao mais antigo."""
    stmt = (
        select(ObjetoServico)
        .where(
            ObjetoServico.cliente_id == cliente_id,
            ObjetoServico.ativo == True,
        )
        .order_by(ObjetoServico.data_criacao.desc())
    )
    return db.scalars(stmt).all()
