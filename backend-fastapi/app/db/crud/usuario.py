# Arquivo de serviço para operações relacionadas a usuários

from sqlalchemy.orm import Session  # type: ignore
from app.db.models.usuario import Usuario as UsuarioModel  # Importa o modelo SQLAlchemy

# Função para obter um usuário pelo email
def get_usuario_by_email(db: Session, email: str):
    return db.query(UsuarioModel).filter(UsuarioModel.email == email).first()

# Função para criar um novo usuário
def create_usuario_db(db: Session, novo_usuario: UsuarioModel):
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario