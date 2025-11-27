# ---------------------------------------------------------------------------
# ARQUIVO: services/cargo.py
# DESCRIÇÃO: Camada de serviço com a lógica de negócio para a entidade Cargo.
#            Implementa CRUD e validações de conflito (unicidade).
# ---------------------------------------------------------------------------

from typing import Sequence, Dict # Import adicionado para tipagem
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.cargo import CargoCreate, CargoUpdate
from app.db.models.cargo import Cargo as CargoModel
from app.db.crud import cargo as cargo_crud

# Exceções pré-definidas para reutilização (boa prática)
conflict_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Cargo já cadastrado no sistema."
)

not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Cargo não encontrado no sistema."
)


# =========================
# Serviço: Criar Cargo
# =========================
def create_cargo_funcionario(db: Session, user_token: Dict[str, int], new_cargo: CargoCreate) -> CargoModel:
    """
    Cria um novo cargo, garantindo que o nome seja único e vinculando
    o cargo à empresa do usuário logado (via user_token).
    """
    # 1. Validação de Conflito: Verifica se o cargo já existe pelo nome
    cargo_in_db = cargo_crud.get_cargo_funcionario_by_name(db, new_cargo.nome)
    if cargo_in_db:
        raise conflict_exce
    
    # 2. Mapeamento e Vinculação: Prepara o objeto ORM
    cargo_data = new_cargo.model_dump()

    cargo_to_db = CargoModel(
        **cargo_data,
        # Vincula o cargo à empresa do usuário logado (Multi-tenancy implícito)
        empresa_id=user_token["empresa_id"] 
    )

    # 3. Persistência: Delega a criação ao CRUD
    # O objeto é adicionado à sessão e será comitado pelo _handle_db_transaction
    cargo_in_db = cargo_crud.create_cargo_funcionario(db, cargo_to_add=cargo_to_db)    

    # Nota: O objeto retornado aqui é o 'cargo_to_db' (já anexado na sessão, mas sem o ID gerado), 
    # o 'cargo_in_db' é o retorno do CRUD (que pode ser o mesmo objeto, dependendo da implementação).
    return cargo_to_db 


# =========================
# Serviço: Buscar Todos os Cargos
# =========================
def get_all_cargo_funcionario(db: Session) -> Sequence[CargoModel]:
    """
    Retorna todos os cargos. (Delega para o CRUD).
    """
    return cargo_crud.get_all_cargos_funcionario(db)


# =========================
# Serviço: Atualizar Cargo
# =========================
def update_cargo_funcionario(db: Session, cargo_id: int, update_cargo: CargoUpdate) -> CargoModel:
    """
    Busca um cargo pelo ID, aplica as alterações e persiste.
    """
    # 1. Busca: Verifica se o cargo existe (Lança 404 se não existir)
    cargo_in_db = cargo_crud.get_cargo_funcionario_by_id(db, cargo_id=cargo_id)
    if not cargo_in_db:
        raise not_found_exce

    # 2. Atualização Parcial: Extrai apenas os campos que foram enviados
    update_cargo_data = update_cargo.model_dump(exclude_unset=True)
    
    # 3. Aplicação: Itera e atualiza o objeto ORM em memória
    for key, value in update_cargo_data.items():
        setattr(cargo_in_db, key, value)

    # 4. Persistência: Delega a atualização ao CRUD
    cargo_updated = cargo_crud.update_cargo_funcionaio(db, cargo_to_update=cargo_in_db)

    return cargo_updated


# =========================
# Serviço: Deletar Cargo
# =========================
def delete_cargo_funcionario(db: Session, cargo_id: int) -> None:
    """
    Deleta um cargo pelo ID.
    """
    # 1. Busca: Verifica se o cargo existe (Lança 404 se não existir)
    cargo_in_db = cargo_crud.get_cargo_funcionario_by_id(db, cargo_id=cargo_id)
    if not cargo_in_db:
        raise not_found_exce
    
    # 2. Deleção: Delega a exclusão ao CRUD
    return cargo_crud.delete_cargo_funcionario(db, cargo_to_delete=cargo_in_db)