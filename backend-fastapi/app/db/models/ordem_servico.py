# ---------------------------------------------------------------------------
# ARQUIVO: db/models/ordem_servico.py
# DESCRICAO: Modelo SQLAlchemy para a tabela 'ordens_servico'.
# ---------------------------------------------------------------------------

from datetime import datetime
from sqlalchemy import Integer, String, Boolean, DateTime, Text, Enum as SqlAlchemyEnum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING

from app.db.base import Base
from app.core.enum import OrdemServicoStatus, OrdemServicoPrioridade

if TYPE_CHECKING:
    from .cliente import Cliente
    from .funcionario import Funcionario
    from .ordem_servico_equipamento import OrdemServicoEquipamento
    from .ordem_servico_item import OrdemServicoItem
    from .ordem_servico_pagamento import OrdemServicoPagamento
    from .ordem_servico_foto import OrdemServicoFoto


class OrdemServico(Base):
    """Modelo ORM que representa uma Ordem de Servico na tabela 'ordens_servico'."""

    __tablename__ = "ordens_servico"

    # --- Identificacao ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID unico da OS (PK)")
    numero_os: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False, doc="Numero sequencial da OS (ex: OS-2026-000001)")

    # --- Vinculos ---
    funcionario_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("funcionarios.id"), nullable=True, doc="ID do funcionario responsavel (FK)")
    equipamento_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ordem_servico_equipamentos.id"),
        nullable=False,
        doc="ID do equipamento usado na OS (FK)"
    )

    # --- Status e Prioridade ---
    status: Mapped[OrdemServicoStatus] = mapped_column(
        SqlAlchemyEnum(OrdemServicoStatus),
        default=OrdemServicoStatus.ABERTA,
        nullable=False,
        doc="Status atual da OS"
    )
    prioridade: Mapped[OrdemServicoPrioridade] = mapped_column(
        SqlAlchemyEnum(OrdemServicoPrioridade),
        default=OrdemServicoPrioridade.NORMAL,
        nullable=False,
        doc="Prioridade da OS"
    )

    # --- Descricao do Servico ---
    defeito_relatado: Mapped[str] = mapped_column(Text, nullable=False, doc="Defeito relatado pelo cliente")
    diagnostico: Mapped[Optional[str]] = mapped_column(Text, nullable=True, doc="Diagnostico tecnico")
    solucao: Mapped[Optional[str]] = mapped_column(Text, nullable=True, doc="Solucao aplicada")
   
    # --- Observações do Servico ---
    senha_aparelho: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, doc="Senha do aparelho")
    acessorios: Mapped[Optional[str]] = mapped_column(Text, nullable=True, doc="Acessorios entregues junto")
    condicoes_aparelho: Mapped[Optional[str]] = mapped_column(Text, nullable=True, doc="Condicoes fisicas do aparelho")
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True, doc="Observacoes gerais")

    # --- Financeiro (valores em centavos) ---
    valor_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="Valor total da OS (centavos)")
    desconto: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="Desconto aplicado (centavos)")
    valor_entrada: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="Valor de entrada (centavos)")
    garantia: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, doc="Garantia em dias")

    # --- Datas ---
    data_previsao: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, doc="Data prevista para conclusao")
    data_finalizacao: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, doc="Data de finalizacao efetiva")
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, doc="Data de criacao da OS")
    data_atualizacao: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, doc="Data da ultima atualizacao")

    # --- Status ---
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, doc="Status ativo (soft delete)")

    # --- Relacionamentos ---
    funcionario_rel: Mapped[Optional["Funcionario"]] = relationship(
        "Funcionario",
        back_populates="ordens_servico",
        doc="Funcionario responsavel"
    )
    equipamento_rel: Mapped["OrdemServicoEquipamento"] = relationship(
        "OrdemServicoEquipamento",
        back_populates="ordens_servico",
        doc="Equipamento utilizado nesta OS"
    )
    itens: Mapped[List["OrdemServicoItem"]] = relationship(
        "OrdemServicoItem",
        back_populates="ordem_servico",
        cascade="all, delete-orphan",
        doc="Itens/servicos da OS"
    )
    pagamentos: Mapped[List["OrdemServicoPagamento"]] = relationship(
        "OrdemServicoPagamento",
        back_populates="ordem_servico",
        cascade="all, delete-orphan",
        doc="Pagamentos da OS"
    )
    fotos: Mapped[List["OrdemServicoFoto"]] = relationship(
        "OrdemServicoFoto",
        back_populates="ordem_servico",
        cascade="all, delete-orphan",
        doc="Fotos da OS"
    )

    @property
    def cliente(self) -> Optional["Cliente"]:
        return self.equipamento_rel.cliente if self.equipamento_rel else None
