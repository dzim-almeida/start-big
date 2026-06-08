from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.comunicado import Comunicado
from app.db.crud import comunicado as crud
from app.schemas.comunicado import ComunicadoCreate, ComunicadoRead


def listar_comunicados(db: Session, empresa_id: int, funcionario_id: int) -> list[ComunicadoRead]:
    comunicados = crud.get_comunicados_empresa(db, empresa_id)
    lidos = crud.get_lidos_ids(db, funcionario_id, empresa_id)
    result = []
    for c in comunicados:
        item = ComunicadoRead.model_validate(c)
        item.lido = c.id in lidos
        result.append(item)
    return result


def criar_comunicado(db: Session, empresa_id: int, funcionario_autor_id: int, data: ComunicadoCreate) -> ComunicadoRead:
    comunicado = Comunicado(
        empresa_id=empresa_id,
        funcionario_autor_id=funcionario_autor_id,
        titulo=data.titulo,
        mensagem=data.mensagem,
    )
    criado = crud.create_comunicado(db, comunicado)
    crud.marcar_lido(db, criado.id, funcionario_autor_id)
    resultado = ComunicadoRead.model_validate(criado)
    resultado.lido = True
    return resultado


def marcar_lido(db: Session, comunicado_id: int, empresa_id: int, funcionario_id: int) -> None:
    comunicado = crud.get_comunicado_by_id(db, comunicado_id)
    if not comunicado or comunicado.empresa_id != empresa_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comunicado não encontrado.")
    crud.marcar_lido(db, comunicado_id, funcionario_id)
