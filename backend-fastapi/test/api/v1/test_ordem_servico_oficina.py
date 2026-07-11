# ---------------------------------------------------------------------------
# ARQUIVO: test_ordem_servico_oficina.py
# DESCRICAO: Testes de integracao do segmento de oficina mecanica na OS.
#            Cobre a validacao de placa (gated por segmento) e um teste
#            GUARDIAO garantindo que o segmento de informatica/assistencia
#            tecnica NAO sofre a validacao de placa (permanece intacto).
# ---------------------------------------------------------------------------

from starlette import status

TEST_USER_EMAIL = "teste.funcionario@example.com"
TEST_USER_PASSWORD = "senhaSegura456"


# =========================
# Helpers de setup
# =========================

def _autenticar_e_criar_empresa(client, segmento: str) -> dict:
    """Cria o usuario master, faz login e cria a empresa com o segmento dado.
    Retorna o header Authorization."""
    client.post("/api/v1/usuarios/", json={
        "nome": "Admin Master",
        "email": TEST_USER_EMAIL,
        "senha": TEST_USER_PASSWORD,
    })

    login = client.post("/api/v1/auth/login", data={
        "username": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
    })
    assert login.status_code == 200, login.text
    header = {"Authorization": f"Bearer {login.json()['access_token']}"}

    empresa = {
        "razao_social": "Empresa Teste 000199 LTDA",
        "nome_fantasia": "Teste",
        "is_cnpj": True,
        "documento": "12345678000199",
        "regime_tributario": "Simples Nacional",
        "celular": "11999998888",
        "segmento": segmento,
        "endereco": [{
            "logradouro": "Av. Paulista", "numero": "1000", "bairro": "Bela Vista",
            "cidade": "São Paulo", "estado": "SP", "cep": "01310-100",
        }],
    }
    r = client.post("/api/v1/empresas/", json=empresa, headers=header)
    assert r.status_code == 201, r.text
    return header


def _criar_cliente(client, header: dict) -> int:
    payload = {
        "nome": "João Pedro Silva",
        "cpf": "98765432101",
        "tipo": "PF",
        "celular": "11987654321",
        "endereco": [{
            "logradouro": "Rua das Flores", "numero": "100", "bairro": "Centro",
            "cidade": "Campinas", "estado": "SP", "cep": "13010-000",
        }],
    }
    r = client.post("/api/v1/clientes/cliente_pf", json=payload, headers=header)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _os_payload(cliente_id: int, numero_serie: str, dados_adicionais: dict | None = None,
                itens: list | None = None, os_dados_adicionais: dict | None = None) -> dict:
    return {
        "cliente_id": cliente_id,
        "prioridade": "NORMAL",
        "defeito_relatado": "Barulho ao frear",
        # dados_adicionais no nível da OS (check-in: km_entrada, combustível, vistoria)
        "dados_adicionais": os_dados_adicionais or {},
        "objeto": {
            "marca": "Fiat",
            "modelo": "Uno",
            "numero_serie": numero_serie,
            # dados_adicionais do objeto/veículo (placa, chassi, ano)
            "dados_adicionais": dados_adicionais or {},
        },
        "itens": itens if itens is not None else [],
    }


def _item(nome: str, valor_unitario: int, **extra) -> dict:
    base = {
        "tipo": "SERVICO",
        "nome": nome,
        "unidade_medida": "UN",
        "quantidade": 1,
        "valor_unitario": valor_unitario,
    }
    base.update(extra)
    return base


# =========================
# OFICINA MECANICA
# =========================

def test_criar_os_oficina_com_placa_valida(client, db_session):
    """Oficina: placa valida (Mercosul) cria a OS e persiste dados_adicionais."""
    header = _autenticar_e_criar_empresa(client, "oficina_mecanica")
    cliente_id = _criar_cliente(client, header)

    dados = {"km_entrada": 85000, "combustivel_nivel": "1/2", "pneus_estado": "BOM"}
    r = client.post(
        "/api/v1/ordens-servico/",
        json=_os_payload(cliente_id, "ABC1D23", dados),
        headers=header,
    )
    assert r.status_code == status.HTTP_201_CREATED, r.text
    body = r.json()
    assert body["objeto"]["numero_serie"] == "ABC1D23"
    assert body["objeto"]["dados_adicionais"]["km_entrada"] == 85000
    assert body["objeto"]["dados_adicionais"]["pneus_estado"] == "BOM"


def test_criar_os_oficina_com_placa_invalida_bloqueia(client, db_session):
    """Oficina: numero_serie que nao e placa valida deve retornar 422."""
    header = _autenticar_e_criar_empresa(client, "oficina_mecanica")
    cliente_id = _criar_cliente(client, header)

    r = client.post(
        "/api/v1/ordens-servico/",
        json=_os_payload(cliente_id, "SEM-PLACA-123"),
        headers=header,
    )
    assert r.status_code == 422, r.text


