# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/usuario.py
# DESCRIÇÃO: Modelo SQLAlchemy para a tabela 'usuarios'.
#            Define a estrutura de acesso ao sistema (login),
#            vinculada obrigatoriamente a uma empresa (Multi-tenancy).
# ---------------------------------------------------------------------------

from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from app.db.base import Base
from typing import TYPE_CHECKING # Importa para type hints (opcional, mas boa prática)

# Previne circular import para type checking
if TYPE_CHECKING:
    from .empresa import Empresa
    from .funcionario import Funcionario

class Usuario(Base):
    """
    Representa o usuário de acesso ao sistema (credenciais de login/senha).
    Cada usuário está vinculado a uma Empresa e pode estar vinculado a um Funcionario.
    """
    __tablename__ = "usuarios"

    # --- Identificação ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="ID único do usuário (Chave primária)")
    
    # --- Vínculos e Hierarquia ---
    # VINCULO OBRIGATÓRIO COM A EMPRESA (Multi-tenancy)
    empresa_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("empresas.id"), 
        nullable=True, 
        index=True, 
        doc="ID da empresa à qual o usuário pertence (Chave Estrangeira)"
    )
    
    # Define se é o "Dono" (Master) ou não. 
    is_master: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        doc="Se True, é a conta Master da empresa (Super Admin)"
    )

    # --- Credenciais e Dados ---
    nome: Mapped[str] = mapped_column(String(255), nullable=False, doc="Nome completo do usuário (geralmente o nome de login)")
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True, doc="E-mail único usado para login")
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False, doc="Hash da senha para autenticação")
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, doc="Status de ativo/inativo para acesso")

    # --- Metadados ---
    # Nota: A data_criacao deve ser default para a hora atual se o ORM não fizer isso
    data_criacao: Mapped[datetime] = mapped_column(DateTime, doc="Data de criação do usuário no sistema")
    
    # =========================
    # RELACIONAMENTOS
    # =========================
    
    # Relacionamento M:1 com Empresa
    empresa: Mapped["Empresa"] = relationship(
        back_populates="usuarios",
        doc="Empresa à qual este usuário está vinculado"
    )
    
    # Relacionamento 1:1 com Funcionario
    # uselist=False garante que o SQLAlchemy espere apenas um objeto (1:1)
    funcionario: Mapped["Funcionario"] = relationship(
        back_populates="usuario", 
        uselist=False,
        doc="Funcionário (dados pessoais, documentos) associado a este usuário de acesso (1:1)"
    )