# ---------------------------------------------------------------------------
# ARQUIVO: test_produtos.py
# DESCRIÇÃO: Testes de integração para os endpoints CRUD de Produtos.
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
# Testes de Criação de Produto
# =========================
def test_criar_produto_usuario_logado(client: TestClient, header_with_token: dict):
    """
    Testa o "caminho feliz": a criação bem-sucedida de um Produto
    quando o usuário está autenticado.
    """
    # Arrange: Define o payload (corpo da requisição JSON) para o novo produto
    data_product = {
        "nome": "Café Gourmet Moído 500g",
        "codigo_produto": "123456",
        "unidade_medida": "UN",
        "observacao": "Armazenar em local seco.",
        "nota_fiscal": "1004.22.99",
        "categoria": "Bebidas",
        "marca": "Fazenda Boa Vista",
        "id_fornecedor": None, # Campo opcional adicionado
        # Objeto de estoque aninhado
        "estoque": {
            "valor_varejo": 2999,
            "quantidade": 100,
            "valor_entrada": 1500,
            "valor_atacado": 2500,
            "quantidade_minima": 20
        }
    }
    # Act: Envia a requisição POST para o endpoint de criação de produtos
    response = client.post("/api/v1/produtos/", json=data_product, headers=header_with_token)
    
    # Assert: Verifica se a criação foi bem-sucedida
    assert response.status_code == 201
    assert "nome" in response.json()

def test_criar_produto_sem_token(client: TestClient):
    """
    Testa o "caminho triste": a falha ao tentar criar um Produto
    sem enviar um token de autenticação (usuário não logado).
    """
    # Arrange: Define o payload
    data_product = {
        "nome": "Café Gourmet Moído 500g",
        "codigo_produto": "123456",
        "unidade_medida": "UN",
        "observacao": "Armazenar em local seco.",
        "nota_fiscal": "1004.22.99",
        "categoria": "Bebidas",
        "marca": "Fazenda Boa Vista",
        "id_fornecedor": None, # Campo opcional adicionado
        "estoque": {
            "valor_varejo": 2999,
            "quantidade": 100,
            "valor_entrada": 1500,
            "valor_atacado": 2500,
            "quantidade_minima": 20
        }
    }
    # Act: Envia a requisição POST, mas SEM os headers de autenticação
    response = client.post("/api/v1/produtos/", json=data_product)
    
    # Assert: Verifica se a API protegeu o endpoint, retornando 401 Unauthorized
    assert response.status_code == 401

def test_criar_produto_com_codigo_existente(client: TestClient, header_with_token: dict):
    """
    Testa a regra de negócio: não deve ser possível criar dois
    produtos com o mesmo 'codigo_produto'.
    """
    # Arrange: Define o payload
    data_product = {
        "nome": "Café Gourmet Moído 500g",
        "codigo_produto": "123456",
        "unidade_medida": "UN",
        "observacao": "Armazenar em local seco.",
        "nota_fiscal": "1004.22.99",
        "categoria": "Bebidas",
        "marca": "Fazenda Boa Vista",
        "id_fornecedor": None, # Campo opcional adicionado
        "estoque": {
            "valor_varejo": 2999,
            "quantidade": 100,
            "valor_entrada": 1500,
            "valor_atacado": 2500,
            "quantidade_minima": 20
        }
    }
    # Act 1: Cria o primeiro produto
    first_response = client.post("/api/v1/produtos/", json=data_product, headers=header_with_token)
    # Assert 1: Garante que a primeira criação funcionou
    assert first_response.status_code == 201

    # Act 2: Tenta criar o MESMO produto novamente
    second_response = client.post("/api/v1/produtos/", json=data_product, headers=header_with_token)
    # Assert 2: Verifica se a API retornou 409 Conflict (código duplicado)
    assert second_response.status_code == 409

