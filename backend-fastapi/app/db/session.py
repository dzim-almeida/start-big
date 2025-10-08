# Arquivo para conexão com banco dados

from sqlalchemy import create_engine # type: ignore
from sqlalchemy.orm import sessionmaker # type: ignore
from app.core.config import settings # <-- Importando a configuração com a variável ambiente

# Criando a engine e a sessão
# connect_args={"check_same_thread": False} --> Necessário para SQLite
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})

# Criando a sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally:
        db.close()
