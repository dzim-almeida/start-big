# ---------------------------------------------------------------------------
# ARQUIVO: cliente.py
# DESCRIÇÃO: Define os endpoints (rotas) da API para operações
#            relacionadas a Clientes (PF, PJ e buscas).
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session

# Importa os schemas necessários para entrada (Create) e saída (Read)
from app.schemas.cliente import ClienteRead, ClientePFCreate, ClientePFRead, ClientePJCreate, ClientePJRead
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
    response_model=ClientePFRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria clientes para pessoa física"
)
def create_new_client_pf(
    client_pf: ClientePFCreate,
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Endpoint para criar um novo cliente do tipo Pessoa Física.

    Este endpoint é protegido e requer autenticação (token).
    Ele gerencia a transação do banco de dados, garantindo que a operação
    seja atômica (ou tudo é salvo, ou nada é salvo).

    Args:
        client_pf (ClientePFCreate): Schema Pydantic com os dados do novo cliente.
        token (dict): Dependência que valida o token do usuário autenticado.
        db (Session): Dependência que injeta a sessão do banco de dados.

    Raises:
        HTTPException: Lança erros 4xx (como 409 Conflict) para erros de negócio
                       e 500 para erros inesperados do servidor.

    Returns:
        ClientePFRead: O objeto do cliente recém-criado, formatado pelo schema.
    """
    try:
        # 1. TENTA EXECUTAR A LÓGICA DE NEGÓCIO
        # Chama o serviço específico para criar Cliente PF
        new_client_pf = client_service.create_client_pf_service(db, client_pf)

        # 2. CAMINHO FELIZ: Se o serviço foi concluído sem erros,
        #    salva permanentemente todas as alterações no banco.
        db.commit()

        # 3. Retorna o novo cliente criado
        return new_client_pf

    except HTTPException as http_exec:
        # 4A. CAMINHO TRISTE (Erro de Negócio):
        # Captura erros de negócio (ex: CPF duplicado) lançados pelo serviço.
        print(f"Erro de negócio: {http_exec.detail}")
        db.rollback()  # Desfaz todas as alterações pendentes na sessão.
        raise http_exec  # Relança o erro para o FastAPI retornar ao cliente.

    except Exception as e:
        # 4B. CAMINHO TRISTE (Erro Inesperado):
        # Captura qualquer outro erro (ex: falha de conexão com o banco).
        print(f"Erro inesperado: {e}")
        db.rollback()  # Desfaz todas as alterações.

        # Lança um erro 500 genérico para proteger os detalhes internos.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )


# =========================
# Endpoint: Criar Cliente PJ
# =========================
@router.post(
    "/cliente_pj",
    response_model=ClientePJRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria clientes para pessoa jurídica"
)
def create_new_client_pf( # Nota: O nome da função está 'create_new_client_pf'
    client_pj: ClientePJCreate,
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Endpoint para criar um novo cliente do tipo Pessoa Jurídica.

    Este endpoint é protegido e requer autenticação (token).
    Ele gerencia a transação do banco de dados (commit/rollback).

    Args:
        client_pj (ClientePJCreate): Schema Pydantic com os dados do novo cliente.
        token (dict): Dependência que valida o token do usuário autenticado.
        db (Session): Dependência que injeta a sessão do banco de dados.

    Raises:
        HTTPException: Lança erros 4xx (como 409 Conflict) para erros de negócio
                       e 500 para erros inesperados do servidor.

    Returns:
        ClientePJRead: O objeto do cliente recém-criado, formatado pelo schema.
    """
    try:
        # 1. TENTA EXECUTAR A LÓGICA DE NEGÓCIO
        # Chama o serviço específico para criar Cliente PJ
        new_client_pj = client_service.create_client_pj_service(db, client_pj)

        # 2. CAMINHO FELIZ: Se o serviço foi concluído sem erros, comita.
        db.commit()

        # 3. Retorna o novo cliente criado
        return new_client_pj

    except HTTPException as http_exec:
        # 4A. CAMINHO TRISTE (Erro de Negócio):
        print(f"Erro de negócio: {http_exec.detail}")
        db.rollback()  # Desfaz todas as alterações.
        raise http_exec  # Relança o erro.

    except Exception as e:
        # 4B. CAMINHO TRISTE (Erro Inesperado):
        print(f"Erro inesperado: {e}")
        db.rollback()  # Desfaz todas as alterações.

        # Lança um erro 500 genérico.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )


# =========================
# Endpoint: Buscar Clientes
# =========================
@router.get(
    "/",
    response_model=list[ClienteRead], # A resposta é uma lista de Clientes (PF ou PJ)
    status_code=status.HTTP_200_OK,
    summary="Retorna Cliente de acordo com uma busca"
)
def get_client_by_indetification(
    # 'busca' é um parâmetro de query obrigatório (ex: /clientes/?busca=Joao)
    buscar: str = Query(
        ..., # Indica que o parâmetro é obrigatório
        min_length=1,
        max_length=255,
        description="Entrada que pode ser nome, cpf, razão social, cnpj ou nome fantasia."
    ),
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Endpoint para buscar clientes (PF ou PJ) de forma polimórfica.

    A busca é realizada pela camada de serviço.
    Retorna uma lista de clientes ou uma lista vazia.
    """
    # Delega a lógica de busca para o serviço
    client = client_service.get_client_by_search(db, buscar)
    
    # Retorna a lista de resultados (pode ser vazia)
    return client