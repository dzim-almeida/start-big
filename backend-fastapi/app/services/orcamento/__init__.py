# ---------------------------------------------------------------------------
# ARQUIVO: services/orcamento/__init__.py
# DESCRICAO: Regras do orcamento (o pre-venda que vira venda).
#
# Era um arquivo so (orcamento.py) ate 13/10/2026; virou pacote:
#   calculo.py   - total e desconto
#   consultas.py - buscar um orcamento, listar e resumo por status
#   cadastro.py  - criar, editar e apagar
#   itens.py     - incluir, editar e remover item
#   conversao.py - converter o orcamento em venda
#
# Este __init__ reexporta tudo: `from app.services import orcamento` continua
# valendo como antes.
# ---------------------------------------------------------------------------

from app.services.orcamento.calculo import (
    _recalc_total_orcamento,
    _apply_discount,
)

from app.services.orcamento.consultas import (
    get_orcamento_by_id,
    get_orcamentos,
    get_orcamentos_status,
)

from app.services.orcamento.cadastro import (
    create_orcamento,
    update_orcamento,
    delete_orcamento,
)

from app.services.orcamento.itens import (
    add_item_to_orcamento,
    update_item_in_orcamento,
    remove_item_from_orcamento,
)

from app.services.orcamento.conversao import (
    converter_orcamento,
)

__all__ = [
    "_recalc_total_orcamento",
    "_apply_discount",
    "get_orcamento_by_id",
    "get_orcamentos",
    "get_orcamentos_status",
    "create_orcamento",
    "update_orcamento",
    "delete_orcamento",
    "add_item_to_orcamento",
    "update_item_in_orcamento",
    "remove_item_from_orcamento",
    "converter_orcamento",
]
