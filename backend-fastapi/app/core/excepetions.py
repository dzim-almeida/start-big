import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
# CORREÇÃO AQUI: Importar do SQLAlchemy
from sqlalchemy.exc import IntegrityError 

logger = logging.getLogger(__name__)

def setup_exception_handlers(app: FastAPI):
    
    # 1. Erros de Negócio (Manual)
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        error_mapping = {
            status.HTTP_400_BAD_REQUEST: "Regra de negócio violada",
            status.HTTP_401_UNAUTHORIZED: "Não autorizado",
            status.HTTP_403_FORBIDDEN: "Acesso proibido",
            status.HTTP_404_NOT_FOUND: "Recurso não encontrado"
        }
        error_msg = error_mapping.get(exc.status_code, "Requisição inválida")

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": error_msg,
                "detail": exc.detail
            }
        )

    # 2. Erros de Validação (Pydantic/Schema)
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        formated_errors = []
        for error in exc.errors():
            formated_errors.append({
                "field": ".".join(map(str, error.get("loc", []))),
                "message": error.get("msg", "Dado inválido"),
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Dados de entrada inválidos",
                "detail": formated_errors
            }
        )

    # 3. Erros de Banco de Dados (Constraints)
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        # Logamos o erro técnico no servidor
        logger.error(f"Erro de integridade no Banco: {exc}")

        # Retornamos uma mensagem segura para o cliente
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Conflito de integridade",
                "detail": "A operação viola regras do banco de dados (ex: registro duplicado ou valor inválido)."
            }
        )

    # 4. Erros Inesperados (Crash de Código)
    @app.exception_handler(Exception)
    async def default_exception_handler(request: Request, exc: Exception):
        logger.error(f"Erro inesperado: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Erro interno do servidor",
                "detail": "Ocorreu um erro inesperado no servidor. Nossa equipe técnica foi notificada."
            }
        )