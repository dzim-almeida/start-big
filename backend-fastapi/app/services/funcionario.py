# ---------------------------------------------------------------------------
# ARQUIVO: funcionario_service.py
# DESCRIÇÃO: Camada de serviço com a lógica de negócio para Funcionários.
#            Lida com a criação, validação e atualização do Funcionario
#            e seus endereços.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Sequence, List

# Importa os schemas Pydantic
from app.schemas.funcionario import FuncionarioCreate, FuncionarioUpdate
# Importa o modelo ORM
from app.db.models.funcionario import Funcionario as FuncionarioModel
# Importa a camada de acesso a dados (CRUD)
from app.db.crud import funcionario as employee_crud
# Importa o serviço de endereço para reutilização da lógica
from app.services import endereco as address_service
# Importa os Enums para tipagem de entidade
from app.core.enum import EntityType


# =========================
# Serviço: Criar Funcionário
# =========================
def create_employee(db: Session, new_employee: FuncionarioCreate) -> FuncionarioModel:
    """
    Serviço para criar um novo funcionário, validar conflitos e estabelecer
    a relação 1:1 com o usuário logado (user_id).
    """

    validation_errors = []

    # 1. REGRA DE NEGÓCIO: Verificar restrição 1:1 com Usuário
    existing_employee_by_user = employee_crud.get_employee_by_user_id(db, new_employee.usuario_id)
    if existing_employee_by_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O usuário já está associado a um registro de funcionário."
        )

    # 2. Validações de Conflito (CPF, Email, RG, etc.)
    
    # Validação de CPF
    error_cpf = employee_crud.verify_employee_conflict(
        db, new_employee.cpf, employee_crud.get_employee_by_cpf, "CPF"
    )
    if error_cpf:
        if error_cpf == "disabled employee":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Funcionário desabilitado com este CPF. Por favor, reative o cadastro."
            )
        validation_errors.append({"campo": "cpf", "mensagem": error_cpf})

    # Validação de Email
    if new_employee.email: # Só valida se o email for fornecido (nullable=True no modelo)
        error_email = employee_crud.verify_employee_conflict(
            db, new_employee.email, employee_crud.get_employee_by_email, "Email"
        )
        if error_email:
            validation_errors.append({"campo": "email", "mensagem": error_email})
            
    # Validação de RG (Se existir a regra UNIQUE no modelo, deve ser validado)
    if new_employee.rg:
        error_rg = employee_crud.verify_employee_conflict(
            db, new_employee.rg, employee_crud.get_employee_by_rg, "RG"
        )
        if error_rg:
            validation_errors.append({"campo": "rg", "mensagem": error_rg})
    
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=validation_errors
        )

    # 3. MAPEAMENTO: Cria a instância do modelo SQLAlchemy
    employee_to_db = FuncionarioModel(
        # Dados do Funcionario
        nome=new_employee.nome,
        email=new_employee.email,
        contato=new_employee.contato,
        observacao=new_employee.observacao,
        cpf=new_employee.cpf,
        rg=new_employee.rg,
        carteira_trabalho=new_employee.carteira_trabalho,
        cnh=new_employee.cnh,
        funcao=new_employee.funcao,
        mae=new_employee.mae,
        pai=new_employee.pai,
        banco=new_employee.banco,
        agencia=new_employee.agencia,
        conta=new_employee.conta,
        
        # Chave Estrangeira (FK)
        usuario_id=new_employee.usuario_id
    )

    # 4. CHAMA A CAMADA CRUD (para obter o ID)
    new_employee_in_db = employee_crud.create_employee(db, employee_to_db)

    # 5. PREPARA E VINCULA OS ENDEREÇOS (Polimórfico)
    if new_employee.endereco:
        new_address_employee_to_db = address_service.address_to_db(
            new_employee_in_db.id,
            EntityType.FUNCIONARIO, # Uso do Enum correto
            new_employee.endereco
        )
        new_employee_in_db.endereco = new_address_employee_to_db
    
    # 6. RETORNA O OBJETO PERSISTIDO
    return new_employee_in_db


# =========================
# Serviço: Buscar TODOS os Funcionários
# =========================
def get_all_employees(db: Session) -> Sequence[FuncionarioModel]:
    """
    Busca TODOS os funcionários ativos. (Delega para o CRUD).
    """
    return employee_crud.get_all_employees(db)


# =========================
# Serviço: Buscar Funcionários por Termo
# =========================
def get_employee_by_search(db: Session, search: str) -> Sequence[FuncionarioModel]:
    """
    Busca funcionários por nome, CPF, email, etc. (Delega para o CRUD).
    """
    return employee_crud.get_employee_by_search(db, search)


# =========================
# Serviço: Atualizar Funcionário
# =========================
def update_employee_by_id(db: Session, employee_id: int, employee: FuncionarioUpdate) -> FuncionarioModel:
    """
    Atualiza um funcionário existente pelo ID.
    Aplica atualizações parciais (patch) e lida com a lista de endereços.
    """
    
    # 1. Busca o funcionário existente no banco pelo ID
    update_employee = employee_crud.get_employee_by_id(db, employee_id)

    if not update_employee:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Funcionário não encontrado")
    
    # 2. Extrai apenas os dados enviados na requisição (para atualização parcial)
    update_data = employee.model_dump(exclude_unset=True)
    
    # 3. Tratamento especial para atualizar/substituir a lista de endereços
    if "endereco" in update_data and update_data["endereco"] is not None:
        updated_addresses = address_service.update_address_in_db(
            update_employee.endereco, # Lista atual do ORM
            employee.endereco,        # Lista nova/editada do Pydantic
            update_employee.id,
            EntityType.FUNCIONARIO
        )
        update_employee.endereco = updated_addresses
        # Remove 'endereco' do dict principal para evitar conflito com relacionamento ORM
        del update_data["endereco"]
    
    # 4. Itera sobre os dados restantes (simples) e atualiza o objeto SQLAlchemy
    for key, value in update_data.items():
        # A FK usuario_id é mantida (não está no schema de update)
        setattr(update_employee, key, value)
    
    # 5. Chama o CRUD para persistir as alterações
    return employee_crud.update_employee_in_db(db, update_employee)


# =========================
# Serviço: Ativar Funcionário
# =========================
def active_employee_by_id(db: Session, employee_id: int) -> FuncionarioModel:
    """
    Serviço para ativar um funcionário pelo seu ID.
    """
    # 1. Busca o funcionário
    existing_employee = employee_crud.get_employee_by_id(db, employee_id)

    if not existing_employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Funcionário não encontrado")
    
    # 2. Atualiza o objeto em memória
    existing_employee.ativo = True

    # 3. Delega a ativação para o CRUD e retorna o objeto
    return employee_crud.active_employee_by_id(db, existing_employee)


# =========================
# Serviço: Desativar Funcionário
# =========================
def disable_employee_by_id(db: Session, employee_id: int) -> FuncionarioModel:
    """
    Serviço para desativar um funcionário pelo seu ID (Soft Delete).
    """
    # 1. Busca o funcionário
    existing_employee = employee_crud.get_employee_by_id(db, employee_id)

    if not existing_employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Funcionário não encontrado")
    
    # 2. Atualiza o objeto em memória
    existing_employee.ativo = False

    # 3. Delega a desativação para o CRUD e retorna o objeto
    return employee_crud.disable_employee_by_id(db, existing_employee)