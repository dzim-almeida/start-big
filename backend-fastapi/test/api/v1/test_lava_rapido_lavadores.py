# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_lava_rapido_lavadores.py
# DESCRICAO: Lavadores da OS e comissao Dividir/Inteira (docs/lava-rapido/
#            SPEC-10A, casos de teste).
#
# O caso do cliente (12/11/2026): "La so trabalha ele e outro rapaz... pode
# ter 1 lavador por carro ou dois." E o dono decide se, com dois, a comissao
# e dividida ou paga inteira a cada um.
#
# Valores redondos de proposito: OS de R$ 100,00 de lavagem, 10% de comissao.
# ---------------------------------------------------------------------------

from datetime import date

from fastapi import status

from test.api.v1.test_comissao_sobre_lucro import _forma_pagamento, _seed_contador_venda
from test.api.v1.test_segmento_lava_rapido import _autenticar_e_criar_empresa

URL = "/api/v1/lava-rapido"


def _cargo(client, header, nome="Lavador", divisao=None) -> int:
    corpo = {"nome": nome, "permissoes": {}, "comissao_servico_percentual": 1000}   # 10%
    if divisao:
        corpo["comissao_divisao"] = divisao
    r = client.post("/api/v1/cargos/", json=corpo, headers=header)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _funcionario(client, header, cargo_id, nome, cpf, email) -> int:
    r = client.post("/api/v1/funcionarios/", json={
        "nome": nome, "cpf": cpf, "contato": "11999999999",
        "usuario": {"nome": email.split("@")[0], "email": email, "senha": "SenhaForte123!"},
        "endereco": [{"logradouro": "Rua X", "numero": "1", "cep": "12345-678",
                      "bairro": "Centro", "cidade": "Lab City", "estado": "SP"}],
    }, headers=header)
    assert r.status_code in (200, 201), r.text
    fid = r.json()["id"]
    lk = client.put(f"/api/v1/funcionarios/{fid}/cargo?cargo_id={cargo_id}", headers=header)
    assert lk.status_code == 200, lk.text
    return fid


def _cliente(client, header) -> int:
    r = client.post("/api/v1/clientes/cliente_pf", json={"nome": "João Motorista", "celular": "11988887777"},
                    headers=header)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _abrir_os(client, header, cliente_id, responsavel_id, placa="ABC1D23") -> str:
    r = client.post("/api/v1/ordens-servico/", json={
        "cliente_id": cliente_id, "prioridade": "NORMAL", "defeito_relatado": "Lavagem completa",
        "funcionario_id": responsavel_id,
        "dados_adicionais": {"tipo_trabalho": "carro"},
        "objeto": {"modelo": "Gol prata", "numero_serie": placa, "dados_adicionais": {"porte": "Hatch"}},
        "itens": [{"tipo": "SERVICO", "nome": "Lavagem completa", "unidade_medida": "UN",
                   "quantidade": 1, "valor_unitario": 10000}],
    }, headers=header)
    assert r.status_code == status.HTTP_201_CREATED, r.text
    return r.json()["numero_os"]


def _finalizar(client, header, numero, fp_id):
    r = client.put(f"/api/v1/ordens-servico/{numero}/finalizar", json={
        "situacao_equipamento": "REPARADO",
        "pagamentos": [{"forma_pagamento_id": fp_id, "valor": 10000}],
    }, headers=header)
    assert r.status_code == 200, r.text


def _base_os(client, header) -> dict:
    """{funcionario_id: base de servico} no relatorio de comissao de hoje."""
    hoje = date.today().isoformat()
    r = client.get(f"/api/v1/relatorios/comissoes?inicio={hoje}&fim={hoje}", headers=header)
    assert r.status_code == 200, r.text
    return {i["funcionario_id"]: i["faturamento_os"] for i in r.json()["itens"]}


def _loja(client, db_session, divisao_cargo=None):
    """Lava-rapido com atendente (responsavel) e dois lavadores."""
    _seed_contador_venda(db_session)
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    cargo = _cargo(client, header, divisao=divisao_cargo)
    atendente = _funcionario(client, header, cargo, "Ana Atendente", "11122233344", "ana@lava.com")
    pedro = _funcionario(client, header, cargo, "Pedro Lavador", "22233344455", "pedro@lava.com")
    joao = _funcionario(client, header, cargo, "Joao Lavador", "33344455566", "joao@lava.com")
    return header, atendente, pedro, joao, _cliente(client, header), _forma_pagamento(client, header)


# =========================
# Lavadores da OS
# =========================

def test_definir_e_ler_os_lavadores(client, db_session):
    header, atendente, pedro, joao, cliente, _ = _loja(client, db_session)
    numero = _abrir_os(client, header, cliente, atendente)

    r = client.put(f"{URL}/os/{numero}/lavadores", json={"funcionario_ids": [pedro, joao, pedro]}, headers=header)
    assert r.status_code == 200, r.text
    assert [l["funcionario_id"] for l in r.json()] == [pedro, joao]          # sem repetir, na ordem
    assert [l["nome"] for l in client.get(f"{URL}/os/{numero}/lavadores", headers=header).json()] \
        == ["Pedro Lavador", "Joao Lavador"]

    # Lista vazia tira todos.
    r = client.put(f"{URL}/os/{numero}/lavadores", json={"funcionario_ids": []}, headers=header)
    assert r.json() == []


