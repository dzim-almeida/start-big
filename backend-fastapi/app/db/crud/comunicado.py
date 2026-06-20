from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.comunicado import Comunicado, ComunicadoLeitura


def get_comunicados_empresa(db: Session, empresa_id: int) -> list[Comunicado]:
    stmt = (
        select(Comunicado)
        .where(Comunicado.empresa_id == empresa_id)
        .order_by(Comunicado.criado_em.desc())
    )
    return list(db.scalars(stmt).all())


def get_comunicado_by_id(db: Session, comunicado_id: int) -> Comunicado | None:
    return db.get(Comunicado, comunicado_id)


def create_comunicado(db: Session, comunicado: Comunicado) -> Comunicado:
    db.add(comunicado)
    db.flush()
    db.refresh(comunicado)
    return comunicado


def marcar_lido(db: Session, comunicado_id: int, funcionario_id: int) -> None:
    existe = db.scalar(
        select(ComunicadoLeitura).where(
            ComunicadoLeitura.comunicado_id == comunicado_id,
            ComunicadoLeitura.funcionario_id == funcionario_id,
        )
    )
    if not existe:
        leitura = ComunicadoLeitura(comunicado_id=comunicado_id, funcionario_id=funcionario_id)
        db.add(leitura)
        db.flush()


def get_lidos_ids(db: Session, funcionario_id: int, empresa_id: int) -> set[int]:
    stmt = (
        select(ComunicadoLeitura.comunicado_id)
        .join(Comunicado, Comunicado.id == ComunicadoLeitura.comunicado_id)
        .where(
            ComunicadoLeitura.funcionario_id == funcionario_id,
            Comunicado.empresa_id == empresa_id,
        )
    )
    return set(db.scalars(stmt).all())
