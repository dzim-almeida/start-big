# Arquivo de teste para o modelo de usuário

from fastapi.testclient import TestClient  # type: ignore   
from sqlalchemy.orm import Session  # type: ignore

from datetime import datetime

from app.db.models.usuario import Usuario as UsuarioModel
from app.schemas.usuario import UsuarioCreate as UsuarioCreate
from app.services import usuario as usuario_service
from app.core import security
from app.core.enum import UserType

# Teste de criação de usuário com sucesso
def test_criar_usuario_com_sucesso(client: TestClient, db_session: Session):
    # Payload de teste para criar um usuário
    USUARIO_PAYLOAD = {
        "nome": "João Silva",
        "email": "joao.silva@example.com",
        "senha": "senhaSegura123"
    } 

    # Envia a requisição POST para criar o usuário
    resposta = client.post("/api/v1/usuarios/", json=USUARIO_PAYLOAD)
    # Verifica se a resposta foi 201 Created
    assert resposta.status_code == 201


# Teste de criação de usuário com email já existente
def test_criar_usuario_com_email_existente(client: TestClient, db_session: Session):
    # Payload de teste para criar um usuário
    USUARIO_PAYLOAD = {
        "nome": "Maria Oliveira",
        "email": "maria.oliveira@example.com",
        "senha": "senhaSegura123"
    }
    # Cria o usuário pela primeira vez
    usuario_service.create_user_admin_service(db_session, UsuarioCreate(**USUARIO_PAYLOAD))
    resposta_2 = client.post("/api/v1/usuarios/", json=USUARIO_PAYLOAD)
    # Verifica se a resposta foi 409 Conflit ao tentar criar com email existente
    assert resposta_2.status_code == 409

#  
def test_criar_usuario_me_sem_token_falha(client: TestClient):
    response = client.get("/api/v1/usuarios/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_criar_usuario_me_com_sucesso(client: TestClient, db_session: Session):
    # Cria um usuário de teste diretamente no banco de dados
    email = "teste.usuario@example.com"
    senha_plana = "senhaSegura123"

    # Payload do usuário de teste
    usuario_teste = UsuarioModel(
        nome="Teste Usuario",
        email=email,
        senha_hash=security.hash_password(senha_plana),
        tipo=UserType.USER,
        data_criacao=datetime.now()
    )

    # Adiciona o usuário de teste ao banco de dados
    db_session.add(usuario_teste)
    db_session.commit()

    # Dados de login para o teste
    USUARIO_PAYLOAD = {
        "username": email,
        "password": senha_plana
    }

    response = client.post("/api/v1/auth/login", data=USUARIO_PAYLOAD)

    assert response.status_code == 200
    token = response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    reponse = client.get("/api/v1/usuarios/me", headers=headers)
    assert reponse.status_code == 200


