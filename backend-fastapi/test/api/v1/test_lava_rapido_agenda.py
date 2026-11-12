# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_lava_rapido_agenda.py
# DESCRICAO: Agenda do lava-rapido (docs/lava-rapido/SPEC-08A, casos de teste).
#
# O agendamento vem ANTES da OS. Quando o cliente chega, a comanda abre a OS
# e o agendamento fica CHEGOU com o numero dela.
# ---------------------------------------------------------------------------

from datetime import date, datetime, timedelta

from fastapi import status

from test.api.v1.test_lava_rapido_lavadores import _abrir_os, _loja
from test.api.v1.test_segmento_lava_rapido import _autenticar_e_criar_empresa

URL = "/api/v1/lava-rapido/agendamentos"


def _hoje_iso() -> str:
    return date.today().isoformat()


def _criar(client, header, **extra) -> dict:
    corpo = {
        # Meio-dia UTC de hoje: cai "hoje" em qualquer fuso do Brasil.
        "inicio": f"{_hoje_iso()}T12:00:00Z",
        "duracao_minutos": 40,
        "cliente_nome": "  Maria Cliente  ",
        "cliente_contato": "88999991234",
        "placa": "ABC1D23",
        "veiculo": "Gol prata",
        "tipo_veiculo": "carro",
        "servicos": [{"servico_id": None, "nome": "Lavagem completa", "valor": 6000}],
        **extra,
    }
    r = client.post(URL, json=corpo, headers=header)
    assert r.status_code == status.HTTP_201_CREATED, r.text
    return r.json()


def _do_dia(client, header, dia: str = None) -> list:
    dia = dia or _hoje_iso()
    r = client.get(URL, params={"inicio": dia, "fim": dia}, headers=header)
    assert r.status_code == 200, r.text
    return r.json()


def test_criar_e_listar_no_dia(client, db_session):
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    criado = _criar(client, header)
    assert criado["situacao"] == "AGENDADO"
    assert criado["cliente_nome"] == "Maria Cliente"            # sem espacos nas pontas
    assert criado["inicio"].startswith(f"{_hoje_iso()}T12:00")  # gravado em UTC
    assert [a["id"] for a in _do_dia(client, header)] == [criado["id"]]

    amanha = (date.today() + timedelta(days=1)).isoformat()
    assert _do_dia(client, header, amanha) == []


def test_ordem_pela_hora(client, db_session):
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    tarde = _criar(client, header, inicio=f"{_hoje_iso()}T17:00:00Z")
    manha = _criar(client, header, inicio=f"{_hoje_iso()}T11:00:00Z")
    assert [a["id"] for a in _do_dia(client, header)] == [manha["id"], tarde["id"]]


def test_remarcar_e_marcar_nao_veio(client, db_session):
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    ag = _criar(client, header)
    r = client.put(f"{URL}/{ag['id']}", json={"inicio": f"{_hoje_iso()}T14:30:00Z"}, headers=header)
    assert r.status_code == 200 and r.json()["inicio"].startswith(f"{_hoje_iso()}T14:30"), r.text
    r = client.put(f"{URL}/{ag['id']}", json={"situacao": "NAO_VEIO"}, headers=header)
    assert r.json()["situacao"] == "NAO_VEIO"


def test_chegou_exige_a_os_e_nao_volta(client, db_session):
    header, atendente, _, _, cliente, _ = _loja(client, db_session)
    ag = _criar(client, header, cliente_id=cliente)

    r = client.put(f"{URL}/{ag['id']}", json={"situacao": "CHEGOU"}, headers=header)
    assert r.status_code == 422, r.text                        # sem OS, nao "chegou"

    numero = _abrir_os(client, header, cliente, atendente)
    r = client.put(f"{URL}/{ag['id']}", json={"situacao": "CHEGOU", "numero_os": numero}, headers=header)
    assert r.status_code == 200 and r.json()["numero_os"] == numero, r.text

    r = client.put(f"{URL}/{ag['id']}", json={"situacao": "CANCELADO"}, headers=header)
    assert r.status_code == 422, r.text                        # ja virou OS


def test_excluir_so_cancelado(client, db_session):
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    ag = _criar(client, header)
    assert client.delete(f"{URL}/{ag['id']}", headers=header).status_code == 422
    client.put(f"{URL}/{ag['id']}", json={"situacao": "CANCELADO"}, headers=header)
    assert client.delete(f"{URL}/{ag['id']}", headers=header).status_code == 204
    assert _do_dia(client, header) == []


def test_validacoes(client, db_session):
    header = _autenticar_e_criar_empresa(client, "lava_rapido")
    r = client.post(URL, json={"inicio": f"{_hoje_iso()}T12:00:00Z", "cliente_nome": "  "}, headers=header)
    assert r.status_code == 422, r.text                        # nome vazio
    r = client.get(URL, params={"inicio": _hoje_iso(), "fim": "2020-01-01"}, headers=header)
    assert r.status_code == 422, r.text                        # fim antes do inicio
    r = client.put(f"{URL}/99999", json={"situacao": "NAO_VEIO"}, headers=header)
    assert r.status_code == 404, r.text


def test_fora_do_lava_rapido_nao_existe(client, db_session):
    header = _autenticar_e_criar_empresa(client, "oficina_mecanica")
    r = client.get(URL, params={"inicio": _hoje_iso(), "fim": _hoje_iso()}, headers=header)
    assert r.status_code == 404
