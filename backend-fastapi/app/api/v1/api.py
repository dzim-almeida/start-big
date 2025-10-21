# ---------------------------------------------------------------------------
# ARQUIVO: api.py
# DESCRIÇÃO: Roteador principal que agrega todos os endpoints da versão V1
#            da API. Este arquivo centraliza os módulos de rotas.
# ---------------------------------------------------------------------------

from fastapi import APIRouter
from app.api.v1.endpoints import auth, cliente, usuario

# Cria a instância principal do roteador para a V1
router = APIRouter()

# Inclui o roteador de usuários sob o prefixo /usuarios
# Todos os endpoints definidos em 'usuario.py' serão acessados via /api/v1/usuarios/...
router.include_router(usuario.router, prefix="/usuarios", tags=["Usuários"])

# Inclui o roteador de autenticação sob o prefixo /auth
# Endpoints de login/logout serão acessados via /api/v1/auth/...
router.include_router(auth.router, prefix="/auth", tags=["Login"])

# Inclui o roteador de clientes sob o prefixo /clientes
# Endpoints de clientes serão acessados via /api/v1/clientes/...
router.include_router(cliente.router, prefix="/clientes", tags=["Clientes"])