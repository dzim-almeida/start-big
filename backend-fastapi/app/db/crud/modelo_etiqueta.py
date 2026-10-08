# ---------------------------------------------------------------------------
# ARQUIVO: app/db/crud/modelo_etiqueta.py
# MÓDULO: Repository — Modelos de etiqueta
# ---------------------------------------------------------------------------

from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.modelo_etiqueta import ModeloEtiqueta


def listar_modelos(db: Session, empresa_id: int) -> Sequence[ModeloEtiqueta]:
    stmt = (
        select(ModeloEtiqueta)
        .where(ModeloEtiqueta.empresa_id == empresa_id)
        .order_by(ModeloEtiqueta.nome)
    )
    return db.scalars(stmt).all()


def get_modelo(db: Session, empresa_id: int, modelo_id: int) -> Optional[ModeloEtiqueta]:
    """O modelo — só se for da empresa."""
    stmt = select(ModeloEtiqueta).where(
        ModeloEtiqueta.id == modelo_id, ModeloEtiqueta.empresa_id == empresa_id
    )
    return db.scalars(stmt).first()


def existe_nome(db: Session, empresa_id: int, nome: str, ignorar_id: Optional[int] = None) -> bool:
    """Nome já usado na empresa? Compara sem diferenciar maiúsculas."""
    stmt = select(ModeloEtiqueta.id).where(
        ModeloEtiqueta.empresa_id == empresa_id,
        func.lower(ModeloEtiqueta.nome) == nome.lower(),
    )
    if ignorar_id is not None:
        stmt = stmt.where(ModeloEtiqueta.id != ignorar_id)
    return db.scalars(stmt).first() is not None


def criar_modelo(db: Session, empresa_id: int, nome: str, fonte: str, definicao: dict) -> ModeloEtiqueta:
    modelo = ModeloEtiqueta(empresa_id=empresa_id, nome=nome, fonte=fonte, definicao=definicao)
    db.add(modelo)
    db.flush()
    db.refresh(modelo)
    return modelo


def atualizar_modelo(db: Session, modelo: ModeloEtiqueta, nome: str, fonte: str, definicao: dict) -> ModeloEtiqueta:
    modelo.nome = nome
    modelo.fonte = fonte
    modelo.definicao = definicao
    db.flush()
    db.refresh(modelo)
    return modelo


def deletar_modelo(db: Session, modelo: ModeloEtiqueta) -> None:
    db.delete(modelo)
    db.flush()
