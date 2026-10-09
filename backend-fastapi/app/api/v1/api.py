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
from app.api.v1.endpoints import financeiro
from app.api.v1.endpoints import sessao_caixa
from app.api.v1.endpoints import terminal
from app.api.v1.endpoints import venda
from app.api.v1.endpoints import orcamento
from app.api.v1.endpoints import dashboard
from app.api.v1.endpoints import relatorios
from app.api.v1.endpoints import movimentacao_estoque
from app.api.v1.endpoints import configuracao
from app.api.v1.endpoints import comunicado
from app.api.v1.endpoints import licenca
from app.api.v1.endpoints import checklist_mobile
from app.api.v1.endpoints import backup
from app.api.v1.endpoints import fiscal
from app.api.v1.endpoints import fiscal_produto
from app.api.v1.endpoints import etiquetas
from app.api.v1.endpoints import produto_embalagem
from app.api.v1.endpoints import produto_regra_preco
from app.api.v1.endpoints import nfe_entrada
from app.api.v1.endpoints import compras
from app.api.v1.endpoints import fabrica
from app.api.v1.endpoints import marcenaria_orcamento, marcenaria_orcamento_itens
from app.services.marcenaria import ganchos as marcenaria_ganchos

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
# Inclui o roteador de movimentações de estoque sob o prefixo /produtos
# Contém sub-recursos: registrar movimentação e listar movimentações
#
# IMPORTANTE: precisa vir ANTES de produto.router. Desde que produto.py ganhou
# GET /produtos/{produto_id}, o caminho literal /produtos/movimentacoes passa a
# casar com {produto_id}, e o FastAPI tenta converter "movimentacoes" em int --
# devolvendo 422 numa rota que funcionava.
router.include_router(movimentacao_estoque.router, prefix="/produtos", tags=["Movimentações de Estoque"])
# Embalagens (fardo/caixa) — também antes de produto.router, pelo mesmo motivo.
router.include_router(produto_embalagem.router, prefix="/produtos", tags=["Embalagens do Produto"])
router.include_router(produto_regra_preco.router, prefix="/produtos", tags=["Regras de Preço do Produto"])
# Entrada de mercadoria pela XML da NF-e do fornecedor.
router.include_router(nfe_entrada.router, prefix="/estoque/nfe-entrada", tags=["Entrada por XML da NF-e"])

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

# Inclui o roteador de vendas (PDV) sob o prefixo /vendas
# Contém sub-recursos: itens do carrinho e ações de status (cancelar, finalizar)
router.include_router(venda.router, prefix="/vendas", tags=["Vendas"])

# Turno de caixa (abrir, sangria, suprimento, fechar).
# So responde quando a empresa liga `controlar_caixa`; sem isso o service
# recusa toda operacao -- a rota existir nao muda nada para quem nao usa.
router.include_router(sessao_caixa.router, prefix="/caixa", tags=["Caixa"])

# Cadastro duravel das maquinas. Separado de /licenca (que cuida da PRESENCA
# por HWID) porque sao dois tempos de vida: presenca some no logout, cadastro
# fica.
router.include_router(terminal.router, prefix="/terminais", tags=["Terminais"])

# Inclui o roteador de orcamentos sob o prefixo /orcamentos
router.include_router(orcamento.router, prefix="/orcamentos", tags=["Orcamentos"])

# Inclui o roteador do Dashboard sob o prefixo /dashboard
# Endpoints read-only para metricas, OS vencendo, estoque e vendas recentes
router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])

# Inclui o roteador de Relatorios sob o prefixo /relatorios
# Endpoints read-only de faturamento/analytics, protegidos por permissao
router.include_router(relatorios.router, prefix="/relatorios", tags=["Relatórios"])

# Inclui o roteador de configurações do sistema sob o prefixo /configuracoes
router.include_router(configuracao.router, prefix="/configuracoes", tags=["Configurações"])
router.include_router(comunicado.router, prefix="/comunicados", tags=["Comunicados"])

# Inclui o roteador de licença sob o prefixo /licenca
# Endpoint público (sem autenticação) para verificação de licença no boot
router.include_router(licenca.router, prefix="/licenca", tags=["Licença"])

# Inclui o roteador do checklist mobile (formulario web via QR code)
# Endpoints publicos autenticados por token HMAC + gerador de token via JWT
router.include_router(checklist_mobile.router, prefix="/checklist", tags=["Checklist Mobile"])

# Inclui o roteador de backup sob o prefixo /backup
# Restauracao de cadeia vinda da nuvem — exclusivo do Master
router.include_router(backup.router, prefix="/backup", tags=["Backup"])

# Inclui o roteador de Gestao Financeira sob o prefixo /financeiro
# Contas a pagar, plano de contas e contas bancarias. TODA rota exige o modulo
# FINANCEIRO na licenca (403 MODULO_NAO_CONTRATADO) alem da permissao do cargo.
router.include_router(financeiro.router, prefix="/financeiro", tags=["Financeiro"])

# Inclui o roteador do Centro Fiscal sob o prefixo /fiscal
# Documentos fiscais, resumo e pendencias globais da NF-e.
router.include_router(fiscal.router, prefix="/fiscal", tags=["Fiscal"])
# O lado fiscal do cadastro de produto (sugestão, campos, NCM, pré-validação).
# MESMO prefixo: saiu de fiscal.py pelo teto do PyArmor, e nenhuma URL mudou.
router.include_router(fiscal_produto.router, prefix="/fiscal", tags=["Fiscal"])

# Central de Etiquetas: modelos de layout compartilhados pela loja. Imprimir é
# papel do terminal (Tauri), não do backend -- ver docs/etiquetas-plano.md.
router.include_router(etiquetas.router, prefix="/etiquetas", tags=["Etiquetas"])
# Módulo de Compras (docs/compras-plano.md): o router inteiro exige o módulo
# COMPRAS na licença; cada rota, a linha "Compras" da tela de Cargos.
router.include_router(compras.router, prefix="/compras", tags=["Compras"])
# Marcenaria-fábrica (docs/marcenaria-fabrica-plano.md): o router inteiro só
# responde no segmento Marcenaria.
router.include_router(fabrica.router, prefix="/fabrica", tags=["Marcenaria-fábrica"])
# Orçamento de marcenaria (docs/marcenaria/, Spec 06A): tudo responde 404 fora
# de segmento com a capacidade `orcamento_tecnico`. Dois arquivos, um prefixo.
router.include_router(marcenaria_orcamento.router, prefix="/marcenaria/orcamentos", tags=["Marcenaria - Orçamento"])
router.include_router(marcenaria_orcamento_itens.router, prefix="/marcenaria/orcamentos", tags=["Marcenaria - Orçamento"])
# Spec 09A: a marcenaria reage a finalizacao/reabertura/cancelamento da OS (conta
# do RT do arquiteto). Nas OS dos outros segmentos os ganchos saem na hora.
marcenaria_ganchos.registrar()
