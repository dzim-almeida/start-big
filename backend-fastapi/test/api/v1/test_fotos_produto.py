# ---------------------------------------------------------------------------
# ARQUIVO: test_fotos_produto.py
# DESCRIÇÃO: Testes de integração para os endpoints de upload e deleção de
#            fotos de produto.
# ---------------------------------------------------------------------------

from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette import status # Boa prática para usar status codes nominais
import io
import os # Necessário para mockar operações de I/O em testes mais avançados

from app.db.models.usuario import Usuario as UsuarioModel
from app.db.models.produto_fotos import ProdutoFoto as ProdutoFotoModel # Importa o modelo
from app.core.security import hash_password
from app.core.enum import UserType

# --- Constantes de Teste ---
TEST_USER_EMAIL = "teste.usuario@example.com"
TEST_USER_PASSWORD = "senhaSegura123"

# Mock de conteúdo de arquivo (GIF minimalista válido)
FILE_CONTENT_MOCK = b"GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"

# =========================
# Fixture de Autenticação (Setup Básico)
# =========================
@pytest.fixture(scope="function")
def header_with_token(client: TestClient, db_session: Session) -> dict:
    """
    Fixture reutilizável que cria um usuário de teste, realiza o login
    via API e retorna um dicionário de headers com o token Bearer.
    
    'scope="function"' garante que o estado é limpo para cada teste.
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
    db_session.refresh(user) # Garante que o objeto está atualizado (opcional)

    # Arrange 2: Preparar dados para fazer login via API
    login_data = {"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    
    # Act: Realizar o login para obter um token de acesso
    response = client.post("/api/v1/auth/login", data=login_data)
    
    # Assert (pré-condição): Garante que o login da fixture funcionou
    assert response.status_code == status.HTTP_200_OK
    
    # Arrange 3: Extrair o token e montar o header de autorização
    token = response.json()["access_token"]
    header_with_token = {"Authorization": f"Bearer {token}"}
    
    # Retorna os headers para serem usados pelos testes
    return header_with_token

# =========================
# Função Auxiliar: Criar Produto
# =========================
def create_test_product(client: TestClient, header: dict) -> int:
    """Função auxiliar para criar um produto, garantindo o ID necessário para o upload."""
    data_product = {
        "nome": "Produto Teste Foto",
        "codigo_produto": "PHOTO-123",
        "unidade_medida": "UN",
        "observacao": "Para testes de upload.",
        "nota_fiscal": "1004.22.99",
        "categoria": "Testes",
        "marca": "Pytest",
        "id_fornecedor": None,
        "estoque": {
            "valor_varejo": 1000,
            "quantidade": 10,
            "valor_entrada": 500,
            "valor_atacado": 800,
            "quantidade_minima": 5
        }
    }
    response = client.post("/api/v1/produtos/", json=data_product, headers=header)
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()["id"]

# =========================================================
# Testes de Upload (POST)
# =========================================================

def test_adicionar_foto_ao_produto_sucesso(client: TestClient, header_with_token: dict):
    """Testa o cenário de sucesso ao fazer upload de uma foto."""
    # Arrange: Cria um produto pai e prepara o mock do arquivo
    product_id = create_test_product(client, header_with_token)

    # Prepara o mock do arquivo binário e o payload multipart
    file_mock = io.BytesIO(FILE_CONTENT_MOCK)
    file_payload = {
        "file": ("foto_teste_principal.gif", file_mock, "image/gif")
    }

    # Prepara o campo de texto 'principal'
    data_payload = {
        "principal": "True" # Deve ser enviado como string no multipart/form-data
    }

    upload_url = f"/api/v1/produtos/{product_id}/fotos"

    # Act: Envia a requisição POST (multipart/form-data)
    create_image_response = client.post(
        upload_url,
        headers=header_with_token,
        files=file_payload,
        data=data_payload
    )

    # Assert 1: Verifica o Status Code
    assert create_image_response.status_code == status.HTTP_201_CREATED
    image_data = create_image_response.json()

    # Assert 2: Verifica os dados de retorno
    assert "id" in image_data
    assert image_data["produto_id"] == product_id
    assert image_data["principal"] is True # Pydantic deve converter 'True' (string) para True (bool)
    assert image_data["nome_arquivo"] == "foto_teste_principal.gif"
    assert "url" in image_data # Deve conter o caminho (URL) onde o arquivo foi salvo

def test_adicionar_foto_produto_nao_existente(client: TestClient, header_with_token: dict):
    """Testa a falha ao tentar anexar uma foto a um produto que não existe."""
    # Arrange: ID de produto inexistente
    non_existent_product_id = 999999

    file_mock = io.BytesIO(FILE_CONTENT_MOCK)
    file_payload = {
        "file": ("foto_invalida.gif", file_mock, "image/gif")
    }
    data_payload = {"principal": "False"}

    upload_url = f"/api/v1/produtos/{non_existent_product_id}/fotos"

    # Act: Tenta fazer o upload
    response = client.post(
        upload_url,
        headers=header_with_token,
        files=file_payload,
        data=data_payload
    )

    # Assert: Espera 404 Not Found (validado no Service Layer)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Produto não encontrado" in response.json()["detail"]

# =========================================================
# Testes de Deleção (DELETE)
# =========================================================

def test_deletar_foto_produto_sucesso(client: TestClient, header_with_token: dict, db_session: Session):
    """Testa o cenário de sucesso ao deletar uma foto e verificar sua remoção do BD."""
    # Arrange 1: Cria produto e faz o upload da foto (Setup)
    product_id = create_test_product(client, header_with_token)
    
    file_mock = io.BytesIO(FILE_CONTENT_MOCK)
    file_payload = {"file": ("foto_deletar.gif", file_mock, "image/gif")}
    data_payload = {"principal": "False"}
    upload_url = f"/api/v1/produtos/{product_id}/fotos"

    create_image_response = client.post(
        upload_url, headers=header_with_token, files=file_payload, data=data_payload
    )
    
    assert create_image_response.status_code == status.HTTP_201_CREATED
    image_data = create_image_response.json()
    image_id = image_data["id"]
    delete_url = f"/api/v1/produtos/fotos/{image_id}"
    
    # Act: Deleta a foto
    delete_image_response = client.delete(
        delete_url,
        headers=header_with_token
    )

    # Assert 1: Verifica o Status Code (204 No Content)
    assert delete_image_response.status_code == status.HTTP_204_NO_CONTENT
    
    # Assert 2 (Teste de Regressão): Verifica se a foto foi realmente removida do BD
    # Tenta buscar a foto diretamente no banco de dados (fora da API)
    deleted_image_in_db = db_session.query(ProdutoFotoModel).filter(
        ProdutoFotoModel.id == image_id
    ).first()
    
    assert deleted_image_in_db is None

def test_deletar_foto_produto_nao_existente(client: TestClient, header_with_token: dict):
    """Testa a falha ao tentar deletar uma foto com um ID inexistente."""
    # Arrange: ID de imagem inexistente
    non_existent_image_id = 888888

    delete_url = f"/api/v1/produtos/fotos/{non_existent_image_id}"

    # Act: Tenta deletar
    delete_image_response = client.delete(
        delete_url,
        headers=header_with_token
    )

    # Assert: Espera 404 Not Found (validado no Service Layer)
    assert delete_image_response.status_code == status.HTTP_404_NOT_FOUND
    assert "Imagem não encontrada" in delete_image_response.json()["detail"]