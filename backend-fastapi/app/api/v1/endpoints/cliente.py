# ---------------------------------------------------------------------------
# ARQUIVO: cliente.py
# DESCRIÇÃO: Define os endpoints (rotas) da API para operações CRUD
#            relacionadas a Clientes (PF, PJ, Busca, Atualização, Deleção).
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, status, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import Sequence

# Importa os schemas necessários para entrada (Create/Update) e saída (Read)
from app.schemas.cliente import ClienteRead, ClienteUpdate
from app.schemas.cliente import ClientePFCreate, ClientePFRead
from app.schemas.cliente import ClientePJCreate, ClientePJRead
# Importa as dependências de autenticação e sessão
from app.core.depends import get_token
from app.db.session import get_db
# Importa a camada de serviço que contém a lógica de negócio
from app.services import cliente as client_service

# Cria um roteador específico para este módulo
router = APIRouter()


# =========================
# Endpoint: Criar Cliente PF
# =========================
@router.post(
    "/cliente_pf",
    response_model=ClientePFRead, # Define o schema da resposta
    status_code=status.HTTP_201_CREATED, # Define o status code de sucesso
    summary="Cria clientes para pessoa física"
)
def create_new_client_pf(
    client_pf: ClientePFCreate, # Valida o corpo da requisição com o schema
    token: dict = Depends(get_token), # Garante autenticação
    db: Session = Depends(get_db) # Injeta a sessão do banco
):
    """
    Endpoint para criar um novo cliente do tipo Pessoa Física.

    Gerencia a transação do banco de dados (commit/rollback).
    """
    try:
        # Delega a lógica de criação para a camada de serviço
        new_client_pf = client_service.create_client_pf(db, client_pf)

        # Comita a transação se o serviço foi bem-sucedido
        db.commit()

        # Retorna o objeto do cliente criado, formatado pelo response_model
        return new_client_pf

    except HTTPException as http_exce:
        # Captura erros de negócio (ex: 409 Conflict)
        print(f"Erro de negócio: {http_exce.detail}")
        db.rollback()  # Desfaz a transação
        raise http_exce  # Relança o erro para o cliente

    except Exception as e:
        # Captura erros inesperados
        print(f"Erro inesperado ao criar cliente PF: {e}")
        db.rollback()  # Desfaz a transação
        raise HTTPException( # Retorna um erro 500 genérico
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )


# =========================
# Endpoint: Criar Cliente PJ
# =========================
@router.post(
    "/cliente_pj",
    response_model=ClientePJRead, # Define o schema da resposta
    status_code=status.HTTP_201_CREATED, # Define o status code de sucesso
    summary="Cria clientes para pessoa jurídica"
)
# Nota: Nome da função está igual à anterior, idealmente seria diferente
def create_new_client_pf(
    client_pj: ClientePJCreate, # Valida o corpo da requisição com o schema
    token: dict = Depends(get_token), # Garante autenticação
    db: Session = Depends(get_db) # Injeta a sessão do banco
):
    """
    Endpoint para criar um novo cliente do tipo Pessoa Jurídica.

    Gerencia a transação do banco de dados (commit/rollback).
    """
    try:
        # Delega a lógica de criação para a camada de serviço
        new_client_pj = client_service.create_client_pj(db, client_pj)

        # Comita a transação se o serviço foi bem-sucedido
        db.commit()

        # Retorna o objeto do cliente criado
        return new_client_pj

    except HTTPException as http_exce:
        # Captura erros de negócio (ex: 409 Conflict)
        print(f"Erro de negócio: {http_exce.detail}")
        db.rollback()  # Desfaz a transação
        raise http_exce  # Relança o erro para o cliente

    except Exception as e:
        # Captura erros inesperados
        print(f"Erro inesperado ao criar cliente PJ: {e}")
        db.rollback()  # Desfaz a transação
        raise HTTPException( # Retorna um erro 500 genérico
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )

# =========================
# Endpoint: Buscar TODOS os Clientes
# =========================
@router.get(
    "/a",
    response_model=Sequence[ClienteRead],
    status_code=status.HTTP_200_OK,
    summary="Retorna todos os clientes cadastrados"
)
def get_all_clients(
    token: dict = Depends(get_token), # Garante autenticação
    db: Session = Depends(get_db) # Injeta a sessão do banco
):
    """
    Endpoint para buscar TODOS os clientes cadastrados no sistema.
    (Nota: Rota de utilidade, sem paginação)
    """
    # Delega a busca para a camada de serviço
    clients_in_db = client_service.get_all_clients(db)
    # Retorna a lista de clientes
    return clients_in_db

