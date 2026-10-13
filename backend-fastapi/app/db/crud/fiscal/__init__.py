# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/fiscal/__init__.py
# DESCRICAO: Acesso ao banco do modulo fiscal.
#
# Ate 13/10/2026 o crud fiscal era um arquivo so (db/crud/fiscal.py), e os
# cruds irmaos ficavam soltos. Vieram INTEIROS para esta pasta:
#   nucleo.py           - configuracao fiscal, numeracao, documentos e token da
#                         licenca (era db/crud/fiscal.py)
#   perfil_tributario.py - (era db/crud/perfil_tributario.py)
#   produto.py          - fiscal do produto (era db/crud/produto_fiscal.py)
#   servico.py          - fiscal do servico (era db/crud/servico_fiscal.py)
#   tributacao.py       - (era db/crud/tributacao.py)
#
# Este __init__ reexporta TUDO do nucleo: `from app.db.crud import fiscal as crud`
# e `crud.get_licenca_token(...)` continuam valendo como antes (34 lugares).
# Os testes que trocam `X.crud.get_licenca_token` trocam aqui no pacote, e quem
# chama usa `crud.<nome>` -- a troca chega. Nenhuma funcao do nucleo chama por
# dentro um nome que os testes trocam (conferido em 13/10/2026).
# Os irmaos ficam nos submodulos: `from app.db.crud.fiscal import tributacao`.
# ---------------------------------------------------------------------------

from app.db.crud.fiscal.nucleo import (
    get_empresa,
    get_endereco_empresa,
    get_fiscal_settings,
    reservar_proximo_numero_nfe,
    reservar_proximo_numero_nfce,
    get_produto_fiscal,
    get_servico_fiscal,
    get_venda_completa,
    get_os_completa,
    get_licenca_token,
    get_documento_fiscal,
    get_documento_by_tentativa_anterior,
    salvar_documento,
    STATUS_DOCUMENTO_VIVO,
    _SO_NOTA_DA_OPERACAO,
    get_documento_ativo_por_venda,
    get_documento_ativo_por_os,
    get_documentos_ativos_por_vendas,
    get_documentos_relevantes_por_vendas,
    get_vendas_completas_batch,
    get_venda_id_por_numero,
    contar_documentos_por_venda,
    contar_documentos_por_os,
    get_nomes_destinatarios_por_vendas,
    get_aliquota_uf,
)

__all__ = [
    "get_empresa",
    "get_endereco_empresa",
    "get_fiscal_settings",
    "reservar_proximo_numero_nfe",
    "reservar_proximo_numero_nfce",
    "get_produto_fiscal",
    "get_servico_fiscal",
    "get_venda_completa",
    "get_os_completa",
    "get_licenca_token",
    "get_documento_fiscal",
    "get_documento_by_tentativa_anterior",
    "salvar_documento",
    "STATUS_DOCUMENTO_VIVO",
    "_SO_NOTA_DA_OPERACAO",
    "get_documento_ativo_por_venda",
    "get_documento_ativo_por_os",
    "get_documentos_ativos_por_vendas",
    "get_documentos_relevantes_por_vendas",
    "get_vendas_completas_batch",
    "get_venda_id_por_numero",
    "contar_documentos_por_venda",
    "contar_documentos_por_os",
    "get_nomes_destinatarios_por_vendas",
    "get_aliquota_uf",
]
