# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_inutilizacao_recusa_local.py
# DESCRIÇÃO: O 4xx da plataforma na inutilização passa pelo `_recusa_local`,
#            como na emissão -- e o corpo da resposta vai para o log.
#
# Contexto (19/09/2026): a plataforma respondeu ao RFC de inutilização dizendo
# que um 404 nessa rota tem DUAS causas possíveis, e que o corpo decide qual:
#
#   (a) versão antiga no servidor  -> corpo "Cannot POST ...", sem `codigo`
#   (b) licença sem ficha fiscal   -> corpo com `codigo: "SEM_CONFIGURACAO_FISCAL"`
#
# Pediram o corpo que vimos. Não tínhamos: o log gravava só o status. E os
# dois casos viravam REJEITADA -- "rejeitada pela SEFAZ", para um pedido que
# nunca saiu do prédio. Este arquivo trava os dois consertos.
# ---------------------------------------------------------------------------

import logging

import httpx
import pytest

from app.services.fiscal.http.client import RESULTADO_NAO_TRANSMITIDO
from app.services.fiscal.http.client_startbig import FiscalClientStartBig

PAYLOAD = {
    "serie": 1, "numero_inicial": 3, "numero_final": 4,
    "justificativa": "Numeros queimados por rejeicao", "ano": 2026,
}


def _client():
    return FiscalClientStartBig(ambiente=2, token="token-de-teste")


def _responde(status_code, **kwargs):
    def _post(*_a, **_k):
        return httpx.Response(
            status_code, request=httpx.Request("POST", "http://x"), **kwargs,
        )
    return _post


# --- (a) servidor antigo: corpo de texto, sem JSON -------------------------

def test_404_de_rota_inexistente_e_nao_transmitido(monkeypatch):
    monkeypatch.setattr(httpx.Client, "post", _responde(404, text="Cannot POST /erp/fiscal/nfe/inutilizar"))

    resultado = _client().inutilizar_numeracao("inut-1", PAYLOAD)

    assert resultado["status"] == RESULTADO_NAO_TRANSMITIDO
    assert resultado["status"] != "erro"
    # A frase diz INUTILIZAÇÃO, não "emissão": o lojista precisa olhar a
    # configuração, não a SEFAZ.
    assert "inutilização" in resultado["mensagem_sefaz"]
    assert "antes de enviar a SEFAZ" in resultado["mensagem_sefaz"]


# --- (b) licença sem ficha fiscal: JSON com `codigo`, sem `codigo_sefaz` ----

def test_404_de_licenca_sem_ficha_fiscal_e_nao_transmitido_com_a_mensagem_deles(monkeypatch):
    monkeypatch.setattr(httpx.Client, "post", _responde(
        404, json={"codigo": "SEM_CONFIGURACAO_FISCAL", "message": "Licença sem configuração fiscal."},
    ))

    resultado = _client().inutilizar_numeracao("inut-1", PAYLOAD)

    assert resultado["status"] == RESULTADO_NAO_TRANSMITIDO
    # A mensagem da plataforma é a que vale -- é ela que diz a causa.
    assert resultado["mensagem_sefaz"] == "Licença sem configuração fiscal."
    assert resultado.get("codigo_sefaz") is None


# --- Rejeição de verdade: `codigo_sefaz` veio, a SEFAZ falou ---------------

def test_4xx_com_codigo_sefaz_e_rejeicao_e_nao_recusa_local(monkeypatch):
    monkeypatch.setattr(httpx.Client, "post", _responde(422, json={
        "status": "erro",
        "status_focus": "erro_autorizacao",
        "codigo_sefaz": 241,
        "mensagem_sefaz": "Rejeicao: Um numero da faixa ja esta inutilizado",
    }))

    resultado = _client().inutilizar_numeracao("inut-1", PAYLOAD)

    assert resultado["status"] == "erro"
    assert resultado["codigo_sefaz"] == 241
    assert resultado["status_focus"] == "erro_autorizacao"


# --- O corpo vai para o log -------------------------------------------------

def test_corpo_do_4xx_vai_para_o_log(monkeypatch, caplog):
    """É o que permite responder "mandem o corpo da resposta que viram"."""
    monkeypatch.setattr(httpx.Client, "post", _responde(
        404, json={"codigo": "SEM_CONFIGURACAO_FISCAL", "message": "Licença sem configuração fiscal."},
    ))

    with caplog.at_level(logging.ERROR, logger="app.services.fiscal.http.client_startbig"):
        _client().inutilizar_numeracao("inut-1", PAYLOAD)

    registro = " ".join(r.getMessage() for r in caplog.records)
    assert "404" in registro
    assert "SEM_CONFIGURACAO_FISCAL" in registro


# --- 5xx segue incerto: nada muda -------------------------------------------

def test_5xx_continua_incerto(monkeypatch):
    from app.services.fiscal.http.client_startbig import EmissaoIncertaError

    monkeypatch.setattr(httpx.Client, "post", _responde(502, text="Bad Gateway"))

    with pytest.raises(EmissaoIncertaError):
        _client().inutilizar_numeracao("inut-1", PAYLOAD)
