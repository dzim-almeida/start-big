# ---------------------------------------------------------------------------
# ARQUIVO: test_servico.py
# DESCRIÇÃO: Testes de integração (API) para os endpoints de /servicos.
#            Utiliza o TestClient do FastAPI e fixtures do Pytest.
# ---------------------------------------------------------------------------

from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.usuario import Usuario as UsuarioModel
from app.core.security import hash_password
from app.core.enum import UserType

# --- Constantes de Teste ---
# Usar constantes torna os testes mais fáceis de manter
TEST_USER_EMAIL = "teste.funcionario@example.com"
TEST_USER_PASSWORD = "senhaSegura456"

# =========================
# Fixture de Autenticação
# =========================
@pytest.fixture(scope="function")
def header_with_token(client: TestClient, db_session: Session, create_test_empresa) -> dict:

    login_data = {"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200 
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# =========================
# TESTE: Criar Serviço
# =========================
def test_criar_novo_servico(client: TestClient, header_with_token: dict):
    """
    Testa a criação bem-sucedida de um novo serviço (POST /servicos/).
    Verifica se o status code é 201 e se a descrição retornada é correta.
    """
    # Arrange: Dados do novo serviço a ser criado
    data_service = {
        "descricao": "Troca de tela do Iphone 16",
        "valor": 75049
    }

    # Act: Faz a requisição POST para o endpoint
    response = client.post("/api/v1/servicos/", json=data_service, headers=header_with_token)
    
    # Assert: Verifica se a criação foi bem-sucedida
    assert response.status_code == 201
    assert response.json()["descricao"] == "Troca de tela do Iphone 16"

# =========================
# TESTE: Buscar Serviço
# =========================
def test_buscar_servico(client: TestClient, header_with_token: dict):
    """
    Testa a busca de um serviço (GET /servicos/?buscar=...).
    Primeiro cria um serviço e depois o busca pela descrição.
    """
    # Arrange 1: Criar um serviço para poder ser buscado
    data_service = {
        "descricao": "Manutenção de Placa de Vídeo",
        "valor": 75049
    }
    create_response = client.post("/api/v1/servicos/", json=data_service, headers=header_with_token)
    assert create_response.status_code == 201

    # Arrange 2: Definir o termo de busca
    search = data_service["descricao"]
    
    # Act: Fazer a requisição GET com o parâmetro de busca
    search_response = client.get(f"/api/v1/servicos/?buscar={search}", headers=header_with_token)
    
    # Assert: Verificar se a busca retornou o item correto
    assert search_response.status_code == 200
    assert len(search_response.json()) == 1 # Deve retornar uma lista com 1 item
    assert search_response.json()[0]["descricao"] == search

# =========================
# TESTE: Editar Serviço
# =========================
def test_editar_servico(client: TestClient, header_with_token: dict):
    """
    Testa a atualização (PUT /servicos/{id}) de um serviço existente.
    Cria um serviço, depois envia um PUT para alterar seu valor.
    """
    # Arrange 1: Criar o serviço a ser editado
    data_service = {
        "descricao": "Formatação de Notebook",
        "valor": 75049
    }
    create_response = client.post("/api/v1/servicos/", json=data_service, headers=header_with_token)
    assert create_response.status_code == 201
    service_id = create_response.json()["id"]

    # Arrange 2: Definir os dados de atualização
    data_updated_service = {
        "valor": 80049
    }
    
    # Act: Fazer a requisição PUT para o ID específico
    edit_response = client.put(f"/api/v1/servicos/{service_id}", json=data_updated_service, headers=header_with_token)
    
    # Assert: Verificar se a edição foi bem-sucedida e o valor foi alterado
    assert edit_response.status_code == 200
    assert edit_response.json()["valor"] == data_updated_service["valor"]

# =========================
# TESTE: Deletar Serviço
# =========================
def test_deletar_servico(client: TestClient, header_with_token: dict):
    """
    Testa a exclusão (DELETE /servicos/{id}) de um serviço.
    Cria, deleta e depois busca para confirmar que não existe mais.
    """
    # Arrange: Criar o serviço a ser deletado
    data_service = {
        "descricao": "Instalação de Software Específico",
        "valor": 75049
    }
    create_response = client.post("/api/v1/servicos/", json=data_service, headers=header_with_token)
    assert create_response.status_code == 201
    service_id = create_response.json()["id"]

    # Act 1: Fazer a requisição DELETE
    delete_response = client.delete(f"/api/v1/servicos/{service_id}", headers=header_with_token)
    
    # Assert 1: Verificar se o status de exclusão (Sem Conteúdo) está correto
    assert delete_response.status_code == 204

    # Act 2: Tentar buscar o serviço deletado para confirmar a exclusão
    search = data_service["descricao"]
    search_response = client.get(f"/api/v1/servicos/?buscar={search}", headers=header_with_token)
    
    # Assert 2: A busca deve retornar 200, mas com uma lista vazia
    assert search_response.status_code == 200
    assert len(search_response.json()) == 0