# ---------------------------------------------------------------------------
# ARQUIVO: app/db/crud/lava_rapido/porte.py
# DESCRICAO: Consultas e escrita de portes e precos por porte (Spec 02A).
#            So acesso a dados: a regra fica em services/lava_rapido/portes.py.
# ---------------------------------------------------------------------------

from typing import List, Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.lava_rapido import PorteVeiculo, ServicoPrecoPorte
from app.db.models.servico import Servico


# =========================
# Portes
# =========================

def contar_portes(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(PorteVeiculo)) or 0


def listar_portes(db: Session, tipo_veiculo: Optional[str] = None,
                  incluir_inativos: bool = False) -> Sequence[PorteVeiculo]:
    consulta = select(PorteVeiculo)
    if tipo_veiculo:
        consulta = consulta.where(PorteVeiculo.tipo_veiculo == tipo_veiculo)
    if not incluir_inativos:
        consulta = consulta.where(PorteVeiculo.ativo.is_(True))
    consulta = consulta.order_by(PorteVeiculo.tipo_veiculo, PorteVeiculo.ordem, PorteVeiculo.id)
    return db.scalars(consulta).all()


def get_porte(db: Session, porte_id: int) -> Optional[PorteVeiculo]:
    return db.get(PorteVeiculo, porte_id)


def get_porte_por_nome(db: Session, tipo_veiculo: str, nome: str) -> Optional[PorteVeiculo]:
    """Comparacao sem diferenca de maiusculas: "suv" e "SUV" sao o mesmo porte."""
    return db.scalar(
        select(PorteVeiculo).where(
            PorteVeiculo.tipo_veiculo == tipo_veiculo,
            func.lower(PorteVeiculo.nome) == nome.lower(),
        )
    )


def proxima_ordem(db: Session, tipo_veiculo: str) -> int:
    maior = db.scalar(
        select(func.max(PorteVeiculo.ordem)).where(PorteVeiculo.tipo_veiculo == tipo_veiculo)
    )
    return (maior + 1) if maior is not None else 0


def adicionar_porte(db: Session, porte: PorteVeiculo) -> PorteVeiculo:
    db.add(porte)
    db.flush()
    return porte


# =========================
# Precos
# =========================

def listar_precos_do_servico(db: Session, servico_id: int) -> Sequence[ServicoPrecoPorte]:
    return db.scalars(
        select(ServicoPrecoPorte).where(ServicoPrecoPorte.servico_id == servico_id)
        .order_by(ServicoPrecoPorte.porte_id)
    ).all()


def substituir_precos_do_servico(db: Session, servico_id: int,
                                 linhas: List[ServicoPrecoPorte]) -> None:
    """Apaga a grade do servico e grava a nova (PUT da grade inteira)."""
    for antiga in listar_precos_do_servico(db, servico_id):
        db.delete(antiga)
    db.flush()                                   # a unique (servico, porte) nao colide
    db.add_all(linhas)
    db.flush()


def listar_servicos_ativos(db: Session) -> Sequence[Servico]:
    return db.scalars(
        select(Servico).where(Servico.ativo.is_(True)).order_by(Servico.descricao)
    ).all()


def precos_do_porte(db: Session, porte_id: int) -> dict:
    """{servico_id: ServicoPrecoPorte} de um porte."""
    linhas = db.scalars(
        select(ServicoPrecoPorte).where(ServicoPrecoPorte.porte_id == porte_id)
    ).all()
    return {linha.servico_id: linha for linha in linhas}
