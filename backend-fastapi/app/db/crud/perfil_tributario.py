# ---------------------------------------------------------------------------
# ARQUIVO: app/db/crud/perfil_tributario.py
# MÓDULO: Repository — Perfis tributários interestaduais e suas regras
# ---------------------------------------------------------------------------

from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models.perfil_tributario import PerfilTributario
from app.db.models.regra_perfil_tributario import RegraPerfilTributario


def listar_perfis_com_contagem(db: Session, empresa_id: int) -> Sequence[tuple[PerfilTributario, int]]:
    """Os perfis da empresa, por descrição, cada um com quantas regras tem.

    Não carrega as regras: a listagem só mostra a contagem.
    """
    contagem = (
        select(RegraPerfilTributario.perfil_id, func.count().label("quantidade"))
        .group_by(RegraPerfilTributario.perfil_id)
        .subquery()
    )
    stmt = (
        select(PerfilTributario, func.coalesce(contagem.c.quantidade, 0))
        .outerjoin(contagem, contagem.c.perfil_id == PerfilTributario.id)
        .where(PerfilTributario.empresa_id == empresa_id)
        .order_by(PerfilTributario.descricao)
    )
    return [(perfil, int(quantidade)) for perfil, quantidade in db.execute(stmt)]


def get_perfil(db: Session, empresa_id: int, perfil_id: int) -> Optional[PerfilTributario]:
    """O perfil com as regras carregadas — só se for da empresa."""
    stmt = (
        select(PerfilTributario)
        .options(selectinload(PerfilTributario.regras))
        .where(PerfilTributario.id == perfil_id, PerfilTributario.empresa_id == empresa_id)
    )
    return db.scalars(stmt).first()


def _novas_regras(regras: list[dict]) -> list[RegraPerfilTributario]:
    return [RegraPerfilTributario(**campos) for campos in regras]


def criar_perfil(db: Session, empresa_id: int, descricao: str, regras: list[dict]) -> PerfilTributario:
    perfil = PerfilTributario(empresa_id=empresa_id, descricao=descricao)
    perfil.regras = _novas_regras(regras)
    db.add(perfil)
    db.flush()
    db.refresh(perfil)
    return perfil


def substituir_regras(db: Session, perfil: PerfilTributario, descricao: str, regras: list[dict]) -> PerfilTributario:
    """Replace-all: as regras antigas saem (delete-orphan) e as novas entram.

    O flush no meio é obrigatório: a unit of work do SQLAlchemy faz os INSERTs
    antes dos DELETEs da mesma tabela, e reenviar a regra de SP com outra
    alíquota colidiria na UNIQUE (perfil, uf, ncm) com a linha que ainda não
    saiu. Tudo continua na mesma transação -- se algo falhar, nada muda.
    """
    perfil.descricao = descricao
    perfil.regras.clear()
    db.flush()
    perfil.regras = _novas_regras(regras)
    db.flush()
    db.refresh(perfil)
    return perfil


def deletar_perfil(db: Session, perfil: PerfilTributario) -> None:
    db.delete(perfil)
    db.flush()


def produtos_que_usam(db: Session, perfil_id: int) -> list[str]:
    """Nomes dos produtos vinculados ao perfil — guarda da exclusão.

    Até a TASK006 não existe `produto_fiscal.perfil_tributario_id`; nenhum
    produto aponta para perfil e a lista é sempre vazia. A TASK006 troca o
    corpo desta função pela consulta real sem mexer no serviço nem no endpoint.
    """
    return []
