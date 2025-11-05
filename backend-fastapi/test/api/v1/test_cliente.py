# ---------------------------------------------------------------------------
# ARQUIVO: test_cliente.py
# DESCRIÇÃO: Testes de integração para os endpoints de Cliente (PF, PJ, Busca),
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
# Testes de Criação de Cliente PF
# =========================
def test_criar_cliente_pf_usuario_logado(client: TestClient, header_with_token: dict):
    """
    Testa o "caminho feliz": a criação bem-sucedida de um Cliente PF
    quando o usuário está autenticado.
    """
    # Arrange: Define o payload (corpo da requisição JSON) para o novo cliente PF
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

    # Act: Envia a requisição POST para o endpoint de criação de PF,
    # incluindo o payload e os headers de autenticação obtidos da fixture.
    response = client.post("/api/v1/clientes/cliente_pf", json=data_client, headers=header_with_token)
    
    # Assert: Verifica se a criação foi bem-sucedida
    assert response.status_code == status.HTTP_201_CREATED # Verifica o status HTTP 201 Created
    data = response.json()
    assert data["nome"] == "João Pedro Silva" # Verifica se o nome na resposta está correto
    assert data["email"] == "joao.silva@meu-pdv.com" # Verifica se o email na resposta está correto

def test_criar_cliente_sem_token(client: TestClient):
    """
    Testa o "caminho triste": a falha ao tentar criar um Cliente PF
    sem enviar um token de autenticação (usuário não logado).
    """
    # Arrange: Define o payload (corpo da requisição JSON) para o novo cliente PF
    data_client = {
        "nome": "João Pedro Silva",
        "cpf": "98765432101",
        "rg": "12345678",
        "genero": "MASCULINO",
        "data_nascimento": "1995-12-15",
        "email": "joao.silva@meu-podv.com",
        "contato": "11987654321",
        "observacoes": "Cliente novo, aceita e-mail marketing.",
        "endereco": [
            # ... (lista de endereços) ...
        ]
    }

    # Act: Envia a requisição POST, mas desta vez SEM os headers de autenticação
    response = client.post("/api/v1/clientes/cliente_pf", json=data_client)
    
    # Assert: Verifica se a API protegeu o endpoint corretamente, retornando 401 Unauthorized
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# =========================
# Testes de Criação de Cliente PJ
# =========================
def test_criar_cliente_pj_usuario_logado(client: TestClient, header_with_token: dict):
    """
    Testa o "caminho feliz": a criação bem-sucedida de um Cliente PJ
    quando o usuário está autenticado.
    """
    # Arrange: Define o payload (corpo da requisição JSON) para o novo cliente PJ
    data_client = {
        "razao_social": "Minha Empresa de Tecnologia LTDA",
        "cnpj": "12345678000199",
        "nome_fantasia": "Tech Solutions",
        "ie": "123456789",
        "responsavel": "Ana Gerente",
        "email": "contato@techsolutions.com",
        "contato": "1155554444",
        "observacoes": "Primeiro contato feito na feira de tecnologia.",
        "endereco": [
            {
                "logradouro": "Avenida das Nações",
                "numero": "1001",
                "complemento": "Andar 15, Sala 1502",
                "bairro": "Distrito Empresarial",
                "cidade": "São Paulo",
                "estado": "SP",
                "cep": "04578-000"
            }
        ]
    }

    # Act: Envia a requisição POST para o endpoint de criação de PJ,
    # incluindo o payload e os headers de autenticação.
    response = client.post("/api/v1/clientes/cliente_pj", json=data_client, headers=header_with_token)
    
    # Assert: Verifica se a criação foi bem-sucedida
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["cnpj"] == "12345678000199" # Verifica se o CNPJ na resposta está correto
    assert data["email"] == "contato@techsolutions.com" # Verifica se o email na resposta está correto

