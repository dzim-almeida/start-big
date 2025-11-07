# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/servico.py
# DESCRIÇÃO: Define os endpoints (rotas) da API para operações CRUD
#            relacionadas a Serviços.
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session
from typing import Sequence

from app.core.depends import get_token
from app.db.session import get_db

from app.schemas.servico import ServicoCreate, ServicoRead, ServicoUpdate
from app.services import servico as service_services

# Cria um roteador específico para este módulo
router = APIRouter()

# =========================
# Endpoint: Criar Serviço
# =========================
@router.post(
    "/",
    response_model=ServicoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma nova oferta de serviço."
)
def create_service(
    service: ServicoCreate, # Valida o corpo da requisição com o schema
    token: dict = Depends(get_token), # Garante autenticação
    db: Session = Depends(get_db) # Injeta a sessão do banco
):
    """
    Endpoint para criar um novo Serviço.

    Recebe um payload com os dados do serviço e gerencia
    a transação do banco de dados (commit/rollback).
    """
    try:
        # 1. TENTA EXECUTAR A LÓGICA DE NEGÓCIO
        # Delega a criação para a camada de serviço
        new_service = service_services.create_service(db, service)
        
        # 2. CAMINHO FELIZ: Comita a transação
        db.commit()
        
        # 3. Retorna o novo serviço criado
        return new_service

    except HTTPException as http_exce:
        # 4A. CAMINHO TRISTE (Erro de Negócio):
        print(f"Erro de negócio: {http_exce.detail}")
        db.rollback() # Desfaz quaisquer alterações pendentes
        raise http_exce
    
    except Exception as e:
        # 4B. CAMINHO TRISTE (Erro Inesperado):
        print(f"Erro inesperado ao cadastrar serviço: {e}")
        db.rollback() # Desfaz quaisquer alterações pendentes
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )

# =========================
# Endpoint: Buscar Serviços
# =========================
@router.get(
    "/",
    response_model=list[ServicoRead], # A resposta é uma lista de serviços
    status_code=status.HTTP_200_OK,
    summary="Buscar um serviço através da descrição."
)
def get_service(
    # Define 'buscar' como um parâmetro de query (ex: /servicos/?buscar=...)
    buscar: str = Query(
        ..., # Indica que o parâmetro é obrigatório
        max_length=255,
        description="Termo de busca do serviço."
    ),
    token: dict = Depends(get_token), # Garante autenticação
    db: Session = Depends(get_db) # Injeta a sessão do banco
):
    """
    Endpoint para buscar serviços pela sua descrição.
    Retorna uma lista de serviços ou uma lista vazia.
    """
    # Delega a lógica de busca para o serviço
    services_in_db = service_services.get_service_by_search(db, search=buscar)
    
    # Retorna a lista de resultados
    return services_in_db

# =========================
# Endpoint: Atualizar Serviço (PUT)
# =========================
@router.put(
    "/{id}", # Recebe o ID do serviço na URL
    response_model=ServicoRead, # Retorna o serviço atualizado
    status_code=status.HTTP_200_OK,
    summary="Edita atributos de um serviço existente."
)
def update_service(
    # Extrai o ID da URL, valida se é um inteiro
    id: int = Path(
        ...,
        description="ID único do servico a ser editado."
    ),
    *, # Força os parâmetros seguintes a serem nomeados (keyword-only)
    
    # Valida o corpo da requisição (JSON) com o schema de atualização
    service: ServicoUpdate,
    
    token: dict = Depends(get_token), # Garante autenticação
    db: Session = Depends(get_db) # Injeta a sessão do banco
):
    """
    Endpoint para atualizar um serviço existente pelo seu ID.
    Gerencia a transação (commit/rollback).
    """
    try:
        # Delega a lógica de atualização para o serviço
        updated_service = service_services.update_service(db, id, service)
        
        # Comita a transação se o serviço foi bem-sucedido
        db.commit()
        
        # Retorna o serviço atualizado
        return updated_service
    
    except HTTPException as http_exce:
        # Captura erros de negócio (ex: 404 Not Found)
        print(f"Erro de negócio: {http_exce.detail}")
        db.rollback() # Desfaz quaisquer alterações pendentes
        raise http_exce
    
    except Exception as e:
        # Captura erros inesperados
        print(f"Erro inesperado ao atualizar serviço: {e}")
        db.rollback() # Desfaz quaisquer alterações pendentes
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )

# =========================
# Endpoint: Deletar Serviço (DELETE)
# =========================
@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT, # Define o status de sucesso
    summary="Delete um serviço ofertado."
)
def delete_service(
    # Extrai o ID da URL, valida se é um inteiro
    id: int = Path(
        ...,
        description="ID único do servico a ser excluído."
    ),
    token: dict = Depends(get_token), # Garante autenticação
    db: Session = Depends(get_db) # Injeta a sessão do banco
):
    """
    Endpoint para deletar um serviço existente pelo seu ID.
    Gerencia a transação (commit/rollback).
    """
    try:
        # Delega a lógica de deleção para o serviço
        service_services.delete_service(db, id)
        
        # Comita a transação
        db.commit()
        
    except HTTPException as http_exce:
        # Captura erros de negócio (ex: 404 Not Found)
        print(f"Erro de negócio: {http_exce.detail}")
        db.rollback() # Desfaz quaisquer alterações pendentes
        raise http_exce
    
    except Exception as e:
        # Captura erros inesperados
        print(f"Erro inesperado ao deletar serviço: {e}")
        db.rollback() # Desfaz quaisquer alterações pendentes
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )