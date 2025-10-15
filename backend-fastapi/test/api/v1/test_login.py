# Testes para a funcionalidade de login

from fastapi.testclient import TestClient  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from datetime import datetime

from app.db.models.usuario import Usuario as UsuarioModel # type: ignore
from app.core import security
from app.core.enum import UserType


# Teste de login bem-sucedido
def test_login_com_sucesso(client: TestClient, db_session: Session):
    # Cria um usuário de teste diretamente no banco de dados
    email = "teste.usuario@example.com"
    senha = "senhaSegura123"

    # Payload do usuário de teste
    usuario_teste = UsuarioModel(
        nome="Teste Usuario",
        email= email,
        senha_hash=security.hash_password(senha),
        tipo=UserType.USER,
        data_criacao=datetime.now()
    )

    # Adiciona o usuário de teste ao banco de dados
    db_session.add(usuario_teste)
    db_session.commit()
    
    # Dados de login para o teste
    login_data = {
        "username": email,
        "password": senha
    }

    # Realiza o login
    response = client.post("/api/v1/auth/login", data=login_data)

    # Verifica se o login foi bem-sucedido
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 900
    
def test_login_com_senha_incorreta(client: TestClient, db_session: Session):
    # Cria um usuário de teste diretamente no banco de dados
    email = "teste.usuario@example.com"
    senha_correta = "senhaSegura123"
    senha_errada = "naoexiste123"

# Payload do usuário de teste
    usuario_teste = UsuarioModel(
        nome="Teste Usuario",
        email= email,
        senha_hash=security.hash_password(senha_correta),
        tipo=UserType.USER,
        data_criacao=datetime.now()
    )

    # Adiciona o usuário de teste ao banco de dados
    db_session.add(usuario_teste)
    db_session.commit()
    
    # Dados de login para o teste
    login_data = {
        "username": email,
        "password": senha_errada
    }

    # Realiza o login
    response = client.post("/api/v1/auth/login", data=login_data)

    assert response.status_code == 401
    assert "Email ou senha inválidos" in response.json()["detail"]

def test_login_com_senha_incorreta(client: TestClient, db_session: Session):
    # Cria um usuário de teste diretamente no banco de dados
    email_correto = "teste.usuario@example.com"
    email_errado = "naoexiste@gmail.com"
    senha = "senhaSegura123"

    # Payload do usuário de teste
    usuario_teste = UsuarioModel(
        nome="Teste Usuario",
        email= email_correto,
        senha_hash=security.hash_password(senha),
        tipo=UserType.USER,
        data_criacao=datetime.now()
    )

    # Adiciona o usuário de teste ao banco de dados
    db_session.add(usuario_teste)
    db_session.commit()
    
    # Dados de login para o teste
    login_data = {
        "username": email_errado,
        "password": senha
    }

    # Realiza o login
    response = client.post("/api/v1/auth/login", data=login_data)

    assert response.status_code == 401
    assert "Email ou senha inválidos" in response.json()["detail"]

def test_logout_com_sucesso(client: TestClient, db_session: Session):

    payload_login = {
        "username": "teste.usuario@example.com",
        "password": "senhaSegura123"
    }

    # Payload do usuário de teste
    test_user = UsuarioModel(
        nome="Logout Sucesso",
        email= payload_login["username"],
        senha_hash=security.hash_password(payload_login["password"]),
        tipo=UserType.USER,
        data_criacao=datetime.now()
    )

    db_session.add(test_user)
    db_session.commit()

    response_login = client.post("/api/v1/auth/login", data=payload_login)
    assert response_login.status_code == 200
    token = response_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response_logout = client.post("/api/v1/auth/logout", headers=headers)
    assert response_logout.status_code == 200
    assert "Logout bem-sucedido" in response_logout.json()["message"]

def test_usar_token_revogado(client: TestClient, db_session: Session):
     
    payload_login = {
        "username": "teste.usuario@example.com",
        "password": "senhaSegura123"
    }

    # Payload do usuário de teste
    test_user = UsuarioModel(
        nome="Logout Sucesso",
        email= payload_login["username"],
        senha_hash=security.hash_password(payload_login["password"]),
        tipo=UserType.USER,
        data_criacao=datetime.now()
    )

    db_session.add(test_user)
    db_session.commit()

    response_login = client.post("/api/v1/auth/login", data=payload_login)
    assert response_login.status_code == 200
    token = response_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response_logout = client.post("/api/v1/auth/logout", headers=headers)
    assert response_logout.status_code == 200
    assert "Logout bem-sucedido" in response_logout.json()["message"]

    response_me = client.get("/api/v1/usuarios/me", headers=headers)

    assert response_me.status_code == 401
    assert "Não foi possível validar as credenciais" in response_me.json()["detail"]

    

    
    

