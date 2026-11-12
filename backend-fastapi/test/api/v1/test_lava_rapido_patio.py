# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_lava_rapido_patio.py
# DESCRICAO: Patio do lava-rapido (docs/lava-rapido/SPEC-04A, casos de teste).
#
# O dia do lava-rapido e uma fila: Aguardando -> Lavando -> Pronto, e o
# Pronto sai pelo recebimento de sempre. Cada cartao e uma OS comum.
# ---------------------------------------------------------------------------

from fastapi import status

from test.api.v1.test_lava_rapido_lavadores import _abrir_os, _finalizar, _loja

URL = "/api/v1/lava-rapido"


def _patio(client, header) -> dict:
    r = client.get(f"{URL}/patio", headers=header)
    assert r.status_code == 200, r.text
    return r.json()


def _numeros(coluna) -> list:
    return [c["numero_os"] for c in coluna]


def test_os_nova_entra_em_aguardando_com_o_que_o_cartao_mostra(client, db_session):
    header, atendente, pedro, _, cliente, _ = _loja(client, db_session)
    numero = _abrir_os(client, header, cliente, atendente)
    client.put(f"{URL}/os/{numero}/lavadores", json={"funcionario_ids": [pedro]}, headers=header)

    patio = _patio(client, header)
    assert _numeros(patio["aguardando"]) == [numero]
    cartao = patio["aguardando"][0]
    assert cartao["placa"] == "ABC1D23" and cartao["modelo"] == "Gol prata"
    assert cartao["porte"] == "Hatch" and cartao["tipo_veiculo"] == "carro"
    assert cartao["servicos"] == ["Lavagem completa"] and cartao["valor_total"] == 10000
    assert cartao["cliente_nome"] == "João Motorista" and cartao["cliente_contato"] == "11988887777"
    assert [l["nome"] for l in cartao["lavadores"]] == ["Pedro Lavador"]
    assert cartao["responsavel"] == "Ana Atendente"


def test_avancar_ate_pronto_e_receber(client, db_session):
    header, atendente, _, _, cliente, fp = _loja(client, db_session)
    numero = _abrir_os(client, header, cliente, atendente)

    r = client.post(f"{URL}/os/{numero}/avancar", headers=header)
    assert r.status_code == 200 and r.json()["status"] == "EM_ANDAMENTO", r.text
    assert _numeros(_patio(client, header)["lavando"]) == [numero]

    r = client.post(f"{URL}/os/{numero}/avancar", headers=header)
    assert r.json()["status"] == "AGUARDANDO_RETIRADA"
    assert _numeros(_patio(client, header)["pronto"]) == [numero]

    # Do Pronto nao se "avanca": recebe-se.
    r = client.post(f"{URL}/os/{numero}/avancar", headers=header)
    assert r.status_code == 422, r.text

    _finalizar(client, header, numero, fp)
    patio = _patio(client, header)
    assert _numeros(patio["entregues_hoje"]) == [numero]
    assert not patio["pronto"]


def test_voltar_desfaz_o_engano(client, db_session):
    header, atendente, _, _, cliente, _ = _loja(client, db_session)
    numero = _abrir_os(client, header, cliente, atendente)
    client.post(f"{URL}/os/{numero}/avancar", headers=header)
    r = client.post(f"{URL}/os/{numero}/voltar", headers=header)
    assert r.json()["status"] == "ABERTA"
    r = client.post(f"{URL}/os/{numero}/voltar", headers=header)
    assert r.status_code == 422, r.text                     # ja esta no inicio


def test_ordem_de_chegada(client, db_session):
    header, atendente, _, _, cliente, _ = _loja(client, db_session)
    primeiro = _abrir_os(client, header, cliente, atendente, placa="AAA1A11")
    segundo = _abrir_os(client, header, cliente, atendente, placa="BBB2B22")
    assert _numeros(_patio(client, header)["aguardando"]) == [primeiro, segundo]


def test_cancelada_some_do_patio(client, db_session):
    header, atendente, _, _, cliente, _ = _loja(client, db_session)
    numero = _abrir_os(client, header, cliente, atendente)
    r = client.put(f"/api/v1/ordens-servico/{numero}/cancelar", json={"motivo": "Cliente desistiu"},
                   headers=header)
    assert r.status_code == 200, r.text
    patio = _patio(client, header)
    assert numero not in _numeros(patio["aguardando"]) + _numeros(patio["entregues_hoje"])


def test_fora_do_lava_rapido_nao_existe(client, db_session):
    from test.api.v1.test_segmento_lava_rapido import _autenticar_e_criar_empresa

    header = _autenticar_e_criar_empresa(client, "oficina_mecanica")
    assert client.get(f"{URL}/patio", headers=header).status_code == status.HTTP_404_NOT_FOUND
    assert client.post(f"{URL}/os/OS-1/avancar", headers=header).status_code == status.HTTP_404_NOT_FOUND
