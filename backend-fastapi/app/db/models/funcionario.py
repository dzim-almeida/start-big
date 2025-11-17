from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign
from typing import Optional # Importado Optional para clareza
from app.db.base import Base

from app.db.models.endereco import Endereco

# Assumindo que a classe Usuario está em app.db.models.usuario
# Assumindo que o Enum UserType (admin/usuario) está definido em app.db.models.usuario ou app.core.enum

class Funcionario(Base):
    """
    Representa a tabela 'funcionarios', contendo dados pessoais,
    documentos e a chave estrangeira para o usuário de acesso (1:1).
    """
    __tablename__ = "funcionarios"

    # Chave primária: funcionario_id(PK)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID único do funcionário (PK)")
    
    # CHAVE ESTRANGEIRA (FK) para a relação 1:1 com Usuarios
    # usuario_id(FK)
    usuario_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("usuarios.id"), 
        unique=True, # ESSENCIAL para impor a restrição 1:1 (Um funcionário -> Um usuário de acesso)
        nullable=False,
        doc="ID do usuário de acesso associado (FK)"
    )

    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, doc="Define se o funcionário está ativo (True) ou desativado (False)")

    # Dados Pessoais/Gerais
    nome: Mapped[str] = mapped_column(String(255), nullable=False, doc="Nome completo do funcionário")
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, doc="E-mail de contato")
    contato: Mapped[str | None] = mapped_column(String(20), nullable=True, doc="Telefone de contato")
    
    # Documentos
    cpf: Mapped[str] = mapped_column(String(11), unique=True, nullable=False, doc="CPF (11 dígitos)")
    rg: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, doc="RG")
    carteira_trabalho: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True, doc="Número da Carteira de Trabalho")
    cnh: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, doc="Número da CNH")
    
    # Dados Hierárquicos/Estruturais
    funcao: Mapped[str | None] = mapped_column(String(100), nullable=True, doc="Cargo ou função atual")
    
    # Dados Bancários (melhor se fosse 1:N com tabela Bancos/Contas)
    agencia: Mapped[str | None] = mapped_column(String(10), nullable=True, doc="Número da agência")
    conta: Mapped[str | None] = mapped_column(String(20), nullable=True, doc="Número da conta")
    banco: Mapped[str | None] = mapped_column(String(50), nullable=True, doc="Nome do Banco")

    # Outros
    mae: Mapped[str | None] = mapped_column(String(255), nullable=True, doc="Nome completo da mãe")
    pai: Mapped[str | None] = mapped_column(String(255), nullable=True, doc="Nome completo do pai")
    observacao: Mapped[str | None] = mapped_column(String(500), nullable=True, doc="Observações internas")

    # RELACIONAMENTO 1:1 com Usuario (usando string literal para evitar ciclo)
    usuario = relationship(
        "Usuario",
        back_populates="funcionario",
        doc="Relacionamento Um-para-Um com o usuário de acesso"
    )

    endereco: Mapped[list[Endereco]] = relationship(
        "Endereco",
        # Define a condição de junção manual para esta relação polimórfica
        primaryjoin="and_(foreign(Endereco.id_entidade) == Funcionario.id, foreign(Endereco.tipo_entidade) == 'FUNCIONARIO')",
        cascade="all, delete-orphan", 
        # uselist=True é o padrão
        overlaps="endereco",
        doc="Lista de endereços associados a este funcionario"
    )   