def test_lavador_inexistente_e_limite(client, db_session):
    header, atendente, pedro, _, cliente, _ = _loja(client, db_session)
    numero = _abrir_os(client, header, cliente, atendente)
    r = client.put(f"{URL}/os/{numero}/lavadores", json={"funcionario_ids": [99999]}, headers=header)
    assert r.status_code == 422, r.text
    r = client.put(f"{URL}/os/{numero}/lavadores", json={"funcionario_ids": list(range(1, 8))}, headers=header)
    assert r.status_code == 422, r.text
    r = client.put(f"{URL}/os/OS-0000-999999/lavadores", json={"funcionario_ids": [pedro]}, headers=header)
    assert r.status_code == 404, r.text


def test_os_finalizada_nao_troca_lavador(client, db_session):
    header, atendente, pedro, _, cliente, fp = _loja(client, db_session)
    numero = _abrir_os(client, header, cliente, atendente)
    _finalizar(client, header, numero, fp)
    r = client.put(f"{URL}/os/{numero}/lavadores", json={"funcionario_ids": [pedro]}, headers=header)
    assert r.status_code == 422, r.text


def test_fora_do_lava_rapido_nao_existe(client, db_session):
    header = _autenticar_e_criar_empresa(client, "oficina_mecanica")
    assert client.get(f"{URL}/os/OS-1/lavadores", headers=header).status_code == 404


# =========================
# Comissao (O7c)
# =========================

def test_sem_lavador_a_comissao_e_do_responsavel_como_sempre(client, db_session):
    header, atendente, pedro, _, cliente, fp = _loja(client, db_session)
    _finalizar(client, header, _abrir_os(client, header, cliente, atendente), fp)
    base = _base_os(client, header)
    assert base[atendente] == 10000
    assert pedro not in base                                   # nao faturou nada


def test_dois_lavadores_dividem_por_padrao(client, db_session):
    header, atendente, pedro, joao, cliente, fp = _loja(client, db_session)
    numero = _abrir_os(client, header, cliente, atendente)
    client.put(f"{URL}/os/{numero}/lavadores", json={"funcionario_ids": [pedro, joao]}, headers=header)
    _finalizar(client, header, numero, fp)

    base = _base_os(client, header)
    assert base[pedro] == 5000 and base[joao] == 5000
    assert atendente not in base                               # quem abriu nao lavou


def test_inteira_no_cargo_paga_o_valor_todo_a_cada_um(client, db_session):
    header, atendente, pedro, joao, cliente, fp = _loja(client, db_session, divisao_cargo="inteira")
    numero = _abrir_os(client, header, cliente, atendente)
    client.put(f"{URL}/os/{numero}/lavadores", json={"funcionario_ids": [pedro, joao]}, headers=header)
    _finalizar(client, header, numero, fp)
    base = _base_os(client, header)
    assert base[pedro] == 10000 and base[joao] == 10000


def test_funcionario_sobrescreve_o_cargo(client, db_session):
    """Cascata funcionario -> cargo, igual ao comissao_modo."""
    header, atendente, pedro, joao, cliente, fp = _loja(client, db_session)       # cargo: dividir
    r = client.put(f"/api/v1/funcionarios/{joao}", json={"comissao_divisao": "inteira"}, headers=header)
    assert r.status_code == 200, r.text
    assert r.json()["comissao_divisao"] == "inteira"

    numero = _abrir_os(client, header, cliente, atendente)
    client.put(f"{URL}/os/{numero}/lavadores", json={"funcionario_ids": [pedro, joao]}, headers=header)
    _finalizar(client, header, numero, fp)
    base = _base_os(client, header)
    assert base[pedro] == 5000 and base[joao] == 10000


def test_um_lavador_recebe_tudo(client, db_session):
    header, atendente, pedro, _, cliente, fp = _loja(client, db_session)
    numero = _abrir_os(client, header, cliente, atendente)
    client.put(f"{URL}/os/{numero}/lavadores", json={"funcionario_ids": [pedro]}, headers=header)
    _finalizar(client, header, numero, fp)
    assert _base_os(client, header)[pedro] == 10000


def test_extrato_bate_com_o_ranking(client, db_session):
    header, atendente, pedro, joao, cliente, fp = _loja(client, db_session)
    numero = _abrir_os(client, header, cliente, atendente)
    client.put(f"{URL}/os/{numero}/lavadores", json={"funcionario_ids": [pedro, joao]}, headers=header)
    _finalizar(client, header, numero, fp)
    _finalizar(client, header, _abrir_os(client, header, cliente, pedro, placa="XYZ9A87"), fp)  # sozinho

    hoje = date.today().isoformat()
    r = client.get(f"/api/v1/relatorios/extrato-funcionario?funcionario_id={pedro}&inicio={hoje}&fim={hoje}",
                   headers=header)
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert corpo["total_mao_de_obra"] == 15000                  # 50 (dividida) + 100 (sozinho)
    assert corpo["total_mao_de_obra"] == _base_os(client, header)[pedro]
    assert any("dividido por 2" in i["servico"] for i in corpo["itens"])

    # O responsavel da OS com lavadores nao ve a OS no extrato dele.
    r = client.get(f"/api/v1/relatorios/extrato-funcionario?funcionario_id={atendente}&inicio={hoje}&fim={hoje}",
                   headers=header)
    assert r.json()["total_mao_de_obra"] == 0


def test_cargo_aceita_e_devolve_a_divisao(client, db_session):
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    cargo = _cargo(client, header, divisao="inteira")
    r = client.get("/api/v1/cargos/", headers=header)
    assert r.status_code == 200, r.text
    lista = r.json() if isinstance(r.json(), list) else r.json().get("items", r.json().get("itens", []))
    alvo = next(c for c in lista if c["id"] == cargo)
    assert alvo["comissao_divisao"] == "inteira"
    r = client.post("/api/v1/cargos/", json={"nome": "X", "permissoes": {}, "comissao_divisao": "metade"},
                    headers=header)
    assert r.status_code == 422, r.text
