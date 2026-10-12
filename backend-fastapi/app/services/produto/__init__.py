# ---------------------------------------------------------------------------
# ARQUIVO: services/produto/__init__.py
# DESCRICAO: Produtos e estoque - cadastro, fotos, baixa/devolucao de
#            estoque, movimentacao (custo medio) e embalagens.
#
# Ate 12/10/2026 eram arquivos soltos (produto.py, movimentacao_estoque.py e produto_embalagem.py). Viraram este pacote,
# um arquivo por assunto. Este __init__ reexporta tudo: `from app.services import
# produto` continua valendo como antes.
# ---------------------------------------------------------------------------

from app.services.produto.cadastro import (
    conflict_codigo_produto_exce,
    not_found_exce,
    internal_error_exce,
    _bad_request_exce,
    create_produto,
    get_produto_by_search,
    get_produto_simple_by_search,
    _CAMPO_LEGIVEL,
    _build_observacao_edicao,
    _registrar_edicao,
    update_produto_by_id,
    toggle_active_disable_produto_by_id,
    get_produto_by_id,
)

from app.services.produto.fotos import (
    create_produto_image,
    replace_produto_principal_image,
    delete_produto_image,
)

from app.services.produto.estoque import (
    _usuario_do_funcionario,
    decrease_product_in_stock,
    restore_product_to_stock,
)

from app.services.produto.movimentacao import (
    not_found_produto,
    estoque_insuficiente,
    quantidade_invalida,
    produto_sem_estoque,
    custo_atual,
    calcular_custo_medio,
    registrar_movimentacao,
    _resolver_custo,
    create_movimentacao,
    _embalagem_da_entrada,
    get_movimentacoes,
)

from app.services.produto.embalagem import (
    CAMPOS,
    _conflito,
    _produto,
    onde_o_codigo_esta,
    listar,
    salvar,
    codigo_de_produto_livre,
    embalagens_ligadas,
    embalagem_para_venda,
    exigir_embalagem_fechada,
    aplicar_embalagem_na_linha,
)

__all__ = [
    "conflict_codigo_produto_exce",
    "not_found_exce",
    "internal_error_exce",
    "_bad_request_exce",
    "create_produto",
    "get_produto_by_search",
    "get_produto_simple_by_search",
    "_CAMPO_LEGIVEL",
    "_build_observacao_edicao",
    "_registrar_edicao",
    "update_produto_by_id",
    "toggle_active_disable_produto_by_id",
    "get_produto_by_id",
    "create_produto_image",
    "replace_produto_principal_image",
    "delete_produto_image",
    "_usuario_do_funcionario",
    "decrease_product_in_stock",
    "restore_product_to_stock",
    "not_found_produto",
    "estoque_insuficiente",
    "quantidade_invalida",
    "produto_sem_estoque",
    "custo_atual",
    "calcular_custo_medio",
    "registrar_movimentacao",
    "_resolver_custo",
    "create_movimentacao",
    "_embalagem_da_entrada",
    "get_movimentacoes",
    "CAMPOS",
    "_conflito",
    "_produto",
    "onde_o_codigo_esta",
    "listar",
    "salvar",
    "codigo_de_produto_livre",
    "embalagens_ligadas",
    "embalagem_para_venda",
    "exigir_embalagem_fechada",
    "aplicar_embalagem_na_linha",
]
