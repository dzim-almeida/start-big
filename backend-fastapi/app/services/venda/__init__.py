# ---------------------------------------------------------------------------
# ARQUIVO: services/venda/__init__.py
# DESCRICAO: Regras de negocio da venda (PDV e balcao).
#
# Era um arquivo so (venda.py, 37 KB) ate 13/10/2026; virou pacote:
#   guarda_fiscal.py   - trava: venda com documento fiscal ativo nao se altera
#   calculo.py         - total, desconto e conferencia dos pagamentos
#   consultas.py       - buscar uma venda, listar e resumo por status
#   cadastro.py        - criar, editar e apagar rascunho
#   itens.py           - incluir, editar e remover item
#   fila.py            - enviar ao caixa e devolver para a montagem
#   finalizacao.py     - finalizar (pagamentos, estoque, caixa)
#   status.py          - cancelar e reabrir
#   correcao_fiscal.py - corrigir dados fiscais da venda
#   atacado.py         - preco de atacado (era services/venda_atacado.py)
#   nota_fiscal.py     - dados fiscais da venda (era services/venda_nota_fiscal.py)
#
# Este __init__ reexporta o que era venda.py: `from app.services import venda`
# continua valendo como antes. atacado e nota_fiscal ficam nos submodulos, sem
# reexport: `from app.services.venda import atacado as venda_atacado`.
#
# TRAVA FISCAL: toda funcao que altera venda passa por
# _assert_sem_documento_fiscal_ativo (guarda_fiscal.py); o teste
# test_todos_os_mutadores_de_venda_chamam_o_guard confere pelo codigo-fonte.
# ---------------------------------------------------------------------------

from app.services.venda.guarda_fiscal import (
    _STATUS_FISCAIS_BLOQUEANTES,
    _documento_fiscal_bloqueante,
    _assert_sem_documento_fiscal_ativo,
)

from app.services.venda.calculo import (
    _recalc_total_sale,
    _aplly_discount,
    _linhas_sem_desconto,
    _payments_valid,
)

from app.services.venda.consultas import (
    get_sale_by_id,
    get_sales,
    get_sales_status,
)

from app.services.venda.cadastro import (
    create_sale,
    update_sale,
    delete_draft_sale,
)

from app.services.venda.itens import (
    add_item_to_sale,
    update_item_in_sale,
    remove_item_from_sale,
)

from app.services.venda.fila import (
    enviar_ao_caixa,
    devolver_para_montagem,
)

from app.services.venda.finalizacao import (
    finish_sale,
)

from app.services.venda.status import (
    cancel_sale,
    reopen_sale,
)

from app.services.venda.correcao_fiscal import (
    corrigir_dados_venda_fiscal,
)

__all__ = [
    "_STATUS_FISCAIS_BLOQUEANTES",
    "_documento_fiscal_bloqueante",
    "_assert_sem_documento_fiscal_ativo",
    "_recalc_total_sale",
    "_aplly_discount",
    "_linhas_sem_desconto",
    "_payments_valid",
    "get_sale_by_id",
    "get_sales",
    "get_sales_status",
    "create_sale",
    "update_sale",
    "delete_draft_sale",
    "add_item_to_sale",
    "update_item_in_sale",
    "remove_item_from_sale",
    "enviar_ao_caixa",
    "devolver_para_montagem",
    "finish_sale",
    "cancel_sale",
    "reopen_sale",
    "corrigir_dados_venda_fiscal",
]
