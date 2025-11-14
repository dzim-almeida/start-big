from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base import Base

class ProdutoFoto(Base):
    """
    Representa a tabela 'produto_fotos', contendo o caminho e os metadados
    de cada imagem associada a um produto.
    """
    __tablename__ = "produto_fotos"

    # Chave primária
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID único do foto (Chave primária)")
    # Chave estrangeira (FK)
    produto_id: Mapped[int] = mapped_column(Integer, ForeignKey("produtos.id"), nullable=False, doc="ID do produto proprietário desta foto")
    # Metadados
    nome_arquivo: Mapped[str] = mapped_column(String(255), nullable=True, doc="Nome do arquivo armazenado")
    url: Mapped[str] = mapped_column(String, nullable=False, doc="Caminho para a foto")
    principal: Mapped[Boolean] = mapped_column(Boolean, nullable=False, doc="Define se a foto é a principal")
    data_upload: Mapped[DateTime] = mapped_column(DateTime, nullable=False, doc="Data e horário em que o arquivo foi armazenado")
    
    # Relação ORM
    produto = relationship(
        "Produto",
        back_populates="fotos",
        doc="Relacionamento de Vários-para-Um com produto (Esta foto pertence a um produto)"
    )