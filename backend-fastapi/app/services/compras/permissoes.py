# ---------------------------------------------------------------------------
# ARQUIVO: app/services/compras/permissoes.py
# DESCRIÇÃO: O que a linha "Compras" da tela de Cargos libera.
# ---------------------------------------------------------------------------
"""
Duas perguntas diferentes protegem o módulo, e as duas são necessárias:

1. A LOJA contratou? `requer_modulo("COMPRAS")` no router (403
   MODULO_NAO_CONTRATADO). É a trava comercial.
2. A PESSOA pode? As chaves abaixo, marcadas no cargo. É a trava interna.

Chaves (o frontend grava também `compra` quando alguma caixa da linha está
marcada, como faz com `etiqueta`):
- view_purchases   → Visualizar: ver fornecedores do produto, necessidades,
                     pedidos e custos;
- manage_purchases → Gerenciar: fornecedores do produto, criar/editar/enviar
                     pedidos;
- delete_purchases → Excluir: CANCELAR pedido (desfaz um compromisso já
                     mandado ao fornecedor — por isso separado de Gerenciar).

LINHA "RECEBIMENTO" (fase 3), separada, para o almoxarife (D14): a chave
genérica dela é `recebimento_compra`, gravada pelo frontend como a `compra`:
- view_receiving    → Visualizar: ver os pedidos a receber, SEM preço;
- receive_purchases → Gerenciar: dar entrada no que chegou.

CUSTO É UMA PERGUNTA À PARTE: `pode_ver_custos` só aceita as caixas da linha
Compras. Quem tem só a linha Recebimento confere quantidade, nunca preço — e o
custo real que ele mandar é ignorado (vale o do pedido).
"""

from typing import Any

from app.core.depends import check_permission

_CHAVES_RECEBIMENTO = ["recebimento_compra", "view_receiving", "receive_purchases"]

PERMISSOES_VER = ["compra", "view_purchases", "manage_purchases", "delete_purchases", *_CHAVES_RECEBIMENTO]
PERMISSOES_GERENCIAR = ["manage_purchases"]
PERMISSOES_CANCELAR = ["delete_purchases"]
# Receber: quem gerencia compras OU quem tem a caixa de receber.
PERMISSOES_RECEBER = ["manage_purchases", "receive_purchases"]
PERMISSOES_CUSTO = ("view_purchases", "manage_purchases", "delete_purchases")

permissao_ver = check_permission(required_permission=PERMISSOES_VER)
permissao_gerenciar = check_permission(required_permission=PERMISSOES_GERENCIAR)
permissao_cancelar = check_permission(required_permission=PERMISSOES_CANCELAR)
permissao_receber = check_permission(required_permission=PERMISSOES_RECEBER)
# Relatórios: só quem vê custo (as caixas da linha Compras), nunca quem só recebe.
permissao_custos = check_permission(required_permission=list(PERMISSOES_CUSTO))


def pode_ver_custos(usuario_token: dict[str, Any]) -> bool:
    """O usuário pode ver preço de compra? (D14)"""
    if usuario_token.get("is_master") is True:
        return True
    permissoes = usuario_token.get("permissoes") or {}
    if permissoes.get("all") is True:
        return True
    return any(permissoes.get(chave) is True for chave in PERMISSOES_CUSTO)
