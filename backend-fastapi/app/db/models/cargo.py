# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/cargo.py
# DESCRIÇÃO: Modelo SQLAlchemy para a tabela 'cargos'.
#            Define os diferentes cargos ou funções, e armazena as permissões.
# ---------------------------------------------------------------------------

from sqlalchemy import Integer, String, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from typing import TYPE_CHECKING, Dict

# Previne circular import para type checking
if TYPE_CHECKING:
    from .funcionario import Funcionario

class Cargo(Base):
    """
    Exemplos: 'Gerente', 'Caixa', 'Estoquista'.
    Define o nível hierárquico e as permissões de acesso e operação para os Funcionários.
    """
    __tablename__ = "cargos"

    # --- Identificação ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, doc="ID único do cargo (Chave primária)")
    
    # --- Vínculo ---
    empresa_id: Mapped[int] = mapped_column(Integer, ForeignKey("empresas.id"), nullable=False, doc="ID da empresa à qual o cargo pertence")
    
    # --- Dados ---
    nome: Mapped[str] = mapped_column(String(50), nullable=False, doc="Nome do cargo (Ex: 'Caixa', 'Gerente de Vendas')") 
    
    # Campo JSON para armazenar permissões dinâmicas
    permissoes: Mapped[Dict[str, bool]] = mapped_column(JSON, nullable=False, default={}, doc="Objeto JSON contendo as permissões de acesso e operação")

    # =========================
    # RELACIONAMENTOS
    # =========================

    # Relacionamento 1:M com Funcionario
    funcionarios: Mapped[list["Funcionario"]] = relationship(
        back_populates="cargo",
        doc="Lista de funcionários que possuem este cargo"
    )