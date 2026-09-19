# ---------------------------------------------------------------------------
# ARQUIVO: app/services/perfil_tributario.py
# DESCRIÇÃO: Regras de negócio dos perfis tributários interestaduais —
#            escopo por empresa, 404 e a guarda "perfil em uso".
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.crud import perfil_tributario as crud
from app.db.models.perfil_tributario import PerfilTributario
from app.schemas.perfil_tributario import PerfilTributarioCreate, PerfilTributarioListItem


def listar_perfis(db: Session, empresa_id: int) -> list[PerfilTributarioListItem]:
    return [
        PerfilTributarioListItem(
            id=perfil.id,
            descricao=perfil.descricao,
            quantidade_regras=quantidade,
            data_atualizacao=perfil.data_atualizacao,
        )
        for perfil, quantidade in crud.listar_perfis_com_contagem(db, empresa_id)
    ]


def obter_perfil(db: Session, empresa_id: int, perfil_id: int) -> PerfilTributario:
    """O perfil da empresa, ou 404 — perfil de outra empresa é invisível."""
    perfil = crud.get_perfil(db, empresa_id, perfil_id)
    if perfil is None:
        raise HTTPException(status_code=404, detail="Perfil tributário não encontrado.")
    return perfil


def criar_perfil(db: Session, empresa_id: int, dados: PerfilTributarioCreate) -> PerfilTributario:
    return crud.criar_perfil(db, empresa_id, dados.descricao, _regras_como_dicts(dados))


def atualizar_perfil(db: Session, empresa_id: int, perfil_id: int, dados: PerfilTributarioCreate) -> PerfilTributario:
    perfil = obter_perfil(db, empresa_id, perfil_id)
    return crud.substituir_regras(db, perfil, dados.descricao, _regras_como_dicts(dados))


def deletar_perfil(db: Session, empresa_id: int, perfil_id: int) -> None:
    perfil = obter_perfil(db, empresa_id, perfil_id)
    _assert_nao_esta_em_uso(db, perfil)
    crud.deletar_perfil(db, perfil)


def _regras_como_dicts(dados: PerfilTributarioCreate) -> list[dict]:
    return [regra.model_dump() for regra in dados.regras]


def _assert_nao_esta_em_uso(db: Session, perfil: PerfilTributario) -> None:
    """Apagar um perfil vinculado deixaria produtos sem alíquota interestadual."""
    produtos = crud.produtos_que_usam(db, perfil.id)
    if not produtos:
        return
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "codigo": "PERFIL_EM_USO",
            "mensagem": (
                f"O perfil '{perfil.descricao}' está vinculado a {len(produtos)} produto(s): "
                f"{', '.join(produtos)}. Desvincule-os antes de excluir."
            ),
        },
    )
