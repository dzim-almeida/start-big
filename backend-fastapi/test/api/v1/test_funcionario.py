# ---------------------------------------------------------------------------
# ARQUIVO: test_funcionario.py
# DESCRIÇÃO: Testes de integração para os endpoints de Funcionario.
#            Utiliza dados dinâmicos para garantir isolamento por função.
# ---------------------------------------------------------------------------

from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette import status 
import random
import string

# Assumindo o caminho de imports
from app.db.models.usuario import Usuario as UsuarioModel
from app.core.security import hash_password 
from app.core.enum import UserType 

# --- Constantes de Teste ---
TEST_USER_EMAIL = "teste.funcionario@example.com"
TEST_USER_PASSWORD = "senhaSegura456"

# Dados base para a criação de um Funcionário (Apenas a estrutura, dados serão gerados)
BASE_FUNCIONARIO_DATA = {
    "nome": "Carlos Roberto Souza",
    "email": "carlos.souza@empresa.com.br",
    "contato": "88998765432",
    "cpf": "11122233344",
    "rg": "11223344",
    "carteira_trabalho": "1234567-8",
    "cnh": "98765432101",
    "funcao": "Vendedor Senior",
    "agencia": "0001",
    "conta": "12345678",
    "banco": "Banco PDV",
    "mae": "Maria Joaquina Souza",
    "pai": "Roberto Carlos Souza",
    "observacao": "Pode cobrir a área de Fortaleza se necessário.",
    "usuario_id": 1,
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
}

# =========================
# Fixture de Autenticação
# =========================
@pytest.fixture(scope="function")
def header_with_token(client: TestClient, db_session: Session) -> dict:
    """
    Cria um usuário de teste, realiza o login e retorna headers com o token Bearer.
    """
    user = UsuarioModel(
        nome="Teste Funcionario",
        email=TEST_USER_EMAIL,
        senha_hash=hash_password(TEST_USER_PASSWORD),
        tipo=UserType.USER,
        data_criacao=datetime.now(),
    )
    db_session.add(user)
    db_session.commit()

    login_data = {"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200 
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ===============================================
# Fixture Geradora de Dados Únicos por Função
# ===============================================
@pytest.fixture(scope="function")
def unique_funcionario_data():
    """
    Gera um dicionário de dados de funcionário com CPF e E-mail únicos.
    """
    def generate_data():
        # Gera um CPF pseudo-aleatório de 11 dígitos
        unique_cpf = "".join(random.choices(string.digits, k=11))
        # Gera um ID de e-mail único
        unique_id = "".join(random.choices(string.ascii_letters, k=8))
        
        data = BASE_FUNCIONARIO_DATA.copy()
        data["cpf"] = unique_cpf
        data["email"] = f"{unique_id}@unique.com.br"
        return data
    
    return generate_data


# =========================
# Testes de Criação de Funcionário (POST)
# =========================
def test_criar_funcionario_com_sucesso(client: TestClient, header_with_token: dict, unique_funcionario_data):
    """
    Testa o "caminho feliz": a criação bem-sucedida de um novo funcionário.
    """
    data_funcionario = unique_funcionario_data()
    
    response = client.post("/api/v1/funcionarios/", json=data_funcionario, headers=header_with_token)
    
    assert response.status_code == status.HTTP_201_CREATED 
    data = response.json()
    assert data["cpf"] == data_funcionario["cpf"]


def test_criar_funcionario_sem_token_falha(client: TestClient):
    """
    Testa a falha ao tentar criar um funcionário sem autenticação.
    """
    data_funcionario = BASE_FUNCIONARIO_DATA.copy()
    
    response = client.post("/api/v1/funcionarios/", json=data_funcionario)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# =========================
# Testes de Busca de Funcionário (GET)
# =========================
def test_buscar_funcionario_por_cpf_com_sucesso(client: TestClient, header_with_token: dict, unique_funcionario_data):
    """
    Testa a funcionalidade de busca por CPF.
    1. Cria um funcionário com CPF único.
    2. Busca por esse CPF.
    """
    # --- Arrange (Setup de Criação) ---
    data_client = unique_funcionario_data()
    
    response_create = client.post("/api/v1/funcionarios/", json=data_client, headers=header_with_token)
    assert response_create.status_code == status.HTTP_201_CREATED 

    # --- Act (Busca) ---
    response_search = client.get(f"/api/v1/funcionarios/?buscar={data_client["cpf"]}", headers=header_with_token)
    
    # --- Assert ---
    assert response_search.status_code == status.HTTP_200_OK
    data = response_search.json()
    assert len(data) == 1 
    assert data[0]["cpf"] == data_client["cpf"]


# =========================
# Testes de Atualização de Funcionário (PUT)
# =========================
def test_editar_funcionario_com_sucesso(client: TestClient, header_with_token: dict, unique_funcionario_data):
    """
    Testa a edição de um funcionário.
    1. Cria o funcionário.
    2. Edita a função e o email.
    3. Verifica a persistência.
    """
    # --- Arrange (Criação) ---
    data_create = unique_funcionario_data()
    
    response_create = client.post("/api/v1/funcionarios/", json=data_create, headers=header_with_token)
    assert response_create.status_code == status.HTTP_201_CREATED
    data_created = response_create.json()
    funcionario_id = data_created["id"]
    
    # --- Arrange (Payload de Edição) ---
    payload_edit = {
        "funcao": "Gerente de Projetos", # Novo valor
        "email": f"novo.email.{random.randint(100, 999)}@empresa.com" # Novo email único
    }

    # --- Act (Edição) ---
    response_edit = client.put(f"/api/v1/funcionarios/{funcionario_id}", json=payload_edit, headers=header_with_token)
    
    # --- Assert ---
    assert response_edit.status_code == status.HTTP_200_OK
    data_edit = response_edit.json()
    assert data_edit["id"] == funcionario_id
    assert data_edit["funcao"] == "Gerente de Projetos"
    assert data_edit["email"] == payload_edit["email"]
    assert data_edit["nome"] == data_create["nome"] # Campo não alterado deve ser mantido


# =========================
# Testes de Status (Desativação/Ativação - PUT)
# =========================
def test_desativar_funcionario_com_sucesso(client: TestClient, header_with_token: dict, unique_funcionario_data):
    """
    Testa a desativação lógica (soft delete).
    1. Cria o funcionário.
    2. Envia requisição PUT para /desativa/{id}.
    3. Verifica 204 No Content.
    """
    # --- Arrange (Criação) ---
    data_create = unique_funcionario_data()

    response_create = client.post("/api/v1/funcionarios/", json=data_create, headers=header_with_token)
    assert response_create.status_code == status.HTTP_201_CREATED
    funcionario_id = response_create.json()["id"]

    # --- Act (Desativação) ---
    response_deactivate = client.put(f"/api/v1/funcionarios/desativa/{funcionario_id}", headers=header_with_token)

    # --- Assert ---
    # 1. Verifica o status 204 No Content (padrão RESTful para soft delete)
    assert response_deactivate.status_code == status.HTTP_204_NO_CONTENT
    # 2. Verifica se o corpo da resposta está vazio (se o endpoint seguir o 204)
    assert response_deactivate.text == ""

# -------------------------------------------------------------
# ÚLTIMA FUNÇÃO: Ativação (PUT /ativa/{id})
# -------------------------------------------------------------
def test_ativar_funcionario_com_sucesso(client: TestClient, header_with_token: dict, unique_funcionario_data):
    """
    Testa a reativação.
    1. Cria e desativa um funcionário (pré-condição).
    2. Envia requisição PUT para /ativa/{id}.
    3. Verifica 200 OK e 'ativo=true' na resposta.
    """
    # --- Arrange (Criação e Desativação - Pré-condição) ---
    data_create = unique_funcionario_data()

    # 1. Criação inicial
    response_create = client.post("/api/v1/funcionarios/", json=data_create, headers=header_with_token)
    assert response_create.status_code == status.HTTP_201_CREATED
    funcionario_id = response_create.json()["id"]

    # 2. Desativação (Soft Delete)
    response_deactivate = client.put(f"/api/v1/funcionarios/desativa/{funcionario_id}", headers=header_with_token)
    assert response_deactivate.status_code == status.HTTP_204_NO_CONTENT
    
    # --- Act (Ativação) ---
    response_activate = client.put(f"/api/v1/funcionarios/ativa/{funcionario_id}", headers=header_with_token)

    # --- Assert ---
    # 1. Verifica o status HTTP 200 OK (padrão para ativação que retorna o objeto)
    assert response_activate.status_code == status.HTTP_200_OK
    
    data_activate = response_activate.json()
    
    # 2. Verifica se o campo 'ativo' foi definido como True na resposta
    assert data_activate["ativo"] == True 
    assert data_activate["id"] == funcionario_id