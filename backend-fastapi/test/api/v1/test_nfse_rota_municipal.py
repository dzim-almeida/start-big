# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_nfse_rota_municipal.py
# DESCRICAO: G6 da NFS-e (docs/nfse-fase2-plano.md): a rota que a plataforma
#            decide (Nacional x prefeitura) muda a conferencia e a DPS no ERP.
#            A plataforma e simulada em `rota.consultar_plataforma`.
# ---------------------------------------------------------------------------

import pytest

from app.services.fiscal.nfse import rota as rota_mod
from app.services.fiscal.nfse.rota import (
    MUNICIPAL, MUNICIPAL_PENDENTE, NACIONAL, RotaNfse, _de_resposta, extensao_municipal,
    pendencias_do_servico, rota_da_empresa,
)

# Fixtures e ajudantes da NFS-e da OS (MEI de Iguatu, plataforma falsa).
from test.api.v1.test_nfse_os import (  # noqa: F401
    AVULSA, NFSE, _criar_os, _item_servico, client, licenca, loja, plataforma, plataforma_avulsa, servico,
)


def _resposta(rota, **obrigatorios):
    return {
        "rota": rota,
        "municipio": {
            "codigo_ibge": "2305506", "nome": "Iguatu", "uf": "CE", "status_nfse": "ativo",
            "exige_login": False, "obrigatorios": obrigatorios,
        },
    }


@pytest.fixture
def cidade(monkeypatch):
    """Roteiriza a resposta da plataforma; o cache da rota zera antes e depois."""
    rota_mod.limpar_cache()
    estado = {"resposta": {}, "chamadas": 0}

    def _consultar(db, empresa_id):
        estado["chamadas"] += 1
        return estado["resposta"]

    monkeypatch.setattr(rota_mod, "consultar_plataforma", _consultar)

    def _definir(resposta):
        estado["resposta"] = resposta
        rota_mod.limpar_cache()
        return estado
    yield _definir
    rota_mod.limpar_cache()


# =========================
# Regras puras
# =========================

def test_resposta_vazia_e_a_nacional_sem_confirmacao():
    r = _de_resposta({})
    assert (r.rota, r.confirmada) == (NACIONAL, False)
    r = _de_resposta(_resposta(MUNICIPAL, codigo_cnae=True))
    assert (r.rota, r.cidade, r.confirmada) == (MUNICIPAL, "Iguatu/CE", True)
    assert r.exige("codigo_cnae") and not r.exige("endereco")


def test_exigencias_so_valem_na_rota_municipal():
    class Fiscal:
        codigo_tributacao_municipio = None
        cnae = None
        codigo_servico_lc116 = "14.01"

    nacional = RotaNfse(rota=NACIONAL, obrigatorios={"codigo_cnae": True}, confirmada=True)
    municipal = RotaNfse(rota=MUNICIPAL, obrigatorios={"codigo_cnae": True, "codigo_tributario_municipio": True},
                         confirmada=True)
    assert pendencias_do_servico(nacional, Fiscal()) == []
    assert {p.campo for p in pendencias_do_servico(municipal, Fiscal())} == {"cnae", "codigo_tributacao_municipio"}
    assert extensao_municipal(nacional, Fiscal()) is None
    assert extensao_municipal(municipal, Fiscal()) == {"item_lista_servico": "14.01"}


def test_cache_guarda_so_o_que_a_plataforma_confirmou(cidade, db_session):
    estado = cidade({})
    rota_da_empresa(db_session, 1)
    rota_da_empresa(db_session, 1)
    assert estado["chamadas"] == 2                 # sem resposta, pergunta de novo

    estado = cidade(_resposta(MUNICIPAL))
    antes = estado["chamadas"]
    assert rota_da_empresa(db_session, 1).rota == MUNICIPAL
    estado["resposta"] = {}                        # a plataforma caiu depois
    assert rota_da_empresa(db_session, 1).rota == MUNICIPAL
    assert estado["chamadas"] - antes == 1         # o segundo veio do cache


def test_sem_licenca_nao_pergunta_a_plataforma(db_session, monkeypatch):
    """Sem token a rota nem sai daqui (e o teste nunca toca a rede)."""
    rota_mod.limpar_cache()
    monkeypatch.setattr("app.services.fiscal.http.get_fiscal_client",
                        lambda *a, **k: pytest.fail("não devia perguntar sem licença"))
    assert rota_mod.consultar_plataforma(db_session, 1) == {}


# =========================
# NFS-e da OS
# =========================

def test_cidade_sem_decisao_vira_pendencia_e_nada_sai(client, loja, servico, db_session, plataforma, cidade):
    cidade(_resposta(MUNICIPAL_PENDENTE))
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])

    r = client.get(f"{NFSE}/os/{numero}/verificar", headers=loja)
    assert r.status_code == 200
    assert "rota_nfse" in {p["campo"] for p in r.json()["pendencias"]}

    r = client.post(f"{NFSE}/os/{numero}/emitir", headers=loja)
    assert r.status_code == 422
    assert plataforma.enviados == []