# =========================
# Endpoint: Buscar Clientes (Search)
# =========================
@router.get(
    "/",
    response_model=list[ClienteRead], # A resposta é uma lista polimórfica
    status_code=status.HTTP_200_OK,
    summary="Retorna Cliente de acordo com uma busca"
)
def get_client_by_indetification(
    # Parâmetro 'buscar' da query string, obrigatório
    buscar: str = Query(
        ...,
        min_length=1,
        max_length=255,
        description="Entrada pode ser nome, cpf, razão social, cnpj ou nome fantasia."
    ),
    token: dict = Depends(get_token), # Garante autenticação
    db: Session = Depends(get_db) # Injeta a sessão do banco
):
    """
    Endpoint para buscar clientes (PF ou PJ) de forma polimórfica.
    Retorna uma lista de clientes ou uma lista vazia.
    """
    # Delega a busca para o serviço
    client = client_service.get_client_by_search(db, buscar)
    
    # Retorna a lista de resultados
    return client


# =========================
# Endpoint: Atualizar Cliente (PUT)
# =========================
@router.put(
    "/{id}", # ID do cliente vem da URL
    response_model=ClienteRead, # Retorna o cliente atualizado
    status_code=status.HTTP_200_OK, # Status de sucesso
    summary="Editar um cliente PF ou PJ através do id" # Descrição
)
def update_client_by_id(
    # Extrai e valida o ID da URL como inteiro >= 1
    id: int = Path(..., description="ID do cliente a ser editado", ge=1),
    
    *,
    
    # Valida o corpo da requisição (JSON) com a Union polimórfica 'ClienteUpdate'
    client: ClienteUpdate,
    
    token: dict = Depends(get_token), # Garante autenticação
    db: Session = Depends(get_db) # Injeta a sessão do banco
):
    """
    Endpoint para atualizar um cliente existente (PF ou PJ) pelo seu ID.
    Gerencia a transação (commit/rollback).
    """
    try:
        # Delega a lógica de atualização para o serviço
        edited_client = client_service.update_client_by_id(db, id, client)

        # Comita a transação se o serviço foi bem-sucedido
        db.commit()

        # Retorna o cliente atualizado
        return edited_client

    except HTTPException as http_exce:
        # Captura erros de negócio (ex: 404 Not Found)
        print(f"Erro de negócio: {http_exce.detail}")
        db.rollback()  # Desfaz a transação
        raise http_exce  # Relança o erro para o cliente

    except Exception as e:
        # Captura erros inesperados
        print(f"Erro inesperado ao atualizar cliente: {e}")
        db.rollback()  # Desfaz a transação
        raise HTTPException( # Retorna um erro 500 genérico
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )

# =========================
# Endpoint: Deletar Cliente (DELETE)
# =========================
@router.delete(
    "/{id}", # ID do cliente vem da URL
    status_code=status.HTTP_204_NO_CONTENT, # Define o status de sucesso
    summary="Deleta um cliente do BD" # Descrição
)
def delete_client_by_id(
    # Extrai e valida o ID da URL como inteiro >= 1
    id: int = Path(..., description="ID do cliente a ser deletado", ge=1),
    
    token: dict = Depends(get_token), # Garante autenticação
    db: Session = Depends(get_db) # Injeta a sessão do banco
):
    """
    Endpoint para deletar um cliente existente pelo seu ID.
    Gerencia a transação (commit/rollback).
    """
    try:
        # Delega a lógica de deleção para o serviço
        client_service.delete_client_by_id(db, id)

        # Comita a transação se o serviço foi bem-sucedido
        db.commit()

    except HTTPException as http_exce:
        # Captura erros de negócio (ex: 404 Not Found)
        print(f"Erro de negócio: {http_exce.detail}")
        db.rollback()  # Desfaz a transação
        raise http_exce  # Relança o erro para o cliente
    
    except Exception as e:
        # Captura erros inesperados
        print(f"Erro inesperado ao deletar cliente: {e}")
        db.rollback()  # Desfaz a transação
        raise HTTPException( # Retorna um erro 500 genérico
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )