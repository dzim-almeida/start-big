from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session

from app.core.depends import get_token
from app.db.session import get_db
from app.core.enum import EntityType
from app.services import endereco as address_service

router = APIRouter()

@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deleta endereços através de um id."
)
def delete_address(
    id: int = Path(
        ...,
        description="ID do endereço a ser excluído."
    ),
    entidade_id: int = Query(
        ...,
        description="ID da entidade responsável pelo endereço."
    ),
    tipo_entidade: EntityType = Query(
        ...,
        description="Tipo da entidade responsável pelo endereço."
    ),
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Endpoint para deletar um endereço existente pelo seu ID,
    validando o ID e o tipo da entidade proprietária.
    Gerencia a transação (commit/rollback).
    """
    try:
        # Delega a lógica de deleção para o serviço
        address_service.delete_address_in_db(db, id, entidade_id, tipo_entidade)
        
        # Comita a transação se a deleção foi bem-sucedida
        db.commit()
        
    except HTTPException as http_exce:
        # Captura erros de negócio (ex: 404 Not Found, 403 Forbidden)
        print(f"Erro de negócio: {http_exce.detail}")
        db.rollback() # Desfaz quaisquer alterações pendentes
        raise http_exce
    
    except Exception as e:
        # Captura erros inesperados
        print(f"Erro inesperado ao deletar endereço: {e}")
        db.rollback() # Desfaz quaisquer alterações pendentes
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )