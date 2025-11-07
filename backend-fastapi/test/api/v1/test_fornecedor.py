# ---------------------------------------------------------------------------
# ARQUIVO: test_fornecedor.py
# DESCRIÇÃO: Testes de integração para os endpoints CRUD de Fornecedores.
# ---------------------------------------------------------------------------

from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

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
    # Arrange 1: Criar o usuário de teste no banco de dados
    user = UsuarioModel(
        nome="Teste Usuario",
        email=TEST_USER_EMAIL,
        senha_hash=hash_password(TEST_USER_PASSWORD),
        tipo=UserType.USER,
        data_criacao=datetime.now(),
    )
    db_session.add(user)
    db_session.commit()

    # Arrange 2: Preparar dados para fazer login via API
    login_data = {"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    
    # Act: Realizar o login para obter um token de acesso
    response = client.post("/api/v1/auth/login", data=login_data)
    
    # Assert (pré-condição): Garante que o login da fixture funcionou
    assert response.status_code == 200
    
    # Arrange 3: Extrair o token e montar o header de autorização
    token = response.json()["access_token"]
    header_with_token = {"Authorization": f"Bearer {token}"}
    
    # Retorna os headers para serem usados pelos testes
    return header_with_token

# =========================
# Testes de Criação de Fornecedor
# =========================
def test_criar_forncedor_com_usuario_logado(client: TestClient, header_with_token: dict):
    """
    Testa o "caminho feliz": a criação bem-sucedida de um Fornecedor
    quando o usuário está autenticado.
    """
    # Arrange: Define o payload (corpo da requisição JSON) para o novo fornecedor
    data_supplier = {
        "nome": "Alan Amorim ME",
        "cnpj": "72345734000132",
        "nome_fantasia": "BigTech",
        "ie": None
    }

    # Act: Envia a requisição POST para o endpoint de criação de fornecedores
    response = client.post("/api/v1/fornecedores/", json=data_supplier, headers=header_with_token)
    
    # Assert: Verifica se a criação foi bem-sucedida
    assert response.status_code == 201
    assert response.json()["nome"] == "Alan Amorim ME"
    
def test_criar_fornecedor_sem_token(client: TestClient):
    """
    Testa o "caminho triste": a falha ao tentar criar um Fornecedor
    sem enviar um token de autenticação (usuário não logado).
    """
    # Arrange: Define o payload
    data_supplier = {
        "nome": "Alan Amorim ME",
        "cpnj": "72345734000132", # (Mantido erro de digitação original 'cpnj')
        "nome_fantasia": "BigTech",
        "ie": None
    }

    # Act: Envia a requisição POST, mas SEM os headers de autenticação
    response = client.post("/api/v1/fornecedores/", json=data_supplier)
    
    # Assert: Verifica se a API protegeu o endpoint, retornando 401 Unauthorized
    assert response.status_code == 401

# =========================
# Teste de Busca de Fornecedor
# =========================
def test_buscar_fornecedor_por_cnpj(client: TestClient, header_with_token: dict):
    """
    Testa a funcionalidade de busca por CNPJ:
    1. Cria um fornecedor.
    2. Busca por esse fornecedor usando seu CNPJ.
    3. Verifica se o fornecedor correto foi retornado.
    """
    # --- Arrange 1: Criar o Fornecedor ---
    data_supplier = {
        "nome": "Alan Amorim ME",
        "cnpj": "72345734000132",
        "nome_fantasia": "BigTech",
        "ie": None
    }

    create_response = client.post("/api/v1/fornecedores/", json=data_supplier, headers=header_with_token)
    assert create_response.status_code == 201

    # --- Arrange 2: Definir termo de busca ---
    search_cnpj = "72345734000132"
    
    # --- Act: Buscar o Fornecedor ---
    search_response = client.get(f"/api/v1/fornecedores/?buscar={search_cnpj}", headers=header_with_token)
    
    # --- Assert: Verificar o resultado da busca ---
    assert search_response.status_code == 200
    search_data = search_response.json()
    assert search_data[0]["nome"] == "Alan Amorim ME"

# =========================
# Teste de Edição de Fornecedor
# =========================
def test_editar_fornecedor(client: TestClient, header_with_token: dict):
    """
    Testa a funcionalidade de edição (PUT) de um fornecedor existente:
    1. Cria um fornecedor.
    2. Modifica o 'nome_fantasia' no objeto retornado.
    3. Envia uma requisição PUT para atualizar o fornecedor.
    4. Verifica se a atualização foi bem-sucedida (status 200) e se o dado foi alterado.
    """
    # --- Arrange 1: Criar o Fornecedor ---
    data_supplier = {
        "nome": "Alan Amorim ME",
        "cnpj": "72345734000132",
        "nome_fantasia": "BigTech",
        "ie": None
    }
    
    create_response = client.post("/api/v1/fornecedores/", json=data_supplier, headers=header_with_token)
    assert create_response.status_code == 201

    # --- Arrange 2: Preparar dados para edição ---
    edited_response = create_response.json()
    edited_response["nome_fantasia"] = "BigTech Editada"

    # --- Act: Enviar a Requisição de Edição (PUT) ---
    update_response = client.put(f"/api/v1/fornecedores/{edited_response['id']}", json=edited_response, headers=header_with_token)
    
    # --- Assert: Verificar o resultado da edição ---
    assert update_response.status_code == 200
    assert update_response.json()["nome_fantasia"] == "BigTech Editada"

# =========================
# Teste de Deleção de Fornecedor
# =========================
def test_deletar_fornecedor(client: TestClient, header_with_token: dict):
    """
    Testa a funcionalidade de deleção (DELETE) de um fornecedor existente:
    1. Cria um fornecedor.
    2. Envia uma requisição DELETE para excluir o fornecedor pelo ID.
    3. Verifica se a deleção foi bem-sucedida (status 204).
    4. Tenta buscar o fornecedor deletado e verifica se a busca retorna uma lista vazia.
    """
    # --- Arrange 1: Criar o Fornecedor ---
    data_supplier = {
        "nome": "Alan Amorim ME",
        "cnpj": "72345734000132",
        "nome_fantasia": "BigTech",
        "ie": None
    }
    
    create_response = client.post("/api/v1/fornecedores/", json=data_supplier, headers=header_with_token)
    assert create_response.status_code == 201

    supplier_id = create_response.json()["id"]

    # --- Act: Enviar a Requisição de Deleção (DELETE) ---
    delete_response = client.delete(f"/api/v1/fornecedores/{supplier_id}", headers=header_with_token)
    
    # --- Assert 1: Verificar o Resultado da Deleção ---
    assert delete_response.status_code == 204

    # --- Assert 2: Verificar se o Fornecedor Foi Deletado ---
    # Tenta buscar o fornecedor pelo CNPJ que acabou de ser deletado
    search_cnpj = "72345734000132"
    search_response = client.get(f"/api/v1/fornecedores/?buscar={search_cnpj}", headers=header_with_token)
    assert search_response.status_code == 200 # A busca deve ser bem-sucedida (200 OK)
    search_data = search_response.json()

    # A lista de resultados da busca DEVE estar vazia agora
    assert len(search_data) == 0