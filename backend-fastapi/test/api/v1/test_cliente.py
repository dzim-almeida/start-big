# ---------------------------------------------------------------------------
# ARQUIVO: test_cliente.py
# DESCRIÇÃO: Testes de integração para os endpoints de Cliente,
#            seguindo a metodologia TDD.
# ---------------------------------------------------------------------------

from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette import status # Boa prática para usar status codes nominais

from app.db.models.usuario import Usuario as UsuarioModel
from app.core.security import hash_password
from app.core.enum import UserType

# --- Constantes de Teste ---
TEST_USER_EMAIL = "teste.usuario@example.com"
TEST_USER_PASSWORD = "senhaSegura123"

# =========================
# Fixture de Autenticação
# =========================
@pytest.fixture(scope="function")
def header_with_token(client: TestClient, db_session: Session) -> dict:
    """
    Fixture reutilizável que cria um usuário de teste, realiza o login
    via API e retorna um dicionário de headers com o token Bearer.
    
    'scope="function"' garante que isso seja executado para cada teste
    que a utiliza, garantindo um estado limpo.
    """
    # Arrange 1: Criar o usuário no banco
    user = UsuarioModel(
        nome="Teste Usuario",
        email=TEST_USER_EMAIL,
        senha_hash=hash_password(TEST_USER_PASSWORD),
        tipo=UserType.USER,
        data_criacao=datetime.now(),
    )
    db_session.add(user)
    db_session.commit()

    # Arrange 2: Fazer login para obter o token
    login_data = {"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200 # Garante que o login da fixture funcionou
    
    # Act: Montar os headers
    token = response.json()["access_token"]
    header_with_token = {"Authorization": f"Bearer {token}"}
    
    # Assert (retorno da fixture)
    return header_with_token

# =========================
# Testes de Criação de Cliente
# =========================
def test_criar_cliente_pf_usuario_logado(client: TestClient, header_with_token: dict):
    """
    Testa o "caminho feliz": a criação bem-sucedida de um Cliente PF
    quando o usuário está autenticado.
    """
    # Arrange: Define o payload (corpo da requisição) para o novo cliente
    data_client = {
        "email": "joao.silva@meu-pdv.com",
        "contato": "11987654321",
        "observacoes": "Cliente novo, aceita e-mail marketing.",
        "endereco": [
            {
                "logradouro": "Rua das Flores",
                "numero": "456A",
                "complemento": "Casa",
                "bairro": "Jardim América",
                "cidade": "Campinas",
                "estado": "SP",
                "cep": "13010-000"
            },
            {
                "logradouro": "Av. Principal",
                "numero": "20",
                "complemento": "Escritório",
                "bairro": "Centro",
                "cidade": "Belo Horizonte",
                "estado": "MG",
                "cep": "30110-010"
            }
        ],
        
        "nome": "João Pedro Silva",
        "cpf": "98765432101", 
        "rg": "12345678",
        "genero": "MASCULINO", 
        "data_nascimento": "1995-12-15"
    }

    # Act: Envia a requisição POST para o endpoint protegido,
    # incluindo o payload (json) e os headers de autenticação (token)
    response = client.post("/api/v1/clientes/cliente_pf", json=data_client, headers=header_with_token)
    
    # Assert: Verifica se a criação foi bem-sucedida
    assert response.status_code == 201 # Verifica o status HTTP 201 Created
    data = response.json()
    assert data["nome"] == "João Pedro Silva" # Verifica se o nome retornado está correto
    assert data["email"] == "joao.silva@meu-pdv.com" # Verifica se o email retornado está correto

def test_criar_cliente_pf_sem_token(client: TestClient):
    """
    Testa o "caminho triste": a falha ao tentar criar um Cliente PF
    sem enviar um token de autenticação.
    """
    # Arrange: Define o mesmo payload (poderia ser simplificado, mas está ok)
    data_client = {
        "email": "joao.silva@meu-podv.com",
        "contato": "11987654321",
        "observacoes": "Cliente novo, aceita e-mail marketing.",
        
        "endereco": [
            {
                "logradouro": "Rua das Flores",
                "numero": "456A",
                "complemento": "Casa",
                "bairro": "Jardim América",
                "cidade": "Campinas",
                "estado": "SP",
                "cep": "13010-000"
            },
            {
                "logradouro": "Av. Principal",
                "numero": "20",
                "complemento": "Escritório",
                "bairro": "Centro",
                "cidade": "Belo Horizonte",
                "estado": "MG",
                "cep": "30110-010"
            }
        ],
        
        "nome": "João Pedro Silva",
        "cpf": "98765432101", 
        "rg": "12345678",
        "genero": "MASCULINO", 
        "data_nascimento": "1995-12-15"
    }

    # Act: Envia a requisição POST, mas desta vez SEM os headers de autenticação
    response = client.post("/api/v1/clientes/cliente_pf", json=data_client)
    
    # Assert: Verifica se a API protegeu o endpoint e retornou 401 Unauthorized
    assert response.status_code == 401