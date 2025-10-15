# ---------------------------------------------------------------------------
# ARQUIVO: usuario.py (dentro da pasta crud)
# DESCRIÇÃO: Este módulo contém as funções de CRUD (Create, Read, Update,
#            Delete) para interagir com a tabela de usuários no banco de dados.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session

from app.db.models.usuario import Usuario as UsuarioModel

def get_user_by_email(db: Session, email: str) -> UsuarioModel | None:
    """
    Busca um único usuário no banco de dados pelo seu endereço de email.

    Args:
        db (Session): A sessão do banco de dados.
        email (str): O email do usuário a ser pesquisado.

    Returns:
        UsuarioModel | None: O objeto do usuário se encontrado, caso contrário None.
    """
    return db.query(UsuarioModel).filter(UsuarioModel.email == email).first()

def get_user_by_id(db: Session, id: int) -> UsuarioModel | None:
    """
    Busca um único usuário no banco de dados pelo seu ID.

    Args:
        db (Session): A sessão do banco de dados.
        id (int): O ID do usuário a ser pesquisado.

    Returns:
        UsuarioModel | None: O objeto do usuário se encontrado, caso contrário None.
    """
    return db.query(UsuarioModel).filter(UsuarioModel.id == id).first()

def create_user(db: Session, new_user: UsuarioModel) -> UsuarioModel:
    """
    Cria um novo registro de usuário no banco de dados.

    Esta função adiciona o novo usuário à sessão e usa 'flush' para que o
    ID gerado pelo banco de dados seja retornado no objeto, mas NÃO 'commita'
    a transação. O commit deve ser feito na camada de endpoint para garantir
    a atomicidade das operações.

    Args:
        db (Session): A sessão do banco de dados.
        usuario_schema (UsuarioCreateSchema): O objeto Pydantic com os dados do novo usuário.

    Returns:
        UsuarioModel: O objeto SQLAlchemy do usuário recém-criado, já com o ID.
    """
    # Converte o schema Pydantic para um modelo SQLAlchemy

    db.add(new_user)
    db.commit()  # Envia as instruções para o DB, o que permite obter o ID gerado.
    db.refresh(new_user) # Atualiza o objeto com os dados do DB (como o ID).
    
    return new_user

# NOTA: Funções para atualizar (update) e deletar (delete) um usuário seguiriam
# a mesma lógica, recebendo a sessão do DB e os dados necessários, e
# seriam adicionadas aqui conforme a necessidade do seu projeto.