# =========================
# Teste de Busca de Cliente
# =========================
def test_buscar_cliente_pf_com_cpf_usuario_logado(client: TestClient, header_with_token: dict):
    """
    Testa a funcionalidade de busca por CPF:
    1. Cria um cliente PF.
    2. Busca por esse cliente usando seu CPF.
    3. Verifica se o cliente correto foi retornado.
    """
    # --- Arrange ---
    # 1. Define o payload para criar o cliente que será buscado
    data_client = {
        "email": "joao.silva@meu-pdv.com",
        "contato": "11987654321",
        "observacoes": "Cliente novo, aceita e-mail marketing.",
        "endereco": [
            {
                "logradouro": "Avenida das Nações",
                "numero": "1001",
                "complemento": "Andar 15, Sala 1502",
                "bairro": "Distrito Empresarial",
                "cidade": "São Paulo",
                "estado": "SP",
                "cep": "04578-000"
            }
        ],
        "nome": "João Pedro Silva",
        "cpf": "98765432101", # O CPF que será usado na busca
        "rg": "12345678",
        "genero": "MASCULINO",
        "data_nascimento": "1995-12-15"
    }

    # 2. Cria o cliente via API (pré-condição para a busca)
    response_create = client.post("/api/v1/clientes/cliente_pf", json=data_client, headers=header_with_token)
    assert response_create.status_code == status.HTTP_201_CREATED # Garante que a criação funcionou

    # --- Act ---
    # 3. Define o termo de busca (o CPF criado)
    client_cpf = "98765432101"

    # 4. Envia a requisição GET para o endpoint de busca,
    #    passando o CPF como parâmetro de query 'buscar'
    response_search = client.get(f"/api/v1/clientes/?buscar={client_cpf}", headers=header_with_token)
    
    # --- Assert ---
    # 5. Verifica se a busca foi bem-sucedida e retornou o cliente correto
    assert response_search.status_code == status.HTTP_200_OK
    data = response_search.json()
    assert len(data) == 1 # A busca deve retornar exatamente um cliente
    assert data[0]["cpf"] == client_cpf # Verifica se o CPF do cliente retornado é o buscado

def test_editar_cliente_com_usuario_logado(client: TestClient, header_with_token: dict):
    data_client = {
        "email": "joao.silva@meu-pdv.com",
        "contato": "11987654321",
        "observacoes": "Cliente novo, aceita e-mail marketing.",
        "endereco": [
           {
                "logradouro": "Avenida das Nações",
                "numero": "1001",
                "complemento": "Andar 15, Sala 1502",
                "bairro": "Distrito Empresarial",
                "cidade": "São Paulo",
                "estado": "SP",
                "cep": "04578-000"
            }
        ],
        "nome": "João Pedro Silva",
        "cpf": "98765432101", # O CPF que será usado na busca
        "rg": "12345678",
        "genero": "MASCULINO",
        "data_nascimento": "1995-12-15"
    }

    response_create = client.post("/api/v1/clientes/cliente_pf", json=data_client, headers=header_with_token)
    assert response_create.status_code == status.HTTP_201_CREATED
    
    client_cpf = "98765432101"
    response_search = client.get(f"/api/v1/clientes/?buscar={client_cpf}", headers=header_with_token)
    assert response_search.status_code == status.HTTP_200_OK
    data_search = response_search.json()

    edited_client = data_search[0]

    edited_client["cpf"] = "65764352122"
    edited_client["endereco"] = [
        {
            "bairro": "Novo Bairro",
            "cep": "13011-000",
            "cidade": "Campinas",
            "estado": "SP",
            "id": 1,
            "logradouro": "Nova Rua",
            "numero": "789"
        },
        {
            "bairro": "Veneza",
            "cep": "63504-360",
            "cidade": "Iguatu",
            "estado": "CE",
            "id": None,
            "logradouro": "Jose Ferreira Lima",
            "numero": "27"
        }
    ]

    response_edit = client.put(f"/api/v1/clientes/{edited_client["id"]}", json=edited_client, headers=header_with_token)
    assert response_edit.status_code == status.HTTP_200_OK
    data_edit = response_edit.json()
    assert data_edit["cpf"] == "65764352122"

def test_deletar_cliente_com_usuario_logado(client: TestClient, header_with_token: dict):
    data_client = {
        "email": "joao.silva@meu-pdv.com",
        "contato": "11987654321",
        "observacoes": "Cliente novo, aceita e-mail marketing.",
        "endereco": [
           {
                "logradouro": "Avenida das Nações",
                "numero": "1001",
                "complemento": "Andar 15, Sala 1502",
                "bairro": "Distrito Empresarial",
                "cidade": "São Paulo",
                "estado": "SP",
                "cep": "04578-000"
            }
        ],
        "nome": "João Pedro Silva",
        "cpf": "98765432101", # O CPF que será usado na busca
        "rg": "12345678",
        "genero": "MASCULINO",
        "data_nascimento": "1995-12-15"
    }

    response_create = client.post("/api/v1/clientes/cliente_pf", json=data_client, headers=header_with_token)
    assert response_create.status_code == status.HTTP_201_CREATED

    data_create = response_create.json()

    response_delete = client.delete(f"/api/v1/clientes/{data_create["id"]}", headers=header_with_token)
    assert response_delete.status_code == status.HTTP_204_NO_CONTENT

    client_cpf = "98765432101"
    response_search = client.get(f"/api/v1/clientes/?buscar={client_cpf}", headers=header_with_token)
    assert response_search.status_code == status.HTTP_200_OK
    data_search = response_search.json()

    assert len(data_search) == 0