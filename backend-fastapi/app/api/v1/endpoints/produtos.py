from fastapi import APIRouter, status, HTTPException
from app.schemas import Produto # Importa o modelo Produto do Pydantic

# Router que agrupará todas as rotas
router = APIRouter()

# Endpoint POST
# Como não temos banco de dados ainda, apenas retornamos o objeto que recebemos. 
# O FastAPI serializa isso e devolve 201.
@router.post("/produtos/", response_model=Produto, status_code=status.HTTP_201_CREATED)
async def criar_produto(produto: Produto):
    # O mínimo para passar
    return produto

