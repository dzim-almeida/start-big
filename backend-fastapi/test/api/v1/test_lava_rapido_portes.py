# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_lava_rapido_portes.py
# DESCRICAO: Portes da loja e preco por porte pela API (docs/lava-rapido/
#            SPEC-02A, secao de casos de teste).
#
# O que se prova aqui:
#   - a primeira leitura grava a lista inicial do registry, uma vez so;
#   - o dono cria, renomeia, reordena e desativa porte (sem apagar);
#   - a grade de precos do servico e gravada inteira e volta ao padrao;
#   - a comanda recebe todo servico ativo com o preco do porte (ou o padrao);
#   - fora do segmento com `preco_por_porte` as rotas nao existem (404).
# ---------------------------------------------------------------------------

from starlette import status

from test.api.v1.test_segmento_lava_rapido import _autenticar_e_criar_empresa

URL = "/api/v1/lava-rapido"


def _criar_servico(client, header, descricao="Lavagem completa", valor=5000) -> int:
    r = client.post("/api/v1/servicos/", json={"descricao": descricao, "valor": valor}, headers=header)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _porte(client, header, tipo, nome) -> dict:
    r = client.get(f"{URL}/portes", params={"tipo_veiculo": tipo}, headers=header)
    assert r.status_code == 200, r.text
    return next(p for p in r.json() if p["nome"] == nome)


# =========================
# Portes
# =========================

def test_primeira_leitura_grava_a_lista_inicial(client, db_session):
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    r = client.get(f"{URL}/portes", params={"tipo_veiculo": "carro"}, headers=header)
    assert r.status_code == 200, r.text
    assert [p["nome"] for p in r.json()] == ["Hatch", "Sedã", "SUV", "Picape", "Van / utilitário"]

    # Todos os tipos ganham a sua lista, inclusive bicicleta (SPEC-00 U5).
    tudo = client.get(f"{URL}/portes", headers=header).json()
    assert {p["tipo_veiculo"] for p in tudo} == {"carro", "moto", "pesado", "bicicleta", "outros"}

    # Segunda leitura nao duplica.
    de_novo = client.get(f"{URL}/portes", headers=header).json()
    assert len(de_novo) == len(tudo)


def test_lista_inicial_nao_volta_depois_de_editada(client, db_session):
    """P2a: a tabela e da loja. Desativar tudo de um tipo nao faz a lista renascer."""
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    for porte in client.get(f"{URL}/portes", params={"tipo_veiculo": "moto"}, headers=header).json():
        client.put(f"{URL}/portes/{porte['id']}", json={"ativo": False}, headers=header)
    assert client.get(f"{URL}/portes", params={"tipo_veiculo": "moto"}, headers=header).json() == []
    inativos = client.get(f"{URL}/portes", params={"tipo_veiculo": "moto", "incluir_inativos": True},
                          headers=header).json()
    assert len(inativos) == 2


def test_criar_renomear_e_desativar_porte(client, db_session):
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    r = client.post(f"{URL}/portes", json={"tipo_veiculo": "carro", "nome": "  SUV grande  "}, headers=header)
    assert r.status_code == 201, r.text
    novo = r.json()
    assert novo["nome"] == "SUV grande"                       # sem espacos nas pontas
    assert novo["ordem"] == 5                                 # entra no fim da fila

    r = client.put(f"{URL}/portes/{novo['id']}", json={"nome": "SUV 7 lugares", "ordem": 3}, headers=header)
    assert r.status_code == 200, r.text
    assert (r.json()["nome"], r.json()["ordem"]) == ("SUV 7 lugares", 3)

    r = client.put(f"{URL}/portes/{novo['id']}", json={"ativo": False}, headers=header)
    assert r.json()["ativo"] is False
    nomes = [p["nome"] for p in client.get(f"{URL}/portes", params={"tipo_veiculo": "carro"},
                                           headers=header).json()]
    assert "SUV 7 lugares" not in nomes


def test_nome_repetido_no_mesmo_tipo_e_recusado(client, db_session):
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    r = client.post(f"{URL}/portes", json={"tipo_veiculo": "carro", "nome": "suv"}, headers=header)
    assert r.status_code == 409, r.text                       # "SUV" ja existe (sem diferenca de caixa)
    # Em outro tipo pode.
    r = client.post(f"{URL}/portes", json={"tipo_veiculo": "outros", "nome": "SUV"}, headers=header)
    assert r.status_code == 201, r.text


def test_tipo_de_veiculo_desconhecido_e_recusado(client, db_session):
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    r = client.post(f"{URL}/portes", json={"tipo_veiculo": "aviao", "nome": "Grande"}, headers=header)
    assert r.status_code == 422, r.text


# =========================
# Preco por porte
# =========================

