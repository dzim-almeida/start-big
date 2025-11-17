# ---------------------------------------------------------------------------
# ARQUIVO: funcionario_crud.py
# DESCRIÇÃO: Funções de CRUD (Create, Read, Update, Delete) para interagir
#            com a tabela de Funcionarios no banco de dados (Repository Layer).
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_
from typing import Sequence, Callable, Optional

# Importa o modelo ORM
from app.db.models.funcionario import Funcionario as FuncionarioModel
# Importa o modelo ORM (Funcionario) para as funções de busca

# =========================
# Funções de Validação/Conflito
# =========================

def verify_employee_conflict(
    db: Session,
    value: str,
    search_method: Callable[[Session, str], FuncionarioModel | None],
    search_name: str
) -> str | None:
    """
    Verifica se o valor fornecido (ex: CPF, Email, RG, CTPS, CNH) já existe no BD e se está ativo.
    """
    if not value:
        return None

    employee_in_db = search_method(db, value)
    
    if employee_in_db:
        # Verifica o status de atividade (para retornar mensagem específica de reativação)
        if not employee_in_db.ativo: 
            return "disabled employee"
    
        # Conflito: Registro ativo encontrado
        return f"{search_name} já cadastrado"

    return None

# =========================
# Funções de Leitura (Read)
# =========================

def get_employee_by_id(db: Session, employee_id: int) -> FuncionarioModel | None:
    """
    Busca um funcionário pelo seu ID (chave primária).
    """
    stmt = select(FuncionarioModel).where(FuncionarioModel.id == employee_id)
    employee_in_db = db.scalars(stmt).first()
    return employee_in_db

def get_employee_by_user_id( db: Session, user_id: int) -> FuncionarioModel | None:
    """
    Busca um funcionário pela Chave Estrangeira usuario_id.
    """
    # Usado para verificar a restrição 1:1 na criação
    stmt = select(FuncionarioModel).where(FuncionarioModel.usuario_id == user_id)
    employee_in_db = db.scalars(stmt).first()
    return employee_in_db

def get_employee_by_cpf(db: Session, employee_cpf: str) -> FuncionarioModel | None:
    """
    Busca um funcionário pelo seu CPF.
    """
    stmt = select(FuncionarioModel).where(FuncionarioModel.cpf == employee_cpf)
    employee_in_db = db.scalars(stmt).first()
    return employee_in_db

def get_employee_by_email(db: Session, employee_email: str) -> FuncionarioModel | None:
    """
    Busca um funcionário pelo seu email.
    """
    stmt = select(FuncionarioModel).where(FuncionarioModel.email == employee_email)
    employee_in_db = db.scalars(stmt).first()
    return employee_in_db

def get_employee_by_rg(db: Session, employee_rg: str) -> FuncionarioModel | None:
    """
    Busca um funcionário pelo seu RG.
    """
    stmt = select(FuncionarioModel).where(FuncionarioModel.rg == employee_rg)
    employee_in_db = db.scalars(stmt).first()
    return employee_in_db

def get_employee_by_ctps(db: Session, employee_ctps: str) -> FuncionarioModel | None:
    """
    Busca um funcionário pela Carteira de Trabalho (CTPS).
    """
    stmt = select(FuncionarioModel).where(FuncionarioModel.carteira_trabalho == employee_ctps)
    employee_in_db = db.scalars(stmt).first()
    return employee_in_db

def get_employee_by_cnh(db: Session, employee_cnh: str) -> FuncionarioModel | None:
    """
    Busca um funcionário pela CNH.
    """
    stmt = select(FuncionarioModel).where(FuncionarioModel.cnh == employee_cnh)
    employee_in_db = db.scalars(stmt).first()
    return employee_in_db

def get_all_employees(db: Session) -> Sequence[FuncionarioModel]:
    """
    Busca TODOS os funcionários ativos cadastrados no banco de dados.
    """
    # Constrói a query: SELECT * FROM funcionarios WHERE ativo = True
    stmt = select(FuncionarioModel).where(FuncionarioModel.ativo == True)
    employees_in_db = db.scalars(stmt).all()
    return employees_in_db

def get_employee_by_search(db: Session, search: str) -> Sequence[FuncionarioModel]:
    """
    Busca funcionários ativos que correspondam ao termo (nome, CPF, RG, email).
    """
    # Define as condições de busca (OR)
    conditions = or_(
        FuncionarioModel.nome.ilike(f"%{search}%"), # Busca por nome
        FuncionarioModel.cpf.startswith(search),    # Busca por CPF
        FuncionarioModel.email.ilike(f"%{search}%"),# Busca por email
        FuncionarioModel.rg.startswith(search)      # Busca por RG
    )

    # Aplica o filtro 'WHERE' com as condições (deve ser ativo E corresponder à busca)
    stmt = select(FuncionarioModel).where(
        and_(
            FuncionarioModel.ativo == True,
            conditions
        )
    )
    
    result = db.scalars(stmt).all()
    return result


# =========================
# Função de Criação (Create)
# =========================

def create_employee(db: Session, new_employee: FuncionarioModel) -> FuncionarioModel:
    """
    Adiciona um novo funcionário ao banco de dados,
    incluindo seus relacionamentos em cascata (Endereços).
    """
    # Adiciona o objeto principal e seus filhos (em cascata) à sessão
    db.add(new_employee)
    # Envia as instruções SQL para o banco para gerar o ID
    db.flush()
    # Atualiza a instância 'new_employee' com os dados do banco (incluindo o ID)
    db.refresh(new_employee)
    return new_employee


# =========================
# Função de Atualização (Update)
# =========================

def update_employee_in_db(db: Session, update_employee: FuncionarioModel) -> FuncionarioModel:
    """
    Persiste as alterações feitas em um objeto Funcionario na sessão.
    O objeto deve ter sido modificado pela camada de serviço.
    """
    db.flush()
    db.refresh(update_employee)
    return update_employee

# =========================
# Funções de Status (Ativar/Desativar)
# =========================

def active_employee_by_id(db: Session, active_employee: FuncionarioModel) -> FuncionarioModel:
    """
    Persiste o status de ativação (ativo=True) para o funcionário na sessão.
    """
    db.flush()
    db.refresh(active_employee)
    return active_employee

def disable_employee_by_id(db: Session, disable_employee: FuncionarioModel) -> FuncionarioModel:
    """
    Persiste o status de desativação (ativo=False) para o funcionário na sessão (Soft Delete).
    """
    db.flush()
    db.refresh(disable_employee)
    return disable_employee