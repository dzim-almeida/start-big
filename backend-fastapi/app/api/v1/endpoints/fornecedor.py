# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/fornecedor.py
# DESCRIÇÃO: Define os endpoints (rotas) da API para operações CRUD
#            relacionadas a Fornecedores.
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session
from typing import Sequence

from app.core.depends import get_token
from app.db.session import get_db

from app.schemas.fornecedor import FornecedorCreate, FornecedorRead, FornecedorUpdate
from app.services import fornecedor as supplier_service

# Cria um roteador específico para este módulo
router = APIRouter()

# =========================
# Endpoint: Criar Fornecedor
# =========================
@router.post(
    "/",
    response_model=FornecedorRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo fornecedor"
)
def create_supplier(
    supplier: FornecedorCreate, # Valida o corpo da requisição com o schema
    token: dict = Depends(get_token), # Garante autenticação
    db: Session = Depends(get_db) # Injeta a sessão do banco
):
    """
    Endpoint para criar um novo Fornecedor e seus endereços associados.

    Recebe um payload aninhado (Fornecedor + Endereços) e gerencia
    a transação do banco de dados (commit/rollback).
    """
    try:
        # 1. TENTA EXECUTAR A LÓGICA DE NEGÓCIO
        # Delega a criação para a camada de serviço
        new_supplier = supplier_service.create_supplier(db, supplier)
        
        # 2. CAMINHO FELIZ: Comita a transação
        db.commit()
        
        # 3. Retorna o novo fornecedor criado
        return new_supplier
    
    except HTTPException as http_exce:
        # 4A. CAMINHO TRISTE (Erro de Negócio):
        print(f"Erro de negócio: {http_exce.detail}")
        db.rollback()
        raise http_exce
    
    except Exception as e:
        # 4B. CAMINHO TRISTE (Erro Inesperado):
        print(f"Erro inesperado ao cadastrar fornecedor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )

# =========================
# Endpoint: Buscar TODOS os Fornecedores
# =========================
@router.get(
    "/a",
    response_model=Sequence[FornecedorRead],
    status_code=status.HTTP_200_OK,
    summary="Retorna todos os fornecedores cadastrados"
)
def get_all_suppliers(
    token: dict = Depends(get_token), # Garante autenticação
    db: Session = Depends(get_db) # Injeta a sessão do banco
):
    """
    Endpoint para buscar TODOS os fornecedores cadastrados no sistema.
    (Nota: Rota de utilidade, sem paginação)
    """
    # Delega a busca para a camada de serviço
    suppliers_in_db = supplier_service.get_all_suppliers(db)
    # Retorna a lista de fornecedores
    return suppliers_in_db

# =========================
# Endpoint: Buscar Fornecedores (Search)
# =========================
@router.get(
    "/",
    response_model=Sequence[FornecedorRead], # A resposta é uma lista de fornecedores
    status_code=status.HTTP_200_OK,
    summary="Buscar os fornecedores por nome ou CNPJ"
)
def get_supplier_by_search(
    # Define 'buscar' como um parâmetro de query (ex: /fornecedores/?buscar=...)
    buscar: str = Query(
        ..., # Indica que o parâmetro é obrigatório
        min_length=1,
        max_length=255,
        description="Busca do fornecedor" # Corrigido: 'Busca do fornecedor'
    ),
    token: dict = Depends(get_token), # Garante autenticação
    db: Session = Depends(get_db) # Injeta a sessão do banco
):
    """
    Endpoint para buscar fornecedores pelo nome ou CNPJ.
    Retorna uma lista de fornecedores ou uma lista vazia.
    """
    # Delega a lógica de busca para o serviço
    suppliers_in_db = supplier_service.get_supplier_by_search(db, buscar)
    
    # Retorna a lista de resultados
    return suppliers_in_db

# =========================
# Endpoint: Atualizar Fornecedor (PUT)
# =========================
@router.put(
    "/{id}", # Recebe o ID do fornecedor na URL
    response_model=FornecedorRead, # Retorna o fornecedor atualizado
    status_code=status.HTTP_200_OK,
    summary="Atualiza os dados do fornecedor"
)
def update_supplier(
    # Extrai o ID da URL, valida se é um inteiro >= 1
    id: int = Path(
        ...,
        description="ID do fornecedor a ser atualizado",
        ge=1
    ),
    *, # Força os parâmetros seguintes a serem nomeados (keyword-only)
    
    # Valida o corpo da requisição (JSON) com o schema de atualização
    supplier: FornecedorUpdate,
    
    token: dict = Depends(get_token), # Garante autenticação
    db: Session = Depends(get_db) # Injeta a sessão do banco
):
    """
    Endpoint para atualizar um fornecedor existente pelo seu ID.
    Gerencia a transação (commit/rollback).
    """
    try:
        # Delega a lógica de atualização para o serviço
        update_supplier = supplier_service.update_supplier(db, id, supplier)
        
        # Comita a transação se o serviço foi bem-sucedido
        db.commit()
        
        # Retorna o fornecedor atualizado
        return update_supplier
    
    except HTTPException as http_exce:
        # Captura erros de negócio (ex: 404 Not Found)
        print(f"Erro de negócio: {http_exce.detail}")
        db.rollback()
        raise http_exce
    
    except Exception as e:
        # Captura erros inesperados
        print(f"Erro inesperado ao atualizar fornecedor: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )
    
# =========================
# Endpoint: Deletar Fornecedor (DELETE)
# =========================
@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT, # Define o status de sucesso
    summary="Deleta um fornecedor do BD" # Corrigido: 'Deleta'
)
def delete_supplier_by_id(
    # Extrai o ID da URL, valida se é um inteiro >= 1
    id: int = Path(
        ...,
        description="ID do fornecedor a ser deletado",
        ge=1
    ),
    token: dict = Depends(get_token), # Garante autenticação
    db: Session = Depends(get_db) # Injeta a sessão do banco
):
    """
    Endpoint para deletar um fornecedor existente pelo seu ID.
    Gerencia a transação (commit/rollback).
    """
    # (Nota: A lógica de try/except foi omitida no original, 
    #  mas é recomendada como nos outros endpoints)
    
    # Delega a lógica de deleção para o serviço
    supplier_service.delete_supplier(db, id)
    # Comita a transação
    db.commit()