def test_grade_de_precos_e_gravada_inteira(client, db_session):
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    servico_id = _criar_servico(client, header)
    hatch = _porte(client, header, "carro", "Hatch")
    suv = _porte(client, header, "carro", "SUV")

    r = client.put(f"{URL}/servicos/{servico_id}/precos", json={"precos": [
        {"porte_id": hatch["id"], "valor": 4000, "duracao_minutos": 30},
        {"porte_id": suv["id"], "valor": 6000, "duracao_minutos": 45},
    ]}, headers=header)
    assert r.status_code == 200, r.text
    assert {(p["porte_id"], p["valor"]) for p in r.json()} == {(hatch["id"], 4000), (suv["id"], 6000)}

    # Nova grade sem o SUV: o SUV volta ao preco padrao.
    client.put(f"{URL}/servicos/{servico_id}/precos", json={"precos": [
        {"porte_id": hatch["id"], "valor": 4500},
    ]}, headers=header)
    r = client.get(f"{URL}/servicos/{servico_id}/precos", headers=header)
    assert [(p["porte_id"], p["valor"], p["duracao_minutos"]) for p in r.json()] == [(hatch["id"], 4500, None)]


def test_porte_repetido_ou_inexistente_na_grade(client, db_session):
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    servico_id = _criar_servico(client, header)
    hatch = _porte(client, header, "carro", "Hatch")
    r = client.put(f"{URL}/servicos/{servico_id}/precos", json={"precos": [
        {"porte_id": hatch["id"], "valor": 1}, {"porte_id": hatch["id"], "valor": 2},
    ]}, headers=header)
    assert r.status_code == 422, r.text
    r = client.put(f"{URL}/servicos/{servico_id}/precos", json={"precos": [
        {"porte_id": 99999, "valor": 1},
    ]}, headers=header)
    assert r.status_code == 404, r.text
    r = client.put(f"{URL}/servicos/{servico_id}/precos", json={"precos": [
        {"porte_id": hatch["id"], "valor": -1},
    ]}, headers=header)
    assert r.status_code == 422, r.text                       # centavos nao negativos


def test_comanda_recebe_preco_do_porte_ou_padrao(client, db_session):
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    lavagem = _criar_servico(client, header, "Lavagem completa", 5000)
    cera = _criar_servico(client, header, "Cera", 3000)
    suv = _porte(client, header, "carro", "SUV")
    client.put(f"{URL}/servicos/{lavagem}/precos", json={"precos": [
        {"porte_id": suv["id"], "valor": 7000, "duracao_minutos": 50},
    ]}, headers=header)

    r = client.get(f"{URL}/portes/{suv['id']}/servicos", headers=header)
    assert r.status_code == 200, r.text
    por_id = {s["servico_id"]: s for s in r.json()}
    assert (por_id[lavagem]["valor"], por_id[lavagem]["duracao_minutos"], por_id[lavagem]["preco_do_porte"]) \
        == (7000, 50, True)
    assert (por_id[cera]["valor"], por_id[cera]["preco_do_porte"]) == (3000, False)   # padrao


def test_servico_desativado_some_da_comanda(client, db_session):
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    servico_id = _criar_servico(client, header)
    r = client.put(f"/api/v1/servicos/toggle_ativo/{servico_id}", headers=header)   # desativa
    assert r.status_code == 200 and r.json()["ativo"] is False, r.text
    suv = _porte(client, header, "carro", "SUV")
    ids = [s["servico_id"] for s in client.get(f"{URL}/portes/{suv['id']}/servicos", headers=header).json()]
    assert servico_id not in ids


# =========================
# Outros segmentos (PR1)
# =========================

def test_fora_do_lava_rapido_as_rotas_nao_existem(client, db_session):
    header = _autenticar_e_criar_empresa(client, "oficina_mecanica")
    servico_id = _criar_servico(client, header)
    assert client.get(f"{URL}/portes", headers=header).status_code == 404
    assert client.post(f"{URL}/portes", json={"tipo_veiculo": "carro", "nome": "X"},
                       headers=header).status_code == 404
    assert client.get(f"{URL}/servicos/{servico_id}/precos", headers=header).status_code == 404


def test_duracao_do_cadastro_do_servico_chega_na_comanda(client, db_session):
    """13/11/2026: sem a grade por porte, a duracao vem do cadastro do servico
    (o patio calcula "Pronto as ..." com ela). Sem duracao: None, como antes."""
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    r = client.post("/api/v1/servicos/", json={"descricao": "Lavagem simples", "valor": 5000,
                                              "duracao_minutos": 40}, headers=header)
    assert r.status_code == status.HTTP_201_CREATED, r.text
    assert r.json()["duracao_minutos"] == 40
    sem = _criar_servico(client, header, descricao="Aspiracao", valor=2000)

    porte = _porte(client, header, "carro", "Hatch")
    lista = {s["descricao"]: s for s in
             client.get(f"{URL}/portes/{porte['id']}/servicos", headers=header).json()}
    assert lista["Lavagem simples"]["duracao_minutos"] == 40
    assert lista["Aspiracao"]["duracao_minutos"] is None

    # Editar e limpar a duracao.
    sid = r.json()["id"]
    assert client.put(f"/api/v1/servicos/{sid}", json={"duracao_minutos": 55},
                      headers=header).json()["duracao_minutos"] == 55
    assert client.put(f"/api/v1/servicos/{sem}", json={"duracao_minutos": None},
                      headers=header).json()["duracao_minutos"] is None


def test_duracao_invalida_e_recusada(client, db_session):
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    r = client.post("/api/v1/servicos/", json={"descricao": "X", "valor": 1, "duracao_minutos": 0},
                    headers=header)
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
