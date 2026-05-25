# ---------------------------------------------------------------------------
# ARQUIVO: fonecedor.py
# DESCRIÇÃO: Modelo SQLAlchemy para a tabela 'fornecedores'.
# ---------------------------------------------------------------------------

from sqlalchemy import Integer, String, Boolean, Text, and_
from sqlalchemy.orm import relationship, Mapped, mapped_column, foreign
from sqlalchemy.sql.sqltypes import Enum as SQLAlchemyEnum
from typing import List, Optional

from app.core.enum import BankAccountType

from app.db.models.endereco import Endereco # Importado Endereco
from app.db.models.produto import Produto as ProdutoModel
from app.db.base import Base
# from app.core.enum import EntityType # Não é necessário importar o Enum aqui se ele for usado apenas na primaryjoin

class Fornecedor(Base):
    """
    Representa a tabela 'fornecedores', contendo os dados de
    um fornecedor de produtos.
    """
    __tablename__ = "fornecedores"

    # Chave primária
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID único do fornecedor (Chave primária)")
    
    # Tipo do fornecedor: 'produto', 'transportadora' ou 'entregador'
    tipo: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default='produto', doc="Tipo do fornecedor: produto, transportadora ou entregador")

    # Campos de dados do fornecedor
    nome: Mapped[str] = mapped_column(String(255, collation="NOCASE"), index=True, nullable=False, doc="Nome ou Razão Social do fornecedor")
    cnpj: Mapped[Optional[str]] = mapped_column(String(14), unique=True, index=True, nullable=True, doc="CNPJ do fornecedor (14 dígitos) - nulo para entregadores")
    cpf: Mapped[Optional[str]] = mapped_column(String(11), unique=True, nullable=True, doc="CPF do entregador (11 dígitos)")
    nome_fantasia: Mapped[Optional[str]] = mapped_column(String(255, collation="NOCASE"), index=True, nullable=True, doc="Nome fantasia da empresa fornecedora")
    ie: Mapped[Optional[str]] = mapped_column(String(14), unique=True, nullable=True, doc="Inscrição Estadual (IE) do fornecedor")

    # Contato
    telefone: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, doc="Telefone de contato do fornecedor")
    celular: Mapped[Optional[str]] = mapped_column(String(11), nullable=True, doc="Celular de contato do fornecedor")
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, doc="Email para contato com fornecedor")
    representante: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, doc="Nome do representante da empresa fornecedora")

    # Campos específicos para entregador
    veiculo: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, doc="Veículo do entregador")
    placa: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, doc="Placa do veículo do entregador")

    # Observação geral
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True, doc="Observações gerais sobre o fornecedor")

    # Dados bancários
    banco: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, doc="Nome do banco")
    agencia: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, doc="Número da agência bancária")
    conta: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, doc="Número da conta bancária")
    tipo_conta: Mapped[Optional[BankAccountType]] = mapped_column(SQLAlchemyEnum(BankAccountType), nullable=True, doc="Tipo da conta: CORRENTE ou POUPANCA")
    pix: Mapped[Optional[str]] = mapped_column(String(150), nullable=True, doc="Chave PIX do fornecedor")

    # Uso de 'bool' para tipagem
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, doc="Define se um Fornecedor está ativo (True) ou desativado (False)")

    # Relação Lado "Um" (Fornecedor) para "Muitos" (Produto)
    # Tipagem: Lista de objetos Produto
    produto: Mapped[list[ProdutoModel]] = relationship(
        "Produto",
        back_populates="fornecedor",
        doc="Relacionamento um-para-muitos com os produtos deste fornecedor",
        # uselist=True é o padrão para list/List, mas pode ser omitido
    )
    
    # Relação Lado "Um" (Fornecedor) para "Muitos" (Endereco) - Polimórfica
    # Tipagem: Lista de objetos Endereco
    endereco: Mapped[List[Endereco]] = relationship(
        "Endereco",
        # Junção manual para relação polimórfica
        primaryjoin="and_(foreign(Endereco.id_entidade) == Fornecedor.id, foreign(Endereco.tipo_entidade) == 'FORNECEDOR')",
        cascade="all, delete-orphan",
        # uselist=True é o padrão
        overlaps="endereco",
        doc="Relacionamento polimórfico um-para-muitos com os endereços"
    )