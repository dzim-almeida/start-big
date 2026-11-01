# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_nfse_saude.py
# DESCRICAO: Cards e "Saude Fiscal" da aba NFS-e (M4 de
#            docs/nfse-melhorias-plano.md): a mesma barra da aba NF-e.
# ---------------------------------------------------------------------------

from datetime import datetime, timedelta, timezone

from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.models.empresa_fiscal_settings import EmpresaFiscalSettings
from app.services.fiscal.nfse import rota as rota_mod

from test.api.v1.test_nfse_os import NFSE, client, licenca, loja, servico  # noqa: F401
from test.api.v1.test_nfse_rota_municipal import _resposta, cidade  # noqa: F401
from app.services.fiscal.nfse.rota import MUNICIPAL, MUNICIPAL_PENDENTE


def _itens(client, loja) -> dict:
    r = client.get(f"{NFSE}/saude", headers=loja)
    assert r.status_code == 200, r.text
    return {i["chave"]: i for i in r.json()["itens"]}, r.json()


def _certificado_ok(db_session):
    fs = db_session.query(EmpresaFiscalSettings).first()
    fs.certificado_status = "CONECTADO_NUVEM"
    fs.certificado_validade = datetime.now(timezone.utc) + timedelta(days=200)
    db_session.commit()


def test_tudo_certo_e_100(client, loja, servico, db_session, cidade):
    cidade({})                       # sem plataforma: vale a Nacional
    _certificado_ok(db_session)
    itens, corpo = _itens(client, loja)
    assert all(i["ok"] for i in itens.values()), itens
    assert (corpo["percentual"], corpo["pendencias"]) == (100, 0)


def test_servico_sem_codigos_aparece_com_o_que_falta(client, loja, servico, db_session, cidade):
    cidade({})
    _certificado_ok(db_session)
    sid = client.post("/api/v1/servicos/", json={"descricao": "Montagem", "valor": 10000}, headers=loja).json()["id"]

    itens, corpo = _itens(client, loja)

    assert itens["servicos"]["ok"] is False
    assert itens["servicos"]["servicos"] == [{"id": sid, "nome": "Montagem", "falta": "código nacional, NBS"}]
    assert corpo["percentual"] == 75


def test_na_municipal_cobra_o_que_a_cidade_exige_e_nao_o_nbs(client, loja, db_session, cidade):
    cidade(_resposta(MUNICIPAL, codigo_cnae=True))
    _certificado_ok(db_session)
    sid = client.post("/api/v1/servicos/", json={"descricao": "Montagem", "valor": 10000}, headers=loja).json()["id"]
    client.put(f"/api/v1/servicos/{sid}/fiscal", json={"codigo_tributacao_nacional": "07.02.01"}, headers=loja)

    itens, _ = _itens(client, loja)

    assert itens["servicos"]["servicos"][0]["falta"] == "cnae"
    assert "prefeitura de Iguatu/CE" in itens["rota"]["detalhe"]


def test_cidade_sem_decisao_e_certificado_ausente_sao_pendencias(client, loja, servico, cidade):
    cidade(_resposta(MUNICIPAL_PENDENTE))
    itens, corpo = _itens(client, loja)
    assert itens["rota"]["ok"] is False
    assert itens["certificado"]["ok"] is False
    assert corpo["pendencias"] == 2


def test_resumo_conta_so_as_nfse(client, loja, db_session):
    agora = datetime.now(timezone.utc)
    for tipo, status in [("NFSE", "AUTORIZADA"), ("NFSE", "PROCESSANDO"), ("NFE", "AUTORIZADA"), ("NFSE", "CANCELADA")]:
        db_session.add(DocumentoFiscal(tipo_documento=tipo, origem_tipo="AVULSA", status=status, ref_api=f"r-{tipo}-{status}",
                                       idempotency_key=f"k-{tipo}-{status}", ambiente_emissao=2,
                                       valor_total=100, data_emissao=agora))
    db_session.commit()

    r = client.get(f"{NFSE}/resumo", headers=loja)

    assert r.status_code == 200
    assert r.json() == {"pendentes": 1, "autorizadas": 1, "rejeitadas": 0, "canceladas": 1}


def test_saude_e_resumo_exigem_o_modulo(client, loja, licenca):
    licenca("NFE")
    assert client.get(f"{NFSE}/saude", headers=loja).status_code == 403
    assert client.get(f"{NFSE}/resumo", headers=loja).status_code == 403
    rota_mod.limpar_cache()


# =========================
# M2: padrão fiscal da loja para serviços novos
# =========================

def test_padrao_fiscal_da_loja_salva_em_digitos_e_volta(client, loja):
    r = client.put(f"{NFSE}/configuracao", json={
        "nfse_padrao_codigo_nacional": "14.01.01", "nfse_padrao_nbs": "1.2001.20.00", "nfse_padrao_aliquota_iss": 250,
    }, headers=loja)
    assert r.status_code == 200, r.text
    corpo = client.get(f"{NFSE}/configuracao", headers=loja).json()
    assert (corpo["nfse_padrao_codigo_nacional"], corpo["nfse_padrao_nbs"], corpo["nfse_padrao_aliquota_iss"]) == (
        "140101", "120012000", 250,
    )
    # O resto da configuração não muda por salvar só o padrão.
    assert corpo["nfse_reter_iss_pj"] is False


def test_padrao_fiscal_recusa_codigo_incompleto(client, loja):
    r = client.put(f"{NFSE}/configuracao", json={"nfse_padrao_codigo_nacional": "1401"}, headers=loja)
    assert r.status_code == 422


# --- Ligada na emissora (O3 de docs/nfe-cfop-e-notas-da-os-plano.md) ----------

def _emissora(monkeypatch, resposta):
    from app.services.fiscal.nfse import saude as saude_mod

    monkeypatch.setattr(saude_mod, "consultar_habilitacao", lambda db, empresa_id: resposta)


def test_plataforma_sem_resposta_nao_mostra_o_item(client, loja, servico, db_session, cidade, monkeypatch):
    cidade({})
    _certificado_ok(db_session)
    _emissora(monkeypatch, {})                      # plataforma velha (404) ou rede fora
    itens, corpo = _itens(client, loja)
    assert "emissora" not in itens
    assert corpo["percentual"] == 100


def test_ligada_na_emissora_conta_como_pronta(client, loja, servico, db_session, cidade, monkeypatch):
    cidade({})
    _certificado_ok(db_session)
    _emissora(monkeypatch, {"estado": "ok", "detalhe": "Rota Nacional, habilitada.", "rota": "NACIONAL"})
    itens, corpo = _itens(client, loja)
    assert itens["emissora"]["ok"] is True
    assert corpo["percentual"] == 100


def test_o_caso_de_29_10_desligada_na_emissora_e_pendencia(client, loja, servico, db_session, cidade, monkeypatch):
    cidade({})
    _certificado_ok(db_session)
    _emissora(monkeypatch, {"estado": "problema", "detalhe": "NFS-e Nacional desligada na Focus para produção.",
                            "rota": "NACIONAL"})
    itens, corpo = _itens(client, loja)
    assert itens["emissora"]["ok"] is False
    assert "suporte StartBig" in itens["emissora"]["detalhe"]
    assert itens["emissora"]["detalhe_suporte"].startswith("NFS-e Nacional desligada")
    assert corpo["pendencias"] == 1
