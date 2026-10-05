# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fabrica/permissoes.py
# DESCRIÇÃO: O que a linha "Fábrica" da tela de Cargos libera (F3).
# ---------------------------------------------------------------------------
"""
A linha só aparece no segmento Marcenaria e não conta no nível do cargo (como
as linhas de Compras). O frontend grava a chave genérica `fabrica` quando
alguma caixa dela está marcada.

- view_fabrica   → Visualizar: ver CUSTO e MARGEM do orçamento;
- manage_fabrica → Gerenciar: montar o orçamento, enviar, registrar a resposta
                   do cliente, liberar compra antes do sinal. Inclui ver custo.

Quem só tem a permissão da OS (`servico`) — o marceneiro, o montador — vê a
aba Orçamento sem custo, avança e volta etapas, marca a instalação. Não muda
o orçamento nem libera compra.
"""

from typing import Any

from app.core.depends import check_permission

PERMISSOES_GERENCIAR = ["manage_fabrica"]
PERMISSOES_CUSTO = ("view_fabrica", "manage_fabrica")

permissao_os = check_permission(required_permission="servico")
permissao_gerenciar = check_permission(required_permission=PERMISSOES_GERENCIAR)


def pode_ver_custos(usuario_token: dict[str, Any]) -> bool:
    if usuario_token.get("is_master") is True:
        return True
    permissoes = usuario_token.get("permissoes") or {}
    if permissoes.get("all") is True:
        return True
    return any(permissoes.get(chave) is True for chave in PERMISSOES_CUSTO)


def nome_do_usuario(usuario_token: dict[str, Any]) -> str:
    return usuario_token.get("nome") or "Desconhecido"
