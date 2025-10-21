# ---------------------------------------------------------------------------
# ARQUIVO: cliente.py
# DESCRIÇÃO: Define os endpoints (rotas) da API para operações
#            relacionadas a Clientes.
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.schemas.cliente import ClientePFCreate, ClientePFRead
from app.core.depends import get_token
from app.db.session import get_db
from app.services import cliente as client_service

# Cria um roteador específico para este módulo
router = APIRouter()


@router.post(
    "/cliente_pf",
    response_model=ClientePFRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria clientes para pessoa física"
)
def create_new_client_pf(
    data_client: ClientePFCreate,
    token: dict = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Endpoint para criar um novo cliente do tipo Pessoa Física.

    Este endpoint é protegido e requer autenticação (token).
    Ele gerencia a transação do banco de dados, garantindo que a operação
    seja atômica (ou tudo é salvo, ou nada é salvo).

    Args:
        data_client (ClientePFCreate): Schema Pydantic com os dados do novo cliente.
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
        # O serviço pode chamar vários CRUDs, todos na mesma sessão 'db'.
        new_client = client_service.create_client_service(db, data_client)

        # 2. CAMINHO FELIZ: Se o serviço foi concluído sem erros,
        #    salva permanentemente todas as alterações no banco.
        db.commit()

        # 3. Retorna o novo cliente criado
        return new_client

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