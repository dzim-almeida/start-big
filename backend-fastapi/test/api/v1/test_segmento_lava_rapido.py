# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_segmento_lava_rapido.py
# DESCRICAO: Fundacao do segmento lava-rapido pela API (docs/lava-rapido/
#            SPEC-01A, secao 11).
#
# O que se prova aqui, de ponta a ponta:
#   - o segmento e aceito no cadastro da empresa;
#   - a placa identifica o veiculo e reaproveita o cadastro na proxima visita;
#   - sem placa (barco, jet ski), o sistema gera VEI-...;
#   - placa estrangeira tambem vale como chave (o segmento nao tem regex);
#   - o backend recusa os status que o segmento nao usa;
#   - e a oficina, que divide o mesmo codigo, continua igual (PR1).
# ---------------------------------------------------------------------------

from starlette import status

TEST_USER_EMAIL = "teste.funcionario@example.com"
TEST_USER_PASSWORD = "senhaSegura456"


# =========================
# Helpers de setup
# =========================

def _autenticar_e_criar_empresa(client, segmento: str) -> dict:
    """Cria o usuario master, faz login e cadastra a empresa do segmento."""
    client.post("/api/v1/usuarios/", json={
        "nome": "Admin Master",
        "email": TEST_USER_EMAIL,
        "senha": TEST_USER_PASSWORD,
    })
    login = client.post("/api/v1/auth/login", data={
        "username": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "hwid": "test-terminal-hwid",
    })
    assert login.status_code == 200, login.text
    header = {"Authorization": f"Bearer {login.json()['access_token']}"}

    r = client.post("/api/v1/empresas/", json={
        "razao_social": "Lava Rapido Teste LTDA",
        "nome_fantasia": "Lava Teste",
        "is_cnpj": True,
        "documento": "12345678000199",
        "regime_tributario": "Simples Nacional",
        "celular": "11999998888",
        "segmento": segmento,
        "endereco": [{
            "logradouro": "Av. Paulista", "numero": "1000", "bairro": "Bela Vista",
            "cidade": "São Paulo", "estado": "SP", "cep": "01310-100",
        }],
    }, headers=header)
    assert r.status_code == 201, r.text
    return header


def _criar_cliente(client, header: dict) -> int:
    r = client.post("/api/v1/clientes/cliente_pf", json={
        "nome": "Joana Motorista",
        "cpf": "52998224725",
        "tipo": "PF",
        "celular": "11987654321",
        "endereco": [{
            "logradouro": "Rua das Flores", "numero": "100", "bairro": "Centro",
            "cidade": "Campinas", "estado": "SP", "cep": "13010-000",
        }],
    }, headers=header)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _post_os(client, header: dict, cliente_id: int, objeto: dict, tipo: str = "carro"):
    """Abre uma OS de lavagem como o formulario do segmento vai abrir."""
    return client.post("/api/v1/ordens-servico/", json={
        "cliente_id": cliente_id,
        "prioridade": "NORMAL",
        "defeito_relatado": "Lavagem completa",
        "dados_adicionais": {"tipo_trabalho": tipo, "pertences": "óculos no porta-luvas"},
        "objeto": objeto,
        "itens": [],
    }, headers=header)


def _objeto(corpo: dict) -> dict:
    return corpo.get("objeto") or corpo.get("equipamento")


CARRO = {
    "numero_serie": "ABC1D23",
    "marca": "Volkswagen",
    "modelo": "Gol",
    "cor": "Prata",
    "dados_adicionais": {"porte": "Hatch"},
}


# =========================
# Casos (Spec 01A, secao 11 -- API)
# =========================

def test_empresa_aceita_o_segmento_lava_rapido(client, db_session):
    """Caso 1: sem 'lava_rapido' em SEGMENTOS_VALIDOS o cadastro dava 422."""
    _autenticar_e_criar_empresa(client, "lava_rapido")


def test_definicao_do_segmento_chega_ao_frontend(client, db_session):
    """O contrato que a Spec 01B vai renderizar."""
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    r = client.get("/api/v1/ordens-servico/definicao-campos", headers=header)
    assert r.status_code == 200, r.text
    definicao = r.json()["definicao"]
    assert [t["id"] for t in definicao["tipos"]] == ["carro", "moto", "pesado", "outros"]
    assert definicao["identificador"]["gerado_se_vazio"] is True
    assert "AGUARDANDO_PECAS" not in definicao["status_usados"]
    # Spec 01B, D9: o rotulo do "usar anterior" vem inteiro, no masculino.
    assert definicao["rotulo_objeto_anterior"] == "Veículo já cadastrado"


