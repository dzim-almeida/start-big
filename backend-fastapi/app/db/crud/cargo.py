# ---------------------------------------------------------------------------
# ARQUIVO: app/db/crud/cargo.py
# DESCRIÇÃO: Funções de CRUD (Create, Read, Update, Delete) para interagir
#            com a tabela de Cargos.
# ---------------------------------------------------------------------------

from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.cargo import Cargo as CargoModel

# =========================
# Funções de Leitura (Read)
# =========================

def get_cargo_funcionario_by_name(db: Session, name_cargo: str) -> CargoModel | None:
    """
    Busca um cargo pelo nome para verificar unicidade.
    """
    stmt = select(CargoModel).where(CargoModel.nome == name_cargo)
    cargo_in_db = db.scalars(stmt).first()
    return cargo_in_db

def get_cargos_funcionario(db: Session, cargo_search: str | None) -> Sequence[CargoModel]:
    """
    Busca e retorna todos os registros de cargos.
    """
    stmt = select(CargoModel)

    if cargo_search:
        stmt = stmt.where(CargoModel.nome.ilike(f"{cargo_search}%"))

    return db.scalars(stmt).all()

def get_cargo_funcionario_by_id(db: Session, cargo_id: int) -> CargoModel | None:
    """
    Busca um cargo pelo seu ID.
    """
    stmt = select(CargoModel).where(CargoModel.id == cargo_id)
    cargo_in_db = db.scalars(stmt).first()
    return cargo_in_db

# =========================
# Função de Criação (Create)
# =========================

def create_cargo_funcionario(db: Session, cargo_to_add: CargoModel) -> CargoModel:
    """
    Adiciona um novo Cargo à sessão.
    """
    db.add(cargo_to_add)
    # Garante que a transação receba o ID gerado pelo banco
    db.flush()
    db.refresh(cargo_to_add)
    return cargo_to_add

# =========================
# Função de Atualização (Update)
# =========================

def update_cargo_funcionaio(db: Session, cargo_to_update: CargoModel) -> CargoModel:
    """
    Persiste as alterações feitas no objeto Cargo em memória.
    """
    # Garante que as alterações em memória sejam enviadas ao banco
    db.flush()
    # Atualiza o objeto para garantir que dados gerados pelo banco (timestamps, etc.) estejam presentes
    db.refresh(cargo_to_update)
    return cargo_to_update

# =========================
# Função de Deleção (Delete)
# =========================

def delete_cargo_funcionario(db: Session, cargo_to_delete: CargoModel) -> None:
    """
    Remove o objeto Cargo do banco de dados (Deleção Física).
    """
    db.delete(cargo_to_delete)
    # Garante que a deleção seja enviada ao banco antes do commit final
    db.flush()