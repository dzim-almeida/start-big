# ---------------------------------------------------------------------------
# ARQUIVO: app/db/crud/empresa.py
# DESCRIÇÃO: Funções de CRUD (Create, Read, Update, Delete) para interagir
#            com a tabela de Empresas no banco de dados (Repository Layer).
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional # Adicionado para tipagem explícita de retorno

# Importa o modelo ORM
from app.db.models.empresa import Empresa as EmpresaModel

# =========================
# Funções de Leitura (Read)
# =========================

def get_enterprise_in_db(db: Session) -> Optional[EmpresaModel]:
    """
    Busca a primeira (e presumivelmente única) empresa cadastrada no sistema
    (Usado para o Multi-tenancy inicial).
    """
    stmt = select(EmpresaModel)
    enterprise_in_db = db.scalars(stmt).first()
    return enterprise_in_db

# =========================
# Função de Criação (Create)
# =========================

def create_enterprise(db: Session, new_enterprise: EmpresaModel) -> EmpresaModel:
    """
    Adiciona uma nova empresa ao banco de dados, incluindo seus
    relacionamentos (Usuários, Endereços) em cascata.
    """
    db.add(new_enterprise)
    # Envia ao banco para obter o ID antes do commit final
    db.flush()
    db.refresh(new_enterprise)
    return new_enterprise