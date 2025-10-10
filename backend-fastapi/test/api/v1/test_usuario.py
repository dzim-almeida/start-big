# Arquivo de teste para o modelo de usuário

from fastapi.testclient import TestClient  # type: ignore   
from sqlalchemy.orm import Session  # type: ignore

from app.db.models.usuario import Usuario as UsuarioModel
from app.schemas.usuario import UsuarioCreate as UsuarioCreate
from app.services import usuario as usuario_service

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

def test_criar_usuario_com_email_existente(client: TestClient, db_session: Session):
    # Payload de teste para criar um usuário
    USUARIO_PAYLOAD = {
        "nome": "Maria Oliveira",
        "email": "maria.oliveira@example.com",
        "senha": "senhaSegura123"
    }
    # Cria o usuário pela primeira vez
    usuario_service.create_usuario_admin_service(db_session, UsuarioCreate(**USUARIO_PAYLOAD))
    resposta_2 = client.post("/api/v1/usuarios/", json=USUARIO_PAYLOAD)
    print("Detalhe do Erro:", resposta_2.json())
    # Verifica se a resposta foi 400 Bad Request ao tentar criar com email existente
    assert resposta_2.status_code == 400