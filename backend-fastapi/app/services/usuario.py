# ---------------------------------------------------------------------------
# ARQUIVO: usuario.py (dentro da pasta services)
# DESCRIÇÃO: Este módulo contém a lógica de negócio (regras, validações)
#            para as operações relacionadas a usuários.
# ---------------------------------------------------------------------------

from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

# Importa o modelo ORM do SQLAlchemy para type hinting e construção de objetos.
from app.db.models.usuario import Usuario as UsuarioModel
# Importa o schema Pydantic para validação dos dados de entrada.
from app.schemas.usuario import UsuarioCreate
# Importa as funções de segurança (neste caso, para gerar hash de senha).
from app.core.security import hash_password
# Importa o Enum para definir o tipo de usuário de forma padronizada.
from app.core.enum import UserType
# Importa as funções de acesso direto ao banco (CRUD).
from app.db.crud import usuario as user_crud


def get_user_by_id(db: Session, user_id: int) -> UsuarioModel:
    """
    Busca um usuário pelo ID, aplicando a regra de negócio de que,
    se o usuário não for encontrado, uma exceção HTTP 404 deve ser retornada.

    Args:
        db (Session): A sessão do banco de dados.
        user_id (int): O ID do usuário a ser buscado.

    Raises:
        HTTPException: Lança um erro 404 se o usuário não for encontrado.

    Returns:
        UsuarioModel: O objeto do usuário encontrado.
    """
    # Chama a camada CRUD para buscar o usuário no banco.
    user = user_crud.get_user_by_id(db, user_id)
    # Se a busca não retornar um usuário, levanta uma exceção.
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return user


def create_user_admin_service(db: Session, new_user: UsuarioCreate):
    """
    Serviço para criar um novo usuário com privilégios de Administrador.

    Args:
        db (Session): A sessão do banco de dados.
        new_user (UsuarioCreate): Os dados do novo usuário validados pelo Pydantic.

    Raises:
        HTTPException: Lança um erro 409 se o email já estiver em uso.

    Returns:
        UsuarioModel: O objeto do usuário recém-criado.
    """
    # REGRA DE NEGÓCIO: Antes de criar, verifica se já existe um usuário com este e-mail.
    user = user_crud.get_user_by_email(db, new_user.email)
    if user:
        # Se o e-mail já existe, informa o conflito.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já cadastrado")

    # Utiliza a função de segurança para gerar um hash seguro da senha.
    password_hash = hash_password(new_user.senha)

    # Prepara o objeto do modelo SQLAlchemy para ser salvo no banco.
    new_user_to_db = UsuarioModel(
        tipo=UserType.ADMIN,  # Define o tipo de usuário como Administrador.
        nome=new_user.nome,
        email=new_user.email,
        senha_hash=password_hash,  # Salva o hash da senha, nunca a senha original.
        data_criacao=datetime.now()
    )

    # Chama a camada CRUD para efetivamente salvar o usuário no banco de dados.
    return user_crud.create_user(db, new_user_to_db)