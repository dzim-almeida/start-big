# Entrada do FastAPI

from fastapi import FastAPI # type: ignore
from app.api.v1 import api

from app.db.base import Base  # Importando as classes base
from app.db.session import engine  # Importando a engine do banco de dados

from app.db.models.usuario import Usuario
from app.db.models.funcionario import Funcionario
from app.db.models.cliente import Cliente, ClientePF
from app.db.models.endereco import Endereco
from app.db.models.token import TokenBlocklist
from app.db.models.produto import Produto
from app.db.models.estoque import Estoque
from app.db.models.fornecedor import Fornecedor
from app.db.models.servico import Servico
from app.db.models.produto_fotos import ProdutoFoto

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BigPDV Backend API",
    description="Sistema de Ponto de Venda (PDV) - API",
    version="1.0.0"
)

app.include_router(api.router, prefix="/api/v1")