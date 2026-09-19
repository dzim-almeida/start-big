# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/regra_perfil_tributario.py
# DESCRIÇÃO: Uma regra interestadual de um perfil tributário — as alíquotas
#            para uma UF de destino (e, opcionalmente, um NCM).
# ---------------------------------------------------------------------------
"""
Hierarquia de match (resolvida no serviço, TASK007/008):

    | Prioridade | uf_destino | ncm_excecao | Significado                          |
    |------------|------------|-------------|--------------------------------------|
    | 1          | "SP"       | "85171200"  | Celulares vendidos para SP           |
    | 2          | "SP"       | NULL        | Qualquer produto vendido para SP     |
    | 3 fallback | NULL       | NULL        | Qualquer produto para qualquer UF    |

O fallback garante que toda operação encontre resposta mesmo sem regra por UF.

Percentuais em centésimos de ponto percentual, como no resto do sistema
(1200 = 12,00%; ver `AliquotaUF`, `ProdutoFiscal.aliquota_icms`). O resolver
converte para Decimal na hora do cálculo.

A UNIQUE (perfil_id, uf_destino, ncm_excecao) não impede dois fallbacks:
o SQLite trata NULL como distinto. Essa unicidade fica na camada de serviço.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.perfil_tributario import PerfilTributario


class RegraPerfilTributario(Base):
    """As alíquotas interestaduais de um perfil para uma UF de destino."""

    __tablename__ = "regra_perfil_tributario"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, doc="Identificador da regra"
    )
    perfil_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("perfil_tributario.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Perfil ao qual a regra pertence",
    )
    uf_destino: Mapped[Optional[str]] = mapped_column(
        String(2), nullable=True, doc="UF de destino (ex: 'SP'). NULL = regra de fallback"
    )
    ncm_excecao: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, doc="NCM específico (ex: '85171200'). NULL = vale para todos os NCMs"
    )

    aliquota_interestadual: Mapped[int] = mapped_column(
        Integer, nullable=False, doc="Alíquota interestadual em centésimos (1200 = 12,00%)"
    )
    aliquota_interna_destino: Mapped[int] = mapped_column(
        Integer, nullable=False, doc="Alíquota interna da UF de destino em centésimos (1800 = 18,00%)"
    )
    percentual_fcp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        doc="Fundo de Combate à Pobreza em centésimos (200 = 2,00%)",
    )
    calculo_base_dupla: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
        doc="True = DIFAL pela fórmula de base dupla (por dentro); False = base única",
    )

    # Substituição tributária — preenchido só quando o perfil tem ST (TASK008)
    mva_st: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="Margem de Valor Agregado do ST em centésimos. Preenchido e > 0 = há ST"
    )
    reducao_base_calculo: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="Redução da base de cálculo do ST em centésimos"
    )

    perfil: Mapped["PerfilTributario"] = relationship(back_populates="regras")

    __table_args__ = (
        UniqueConstraint("perfil_id", "uf_destino", "ncm_excecao", name="uq_regra_perfil_uf_ncm"),
    )

    def __repr__(self) -> str:
        return (
            f"<RegraPerfilTributario(id={self.id}, perfil_id={self.perfil_id}, "
            f"uf={self.uf_destino!r}, ncm={self.ncm_excecao!r})>"
        )
