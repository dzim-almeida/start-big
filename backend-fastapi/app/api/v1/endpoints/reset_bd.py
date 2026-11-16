from fastapi import APIRouter, status

from app.db.base import Base  # Importando as classes base
from app.db.session import engine  # Importando a engine do banco de dados

router = APIRouter()

@router.get(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Reseta o banco de dados"
)
def reset_db():
    try:
        # Destroi e recria todas as tabelas conforme os modelos atuais
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        return "Banco de dados resetado com sucesso!"
    except Exception as e:
        raise(e)