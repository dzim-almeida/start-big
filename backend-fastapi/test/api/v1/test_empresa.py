import io
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.models.empresa import Empresa
from app.db.models.usuario import Usuario

FILE_CONTENT_MOCK = b"GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"

# ===================================================================
# FIXTURES E DADOS AUXILIARES
# ===================================================================

def get_empresa_payload_valido(cnpj_suffix="000199", email_prefix="admin"):
    """
    Gera um payload válido combinando dados da Empresa e do Usuário Master.
    Permite sufixos para criar dados únicos nos testes.
    """
    return {
        # --- Dados da Empresa (EmpresaCreate) ---
        "razao_social": f"Empresa Teste {cnpj_suffix} LTDA",
        "nome_fantasia": "Tech Teste",
        "cnpj": f"12345678{cnpj_suffix}", # Deve ter 14 dígitos (Regex)
        "regime_tributario": "Simples Nacional",
        "celular": "11999998888",
        
        "usuario": {
            "nome": "Admin Master",
            "email": f"{email_prefix}@empresa.com",
            "senha": "SenhaForte123!"
        },
        
        # --- Endereço Inicial (Opcional) ---
        "endereco": [
            {
                "logradouro": "Av. Paulista",
                "numero": "1000",
                "bairro": "Bela Vista",
                "cidade": "São Paulo",
                "estado": "SP",
                "cep": "01310-100"
            }
        ]
    }

def create_test_empresa(client: TestClient):
    payload = get_empresa_payload_valido()

    request_url = "/api/v1/empresas/"

    response = client.post(
        request_url,
        json=payload
    )

    assert response.status_code == status.HTTP_201_CREATED
    return response.json()["id"]

def test_criar_empresa_com_usuario_master_sucesso(client: TestClient, db_session: Session):
    """
    Testa o fluxo principal: Criar empresa, criar usuário master e vincular tudo.
    """
    payload = get_empresa_payload_valido()

    # 1. Envia a requisição
    response = client.post("/api/v1/empresas/", json=payload)

    # 2. Verifica sucesso HTTP
    assert response.status_code == 201, f"Erro: {response.text}"
    data = response.json()
    
    # 3. Verifica retorno da API
    assert "id" in data
    assert data["cnpj"] == payload["cnpj"]
    assert data["ativo"] is True

    # 4. Verificação profunda no Banco de Dados (Garante a integridade)
    empresa_db = db_session.query(Empresa).filter(Empresa.cnpj == payload["cnpj"]).first()
    assert empresa_db is not None
    
    # Verifica se o usuário master foi criado e vinculado
    usuario_master = db_session.query(Usuario).filter(Usuario.email == payload["usuario"]["email"]).first()
    assert usuario_master is not None
    assert usuario_master.empresa_id == empresa_db.id
    assert usuario_master.is_master is True # O ponto crucial da sua regra de negócio


def test_adiconar_imagem_a_uma_empresa_existente(client: TestClient, db_session: Session):

    empresa_id = create_test_empresa(client)
    
    file_mock = io.BytesIO(FILE_CONTENT_MOCK)
    file_payload = {
        "file": ("foto_test_principal.gif", file_mock, "image/gif")
    }

    request_url = f"/api/v1/empresas/{empresa_id}/imagem/"

    response = client.post(
        request_url,
        files=file_payload
    )

    assert response.status_code == status.HTTP_201_CREATED