def test_os_de_carro_grava_a_placa_e_o_porte(client, db_session):
    """Caso 2."""
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    cliente_id = _criar_cliente(client, header)

    r = _post_os(client, header, cliente_id, CARRO)

    assert r.status_code == status.HTTP_201_CREATED, r.text
    objeto = _objeto(r.json())
    assert objeto["numero_serie"] == "ABC1D23"
    assert objeto["dados_adicionais"]["porte"] == "Hatch"


def test_segunda_visita_reaproveita_o_veiculo(client, db_session):
    """Caso 3: o carro e UM cadastro que acumula historico entre as lavagens."""
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    cliente_id = _criar_cliente(client, header)

    primeira = _objeto(_post_os(client, header, cliente_id, CARRO).json())
    segunda = _objeto(_post_os(client, header, cliente_id, CARRO).json())

    assert segunda["id"] == primeira["id"]


def test_outros_sem_placa_recebe_codigo_gerado(client, db_session):
    """Caso 4: barco nao tem placa -- o sistema gera VEI- do numero da OS."""
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    cliente_id = _criar_cliente(client, header)

    r = _post_os(client, header, cliente_id, {
        "marca": "Yamaha",
        "modelo": "Jet ski VX",
        "dados_adicionais": {"porte": "Médio"},
    }, tipo="outros")

    assert r.status_code == status.HTTP_201_CREATED, r.text
    corpo = r.json()
    assert _objeto(corpo)["numero_serie"] == f"VEI-{corpo['numero_os'].removeprefix('OS-')}"


def test_marca_e_modelo_continuam_obrigatorios(client, db_session):
    """D7: gerar a placa nao dispensa marca e modelo, como na oficina."""
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    cliente_id = _criar_cliente(client, header)

    r = _post_os(client, header, cliente_id, {"dados_adicionais": {"porte": "Médio"}}, tipo="outros")

    assert r.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, r.text
    assert "Marca" in r.json()["detail"] and "Modelo" in r.json()["detail"]


def test_placa_estrangeira_vale_como_chave(client, db_session):
    """Caso 5: caminhao do Mercosul. Com o regex da oficina ela nao seria
    chave, e cada visita criaria um veiculo novo (D4)."""
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    cliente_id = _criar_cliente(client, header)
    caminhao = {
        "numero_serie": "AB123CD",
        "marca": "Scania",
        "modelo": "R450",
        "dados_adicionais": {"porte": "Caminhão 3 eixos", "carroceria": "Baú"},
    }

    primeira = _objeto(_post_os(client, header, cliente_id, caminhao, tipo="pesado").json())
    segunda = _objeto(_post_os(client, header, cliente_id, caminhao, tipo="pesado").json())

    assert segunda["id"] == primeira["id"]


def test_status_que_o_segmento_nao_usa_e_recusado(client, db_session):
    """Caso 6: tela e backend dizem a mesma coisa (D9)."""
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    cliente_id = _criar_cliente(client, header)
    numero_os = _post_os(client, header, cliente_id, CARRO).json()["numero_os"]

    recusado = client.put(f"/api/v1/ordens-servico/{numero_os}",
                          json={"status": "AGUARDANDO_PECAS"}, headers=header)
    assert recusado.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, recusado.text

    em_andamento = client.put(f"/api/v1/ordens-servico/{numero_os}",
                              json={"status": "EM_ANDAMENTO"}, headers=header)
    assert em_andamento.status_code == 200, em_andamento.text

    pronto = client.put(f"/api/v1/ordens-servico/{numero_os}",
                        json={"status": "AGUARDANDO_RETIRADA"}, headers=header)
    assert pronto.status_code == 200, pronto.text
    assert pronto.json()["status"] == "AGUARDANDO_RETIRADA"


def test_oficina_continua_aceitando_todos_os_status(client, db_session):
    """Caso 7 -- nao regressao (PR1): a oficina nao declara status_usados."""
    header = _autenticar_e_criar_empresa(client, "oficina_mecanica")
    cliente_id = _criar_cliente(client, header)
    r = client.post("/api/v1/ordens-servico/", json={
        "cliente_id": cliente_id,
        "prioridade": "NORMAL",
        "defeito_relatado": "Barulho na suspensão",
        "dados_adicionais": {},
        "objeto": {"numero_serie": "ABC1D23", "marca": "Fiat", "modelo": "Uno"},
        "itens": [],
    }, headers=header)
    assert r.status_code == status.HTTP_201_CREATED, r.text
    numero_os = r.json()["numero_os"]

    aguardando = client.put(f"/api/v1/ordens-servico/{numero_os}",
                            json={"status": "AGUARDANDO_PECAS"}, headers=header)
    assert aguardando.status_code == 200, aguardando.text
