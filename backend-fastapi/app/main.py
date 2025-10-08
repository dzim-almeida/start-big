# Entrada do FastAPI

from typing import Union

from fastapi import FastAPI # type: ignore

from app.api.v1.endpoints import produtos

app = FastAPI(
    title="BigPDV Backend API",
    description="Sistema de Ponto de Venda (PDV) - API",
    version="1.0.0"
)

app.include_router(produtos.router, prefix="/api/v1", tags=["Produtos"])