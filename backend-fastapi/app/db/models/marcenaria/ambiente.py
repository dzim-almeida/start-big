# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/marcenaria/ambiente.py
# DESCRICAO: A arvore do orcamento: ambiente -> movel -> insumo (Spec 06A, D1).
# ---------------------------------------------------------------------------
"""
Ambiente ("Cozinha Gourmet") tem moveis ("Torre Quente"), e cada movel tem os
insumos que consome (chapa, fita, ferragem).

O insumo guarda COPIA do produto (D2): descricao, codigo, unidade, custo e
`sofre_perda`. Mudar o produto depois nunca muda um orcamento sem aviso (O3);
a tela de "precos desatualizados" mostra a diferenca e o usuario decide.

Unidades (D10): quantidade de insumo em MILESIMOS (1,4 chapa = 1400), horas em
CENTESIMOS (2,5 h = 250), medidas em milimetros, dinheiro em centavos.
"""

from datetime import date
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.fornecedor import Fornecedor
    from app.db.models.marcenaria.etapa import MarcenariaEtapa
    from app.db.models.marcenaria.orcamento import MarcenariaOrcamento


class MarcenariaAmbiente(Base):
    """Um comodo do projeto. A ordem e a da tela e da proposta."""
    __tablename__ = "marcenaria_ambientes"
    __table_args__ = (Index("ix_marcenaria_ambientes_orcamento", "orcamento_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    orcamento_id: Mapped[int] = mapped_column(
        ForeignKey("marcenaria_orcamentos.id", ondelete="CASCADE"), nullable=False,
    )
    nome: Mapped[str] = mapped_column(String(80), nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)

    orcamento: Mapped["MarcenariaOrcamento"] = relationship("MarcenariaOrcamento", back_populates="ambientes")
    # Apagar o ambiente apaga os moveis (e, deles, os insumos).
    moveis: Mapped[List["MarcenariaMovel"]] = relationship(
        "MarcenariaMovel",
        back_populates="ambiente",
        cascade="all, delete-orphan",
        order_by="(MarcenariaMovel.ordem, MarcenariaMovel.id)",
    )


class MarcenariaMovel(Base):
    """Um movel do ambiente: medidas, quantidade, producao e mao de obra."""
    __tablename__ = "marcenaria_moveis"
    __table_args__ = (
        Index("ix_marcenaria_moveis_ambiente", "ambiente_id"),
        Index("ix_marcenaria_moveis_os_item", "os_item_id"),          # Spec 08A
        Index("ix_marcenaria_moveis_pedido", "pedido_compra_id"),     # Spec 11A
        Index("ix_marcenaria_moveis_terc", "terc_situacao", "terc_previsao"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ambiente_id: Mapped[int] = mapped_column(
        ForeignKey("marcenaria_ambientes.id", ondelete="CASCADE"), nullable=False,
    )
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)   # sai na proposta
    largura_mm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    altura_mm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    profundidade_mm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # INTERNA = a loja fabrica; TERCEIRIZADA = pedido a uma central parceira (E6).
    tipo_producao: Mapped[str] = mapped_column(String(12), nullable=False, default="INTERNA")
    central_fornecedor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("fornecedores.id"), nullable=True)
    terceirizado_centavos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)   # custo por unidade

    # Mao de obra por unidade: FIXA (valor), HORAS (x custo/hora) ou NENHUMA.
    mao_obra_modo: Mapped[str] = mapped_column(String(8), nullable=False, default="NENHUMA")
    mao_obra_centavos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mao_obra_horas_centesimos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # NULL ate a aprovacao (Spec 08A, O4): na aprovacao parcial, so os True viram OS.
    aprovado: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    # O item da OS que este movel virou (08A, D7). O vinculo fica so aqui, e nao
    # nos dados da OS: o formulario da OS regrava aqueles dados inteiros.
    os_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("ordem_servico_itens.id", ondelete="SET NULL"), nullable=True,
    )
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- Movel TERCEIRIZADO depois da aprovacao (Spec 11A) ------------------------
    # Com o Compras: o pedido de SERVICO a central; a situacao acompanha o pedido.
    pedido_compra_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("pedidos_compra.id", ondelete="SET NULL"), nullable=True,
    )
    # Sem o Compras: o acompanhamento anotado a mao (nulo = "A pedir").
    terc_situacao: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)   # ENVIADO/RECEBIDO/CONFERIDO
    terc_pedido: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)     # o numero que a central deu
    terc_enviado_em: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    terc_previsao: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    terc_recebido_em: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # Nos dois modos: a fabrica conferiu (pronto para instalar) ou achou problema.
    terc_conferido_em: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    terc_problema: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    ambiente: Mapped["MarcenariaAmbiente"] = relationship("MarcenariaAmbiente", back_populates="moveis")
    central: Mapped[Optional["Fornecedor"]] = relationship("Fornecedor")
    # O PUT do movel substitui a lista: insumo que nao veio e removido (delete-orphan).
    insumos: Mapped[List["MarcenariaMovelInsumo"]] = relationship(
        "MarcenariaMovelInsumo",
        back_populates="movel",
        cascade="all, delete-orphan",
        order_by="(MarcenariaMovelInsumo.ordem, MarcenariaMovelInsumo.id)",
    )
    # Spec 12A: as etapas de producao (so do movel INTERNO aprovado). Sair da
    # lista = apagar a etapa (delete-orphan), como os insumos.
    etapas: Mapped[List["MarcenariaEtapa"]] = relationship(
        "MarcenariaEtapa",
        back_populates="movel",
        cascade="all, delete-orphan",
        order_by="(MarcenariaEtapa.ordem, MarcenariaEtapa.id)",
    )


class MarcenariaMovelInsumo(Base):
    """Um insumo do movel, com a COPIA do produto no momento da inclusao (D2, D3)."""
    __tablename__ = "marcenaria_movel_insumos"
    __table_args__ = (
        Index("ix_marcenaria_movel_insumos_movel", "movel_id"),
        # Ajuda a atualizacao de precos (O3) e a reserva de estoque (Spec 10A).
        Index("ix_marcenaria_movel_insumos_produto", "produto_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movel_id: Mapped[int] = mapped_column(
        ForeignKey("marcenaria_moveis.id", ondelete="CASCADE"), nullable=False,
    )
    # O produto pode sumir do cadastro: o insumo fica, com a copia (SET NULL).
    produto_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("produtos.id", ondelete="SET NULL"), nullable=True,
    )
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)   # copia do nome
    codigo: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)   # copia do SKU
    unidade: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)   # copia da unidade
    quantidade_milesimos: Mapped[int] = mapped_column(Integer, nullable=False)
    custo_unit_centavos: Mapped[int] = mapped_column(Integer, nullable=False)
    # De onde veio o custo: ULTIMA_COMPRA | CUSTO_MEDIO | SEM_CUSTO | MANUAL.
    custo_origem: Mapped[str] = mapped_column(String(14), nullable=False)
    sofre_perda: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)

    movel: Mapped["MarcenariaMovel"] = relationship("MarcenariaMovel", back_populates="insumos")
