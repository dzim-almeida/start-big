"""
Diagnóstico de rejeição no backend (F5, 07/10/2026).

Os casos são os mesmos do `fiscalDiagnostic.spec.ts` do front — as três
rejeições da primeira NF-e real (481, 539, 305) e as regras de precedência
entre cStat e palavra-chave —, para a mudança de lugar não mudar o conselho.
"""
from datetime import datetime

import pytest

from app.schemas.documento_fiscal import DocumentoFiscalRead
from app.services.fiscal.diagnostico_sefaz import TABELA, diagnosticar, ler_chave_da_mensagem

MSG_481 = "Rejeição: Código Regime Tributário do emitente diverge do cadastro na SEFAZ"
MSG_539 = (
    "Rejeição: Duplicidade de NF-e com diferença na Chave de Acesso "
    "[chNFe:35260958348941000109550020000000041750446210][nRec:351025570568140]"
)
MSG_305 = "Rejeição: Destinatário bloqueado na UF"


def test_481_aponta_o_regime_e_nao_o_certificado():
    d = diagnosticar(481, MSG_481)
    assert "Regime Tributário" in d["titulo"]
    assert "4 - MEI" in d["como_resolver"]
    assert "certificado" not in d["como_resolver"].lower()
    assert d["acao"]["tipo"] == "CONFIG_FISCAL"


def test_539_diz_qual_numero_e_quando():
    d = diagnosticar(539, MSG_539)
    assert d["categoria"] == "DUPLICIDADE"
    assert "nº 4 da série 2" in d["explicacao"]
    assert "09/2026" in d["explicacao"]
    assert "informe abaixo" in d["como_resolver"]
    assert "CSOSN" not in d["como_resolver"]


def test_539_sem_chave_na_mensagem_ainda_explica():
    assert diagnosticar(539, "Rejeição: Duplicidade")["explicacao"].startswith("Este número já foi emitido")


def test_305_cliente_bloqueado():
    d = diagnosticar(305, MSG_305)
    assert d["categoria"] == "CLIENTE"
    assert "Bloqueado" in d["titulo"]
    assert "CCC" in d["como_resolver"] or "SINTEGRA" in d["como_resolver"]


def test_207_e_209_sao_do_emitente():
    assert "Sua Empresa" in diagnosticar(207, "Rejeição: CNPJ do emitente inválido")["titulo"]
    assert "Sua Empresa" in diagnosticar(209, "Rejeição: IE do emitente inválida")["titulo"]


def test_204_manda_consultar():
    assert diagnosticar(204, "Rejeição: Duplicidade de NF-e")["acao"]["tipo"] == "RECONSULTAR"


@pytest.mark.parametrize("cstat", range(280, 287))
def test_faixa_do_certificado(cstat):
    assert diagnosticar(cstat, "x")["acao"]["tipo"] == "CENTRO_FISCAL"


@pytest.mark.parametrize("cstat", sorted(TABELA))
def test_todo_codigo_da_tabela_devolve_o_proprio_cstat(cstat):
    d = diagnosticar(cstat, "Rejeição: qualquer")
    assert d["cstat"] == cstat
    assert d["titulo"] and d["explicacao"] and d["como_resolver"]


def test_sem_cstat_configuracao_cai_em_configuracao():
    assert diagnosticar(None, "Empresa não possui configuração fiscal ativa.")["categoria"] == "CONFIGURACAO"


def test_com_cstat_desconhecido_emitente_nao_vira_certificado():
    assert diagnosticar(999, "Rejeição: algo sobre o emitente")["categoria"] == "GENERICO"


def test_ncm_continua_no_bloco_de_produto():
    assert diagnosticar(778, "Rejeição: Informado NCM inexistente")["categoria"] == "PRODUTO"


def test_generico_mostra_a_mensagem_da_sefaz():
    d = diagnosticar(999, "Rejeição: regra nova")
    assert d["explicacao"] == "Rejeição: regra nova"
    assert d["rotulo"] == "cStat 999"


def test_ler_chave_da_mensagem():
    assert ler_chave_da_mensagem(MSG_539) == {
        "chave": "35260958348941000109550020000000041750446210",
        "mes": "09", "ano": "2026", "serie": 2, "numero": 4,
    }
    assert ler_chave_da_mensagem("Rejeição: qualquer") is None
    assert ler_chave_da_mensagem(None) is None


def _doc(status, cstat=None, msg=None):
    agora = datetime.now()
    return DocumentoFiscalRead(
        id=1, tipo_documento="NFE", origem_tipo="VENDA", status=status,
        codigo_status_sefaz=cstat, mensagem_sefaz=msg,
        data_criacao=agora, data_atualizacao=agora,
    )


@pytest.mark.parametrize("status", ["REJEITADA", "DENEGADA"])
def test_documento_rejeitado_ou_denegado_leva_o_diagnostico(status):
    corpo = _doc(status, 481, MSG_481).model_dump()
    assert corpo["diagnostico"]["categoria"] == "CONFIGURACAO"
    assert corpo["diagnostico"]["acao"] == {"tipo": "CONFIG_FISCAL", "label": "Abrir Dados da Empresa"}


@pytest.mark.parametrize("status", ["AUTORIZADA", "PROCESSANDO", "CANCELADA", "NAO_TRANSMITIDA"])
def test_outros_status_nao_tem_diagnostico(status):
    assert _doc(status, 100, "Autorizado o uso").model_dump()["diagnostico"] is None
