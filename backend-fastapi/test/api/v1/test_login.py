# Testes para a funcionalidade de login

from fastapi.testclient import TestClient  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from datetime import datetime

from app.db.models.usuario import Usuario as UsuarioModel # type: ignore
from app.core import security
from app.core.enum import TipoUsuario

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

    # Adiciona o usuário de teste ao banco de dados
    db_session.add(usuario_teste)
    db_session.commit()
    
    # Dados de login para o teste
    login_data = {
        "username": usuario_teste.email,
        "password": senha_plana
    }

    # Realiza o login
    response = client.post("/api/v1/login/", data=login_data)

    # Verifica se o login foi bem-sucedido
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    



