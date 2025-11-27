# ---------------------------------------------------------------------------
# ARQUIVO: funcionario_service.py
# DESCRIÇÃO: Camada de serviço com a lógica de negócio para Funcionários.
#            Lida com a criação aninhada (Usuario, Endereços), validação
#            de conflitos e atualizações.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Sequence, List

# Importa os schemas Pydantic
from app.schemas.funcionario import FuncionarioCreate, FuncionarioUpdate
# Importa o modelo ORM
from app.db.models.funcionario import Funcionario as FuncionarioModel
from app.db.models.usuario import Usuario as UsuarioModel
# Importa a camada de acesso a dados (CRUD)
from app.db.crud import funcionario as employee_crud
from app.db.crud import usuario as user_crud
# Importa o serviço de endereço para reutilização da lógica
from app.services import endereco as address_service
from app.core.security import hash_password
# Importa os Enums para tipagem de entidade
from app.core.enum import EntityType


not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Funcionário não encontrado no sistema"
)

# =========================
# Serviço: Criar Funcionário (Com Usuário e Endereços)
# =========================
def create_employee(db: Session, new_employee: FuncionarioCreate) -> FuncionarioModel:
    """
    Serviço para criar um novo funcionário, incluindo a criação de um novo
    usuário vinculado e seus endereços, garantindo que não haja conflitos
    (CPF, Email, RG) e aplicando a lógica de desabilitado/reativação.
    """

    validation_errors = []

    # 1. COMENTÁRIO DE REGRA DE NEGÓCIO (Mantido como estava)
    # # 1. REGRA DE NEGÓCIO: Verificar restrição 1:1 com Usuário
    # existing_employee_by_user = employee_crud.get_employee_by_user_id(db, new_employee.usuario_id)
    # if existing_employee_by_user:
    #     raise HTTPException(
    #         status_code=status.HTTP_409_CONFLICT,
    #         detail="O usuário já está associado a um registro de funcionário."
    #     )

    # 2. Validações de Conflito (CPF, Email, RG, etc.)
    
    # Validação de CPF (usa a função genérica que lida com o status 'disabled')
    error_cpf = employee_crud.verify_employee_conflict(
        db, new_employee.cpf, employee_crud.get_employee_by_cpf, "CPF"
    )
    if error_cpf:
        if error_cpf == "disabled employee":
            # Exceção específica para funcionário desativado (sugere reativação)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Funcionário desabilitado com este CPF. Por favor, reative o cadastro."
            )
        validation_errors.append({"campo": "cpf", "mensagem": error_cpf})

    # Validação de Email (apenas se fornecido)
    if new_employee.usuario.email:
        error_email = employee_crud.verify_employee_conflict(
            db, new_employee.usuario.email, employee_crud.get_employee_by_email, "Email"
        )
        if error_email:
            validation_errors.append({"campo": "email", "mensagem": error_email})
            
    # Validação de RG (apenas se fornecido)
    if new_employee.rg:
        error_rg = employee_crud.verify_employee_conflict(
            db, new_employee.rg, employee_crud.get_employee_by_rg, "RG"
        )
        if error_rg:
            validation_errors.append({"campo": "rg", "mensagem": error_rg})
    
    if validation_errors:
        # Retorna erro 422 com todos os detalhes de validação
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=validation_errors
        )

    # 3. CRIAÇÃO DO USUÁRIO VINCULADO
    usuario_data = new_employee.usuario.model_dump()
    password = usuario_data.pop("senha") # Extrai e remove a senha do dicionário
    
    usuario_to_db = UsuarioModel(
        **usuario_data,
        senha_hash=hash_password(password), # Gera o hash
        empresa_id=new_employee.empresa_id,
        is_master=False,
        ativo=True,
        data_criacao=datetime.now()
    )
    
    # Cria o usuário para obter o ID
    usuario_in_db = user_crud.create_user(db, usuario_to_db)

    # 4. CRIAÇÃO DO FUNCIONÁRIO
    employee_data = new_employee.model_dump(exclude={"usuario", "endereco"})
    employee_to_db = FuncionarioModel(
        **employee_data,
        # Vincula ao usuário recém criado
        usuario_id=usuario_in_db.id,
    )

    # Cria o funcionário para obter o ID
    new_employee_in_db = employee_crud.create_employee(db, employee_to_db)

    # 5. VINCULAÇÃO DOS ENDEREÇOS (Polimórfico)
    if new_employee.endereco:
        new_address_employee_to_db = address_service.address_to_db(
            new_employee_in_db.id,
            EntityType.FUNCIONARIO, 
            new_employee.endereco
        )
        # Adiciona os endereços à relação ORM
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
    Lida com a atualização de campos simples e a lista de endereços (criação/edição).
    """
    
    # 1. Busca o funcionário existente no banco pelo ID
    update_employee = employee_crud.get_employee_by_id(db, employee_id)

    if not update_employee:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Funcionário não encontrado")
    
    # 2. Extrai apenas os dados enviados na requisição (para atualização parcial)
    update_data = employee.model_dump(exclude_unset=True)
    
    # 3. Tratamento especial para atualizar/substituir/criar endereços
    if "endereco" in update_data and update_data["endereco"] is not None:
        # Usa o serviço utilitário para aplicar as alterações nos endereços existentes
        updated_addresses = address_service.update_address_in_db(
            address_in_db=update_employee.endereco, # Lista atual do ORM
            address_update=employee.endereco,        # Lista nova/editada do Pydantic
            id_entity=update_employee.id,
            type_entity=EntityType.FUNCIONARIO
        )
        update_employee.endereco = updated_addresses
        # Remove 'endereco' do dict principal para atualização dos campos simples
        del update_data["endereco"]
    
    # 4. Itera sobre os dados restantes (campos simples) e atualiza o objeto SQLAlchemy
    for key, value in update_data.items():
        setattr(update_employee, key, value)
    
    # 5. Chama o CRUD para persistir as alterações
    return employee_crud.update_employee_in_db(db, update_employee)


# =========================
# Serviço: Ativar Funcionário (Soft Update)
# =========================
def active_employee_by_id(db: Session, employee_id: int) -> FuncionarioModel:
    """
    Serviço para ativar um funcionário pelo seu ID (seta 'ativo' para True).
    """
    # 1. Busca o funcionário
    existing_employee = employee_crud.get_employee_by_id(db, employee_id)

    if not existing_employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Funcionário não encontrado")
    
    # 2. Atualiza o objeto em memória
    existing_employee.ativo = True

    # 3. Delega a persistência para o CRUD
    return employee_crud.active_employee_by_id(db, existing_employee)


# =========================
# Serviço: Desativar Funcionário (Soft Delete)
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

    # 3. Delega a persistência para o CRUD
    return employee_crud.disable_employee_by_id(db, existing_employee)


# =========================
# Serviço: Atualizar Cargo do Funcionário
# =========================
def update_cargo_funcionario(db: Session, funcionario_id: int, cargo_id: int) -> FuncionarioModel:
    """
    Associa um novo Cargo (via cargo_id) a um Funcionário (via funcionario_id).
    """
    
    # 1. Busca o funcionário
    employee_in_db = employee_crud.get_employee_by_id(db, funcionario_id)

    if not employee_in_db:
        raise not_found_exce
    
    # 2. Atualiza a FK (Foreign Key) do cargo
    employee_in_db.cargo_id = cargo_id

    # 3. Persiste a alteração
    return employee_crud.update_employee_in_db(db, update_employee=employee_in_db)