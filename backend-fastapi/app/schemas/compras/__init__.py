# ---------------------------------------------------------------------------
# ARQUIVO: schemas/compras/__init__.py
# MÓDULO: Schemas Pydantic — Compras (docs/compras-plano.md)
#
# Era um arquivo so (compras.py) ate 13/10/2026; virou pacote:
#   fornecedores.py - fornecedores do produto e produto para pedido
#   pedidos.py      - pedido (escrita, leitura, listagem, parcelas, mensagem)
#                     e a LEITURA do recebimento (o pedido mostra os seus)
#   necessidades.py - o que comprar, alternativas e gerar pedidos
#   recebimentos.py - ESCRITA do recebimento
#   relatorios.py   - fornecedores e variacao de preco
#   demanda_os.py   - compras de uma OS
#   nfe_entrada.py  - importacao da NF-e de entrada (era schemas/nfe_entrada.py)
#
# Este __init__ reexporta tudo: `from app.schemas.compras import ...` continua
# valendo como antes.
# ---------------------------------------------------------------------------
"""(Texto de quando era schemas/compras.py; vale para o pacote inteiro.)

Fase 1: fornecedores do produto. Chegam e saem EM BLOCO (replace-all, como
as embalagens): a tela manda a lista inteira, e o que não veio sai.
Espelho no frontend: `modules/compras/shared/types/compras.types.ts`.

Preço em centavos por UNIDADE DE COMPRA (o fardo, se compra em fardo).
Campos de preço saem nulos para quem não pode ver custo (D14).
"""

from app.schemas.compras.fornecedores import (
    MAX_FORNECEDORES_POR_PRODUTO,
    FornecedorResumo,
    FornecedorDoProdutoRead,
    FornecedorDoProdutoEscrita,
    FornecedoresDoProdutoSalvar,
    EmbalagemResumo,
    ProdutoParaPedido,
)

from app.schemas.compras.pedidos import (
    MAX_ITENS_POR_PEDIDO,
    MAX_PARCELAS_POR_PEDIDO,
    PedidoItemEscrita,
    PedidoParcelaEscrita,
    PedidoEscrita,
    PedidoDadosEscrita,
    MotivoEscrita,
    PedidoItemRead,
    PedidoParcelaRead,
    CompraLogRead,
    RecebimentoItemRead,
    RecebimentoRead,
    PedidoResumo,
    PedidoRead,
    PedidoListagem,
    MensagemFornecedor,
    SimularParcelas,
    ParcelaSimulada,
)

from app.schemas.compras.necessidades import (
    AlternativaMaisBarata,
    OpcaoFornecedor,
    DemandaOSRead,
    NecessidadeItem,
    NecessidadeGrupo,
    GerarPedidoItem,
    GerarPedidos,
)

from app.schemas.compras.recebimentos import (
    RecebimentoItemEscrita,
    RecebimentoEscrita,
)

from app.schemas.compras.relatorios import (
    RelatorioFornecedor,
    VariacaoPreco,
    RelatorioCompras,
)

from app.schemas.compras.demanda_os import (
    PedidoDaOS,
    CompraDaOSItem,
    ComprasDaOS,
)

from app.schemas.compras.nfe_entrada import (
    FornecedorPrevia,
    ProdutoPrevia,
    FiscalSugerido,
    ItemPrevia,
    PedidoAbertoPrevia,
    DuplicataPrevia,
    NotaPrevia,
    ProdutoNovo,
    DecisaoItem,
    ImportarNota,
    EntradaLancada,
    ResultadoImportacao,
    NotaEntradaRead,
)

__all__ = [
    "MAX_FORNECEDORES_POR_PRODUTO",
    "FornecedorResumo",
    "FornecedorDoProdutoRead",
    "FornecedorDoProdutoEscrita",
    "FornecedoresDoProdutoSalvar",
    "EmbalagemResumo",
    "ProdutoParaPedido",
    "MAX_ITENS_POR_PEDIDO",
    "MAX_PARCELAS_POR_PEDIDO",
    "PedidoItemEscrita",
    "PedidoParcelaEscrita",
    "PedidoEscrita",
    "PedidoDadosEscrita",
    "MotivoEscrita",
    "PedidoItemRead",
    "PedidoParcelaRead",
    "CompraLogRead",
    "RecebimentoItemRead",
    "RecebimentoRead",
    "PedidoResumo",
    "PedidoRead",
    "PedidoListagem",
    "MensagemFornecedor",
    "SimularParcelas",
    "ParcelaSimulada",
    "AlternativaMaisBarata",
    "OpcaoFornecedor",
    "DemandaOSRead",
    "NecessidadeItem",
    "NecessidadeGrupo",
    "GerarPedidoItem",
    "GerarPedidos",
    "RecebimentoItemEscrita",
    "RecebimentoEscrita",
    "RelatorioFornecedor",
    "VariacaoPreco",
    "RelatorioCompras",
    "PedidoDaOS",
    "CompraDaOSItem",
    "ComprasDaOS",
    "FornecedorPrevia",
    "ProdutoPrevia",
    "FiscalSugerido",
    "ItemPrevia",
    "PedidoAbertoPrevia",
    "DuplicataPrevia",
    "NotaPrevia",
    "ProdutoNovo",
    "DecisaoItem",
    "ImportarNota",
    "EntradaLancada",
    "ResultadoImportacao",
    "NotaEntradaRead",
]
