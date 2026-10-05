"""
Importa todos os modelos para que Base.metadata seja populado.
Usado pelo Alembic env.py e pelo módulo de migrações.
"""

from app.db.models.usuario import Usuario  # noqa: F401
from app.db.models.funcionario import Funcionario  # noqa: F401
from app.db.models.cliente import Cliente, ClientePF  # noqa: F401
from app.db.models.endereco import Endereco  # noqa: F401
from app.db.models.token import TokenBlocklist  # noqa: F401
from app.db.models.produto import Produto  # noqa: F401
from app.db.models.estoque import Estoque  # noqa: F401
from app.db.models.fornecedor import Fornecedor  # noqa: F401
from app.db.models.servico import Servico  # noqa: F401
from app.db.models.produto_fotos import ProdutoFoto  # noqa: F401
from app.db.models.empresa import Empresa  # noqa: F401
from app.db.models.empresa_fiscal_settings import EmpresaFiscalSettings  # noqa: F401
from app.db.models.cargo import Cargo  # noqa: F401
from app.db.models.ordem_servico import OrdemServico  # noqa: F401
from app.db.models.objeto_servico import ObjetoServico  # noqa: F401
from app.db.models.ordem_servico_item import OrdemServicoItem  # noqa: F401
from app.db.models.ordem_servico_pagamento import OrdemServicoPagamento  # noqa: F401
from app.db.models.ordem_servico_foto import OrdemServicoFoto  # noqa: F401
from app.db.models.forma_pagamento import FormaPagamento  # noqa: F401
from app.db.models.configuracao_clientes import ConfiguracaoClientes  # noqa: F401
from app.db.models.configuracao_produtos import ConfiguracaoProdutos  # noqa: F401
from app.db.models.configuracao_os import ConfiguracaoOS  # noqa: F401
from app.db.models.configuracao_vendas import ConfiguracaoVendas  # noqa: F401
from app.db.models.configuracao_seguranca import ConfiguracaoSeguranca  # noqa: F401
from app.db.models.configuracao_licenca import ConfiguracaoLicenca  # noqa: F401
from app.db.models.configuracao_backup import ConfiguracaoBackup  # noqa: F401
from app.db.models.comunicado import Comunicado, ComunicadoLeitura  # noqa: F401
from app.db.models.sessao_caixa import SessaoCaixa  # noqa: F401
from app.db.models.venda import Venda  # noqa: F401
from app.db.models.venda_produto import ProdutoVenda  # noqa: F401
from app.db.models.venda_pagamento import PagamentoVenda  # noqa: F401
from app.db.models.log_produto import LogProduto  # noqa: F401
from app.db.models.movimentacao_estoque import MovimentacaoEstoque  # noqa: F401
from app.db.models.movimentacao_financeira import MovimentacaoFinanceira  # noqa: F401
from app.db.models.orcamento import Orcamento  # noqa: F401
from app.db.models.orcamento_produto import OrcamentoProduto  # noqa: F401
from app.db.models.contador_venda import ContadorVenda  # noqa: F401
from app.db.models.terminal_conectado import TerminalConectado  # noqa: F401
from app.db.models.terminal import Terminal  # noqa: F401

# --- Gestão financeira (Onda 1) ---
from app.db.models.plano_conta import PlanoConta  # noqa: F401
from app.db.models.conta_bancaria import ContaBancaria  # noqa: F401
from app.db.models.alerta_dispensado import AlertaDispensado  # noqa: F401
from app.db.models.conta_pagar import ContaPagar  # noqa: F401
from app.db.models.historico_financeiro import HistoricoFinanceiro  # noqa: F401
from app.db.models.conta_receber import ContaReceber  # noqa: F401

# --- Modulo fiscal (NF-e) ---
from app.db.models.produto_fiscal import ProdutoFiscal  # noqa: F401
from app.db.models.tributacao import TributacaoPadrao, RegraTributariaNcm  # noqa: F401
from app.db.models.ncm import Ncm  # noqa: F401
from app.db.models.servico_fiscal import ServicoFiscal  # noqa: F401
from app.db.models.venda_nota_fiscal import VendaNotaFiscal  # noqa: F401
from app.db.models.ordem_servico_nota_fiscal import OrdemServicoNotaFiscal  # noqa: F401
from app.db.models.documento_fiscal import DocumentoFiscal  # noqa: F401
from app.db.models.inutilizacao_fiscal import InutilizacaoFiscal  # noqa: F401
from app.db.models.aliquota_uf import AliquotaUF  # noqa: F401
from app.db.models.documento_fiscal_item import DocumentoFiscalItem  # noqa: F401
from app.db.models.perfil_tributario import PerfilTributario  # noqa: F401
from app.db.models.regra_perfil_tributario import RegraPerfilTributario  # noqa: F401

# --- Central de Etiquetas ---
from app.db.models.modelo_etiqueta import ModeloEtiqueta  # noqa: F401

# --- Embalagens do produto (fardo/caixa) ---
from app.db.models.produto_embalagem import ProdutoEmbalagem  # noqa: F401
# --- Regras de preço por quantidade (R2/R3) ---
from app.db.models.produto_regra_preco import ProdutoRegraPreco  # noqa: F401
from app.db.models.nota_entrada import NotaEntrada  # noqa: F401
from app.db.models.produto_codigo_fornecedor import ProdutoCodigoFornecedor  # noqa: F401

# --- Compras (docs/compras-plano.md) ---
from app.db.models.produto_fornecedor import ProdutoFornecedor  # noqa: F401
from app.db.models.pedido_compra import (  # noqa: F401
    PedidoCompra, PedidoCompraItem, PedidoCompraOrigem, PedidoCompraParcela,
)
from app.db.models.compra_log import CompraLog  # noqa: F401
from app.db.models.recebimento_compra import RecebimentoCompra, RecebimentoCompraItem  # noqa: F401

# --- Marcenaria-fábrica (docs/marcenaria-fabrica-plano.md) ---
from app.db.models.fabrica_orcamento import (  # noqa: F401
    FabricaOrcamento, FabricaAmbiente, FabricaMovel, FabricaMaterial, FabricaFaseLog,
)
