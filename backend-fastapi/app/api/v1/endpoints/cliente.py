# ---------------------------------------------------------------------------
# ARQUIVO: cliente.py
# DESCRIÇÃO: Define os endpoints (rotas) da API para operações CRUD
#            relacionadas a Clientes (PF, PJ, Busca, Atualização, Deleção).
#            Rotas: /clientes/pf, /clientes/pj, /clientes/{id}, etc.
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, status, HTTPException, Query, Path, Response
from sqlalchemy.orm import Session
from typing import Sequence, List

# Importa os schemas necessários para entrada (Create/Update) e saída (Read)
from app.schemas.cliente import ClienteRead, ClienteUpdate
from app.schemas.cliente import ClientePFCreate, ClientePFRead
from app.schemas.cliente import ClientePJCreate, ClientePJRead
# Importa as dependências de autenticação e sessão
from app.core.depends import get_token
from app.db.session import get_db
# Importa a camada de serviço que contém a lógica de negócio
from app.services import cliente as client_service

# Cria um roteador específico. Assume que a URL base é /clientes
router = APIRouter()

# Função auxiliar para padronizar o tratamento de transações e exceções
def _handle_db_transaction(db: Session, func, *args, **kwargs):
    """Executa a lógica de serviço, gerencia a transação e trata exceções."""
    try:
        result = func(db, *args, **kwargs)
        db.commit()
        return result
    except HTTPException as http_exce:
        # Erros de negócio (ex: 404 Not Found, 409 Conflict)
        print(f"Erro de negócio: {http_exce.detail}")
        db.rollback()
        raise http_exce
    except Exception as e:
        # Erros inesperados (ex: falha de conexão, erro de lógica no serviço)
        print(f"Erro inesperado: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )


# =========================
# Endpoint: Criar Cliente PF
# Rota: POST /clientes/cliente_pf
# =========================
@router.post(
    "/cliente_pf",
    response_model=ClientePFRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo cliente para pessoa física"
)
def create_new_client_pf(
    client_pf: ClientePFCreate,
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Cria um novo cliente do tipo Pessoa Física.
    Usa o serviço 'create_client_pf' e gerencia a transação.
    """
    return _handle_db_transaction(
        db, 
        client_service.create_client_pf, 
        client_pf
    )


# =========================
# Endpoint: Criar Cliente PJ
# Rota: POST /clientes/cliente_pj
# =========================
@router.post(
    "/cliente_pj",
    response_model=ClientePJRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo cliente para pessoa jurídica"
)
def create_new_client_pj( # Função renomeada para PJ para evitar conflito de nomes
    client_pj: ClientePJCreate,
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Cria um novo cliente do tipo Pessoa Jurídica.
    Usa o serviço 'create_client_pj' e gerencia a transação.
    """
    return _handle_db_transaction(
        db, 
        client_service.create_client_pj, 
        client_pj
    )


# =========================
# Endpoint: Buscar TODOS os Clientes (Sem Paginação)
# Rota: GET /clientes/all
# =========================
@router.get(
    "/all", # Rota alterada de '/a' para '/all' (melhor legibilidade)
    response_model=Sequence[ClienteRead], # Sequence é mais idiomático que List para SQLAlchemy
    status_code=status.HTTP_200_OK,
    summary="Retorna todos os clientes cadastrados (rota de utilidade)"
)
def get_all_clients(
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Busca e retorna a lista completa de clientes (PF e PJ).
    """
    # A busca não altera o estado do BD, então não há necessidade de try/except ou rollback/commit
    return client_service.get_all_clients(db)


# =========================
# Endpoint: Buscar Clientes (Search)
# Rota: GET /clientes/
# =========================
@router.get(
    "/",
    response_model=List[ClienteRead], # Usando List para clareza em Pydantic
    status_code=status.HTTP_200_OK,
    summary="Retorna Cliente(s) de acordo com uma busca polimórfica (nome, CPF, CNPJ, etc.)"
)
def get_client_by_search(
    # Parâmetro 'buscar' da query string, obrigatório
    buscar: str = Query(
        ...,
        min_length=1,
        max_length=255,
        description="Entrada pode ser nome, cpf, razão social, cnpj ou nome fantasia."
    ),
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Busca clientes (PF ou PJ) usando um termo de pesquisa (search term).
    Retorna uma lista de objetos ClienteRead.
    """
    # A busca não altera o estado do BD
    return client_service.get_client_by_search(db, buscar)


# =========================
# Endpoint: Atualizar Cliente (PUT)
# Rota: PUT /clientes/{id}
# =========================
@router.put(
    "/{id}",
    response_model=ClienteRead,
    status_code=status.HTTP_200_OK,
    summary="Atualiza um cliente (PF ou PJ) através do ID"
)
def update_client_by_id(
    id: int = Path(..., description="ID do cliente a ser editado", ge=1),
    *,
    client: ClienteUpdate, # Corpo da requisição com a Union polimórfica
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Atualiza um cliente existente (PF ou PJ) pelo seu ID.
    """
    return _handle_db_transaction(
        db, 
        client_service.update_client_by_id, 
        id, 
        client
    )


# =========================
# Endpoint: Ativar Cliente (Update Lógico)
# Rota: PUT /clientes/ativa/{id}
# =========================
@router.put(
    "/ativa/{id}",
    response_model=ClienteRead,
    status_code=status.HTTP_200_OK,
    summary="Ativa um cliente logicamente no BD (seta 'ativo' para True)"
)
def active_client_by_id(
    id: int = Path(..., description="ID do cliente a ser ativado", ge=1),
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Ativa um cliente existente pelo seu ID.
    """
    return _handle_db_transaction(
        db, 
        client_service.active_client_by_id, 
        id
    )


# =========================
# Endpoint: Desativar Cliente (Update Lógico)
# Rota: PUT /clientes/desativa/{id}
# =========================
@router.put(
    "/desativa/{id}",
    # Retorna uma Response vazia com status 204
    status_code=status.HTTP_204_NO_CONTENT, 
    summary="Desativa um cliente logicamente no BD (seta 'ativo' para False)"
)
def disable_client_by_id(
    id: int = Path(..., description="ID do cliente a ser desativado", ge=1),
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Desativa um cliente existente pelo seu ID (Soft Delete).
    Retorna 204 No Content se a operação for bem-sucedida.
    """
    # Para rotas 204, o serviço é chamado e a resposta é controlada pelo status_code
    _handle_db_transaction(
        db, 
        client_service.disable_client_by_id, 
        id
    )
    # Retorna uma resposta vazia 204 NO CONTENT
    return Response(status_code=status.HTTP_204_NO_CONTENT)