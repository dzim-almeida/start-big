# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/nfse_tabelas.py
# DESCRIÇÃO: Tabelas oficiais da NFS-e Nacional, para o lojista achar o código
#            do serviço e o NBS pela descrição (docs/nfse-plano.md, F1).
# ---------------------------------------------------------------------------
"""
O mesmo desenho do NCM (ver models/ncm.py): dado de referência embarcado em
`app/data/*.csv.gz`, carregado no boot por `core/seed_nfse.py`, e pesquisado
pelo motor de `core/busca.py`. Funciona sem internet.

POR QUE O LOJISTA PRECISA DISTO
-------------------------------
A NFS-e Nacional pede dois códigos que ninguém decora:
- o **código de tributação nacional** (6 dígitos: item, subitem e desdobro da
  LC 116) — "010701" é suporte técnico em informática;
- o **NBS** (9 dígitos), a "NCM dos serviços".

A Receita publica a correlação entre os dois (Anexo VIII): escolhido o código
nacional, o sistema sugere os NBS que cabem nele. É o que os contadores usam à
mão, e é o que responde ao "não sei qual é o meu NBS".

Tabelas novas: nascem pelo `create_all()` do boot, sem migration.
"""

from sqlalchemy import Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NfseServicoNacional(Base):
    """Um código de tributação nacional da lista de serviços (Anexo B)."""

    __tablename__ = "nfse_servicos_nacionais"

    codigo: Mapped[str] = mapped_column(
        String(6), primary_key=True, doc="Código de tributação nacional, 6 dígitos (ex: 010701)"
    )
    descricao: Mapped[str] = mapped_column(String(600), nullable=False)
    descricao_completa: Mapped[str] = mapped_column(
        String(1200), nullable=False, doc="Item / subitem — o que a busca varre"
    )

    def __repr__(self) -> str:
        return f"<NfseServicoNacional({self.codigo} {self.descricao[:40]!r})>"


class Nbs(Base):
    """Um código NBS de 9 dígitos (Anexo B, aba NBS 2.0)."""

    __tablename__ = "nbs"

    codigo: Mapped[str] = mapped_column(String(9), primary_key=True, doc="NBS sem pontuação")
    descricao: Mapped[str] = mapped_column(String(600), nullable=False)
    descricao_completa: Mapped[str] = mapped_column(
        String(2000), nullable=False, doc="A cadeia de grupos, como no NCM"
    )

    __table_args__ = (Index("ix_nbs_descricao", "descricao"),)

    def __repr__(self) -> str:
        return f"<Nbs({self.codigo} {self.descricao[:40]!r})>"


class NfseCorrelacaoNbs(Base):
    """Subitem da LC 116 → NBS que cabe nele (Anexo VIII da Receita)."""

    __tablename__ = "nfse_correlacao_nbs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_lc116: Mapped[str] = mapped_column(
        String(4), nullable=False, index=True, doc="Item + subitem, 4 dígitos (ex: 0107)"
    )
    nbs: Mapped[str] = mapped_column(String(9), nullable=False)
