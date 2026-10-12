# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/produto/__init__.py
# DESCRICAO: Acesso ao banco de produtos e do livro de estoque.
#
# Ate 12/10/2026 eram arquivos soltos (produto.py e movimentacao_estoque.py). Viraram este pacote,
# um arquivo por assunto. Este __init__ reexporta tudo: `from app.db.crud import
# produto` continua valendo como antes.
# ---------------------------------------------------------------------------

from app.db.crud.produto.consultas import (
    _CAMPOS_BUSCA,
    _CAMPOS_EXATOS,
    _TETO_RESGATE,
    _LIMITE_RESGATE,
    _resgatar_por_similaridade,
    get_produto_by_search,
    get_produto_simple_by_search,
    get_produto_by_id,
    get_produto_by_code,
)

from app.db.crud.produto.escrita import (
    create_produto,
    update_produto,
)

from app.db.crud.produto.fotos import (
    get_produto_image_by_id,
    get_produto_principal_image,
    create_produto_image,
    delete_produto_image,
)

from app.db.crud.produto.movimentacao import (
    create_movimentacao,
    get_movimentacoes,
)

__all__ = [
    "_CAMPOS_BUSCA",
    "_CAMPOS_EXATOS",
    "_TETO_RESGATE",
    "_LIMITE_RESGATE",
    "_resgatar_por_similaridade",
    "get_produto_by_search",
    "get_produto_simple_by_search",
    "get_produto_by_id",
    "get_produto_by_code",
    "create_produto",
    "update_produto",
    "get_produto_image_by_id",
    "get_produto_principal_image",
    "create_produto_image",
    "delete_produto_image",
    "create_movimentacao",
    "get_movimentacoes",
]