def test_municipal_cobra_o_que_a_cidade_exige(client, loja, servico, db_session, plataforma, cidade):
    cidade(_resposta(MUNICIPAL, codigo_tributario_municipio=True, codigo_cnae=True))
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])

    campos = {p["campo"] for p in client.get(f"{NFSE}/os/{numero}/verificar", headers=loja).json()["pendencias"]}
    assert {"codigo_tributacao_municipio", "cnae"} <= campos

    r = client.put(f"/api/v1/servicos/{servico}/fiscal", json={
        "codigo_servico_lc116": "01.07", "codigo_tributacao_nacional": "01.07.01", "codigo_nbs": "1.1501.30.00",
        "codigo_tributacao_municipio": "0107", "cnae": "6209100",
    }, headers=loja)
    assert r.status_code == 200, r.text

    r = client.post(f"{NFSE}/os/{numero}/emitir", headers=loja)
    assert r.status_code == 200, r.text
    _ref, dps = plataforma.enviados[0]
    # A mesma DPS da Nacional, com a extensão que a plataforma traduz.
    assert dps["codigo_tributacao_nacional_iss"] == "010701"
    assert dps["codigo_tributacao_municipal_iss"] == "0107"
    # O cadastro guarda o item da LC 116 só com dígitos.
    assert dps["_municipal"] == {"codigo_cnae": "6209100", "item_lista_servico": "0107"}


def test_municipal_nao_cobra_o_nbs(client, loja, db_session, plataforma, cidade):
    cidade(_resposta(MUNICIPAL))
    sid = client.post("/api/v1/servicos/", json={"descricao": "Montagem", "valor": 10000}, headers=loja).json()["id"]
    client.put(f"/api/v1/servicos/{sid}/fiscal", json={"codigo_tributacao_nacional": "07.02.01"}, headers=loja)
    numero = _criar_os(client, loja, db_session, [_item_servico(sid)])

    pendencias = client.get(f"{NFSE}/os/{numero}/verificar", headers=loja).json()["pendencias"]
    assert "codigo_nbs" not in {p["campo"] for p in pendencias}

    cidade(_resposta(NACIONAL))
    pendencias = client.get(f"{NFSE}/os/{numero}/verificar", headers=loja).json()["pendencias"]
    assert "codigo_nbs" in {p["campo"] for p in pendencias}


def test_nacional_nao_leva_extensao(client, loja, servico, db_session, plataforma, cidade):
    cidade(_resposta(NACIONAL))
    numero = _criar_os(client, loja, db_session, [_item_servico(servico)])
    assert client.post(f"{NFSE}/os/{numero}/emitir", headers=loja).status_code == 200
    _ref, dps = plataforma.enviados[0]
    assert "_municipal" not in dps


def test_avulsa_com_cidade_sem_decisao_nao_sai(client, loja, plataforma_avulsa, cidade):
    cidade(_resposta(MUNICIPAL_PENDENTE))
    r = client.post(f"{NFSE}/avulsa/emitir", json=AVULSA, headers=loja)
    assert r.status_code == 422
    assert "rota_nfse" in {p["campo"] for p in r.json()["detail"]["pendencias"]}
    assert plataforma_avulsa.enviados == []


# =========================
# Ativação
# =========================

def test_ativacao_manda_o_codigo_ibge_e_o_login_da_prefeitura(db_session, loja, monkeypatch):
    from app.db.crud import fiscal as crud
    from app.db.models.empresa import Empresa
    from app.services.fiscal.configuracao.ativacao import montar_emitente_para_ativacao
    from app.services.fiscal.http.client_startbig import FiscalClientStartBig

    empresa = db_session.query(Empresa).first()
    emitente = montar_emitente_para_ativacao(
        empresa, crud.get_endereco_empresa(db_session, empresa.id), crud.get_fiscal_settings(db_session, empresa.id),
    )
    assert emitente["endereco"]["codigo_municipio"] == "2305506"   # Iguatu/CE

    enviado = {}

    class Resposta:
        status_code = 200

        def json(self):
            return {"mensagem": "ok"}

    class Http:
        def __init__(self, *a, **k): ...
        def __enter__(self): return self
        def __exit__(self, *a): return False

        def post(self, url, json=None, headers=None):
            enviado.update(json)
            return Resposta()

    monkeypatch.setattr("app.services.fiscal.http.client_startbig.httpx.Client", Http)
    cli = FiscalClientStartBig(ambiente=2, token="t")
    cli.ativar_emissao(emitente, None, None, "MIIPFX", "senha", prefeitura_login="loja", prefeitura_senha="s3")
    assert (enviado["nfse_login_prefeitura"], enviado["nfse_senha_prefeitura"]) == ("loja", "s3")

    enviado.clear()
    cli.ativar_emissao(emitente, None, None, "MIIPFX", "senha")
    assert "nfse_login_prefeitura" not in enviado
