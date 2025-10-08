from fastapi import APIRouter, status, HTTPException # type: ignore
from app.schemas.product import Produto # Importa o modelo Produto do Pydantic

# Router que agrupará todas as rotas
router = APIRouter()

# Endpoint POST 
# O FastAPI serializa isso e devolve 201.
@router.post("/produtos/", response_model=Produto, status_code=status.HTTP_201_CREATED)
async def criar_produto(produto: Produto):
    # O mínimo para passar
    return produto

