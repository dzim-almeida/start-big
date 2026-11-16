# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/perfil_tributario.py
# DESCRIÇÃO: Perfil tributário — agrupa as regras interestaduais (DIFAL,
#            FCP, ICMS-ST) que N produtos compartilham.
# ---------------------------------------------------------------------------
"""
Por que um perfil, e não alíquotas no produto.

Operação interestadual precisa de dados que a cascata de `tributacao.py`
(produto → regra por NCM → padrão da loja) não tem: alíquota interestadual,
alíquota interna do destino, FCP, MVA de ST. Se cada produto guardasse isso
seriam 27 UFs × N produtos — inviável para uma loja. O perfil responde uma
vez ("Varejo - Eletrônicos") e os produtos apontam para ele (TASK006).

O perfil COMPLEMENTA a cascata, não a substitui: CST/CSOSN, CFOP, alíquota
interna e PIS/COFINS continuam vindo de lá.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.regra_perfil_tributario import RegraPerfilTributario


class PerfilTributario(Base):
    """
    Um conjunto nomeado de regras interestaduais, por empresa.

    As regras (`RegraPerfilTributario`) casam por UF de destino e exceção de
    NCM, da mais específica para o fallback — ver o model da regra.
    """

    __tablename__ = "perfil_tributario"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, doc="Identificador único do perfil"
    )
    empresa_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Empresa dona do perfil — cada empresa tem os seus",
    )
    descricao: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        doc="Nome legível do perfil (ex: 'Varejo - Eletrônicos', 'Peças Automotivas - ST')",
    )
    data_criacao: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), doc="Quando o perfil foi criado"
    )
    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        doc="Última modificação do perfil",
    )

    regras: Mapped[list["RegraPerfilTributario"]] = relationship(
        back_populates="perfil",
        cascade="all, delete-orphan",
        doc="Regras do perfil — apagar o perfil apaga todas",
    )

    def __repr__(self) -> str:
        return f"<PerfilTributario(id={self.id}, descricao={self.descricao!r})>"