# =========================
# Teste de Busca de Produto
# =========================
def test_buscar_produto_por_nome_ou_codigo(client: TestClient, header_with_token: dict):
    """
    Testa a funcionalidade de busca (GET /):
    1. Cria um produto.
    2. Busca por esse produto pelo nome.
    3. Busca por esse produto pelo código.
    4. Verifica se os dados retornados estão corretos.
    """
    # --- Arrange ---
    # 1. Define o payload para criar o produto que será buscado
    data_product = {
        "nome": "Café Gourmet Moído 500g",
        "codigo_produto": "123456",
        "unidade_medida": "UN",
        "observacao": "Armazenar em local seco.",
        "nota_fiscal": "1004.22.99",
        "categoria": "Bebidas",
        "marca": "Fazenda Boa Vista",
        "id_fornecedor": None, # Campo opcional adicionado
        "estoque": {
            "valor_varejo": 2999,
            "quantidade": 100,
            "valor_entrada": 1500,
            "valor_atacado": 2500,
            "quantidade_minima": 20
        }
    }
    # 2. Cria o produto via API (pré-condição para a busca)
    create_response = client.post("/api/v1/produtos/", json=data_product, headers=header_with_token)
    assert create_response.status_code == 201 # Garante que a criação funcionou

    # 3. Define os termos de busca
    search_name = "Café Gourmet Moído 500g"
    search_code = "123456"

    # --- Act ---
    # 4. Envia as requisições GET para o endpoint de busca
    get_by_name_response = client.get(f"/api/v1/produtos/?buscar={search_name}", headers=header_with_token)
    assert get_by_name_response.status_code == 200
    
    get_by_code_response = client.get(f"/api/v1/produtos/?buscar={search_code}", headers=header_with_token)
    assert get_by_code_response.status_code == 200

    # --- Assert ---
    # 5. Verifica os resultados da busca
    by_name_data = get_by_name_response.json()
    by_code_data = get_by_code_response.json()

    assert by_name_data[0]["nome"] == search_name
    assert by_code_data[0]["codigo_produto"] == search_code

def test_buscar_produto_por_nome_ou_codigo_inexistente(client: TestClient, header_with_token: dict):
    """
    Testa a busca por um termo que não corresponde a nenhum produto.
    Espera-se um status 200 OK com uma lista vazia.
    """
    # --- Arrange ---
    # 1. Cria um produto de "controle" para garantir que o banco não está vazio
    data_product = {
        "nome": "Café Gourmet Moído 500g",
        "codigo_produto": "123456",
        "unidade_medida": "UN",
        "observacao": "Armazenar em local seco.",
        "nota_fiscal": "1004.22.99",
        "categoria": "Bebidas",
        "marca": "Fazenda Boa Vista",
        "id_fornecedor": None, # Campo opcional adicionado
        "estoque": {
            "valor_varejo": 2999,
            "quantidade": 100,
            "valor_entrada": 1500,
            "valor_atacado": 2500,
            "quantidade_minima": 20
        }
    }
    create_response = client.post("/api/v1/produtos/", json=data_product, headers=header_with_token)
    assert create_response.status_code == 201

    # 2. Define termos de busca que não existem
    search_name = "Macarrao"
    search_code = "432424"

    # --- Act ---
    # 3. Envia as requisições GET para o endpoint de busca
    get_by_name_response = client.get(f"/api/v1/produtos/?buscar={search_name}", headers=header_with_token)
    assert get_by_name_response.status_code == 200 # A busca deve ser bem-sucedida
    
    get_by_code_response = client.get(f"/api/v1/produtos/?buscar={search_code}", headers=header_with_token)
    assert get_by_code_response.status_code == 200 # A busca deve ser bem-sucedida

    # --- Assert ---
    # 4. Verifica se ambas as buscas retornaram uma lista vazia
    by_name_data = get_by_name_response.json()
    assert len(by_name_data) == 0
    by_code_data = get_by_code_response.json()
    assert len(by_code_data) == 0

