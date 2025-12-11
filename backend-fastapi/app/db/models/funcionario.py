# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/funcionario.py
# DESCRIÇÃO: Modelo SQLAlchemy para a tabela 'funcionarios'.
#            Contém os dados pessoais e documentais do colaborador
#            e o vínculo com o Cargo e a conta de Usuário (1:1).
# ---------------------------------------------------------------------------

from datetime import date
from sqlalchemy import Date, String, Integer, Boolean, ForeignKey, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign
from typing import Optional, TYPE_CHECKING
from app.db.base import Base

# Importa o modelo Endereco para o relacionamento polimórfico
from app.db.models.endereco import Endereco 

# Previne circular import para type checking
if TYPE_CHECKING:
    from .usuario import Usuario
    from .empresa import Empresa
    from .cargo import Cargo

class Funcionario(Base):
    """
    Representa a tabela 'funcionarios', contendo dados pessoais,
    documentos e a chave estrangeira para o usuário de acesso (1:1).
    """
    __tablename__ = "funcionarios"

    # --- Identificação ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID único do funcionário (PK)")

    # --- Vínculos (Multi-tenancy e Acesso) ---
    empresa_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("empresas.id"),
        nullable=False,
        doc="ID da empresa à qual o funcionário pertence"
    )

    # CHAVE ESTRANGEIRA (FK) para a relação 1:1 com Usuarios
    usuario_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("usuarios.id"), 
        unique=True, # ESSENCIAL: Garante que um usuário de acesso só pode estar vinculado a um funcionário
        nullable=False,
        doc="ID do usuário de acesso associado (FK, restrição 1:1)"
    )
    
    # --- Dados Pessoais/Gerais ---
    nome: Mapped[str] = mapped_column(String(255), nullable=False, doc="Nome completo do funcionário")
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, doc="E-mail de contato pessoal/profissional")
    telefone: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, doc="Número do telefone fixo para contato")
    celular: Mapped[Optional[str]] = mapped_column(String(11), nullable=True, doc="Número do celular para contato")
    
    # --- Documentos ---
    cpf: Mapped[str] = mapped_column(String(11), unique=True, nullable=False, doc="CPF (11 dígitos, único)")
    rg: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True, doc="RG")
    carteira_trabalho: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, doc="Número da Carteira de Trabalho")
    cnh: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True, doc="Número da CNH")
    tipo_contrato: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, doc="Tipo de contrato do funcionário")
    
    # --- Dados Hierárquicos/Estruturais ---
    cargo_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("cargos.id", ondelete="SET NULL"), # ondelete="SET NULL" é bom para integridade
        nullable=True, 
        doc="ID do cargo atual do funcionário (FK)"
    )
    
    # --- Dados Bancários ---
    agencia: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, doc="Número da agência para pagamento")
    conta: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, doc="Número da conta para pagamento")
    banco: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, doc="Nome do Banco")

    # --- Outros ---
    data_nascimento: Mapped[Optional[date]] = mapped_column(Date, nullable=True, doc="Data de nascimento do funcionário")
    mae: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, doc="Nome completo da mãe")
    pai: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, doc="Nome completo do pai")
    observacao: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, doc="Observações internas/RH")
    
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, doc="Status de ativo/inativo na empresa")

    # =========================
    # RELACIONAMENTOS
    # =========================

    # Relacionamento M:1 com Empresa
    empresa: Mapped["Empresa"] = relationship(
        back_populates="funcionarios",
        doc="Empresa a que este funcionário pertence"
    )

    # RELACIONAMENTO 1:1 com Usuario
    usuario: Mapped["Usuario"] = relationship(
        back_populates="funcionario",
        doc="Relacionamento Um-para-Um com o usuário de acesso associado"
    )

    # Relacionamento M:1 com Cargo
    cargo: Mapped[Optional["Cargo"]] = relationship(
        back_populates="funcionarios", 
        doc="Cargo/Função atual do funcionário"
    )
    
    # Relacionamento Polimórfico com Endereco
    endereco: Mapped[list[Endereco]] = relationship(
        # Define a condição de junção: Endereco.id_entidade == Funcionario.id E Endereco.tipo_entidade == 'FUNCIONARIO'
        primaryjoin=lambda: and_(foreign(Endereco.id_entidade) == Funcionario.id, foreign(Endereco.tipo_entidade) == 'FUNCIONARIO'),
        cascade="all, delete-orphan", 
        doc="Lista de endereços associados a este funcionário (residencial, etc.)"
    )