def test_definicao_campos_oficina(client, db_session):
    """Contrato de campos: oficina retorna definicao dedicada com rotulo Veiculo."""
    header = _autenticar_e_criar_empresa(client, "oficina_mecanica")
    r = client.get("/api/v1/ordens-servico/definicao-campos", headers=header)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["segmento"] == "oficina_mecanica"
    assert body["tem_definicao"] is True
    assert body["definicao"]["rotulo_objeto_singular"] == "Veículo"
    assert len(body["definicao"]["vistoria"]) == 3


# =========================
# GUARDIAO — INFORMATICA INTACTA
# =========================

def test_os_informatica_nao_sofre_validacao_de_placa(client, db_session):
    """GUARDIAO: empresa de informatica cria OS com qualquer numero_serie
    (IMEI/serial), sem a validacao de placa exclusiva da oficina."""
    header = _autenticar_e_criar_empresa(client, "assistencia_tecnica")
    cliente_id = _criar_cliente(client, header)

    dados = {"imei": "359999000000001", "senha_aparelho": "1234"}
    r = client.post(
        "/api/v1/ordens-servico/",
        json=_os_payload(cliente_id, "SERIAL-XYZ-999", dados),
        headers=header,
    )
    assert r.status_code == status.HTTP_201_CREATED, r.text
    assert r.json()["objeto"]["numero_serie"] == "SERIAL-XYZ-999"


def test_definicao_campos_segmento_generico_sem_definicao(client, db_session):
    """Segmento generico (mercado) nao tem definicao dedicada."""
    header = _autenticar_e_criar_empresa(client, "mercado")
    r = client.get("/api/v1/ordens-servico/definicao-campos", headers=header)
    assert r.status_code == 200, r.text
    assert r.json()["tem_definicao"] is False


# =========================
# ONDA 2 — aprovacao / garantia por item / historico de KM
# =========================

def test_item_reprovado_nao_entra_no_total(client, db_session):
    """Item REPROVADO nao entra no valor_total; APROVADO conta."""
    header = _autenticar_e_criar_empresa(client, "oficina_mecanica")
    cliente_id = _criar_cliente(client, header)
    itens = [
        _item("Troca de pastilha", 10000, status_aprovacao="APROVADO"),
        _item("Troca de disco", 5000, status_aprovacao="REPROVADO"),
    ]
    r = client.post("/api/v1/ordens-servico/", json=_os_payload(cliente_id, "ABC1D23", itens=itens), headers=header)
    assert r.status_code == status.HTTP_201_CREATED, r.text
    body = r.json()
    assert body["valor_bruto"] == 10000, "só o item APROVADO deve contar"
    assert body["valor_total"] == 10000


def test_garantia_por_item_persistida(client, db_session):
    """Garantia (dias e KM) por item é persistida e retornada."""
    header = _autenticar_e_criar_empresa(client, "oficina_mecanica")
    cliente_id = _criar_cliente(client, header)
    itens = [_item("Troca de correia", 20000, garantia_dias=90, garantia_km=10000)]
    r = client.post("/api/v1/ordens-servico/", json=_os_payload(cliente_id, "ABC1D23", itens=itens), headers=header)
    assert r.status_code == status.HTTP_201_CREATED, r.text
    item = r.json()["itens"][0]
    assert item["garantia_dias"] == 90
    assert item["garantia_km"] == 10000
    assert item["status_aprovacao"] == "APROVADO"


def test_historico_km_do_veiculo(client, db_session):
    """Histórico de KM lê km_entrada das OS do veículo, da mais antiga p/ recente."""
    header = _autenticar_e_criar_empresa(client, "oficina_mecanica")
    cliente_id = _criar_cliente(client, header)

    # 1a OS com KM 80000 (check-in é nível da OS)
    r1 = client.post("/api/v1/ordens-servico/",
                     json=_os_payload(cliente_id, "ABC1D23", os_dados_adicionais={"km_entrada": 80000}),
                     headers=header)
    assert r1.status_code == 201, r1.text
    objeto_id = r1.json()["objeto"]["id"]

    r = client.get(f"/api/v1/ordens-servico/objeto/{objeto_id}/historico-km", headers=header)
    assert r.status_code == 200, r.text
    hist = r.json()
    assert len(hist) == 1
    assert hist[0]["km_entrada"] == 80000


def test_guardiao_informatica_itens_contam_normalmente(client, db_session):
    """GUARDIAO: sem status enviado, itens default APROVADO contam no total
    (comportamento da informática permanece igual)."""
    header = _autenticar_e_criar_empresa(client, "assistencia_tecnica")
    cliente_id = _criar_cliente(client, header)
    itens = [_item("Formatação", 8000), _item("Limpeza", 2000)]  # sem status_aprovacao
    r = client.post("/api/v1/ordens-servico/", json=_os_payload(cliente_id, "SERIAL-1", itens=itens), headers=header)
    assert r.status_code == status.HTTP_201_CREATED, r.text
    body = r.json()
    assert body["valor_bruto"] == 10000, "todos os itens contam (default APROVADO)"
    assert body["itens"][0]["status_aprovacao"] == "APROVADO"
