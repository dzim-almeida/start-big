
from datetime import datetime
import pytest
from fastapi import status
from fastapi.testclient import TestClient  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.db.models.usuario import Usuario as UsuarioModel  # type: ignore
from app.core import security
from app.core.enum import UserType
from app.core.config import settings

TEST_USER_EMAIL = "teste.usuario@example.com"
TEST_USER_PASSWORD = "senhaSegura123"


def get_empresa_payload_valido(cnpj_suffix="000199", email_prefix="admin"):
    """
    Gera um payload válido combinando dados da Empresa e do Usuário Master.
    Permite sufixos para criar dados únicos nos testes.
    """
    return {
        # --- Dados da Empresa (EmpresaCreate) ---
        "razao_social": f"Empresa Teste {cnpj_suffix} LTDA",
        "nome_fantasia": "Tech Teste",
        "cnpj": f"12345678{cnpj_suffix}", # Deve ter 14 dígitos (Regex)
        "regime_tributario": "Simples Nacional",
        "celular": "11999998888",
        
        "usuario": {
            "nome": "Admin Master",
            "email": TEST_USER_EMAIL,
            "senha": TEST_USER_PASSWORD
        },
        
        # --- Endereço Inicial (Opcional) ---
        "endereco": [
            {
                "logradouro": "Av. Paulista",
                "numero": "1000",
                "bairro": "Bela Vista",
                "cidade": "São Paulo",
                "estado": "SP",
                "cep": "01310-100"
            }
        ]
    }

def create_test_empresa(client: TestClient):
    payload = get_empresa_payload_valido()

    request_url = "/api/v1/empresas/"

    response = client.post(
        request_url,
        json=payload
    )

    assert response.status_code == status.HTTP_201_CREATED

# pylint: disable=unused-argument
# Teste de login bem-sucedido
def test_login_com_sucesso(client: TestClient, db_session: Session):

    create_test_empresa(client)

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


def test_login_com_senha_incorreta(client: TestClient, db_session: Session):

    create_test_empresa(client)

    password_incorrect = "naoexiste123"

    # Dados de login para o teste
    login_data = {"username": TEST_USER_EMAIL, "password": password_incorrect}

    # Realiza o login
    response = client.post("/api/v1/auth/login", data=login_data)

    assert response.status_code == 401
    assert "Email ou senha inválidos" in response.json()["detail"]


def test_login_com_email_incorreto(client: TestClient, db_session: Session):

    create_test_empresa(client)

    email_incorrect = "naoexiste@gmail.com"

    # Dados de login para o teste
    login_data = {"username": email_incorrect, "password": TEST_USER_PASSWORD}

    # Realiza o login
    response = client.post("/api/v1/auth/login", data=login_data)

    assert response.status_code == 401
    assert "Email ou senha inválidos" in response.json()["detail"]


def test_logout_com_sucesso(client: TestClient, db_session: Session):

    create_test_empresa(client)

   # Dados de login para o teste
    login_data = {"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}

    response_login = client.post("/api/v1/auth/login", data=login_data)
    assert response_login.status_code == 200
    token = response_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response_logout = client.post("/api/v1/auth/logout", headers=headers)
    assert response_logout.status_code == 200
    assert "Logout bem-sucedido" in response_logout.json()["message"]


def test_usar_token_revogado(client: TestClient, db_session: Session):

    create_test_empresa(client)

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