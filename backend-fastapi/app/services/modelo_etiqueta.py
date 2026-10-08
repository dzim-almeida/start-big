# ---------------------------------------------------------------------------
# ARQUIVO: app/services/modelo_etiqueta.py
# MÓDULO: Service — Modelos de etiqueta (Central de Etiquetas)
# ---------------------------------------------------------------------------

from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.crud import modelo_etiqueta as modelo_crud
from app.db.models.modelo_etiqueta import ModeloEtiqueta
from app.schemas.modelo_etiqueta import ModeloEtiquetaCreate, ModeloEtiquetaUpdate


def _nao_encontrado() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modelo de etiqueta não encontrado.")


def _garantir_nome_livre(db: Session, empresa_id: int, nome: str, ignorar_id: int | None = None) -> None:
    # Dois modelos com o mesmo nome viram duas opções indistinguíveis no
    # seletor da fila — o lojista imprimiria no layout errado sem perceber.
    if modelo_crud.existe_nome(db, empresa_id, nome, ignorar_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe um modelo de etiqueta chamado '{nome}'.",
        )


def listar_modelos(db: Session, empresa_id: int) -> Sequence[ModeloEtiqueta]:
    return modelo_crud.listar_modelos(db, empresa_id)


def obter_modelo(db: Session, empresa_id: int, modelo_id: int) -> ModeloEtiqueta:
    modelo = modelo_crud.get_modelo(db, empresa_id, modelo_id)
    if modelo is None:
        raise _nao_encontrado()
    return modelo


def criar_modelo(db: Session, empresa_id: int, dados: ModeloEtiquetaCreate) -> ModeloEtiqueta:
    _garantir_nome_livre(db, empresa_id, dados.nome)
    return modelo_crud.criar_modelo(
        db, empresa_id, dados.nome, dados.fonte, dados.definicao.model_dump(mode="json")
    )


def atualizar_modelo(db: Session, empresa_id: int, modelo_id: int, dados: ModeloEtiquetaUpdate) -> ModeloEtiqueta:
    modelo = obter_modelo(db, empresa_id, modelo_id)
    _garantir_nome_livre(db, empresa_id, dados.nome, ignorar_id=modelo_id)
    return modelo_crud.atualizar_modelo(
        db, modelo, dados.nome, dados.fonte, dados.definicao.model_dump(mode="json")
    )


def deletar_modelo(db: Session, empresa_id: int, modelo_id: int) -> None:
    modelo_crud.deletar_modelo(db, obter_modelo(db, empresa_id, modelo_id))
