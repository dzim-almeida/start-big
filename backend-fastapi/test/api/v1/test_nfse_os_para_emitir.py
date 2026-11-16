# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_nfse_os_para_emitir.py
# DESCRICAO: A lista de OS prontas para a NFS-e (M3 de
#            docs/nfse-melhorias-plano.md): escolher com um clique, ou achar
#            pelo numero curto ("158") e pelo cliente.
# ---------------------------------------------------------------------------

from test.api.v1.test_nfse_os import (  # noqa: F401
    NFSE, _criar_os, _item_servico, client, licenca, loja, plataforma, servico,
)

ROTA = f"{NFSE}/os-para-emitir"


def test_lista_a_os_finalizada_com_cliente_e_valor_dos_servicos(client, loja, servico, db_session):
    numero = _criar_os(client, loja, db_session, [_item_servico(servico, valor=15000)])

    r = client.get(ROTA, headers=loja)

    assert r.status_code == 200, r.text
    [os_] = r.json()
    assert (os_["numero_os"], os_["cliente"], os_["valor_servicos"], os_["nfse_parcial"]) == (
        numero, "Maria Souza", 15000, False,
    )


def test_numero_curto_e_nome_do_cliente_acham_a_os(client, loja, servico, db_session):
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])
    curto = str(int(numero.rsplit("-", 1)[1]))              # OS-2026-000001 → "1"

    assert [o["numero_os"] for o in client.get(ROTA, params={"buscar": curto}, headers=loja).json()] == [numero]
    assert [o["numero_os"] for o in client.get(ROTA, params={"buscar": "maria"}, headers=loja).json()] == [numero]
    assert [o["numero_os"] for o in client.get(ROTA, params={"buscar": numero}, headers=loja).json()] == [numero]
    assert client.get(ROTA, params={"buscar": "joao"}, headers=loja).json() == []


# (O `_criar_os` cria sempre o mesmo cliente: uma OS por teste.)
def test_os_nao_finalizada_fica_de_fora(client, loja, servico, db_session):
    _criar_os(client, loja, db_session, [_item_servico(servico)], finalizar=False)
    assert client.get(ROTA, headers=loja).json() == []


def test_os_ja_com_nfse_sai_da_lista(client, loja, servico, db_session, plataforma):
    emitida = _criar_os(client, loja, db_session, [_item_servico(servico)])
    assert client.post(f"{NFSE}/os/{emitida}/emitir", headers=loja).status_code == 200
    assert client.get(ROTA, headers=loja).json() == []


def test_exige_o_modulo(client, loja, licenca):
    licenca("NFE")
    assert client.get(ROTA, headers=loja).status_code == 403