# =========================
# Teste de Edição de Produto
# =========================
def test_editar_produto(client: TestClient, header_with_token: dict):
    """
    Testa a funcionalidade de edição (PUT) de um produto existente:
    1. Cria um produto.
    2. Busca por esse produto.
    3. Modifica dados (nome, categoria).
    4. Envia uma requisição PUT para atualizar o produto.
    5. Verifica se a atualização foi bem-sucedida (status 200) e se os dados foram alterados.
    """
    # --- Arrange 1: Criar o Produto ---
    data_product = {
        "nome": "Café Gourmet Moído 500g",
        "codigo_produto": "123456",
        "unidade_medida": "UN",
        "observacao": "Armazenar em local seco.",
        "nota_fiscal": "1004.22.99",
        "categoria": "Bebidas",
        "marca": "Fazenda Boa Vista",
        "id_fornecedor": None, # Campo opcional adicionado
        "estoque": {
            "valor_varejo": 2999,
            "quantidade": 100,
            "valor_entrada": 1500,
            "valor_atacado": 2500,
            "quantidade_minima": 20
        }
    }
    create_response = client.post("/api/v1/produtos/", json=data_product, headers=header_with_token)
    assert create_response.status_code == 201

    # --- Arrange 2: Buscar o Cliente Criado para obter o ID e dados completos ---
    search_code = "123456"
    get_by_code_response = client.get(f"/api/v1/produtos/?buscar={search_code}", headers=header_with_token)
    assert get_by_code_response.status_code == 200

    by_name_data = get_by_code_response.json()
    
    # Extrai os dados do produto encontrado (que bate com o schema 'ProdutoRead')
    edit_product = by_name_data[0]
    
    # --- Arrange 3: Modificar os Dados ---
    # Altera os campos no dicionário que será enviado como payload
    edit_product["nome"] = "Arroz Agromil 1kg"
    edit_product["categoria"] = "Alimento"

    # --- Act: Enviar a Requisição de Edição (PUT) ---
    # Envia a requisição PUT para a URL correta (com ID) e com o payload modificado
    edit_response = client.put(f"/api/v1/produtos/{edit_product['id']}", json=edit_product, headers=header_with_token)
    
    # --- Assert: Verificar o Resultado da Edição ---
    assert edit_response.status_code == 200 # Verifica se a atualização retornou 200 OK
    edited_product_data = edit_response.json()

    assert edited_product_data["nome"] == edit_product["nome"] # Verifica o novo nome
    assert edited_product_data["categoria"] == edit_product["categoria"] # Verifica a nova categoria

# =========================
# Teste de Deleção de Produto
# =========================
def test_excluir_produto(client: TestClient, header_with_token: dict):
    """
    Testa a funcionalidade de deleção (DELETE) de um produto existente:
    1. Cria um produto.
    2. Envia uma requisição DELETE para excluir o produto pelo ID.
    3. Verifica se a deleção foi bem-sucedida (status 200).
    4. Tenta buscar o produto deletado e verifica se a busca retorna uma lista vazia.
    """
    # --- Arrange 1: Criar o Produto ---
    data_product = {
        "nome": "Café Gourmet Moído 500g",
        "codigo_produto": "123456",
        "unidade_medida": "UN",
        "observacao": "Armazenar em local seco.",
        "nota_fiscal": "1004.22.99",
        "categoria": "Bebidas",
        "marca": "Fazenda Boa Vista",
        "id_fornecedor": None, # Campo opcional adicionado
        "estoque": {
            "valor_varejo": 2999,
            "quantidade": 100,
            "valor_entrada": 1500,
            "valor_atacado": 2500,
            "quantidade_minima": 20
        }
    }
    create_response = client.post("/api/v1/produtos/", json=data_product, headers=header_with_token)
    assert create_response.status_code == 201

    # --- Act: Enviar a Requisição de Deleção (DELETE) ---
    # (Nota: O ID '1' está hardcoded, o que pode falhar se o DB não for resetado.
    #  Seria mais robusto usar 'create_response.json()["id"]')
    exclude_response = client.delete(f"/api/v1/produtos/1", headers=header_with_token)
    
    # --- Assert 1: Verificar o Resultado da Deleção ---
    assert exclude_response.status_code == 204 # Verifica se a deleção retornou 200 OK
    
    # --- Assert 2: Verificar se o Cliente Realmente Foi Deletado ---
    # Tenta buscar o produto pelo código que acabou de ser deletado
    search_code = "123456"
    get_by_code_response = client.get(f"/api/v1/produtos/?buscar={search_code}", headers=header_with_token)
    # A busca deve retornar 200 OK com uma lista vazia
    assert len(get_by_code_response.json()) == 0
    