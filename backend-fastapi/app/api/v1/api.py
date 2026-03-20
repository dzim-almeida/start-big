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
from app.api.v1.endpoints import usuario
from app.api.v1.endpoints import ordem_servico
from app.api.v1.endpoints import forma_pagamento

# Cria a instância principal do roteador para a V1
router = APIRouter()

# Endpoint utilitário para resetar o banco de dados (provavelmente para testes)
router.include_router(reset_bd.router, prefix="/reset", tags=["Resetar BD"])

# Inclui o roteador de autenticação sob o prefixo /auth
router.include_router(auth.router, prefix="/auth", tags=["Login"])

# Inclui o roteador de usuários sob o prefixo /usuarios
router.include_router(usuario.router, prefix="/usuarios", tags=["Usuários"])

# Inclui o roteador de empresas sob o prefixo /empresas
router.include_router(empresa.router, prefix="/empresas", tags=["Empresas"])

# Inclui o roteador de funcionários sob o prefixo /funcionarios
router.include_router(funcionario.router, prefix="/funcionarios", tags=["Funcionários"])

# Inclui o roteador de cargos sob o prefixo /cargos
router.include_router(cargo.router, prefix="/cargos", tags=["Cargos"])

# Inclui o roteador de clientes sob o prefixo /clientes
router.include_router(cliente.router, prefix="/clientes", tags=["Clientes"])

# Inclui o roteador de fornecedores sob o prefixo /fornecedores
router.include_router(fornecedor.router, prefix="/fornecedores", tags=["Fornecedores"])

# Inclui o roteador de produtos sob o prefixo /produtos
router.include_router(produto.router, prefix="/produtos", tags=["Produtos"])

# Inclui o roteador de serviços sob o prefixo /servicos
router.include_router(servico.router, prefix="/servicos", tags=["Serviços"])

# Inclui o roteador de endereços sob o prefixo /enderecos
router.include_router(endereco.router, prefix="/enderecos", tags=["Endereços"])

# Inclui o roteador de ordens de serviço (OS) sob o prefixo /ordens-servico
# Contém também os sub-recursos: itens, fotos e ações de status (finalizar, cancelar, reabrir)
router.include_router(ordem_servico.router, prefix="/ordens-servico", tags=["Ordens de Serviço"])

# Inclui o roteador do catálogo de formas de pagamento sob o prefixo /formas-pagamento
# Entidade global do sistema, usada na finalização de OS
router.include_router(forma_pagamento.router, prefix="/formas-pagamento", tags=["Formas de Pagamento"])
