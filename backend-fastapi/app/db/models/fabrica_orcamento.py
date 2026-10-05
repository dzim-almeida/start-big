# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/fabrica_orcamento.py
# DESCRIÇÃO: Orçamento por móvel da marcenaria-fábrica
#            (docs/marcenaria-fabrica-plano.md, §2 e §4; F2).
# ---------------------------------------------------------------------------
"""
A árvore é VERSÃO → AMBIENTE → MÓVEL → MATERIAL, pendurada na OS (D1). Uma
OS, várias versões, uma aprovada. Aprovar escreve os itens na OS
(services/fabrica/orcamentos.py) — a árvore continua aqui, para a margem por
móvel e para a próxima versão.

Prefixo `fabrica_` porque `orcamentos` já é o orçamento de venda do PDV.
Dinheiro em centavos, medidas em mm, consumo em mm²/mm/unidade, percentuais
em pontos-base (1000 = 10%) — tudo inteiro (plano, D4).
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SituacaoOrcamento:
    RASCUNHO = "RASCUNHO"
    ENVIADO = "ENVIADO"
    APROVADO = "APROVADO"
    RECUSADO = "RECUSADO"

    TODAS = (RASCUNHO, ENVIADO, APROVADO, RECUSADO)
    # VENCIDO não é gravado: é ENVIADO com a validade passada (ver `vencido`).


class FabricaOrcamento(Base):
    __tablename__ = "fabrica_orcamentos"
    __table_args__ = (UniqueConstraint("os_id", "versao", name="uq_fabrica_orcamento_os_versao"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    os_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ordens_servico.id", ondelete="CASCADE"), nullable=False, index=True
    )
    versao: Mapped[int] = mapped_column(Integer, nullable=False)
    situacao: Mapped[str] = mapped_column(String(20), nullable=False, default=SituacaoOrcamento.RASCUNHO)

    perda_bp: Mapped[int] = mapped_column(Integer, nullable=False, default=1000, doc="1000 = 10%")
    sinal_bp: Mapped[int] = mapped_column(Integer, nullable=False, default=5000, doc="5000 = 50%")
    validade: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0, doc="Σ preço dos móveis, centavos")
    custo_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0, doc="Σ custo dos móveis, centavos")
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    enviado_em: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    aprovado_em: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    aprovado_por: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    recusado_motivo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    ambientes = relationship(
        "FabricaAmbiente", back_populates="orcamento", cascade="all, delete-orphan",
        order_by="(FabricaAmbiente.ordem, FabricaAmbiente.id)",
    )

    def vencido(self, hoje: date) -> bool:
        return (
            self.situacao == SituacaoOrcamento.ENVIADO
            and self.validade is not None
            and self.validade < hoje
        )


class FabricaAmbiente(Base):
    __tablename__ = "fabrica_ambientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    orcamento_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fabrica_orcamentos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nome: Mapped[str] = mapped_column(String(60), nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    orcamento = relationship("FabricaOrcamento", back_populates="ambientes")
    moveis = relationship(
        "FabricaMovel", back_populates="ambiente", cascade="all, delete-orphan",
        order_by="(FabricaMovel.ordem, FabricaMovel.id)",
    )


class FabricaMovel(Base):
    __tablename__ = "fabrica_moveis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ambiente_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fabrica_ambientes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    largura_mm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    altura_mm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    profundidade_mm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    preco_venda: Mapped[int] = mapped_column(Integer, nullable=False, default=0, doc="Centavos")
    terceirizado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    custo_terceiro: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, doc="Centavos")
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Central de corte (F5): o pedido de SERVIÇO deste móvel. Nasce já, para a
    # F5 não precisar de migration.
    pedido_compra_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("pedidos_compra.id", ondelete="SET NULL"), nullable=True
    )

    ambiente = relationship("FabricaAmbiente", back_populates="moveis")
    materiais = relationship(
        "FabricaMaterial", back_populates="movel", cascade="all, delete-orphan",
        order_by="FabricaMaterial.id",
    )

    @property
    def medidas(self) -> Optional[str]:
        """"1800×700×350" — o que sai na proposta e no item da OS."""
        partes = [self.largura_mm, self.altura_mm, self.profundidade_mm]
        if not any(partes):
            return None
        return "×".join(str(p) if p else "—" for p in partes)


class FabricaMaterial(Base):
    __tablename__ = "fabrica_materiais"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    movel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fabrica_moveis.id", ondelete="CASCADE"), nullable=False, index=True
    )
    produto_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("produtos.id", ondelete="SET NULL"), nullable=True, index=True
    )
    descricao: Mapped[str] = mapped_column(String(255), nullable=False, doc="Nome do produto ao incluir")
    consumo: Mapped[int] = mapped_column(Integer, nullable=False, doc="Na unidade de consumo: mm², mm ou un")
    custo_unitario: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, doc="Centavos POR UNIDADE DE COMPRA, copiado do cadastro ao incluir"
    )

    movel = relationship("FabricaMovel", back_populates="materiais")
    produto = relationship("Produto", lazy="joined")


class EventoFase:
    AVANCO = "AVANCO"
    RETROCESSO = "RETROCESSO"
    APROVACAO = "APROVACAO"
    LIBERACAO_COMPRA = "LIBERACAO_COMPRA"
    AVISO_IGNORADO = "AVISO_IGNORADO"
    CANCELAMENTO = "CANCELAMENTO"
    REABERTURA = "REABERTURA"


class FabricaFaseLog(Base):
    """O que aconteceu com a OS no trilho (RC18). Só INSERT: nunca se edita."""

    __tablename__ = "fabrica_fases_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    os_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ordens_servico.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fase_anterior: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    fase_nova: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    evento: Mapped[str] = mapped_column(String(30), nullable=False)
    motivo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ocorrido_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
