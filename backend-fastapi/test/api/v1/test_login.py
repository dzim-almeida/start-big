# Testes para a funcionalidade de login

from fastapi.testclient import TestClient  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from datetime import datetime

from app.db.models.usuario import Usuario as UsuarioModel # type: ignore
from app.schemas.usuario import UsuarioCreate
from app.core import security
from app.core.enum import TipoUsuario
from app.services import usuario as usuario_service

# Teste de login bem-sucedido
def test_login_com_sucesso(client: TestClient, db_session: Session):
    # Cria um usuário de teste diretamente no banco de dados
    senha_plana = "senhaSegura123"
    senha_hash = security.generate_senha_hash(senha_plana)

    # Payload do usuário de teste
    usuario_teste = UsuarioModel(
        nome="Teste Usuario",
        email="teste.usuario@example.com",
        senha_hash=senha_hash,
        tipo=TipoUsuario.USER,
        data_criacao=datetime.now()
    )

    usuario_service.create_usuario_admin_service(db_session, UsuarioCreate(usuario_teste))
    
    # Dados de login para o teste
    USUARIO_PAYLOAD = {
        "email": usuario_teste.email,
        "senha": senha_plana
    }

    # Realiza o login
    response = client.post("/api/v1/auth/", json=USUARIO_PAYLOAD)

    # Verifica se o login foi bem-sucedido
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    



