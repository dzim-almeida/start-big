# ---------------------------------------------------------------------------
# ARQUIVO: api.py
# DESCRIÇÃO: Roteador principal que agrega todos os endpoints da versão V1
#            da API. Este arquivo centraliza os módulos de rotas.
# ---------------------------------------------------------------------------

from fastapi import APIRouter
from app.api.v1.endpoints import reset_bd
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import cliente
from app.api.v1.endpoints import produto
from app.api.v1.endpoints import fornecedor
from app.api.v1.endpoints import servico
from app.api.v1.endpoints import endereco
from app.api.v1.endpoints import funcionario
from app.api.v1.endpoints import empresa
from app.api.v1.endpoints import cargo

# Cria a instância principal do roteador para a V1
router = APIRouter()

# Endpoint utilitário para resetar o banco de dados (provavelmente para testes)
router.include_router(reset_bd.router, prefix="/reset", tags=["Resetar BD"])

# Inclui o roteador de empresas sob o prefixo /empresa
# Todos os endpoints definidos em 'empresa.py' serão acessados via /api/v1/empresa/...
router.include_router(empresa.router, prefix="/empresas", tags=["Empresas"])

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

# Inclui o roteador de funcionários sob o prefixo /funcionarios
# Endpoints de funcionários serão acessados via /api/v1/funcionarios/...
router.include_router(funcionario.router, prefix="/funcionarios", tags=["Funcionários"])

router.include_router(cargo.router, prefix="/cargos", tags=["Cargos"])