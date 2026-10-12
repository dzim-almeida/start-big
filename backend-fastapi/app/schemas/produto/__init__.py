# ---------------------------------------------------------------------------
# ARQUIVO: schemas/produto/__init__.py
# DESCRICAO: Schemas Pydantic de produtos e estoque.
#
# Ate 12/10/2026 eram cinco arquivos soltos em schemas/ (produto.py, estoque.py,
# movimentacao_estoque.py, produto_embalagem.py e produto_fotos.py). Viraram
# este pacote; este __init__ reexporta tudo: importe de `app.schemas.produto`.
# ---------------------------------------------------------------------------

from app.schemas.produto.cadastro import (
    ProdutoCreate,
    ProdutoCreateComFiscal,
    ProdutoRead,
    EmbalagemPdvRead,
    ProdutoSimpleRead,
    ProdutoUpdate,
)

from app.schemas.produto.estoque import (
    EstoqueCreate,
    EstoqueRead,
    EstoqueUpdate,
)

from app.schemas.produto.movimentacao import (
    MovimentacaoCreate,
    MovimentacaoRead,
)

from app.schemas.produto.embalagem import (
    MAX_EMBALAGENS,
    _SIGLA,
    _CODIGO,
    EmbalagemBase,
    EmbalagemEscrita,
    EmbalagensSalvar,
    EmbalagemRead,
)

from app.schemas.produto.fotos import (
    ProdutoFotoRead,
)

__all__ = [
    "ProdutoCreate",
    "ProdutoCreateComFiscal",
    "ProdutoRead",
    "EmbalagemPdvRead",
    "ProdutoSimpleRead",
    "ProdutoUpdate",
    "EstoqueCreate",
    "EstoqueRead",
    "EstoqueUpdate",
    "MovimentacaoCreate",
    "MovimentacaoRead",
    "MAX_EMBALAGENS",
    "_SIGLA",
    "_CODIGO",
    "EmbalagemBase",
    "EmbalagemEscrita",
    "EmbalagensSalvar",
    "EmbalagemRead",
    "ProdutoFotoRead",
]
