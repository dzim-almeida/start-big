
from datetime import datetime
import pytest
from fastapi.testclient import TestClient  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.db.models.usuario import Usuario as UsuarioModel  # type: ignore
from app.core import security
from app.core.enum import UserType
from app.core.config import settings

TEST_USER_EMAIL = "teste.usuario@example.com"
TEST_USER_PASSWORD = "senhaSegura123"


@pytest.fixture(scope="function")
def test_user(db_session: Session):
    # Payload do usuário de teste 
    user = UsuarioModel(
        nome="Teste Usuario",
        email=TEST_USER_EMAIL,
        senha_hash=security.hash_password(TEST_USER_PASSWORD),
        tipo=UserType.USER,
        data_criacao=datetime.now(),
    )

    # Adiciona o usuário de teste ao banco de dados
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

# pylint: disable=unused-argument
# Teste de login bem-sucedido
def test_login_com_sucesso(client: TestClient, test_user: UsuarioModel):
    # Dados de login para o teste
    login_data = {"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}

    # Realiza o login
    response = client.post("/api/v1/auth/login", data=login_data)

    # Verifica se o login foi bem-sucedido
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)


def test_login_com_senha_incorreta(client: TestClient, test_user: UsuarioModel):

    password_incorrect = "naoexiste123"

    # Dados de login para o teste
    login_data = {"username": TEST_USER_EMAIL, "password": password_incorrect}

    # Realiza o login
    response = client.post("/api/v1/auth/login", data=login_data)

    assert response.status_code == 401
    assert "Email ou senha inválidos" in response.json()["detail"]


def test_login_com_email_incorreto(client: TestClient, test_user: UsuarioModel):

    email_incorrect = "naoexiste@gmail.com"

    # Dados de login para o teste
    login_data = {"username": email_incorrect, "password": TEST_USER_PASSWORD}

    # Realiza o login
    response = client.post("/api/v1/auth/login", data=login_data)

    assert response.status_code == 401
    assert "Email ou senha inválidos" in response.json()["detail"]


def test_logout_com_sucesso(client: TestClient, test_user: UsuarioModel):

   # Dados de login para o teste
    login_data = {"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}

    response_login = client.post("/api/v1/auth/login", data=login_data)
    assert response_login.status_code == 200
    token = response_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response_logout = client.post("/api/v1/auth/logout", headers=headers)
    assert response_logout.status_code == 200
    assert "Logout bem-sucedido" in response_logout.json()["message"]


def test_usar_token_revogado(client: TestClient, test_user: UsuarioModel):

   # Dados de login para o teste
    login_data = {"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}

    response_login = client.post("/api/v1/auth/login", data=login_data)
    assert response_login.status_code == 200
    token = response_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response_logout = client.post("/api/v1/auth/logout", headers=headers)
    assert response_logout.status_code == 200
    assert "Logout bem-sucedido" in response_logout.json()["message"]

    response_me = client.get("/api/v1/usuarios/me", headers=headers)

    assert response_me.status_code == 401
    assert "Não foi possível validar as credenciais" in response_me.json()["detail"]