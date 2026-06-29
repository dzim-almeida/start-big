# ---------------------------------------------------------------------------
# ARQUIVO: api/v1/endpoints/licenca.py
# DESCRIÇÃO: Endpoints públicos de verificação de licença.
#            Não requer autenticação (executa antes do login).
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.licenca import LicencaStatusResponse
from app.services import licenca as licenca_service

router = APIRouter()


@router.get(
    "/status",
    response_model=LicencaStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Verifica se a licença está ativa",
    responses={
        403: {
            "description": "Licença inválida, expirada ou requer conexão",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "codigo": "REQUISITA_CONEXAO_INTERNET",
                            "mensagem": "Conecte-se à internet para revalidar.",
                        }
                    }
                }
            },
        }
    },
)
def verificar_status_licenca(db: Session = Depends(get_db)):
    """
    Endpoint público (sem autenticação) chamado pelo frontend
    a cada inicialização para verificar a validade da licença.

    - **200**: Licença válida (online ou offline).
    - **403**: Licença inválida com código de erro estruturado.
    """
    return licenca_service.verificar_licenca_ativa(db)


@router.post(
    "/desconectar",
    status_code=status.HTTP_200_OK,
    summary="Desconecta a sessão da licença na API StartBig",
)
async def desconectar_licenca(db: Session = Depends(get_db)):
    """
    Endpoint público chamado no encerramento da aplicação ou logout.
    Liberta a sessão da licença na plataforma StartBig.

    Sempre retorna 200 — falhas de rede são tratadas internamente.
    """
    return await licenca_service.desconectar_licenca(db)
