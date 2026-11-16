# ---------------------------------------------------------------------------
# ARQUIVO: services/relatorio/acesso_comissoes.py
# DESCRICAO: Relatorios - o Master libera cargos para ver as comissoes (e o
#            extrato) de toda a equipe.
#
# Pedido do Alan (13/10/2026): numa empresa grande, o dono nao quer entrar na
# conta dele so para conferir quanto pagar de comissao; quer deixar isso com o
# gerente. O resto da visao da loja (ranking, estoque, contador, faturamento
# inteiro) continua so do Master.
#
# Tres decisoes, todas para nao mudar nada em loja que nao pediu:
#   - A liberacao e uma chave PROPRIA no JSON de permissoes do cargo. Nasce
#     desligada: nenhum cargo existente a tem.
#   - "all" (o "marcar tudo" da tela de cargos) NAO conta. Se contasse, todo
#     cargo que ja tem "all" passaria a ver as comissoes de todos na hora da
#     atualizacao, sem o dono ter pedido.
#   - O criterio e o cargo MARCADO, nunca o nome ("gerente"/"administrador"):
#     nome de cargo e fragil (ver test_relatorio.py, o teste do cargo Gerente).
#
# A tela de cargos preserva chaves que nao conhece (usePositionForm:
# normalizePermissions), entao editar o cargo por la nao apaga a liberacao.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.cargo import Cargo
from app.schemas.relatorio import AcessoComissoes, AcessoComissoesCargo

PERMISSAO_COMISSOES_EQUIPE = "ver_comissoes_equipe"

# As mesmas que abrem a tela de Relatorios (endpoints/relatorios.py: module_permission).
_PERMISSOES_DA_TELA = ("relatorio", "view_reports", "manage_reports")


def pode_ver_comissoes_equipe(user_token: dict) -> bool:
    """Master, ou cargo com a liberacao EXPLICITA (o "all" nao vale aqui)."""
    if user_token.get("is_master") is True:
        return True
    permissoes = user_token.get("permissoes") or {}
    return permissoes.get(PERMISSAO_COMISSOES_EQUIPE) is True


def _abre_relatorios(permissoes: dict) -> bool:
    return permissoes.get("all") is True or any(permissoes.get(p) is True for p in _PERMISSOES_DA_TELA)


def _cargos_da_empresa(db: Session, empresa_id: int) -> list[Cargo]:
    return list(db.scalars(
        select(Cargo).where(Cargo.empresa_id == empresa_id).order_by(Cargo.nome, Cargo.id)
    ).all())


def listar_acesso(db: Session, empresa_id: int) -> AcessoComissoes:
    """Todos os cargos da empresa, com a liberacao de cada um."""
    return AcessoComissoes(cargos=[
        AcessoComissoesCargo(
            id=cargo.id,
            nome=cargo.nome,
            liberado=(cargo.permissoes or {}).get(PERMISSAO_COMISSOES_EQUIPE) is True,
            abre_relatorios=_abre_relatorios(cargo.permissoes or {}),
        )
        for cargo in _cargos_da_empresa(db, empresa_id)
    ])


def definir_acesso(db: Session, empresa_id: int, cargo_ids: list[int]) -> AcessoComissoes:
    """
    Deixa liberados exatamente os cargos de `cargo_ids`; os outros perdem a liberacao.

    So mexe na chave da liberacao: as demais permissoes do cargo ficam como estao.
    """
    cargos = _cargos_da_empresa(db, empresa_id)
    desconhecidos = set(cargo_ids) - {cargo.id for cargo in cargos}
    if desconhecidos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cargo não encontrado: {', '.join(str(i) for i in sorted(desconhecidos))}",
        )

    liberar = set(cargo_ids)
    for cargo in cargos:
        atual = dict(cargo.permissoes or {})
        if cargo.id in liberar:
            atual[PERMISSAO_COMISSOES_EQUIPE] = True
        else:
            atual.pop(PERMISSAO_COMISSOES_EQUIPE, None)
        if atual != (cargo.permissoes or {}):
            # Dict NOVO: coluna JSON sem MutableDict so grava se o objeto trocar.
            cargo.permissoes = atual
    db.flush()
    return listar_acesso(db, empresa_id)
