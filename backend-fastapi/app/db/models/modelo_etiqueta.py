# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/modelo_etiqueta.py
# DESCRIÇÃO: Modelo de etiqueta criado pelo lojista (Central de Etiquetas).
# ---------------------------------------------------------------------------
"""
Por que o layout é um JSON e não colunas.

O modelo é NEUTRO: descreve a etiqueta em milímetros (página + elementos) e
não pertence a nenhuma linguagem de impressora. Quem traduz para HTML, ZPL,
TSPL ou PPLA é o terminal, na hora de imprimir. Colunas por elemento
(x, y, fonte, simbologia...) virariam uma tabela filha que só existe para ser
remontada no mesmo JSON — o backend não consulta dentro do layout, só guarda.

Os presets de fábrica NÃO moram aqui: ficam no código do frontend
(`shared/etiquetas/presets.ts`) para chegarem com a atualização, sem
migração de dados. Esta tabela guarda só o que o lojista criou, e é
compartilhada por todos os terminais da loja.
"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ModeloEtiqueta(Base):
    """Um layout de etiqueta nomeado, por empresa."""

    __tablename__ = "modelo_etiqueta"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, doc="Identificador único do modelo"
    )
    empresa_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Empresa dona do modelo",
    )
    nome: Mapped[str] = mapped_column(
        String(80), nullable=False, doc="Nome legível (ex: 'Gôndola 60x40')"
    )
    fonte: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="De onde vêm os dados impressos: 'produto' (a embalagem e o volume vêm depois)",
    )
    definicao: Mapped[dict] = mapped_column(
        JSON, nullable=False, doc="Página e elementos em mm — ver schemas/modelo_etiqueta.py"
    )
    data_criacao: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), doc="Quando o modelo foi criado"
    )
    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        doc="Última modificação do modelo",
    )

    def __repr__(self) -> str:
        return f"<ModeloEtiqueta(id={self.id}, nome={self.nome!r})>"
