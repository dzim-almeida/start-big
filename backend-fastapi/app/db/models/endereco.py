# ---------------------------------------------------------------------------
# ARQUIVO: endereco.py
# DESCRIÇÃO: Modelo SQLAlchemy para a tabela 'enderecos', que representa
#            os endereços vinculados a diferentes entidades (ex: Clientes).
# ---------------------------------------------------------------------------

from sqlalchemy import Integer, String, Index, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign
from sqlalchemy.sql.sqltypes import Enum as SQLAlchemyEnum

from app.db.base import Base
from app.core.enum import State  # Enum dos estados brasileiros
from app.core.enum import EntityType # Enum dos tipos de entidade (CLIENTE, FORNECEDOR)

# =========================
# Modelo SQLAlchemy: Endereco
# =========================
class Endereco(Base):
    """
    Representa a tabela 'enderecos'. Cada registro é um endereço
    associado a uma entidade polimórfica (Cliente, Fornecedor, etc.).
    """
    __tablename__ = "enderecos"

    # Chave primária da tabela de endereços
    id: Mapped[int] = mapped_column(Integer, primary_key=True, doc="ID único do endereço (Chave primária)")

    # --- Colunas para Relação Polimórfica ---
    # Armazena o ID da entidade (ex: ID do cliente, ID do fornecedor)
    id_entidade: Mapped[int] = mapped_column(Integer, nullable=False, doc="ID da entidade proprietária deste endereço")
    # Armazena o tipo da entidade (ex: 'CLIENTE' ou 'FORNECEDOR')
    tipo_entidade: Mapped[EntityType] = mapped_column(SQLAlchemyEnum(EntityType), nullable=False, doc="Tipo da entidade proprietária (ex: CLIENTE)")
    
    # (Nota: Os relacionamentos em Cliente/Fornecedor criarão os
    # atributos 'cliente' e 'fornecedor' aqui através do 'overlaps')

    # --- Campos de endereço ---
    logradouro: Mapped[str] = mapped_column(String(255), nullable=False, doc="Nome da rua, avenida, etc.")
    numero: Mapped[str] = mapped_column(String(20), nullable=False, doc="Número do endereço")
    complemento: Mapped[str | None] = mapped_column(String(100), nullable=True, doc="Complemento do endereço (opcional)")
    bairro: Mapped[str] = mapped_column(String(100), nullable=False, doc="Bairro")
    cidade: Mapped[str] = mapped_column(String(100), nullable=False, doc="Cidade")
    estado: Mapped[State] = mapped_column(SQLAlchemyEnum(State), nullable=False, doc="Estado (UF)")
    cep: Mapped[str] = mapped_column(String(10), nullable=False, doc="CEP")
    
    # --- Índice Otimizado ---
    # (Permite múltiplos endereços por entidade, otimizando a busca)
    __table_args__ = (
        Index(
            "idx_entidade_tipo", # Nome do índice
            "id_entidade",       # Coluna 1 do índice
            "tipo_entidade"      # Coluna 2 do índice
        ),
    )
