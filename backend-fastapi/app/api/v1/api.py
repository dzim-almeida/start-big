# ---------------------------------------------------------------------------
# ARQUIVO: api.py
# DESCRIÇÃO: Roteador principal que agrega todos os endpoints da versão V1
#            da API. Este arquivo centraliza os módulos de rotas.
# ---------------------------------------------------------------------------

from fastapi import APIRouter
from app.api.v1.endpoints import reset_bd
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import cliente
from app.api.v1.endpoints import usuario
from app.api.v1.endpoints import produto
from app.api.v1.endpoints import fornecedor
from app.api.v1.endpoints import servico
from app.api.v1.endpoints import endereco

# Cria a instância principal do roteador para a V1
router = APIRouter()

# Endpoint utilitário para resetar o banco de dados (provavelmente para testes)
router.include_router(reset_bd.router, prefix="/reset", tags=["Resetar BD"])

# Inclui o roteador de usuários sob o prefixo /usuarios
# Todos os endpoints definidos em 'usuario.py' serão acessados via /api/v1/usuarios/...
router.include_router(usuario.router, prefix="/usuarios", tags=["Usuários"])

# Inclui o roteador de autenticação sob o prefixo /auth
# Endpoints de login/logout serão acessados via /api/v1/auth/...
router.include_router(auth.router, prefix="/auth", tags=["Login"])

# Inclui o roteador de clientes sob o prefixo /clientes
# Endpoints de clientes serão acessados via /api/v1/clientes/...
router.include_router(cliente.router, prefix="/clientes", tags=["Clientes"])

# Inclui o roteador de produtos sob o prefixo /produtos
# Endpoints de produtos serão acessados via /api/v1/produtos/...
router.include_router(produto.router, prefix="/produtos", tags=["Produtos"])

# Inclui o roteador de fornecedores sob o prefixo /fornecedores
# Endpoints de fornecedores serão acessados via /api/v1/fornecedores/...
router.include_router(fornecedor.router, prefix="/fornecedores", tags=["Fornecedores"])

# Inclui o roteador de servicos sob o prefixo /servicos
# Endpoints de servicos serão acessados via /api/v1/servicos/...
router.include_router(servico.router, prefix="/servicos", tags=["Serviços"])

# Inclui o roteador de endereços sob o prefixo /enderecos
# Endpoints de endereços serão acessados via /api/v1/enderecos/...
router.include_router(endereco.router, prefix="/enderecos", tags=["Endereços"])