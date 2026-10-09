# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/permissoes.py
# DESCRICAO: O que a linha "Custos da Marcenaria" da tela de Cargos libera
#            (Spec 04A, D8-D11).
# ---------------------------------------------------------------------------
"""
As chaves abaixo SAO AS MESMAS da matriz de cargos do frontend
(positions.constants.ts, Spec 04B): o cargo grava a chave e o backend confere a
mesma chave, como no financeiro (view_financeiro/manage_financeiro). Por isso
elas NAO entram no MODULE_PERMISSION_MAP do frontend.

- view_custos_marcenaria   -> ver custo, margem, markup, perda, custo/hora e RT;
- manage_custos_marcenaria -> alterar os parametros de preco da marcenaria.
  Quem gere tambem ve (D8).

As chaves view_fabrica/manage_fabrica da fabrica aposentada NAO sao
reaproveitadas: significavam outra coisa (orcar e liberar compra).
"""

from typing import Any

VER_CUSTOS_MARCENARIA = "view_custos_marcenaria"        # ver custos e margens
GERIR_CUSTOS_MARCENARIA = "manage_custos_marcenaria"    # alterar os parametros de preco

# Listas para o check_permission e para o recorte do GET.
PERMISSOES_VER_CUSTOS = [VER_CUSTOS_MARCENARIA, GERIR_CUSTOS_MARCENARIA]   # quem gere tambem ve
PERMISSOES_GERIR_CUSTOS = [GERIR_CUSTOS_MARCENARIA]


def pode_ver_custos_marcenaria(usuario_token: dict[str, Any]) -> bool:
    """Mesma regra do check_permission, sem levantar erro (D9, D11).

    Serve para RECORTAR uma resposta (quem nao ve custo recebe so a parte sem
    custo), e nao para barrar a rota inteira.
    """
    if usuario_token.get("is_master") is True:          # dono da loja: ve tudo
        return True
    permissoes = usuario_token.get("permissoes") or {}  # o que o cargo marcou
    if permissoes.get("all") is True:                   # cargo com acesso total
        return True
    return any(permissoes.get(chave) is True for chave in PERMISSOES_VER_CUSTOS)
