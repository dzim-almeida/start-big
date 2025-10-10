# Arquivo de configuração para testes

import pytest # type: ignore
from fastapi.testclient import TestClient # type: ignore
from sqlalchemy import create_engine # type: ignore
from sqlalchemy.orm import sessionmaker # type: ignore
from sqlalchemy.pool import StaticPool # type: ignore

from app.main import app
from app.db.session import get_db
from app.db.base import Base

from app.db.models.usuario import Usuario

# Configuração do banco de dados de teste (SQLite em memória)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Criando a engine de teste
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Criando a sessão de teste
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# get_db override para usar o banco de dados de teste
def get_db_override():
    db = TestingSessionLocal()
    try: 
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = get_db_override

# Fixture para o cliente de teste
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

# Fixture para o banco de dados de teste
@pytest.fixture(scope="function")
def db_session():
    # Criar todas as tabelas
    Base.metadata.create_all(bind=engine)
    # Criar e fechar sessão após o teste
    session = TestingSessionLocal()
    yield session
    session.close()
    # Dropar todas as tabelas
    Base.metadata.drop_all(bind=engine)

