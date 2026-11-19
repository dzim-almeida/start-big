# ---------------------------------------------------------------------------
# ARQUIVO: test/services/licenca/test_token_offline.py
# DESCRICAO: LIC-02 (CT-01 a CT-12, CT-17 e CT-18) -- o app confia so no que a
#            API assinou: claims do token, identidade, chave publica e os dias.
#
# Os tokens aqui sao assinados DE VERDADE (RS256) com um par de chaves gerado
# no proprio teste, como a API faz com a chave privada dela. Assim a
# conferencia de assinatura tambem e exercitada.
# ---------------------------------------------------------------------------

from datetime import datetime, timedelta, timezone

import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from jose import jwt

from app.db.models.configuracao_licenca import ConfiguracaoLicenca
from app.services.licenca import cadastro
from app.services.licenca import segredos_licenca
from app.services.licenca import validacao as licenca_validacao
from app.services.licenca.cripto import encriptar_valor

HWID = "HWID-DESTE-COMPUTADOR"
CHAVE = "CHAVE-ATIVACAO-DO-CLIENTE"
LICENCA_ID = "lic-abc"
AGORA = datetime.now(timezone.utc)


# ===========================================================================
# Par de chaves RSA (o da API, simulado)
# ===========================================================================

def _gerar_par_de_chaves() -> tuple[str, str]:
    """Gera (chave privada, chave publica) em PEM, como a API tem."""
    privada = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem_privada = privada.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    pem_publica = privada.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return pem_privada, pem_publica


PRIVADA, PUBLICA = _gerar_par_de_chaves()


def _token(**mudancas) -> str:
    """Token assinado com as claims que a API manda; `mudancas` troca algumas."""
    claims = {
        "licencaId": LICENCA_ID,
        "hwid": HWID,
        "dataVencimento": (AGORA + timedelta(days=30)).isoformat().replace("+00:00", "Z"),
        "gracePeriodDias": 7,
        "proximaValidacaoEm": (AGORA + timedelta(days=5)).isoformat().replace("+00:00", "Z"),
        "emCarencia": False,
        "dataLimiteCarencia": None,
        "modulos": ["NFE"],
        "exp": int((AGORA + timedelta(days=7)).timestamp()),
    }
    claims.update(mudancas)
    claims = {k: v for k, v in claims.items() if v is not _SEM}   # _SEM tira a claim
    return jwt.encode(claims, PRIVADA, algorithm="RS256")


_SEM = object()   # marcador: "esta claim nao vem no token"


def _licenca(token: str, **colunas) -> ConfiguracaoLicenca:
    """Licenca local (sem banco) com o token trancado no cofre (LIC-01)."""
    dados = dict(
        cliente_id="cliente-abc",
        hwid=HWID,
        licenca_id=LICENCA_ID,
        chave_ativacao=segredos_licenca.guardar_chave_ativacao(CHAVE),
        public_key=encriptar_valor(PUBLICA, HWID),
        limite=3,
        data_vencimento=AGORA + timedelta(days=30),
        token=segredos_licenca.guardar_token(token),
        ultima_sinc=AGORA,
        grace_period=7,
        proxima_validacao=AGORA + timedelta(days=5),
    )
    dados.update(colunas)
    return ConfiguracaoLicenca(**dados)


def _offline(licenca: ConfiguracaoLicenca) -> dict:
    return licenca_validacao._validar_offline(licenca, PUBLICA, HWID)


def _codigo(erro) -> str:
    return erro.value.detail["codigo"]


# ===========================================================================
# CT-01 a CT-03: identidade do token (D-15)
# ===========================================================================

def test_ct01_token_de_outra_licenca_e_recusado():
    with pytest.raises(HTTPException) as erro:
        _offline(_licenca(_token(licencaId="lic-de-outra-loja")))

    assert _codigo(erro) == "TOKEN_DE_OUTRA_LICENCA"


def test_ct02_token_de_outra_maquina_e_recusado():
    with pytest.raises(HTTPException) as erro:
        _offline(_licenca(_token(hwid="HWID-DE-OUTRO-COMPUTADOR")))

    assert _codigo(erro) == "TOKEN_DE_OUTRA_LICENCA"


def test_ct03_token_com_hwid_nulo_e_aceito_se_a_licenca_confere():
    resultado = _offline(_licenca(_token(hwid=None)))

    assert resultado["status"] == "offline_valid"


# ===========================================================================
# CT-04, CT-05 e CT-18: carencia e vencimento saem do token (D-13)
# ===========================================================================

def test_ct04_carencia_do_token_vale_mesmo_com_as_colunas_vazias():
    token = _token(
        dataVencimento=(AGORA - timedelta(days=2)).isoformat(),
        emCarencia=True,
        dataLimiteCarencia=(AGORA + timedelta(days=5)).isoformat(),
    )

    resultado = _offline(_licenca(token, em_carencia=None, data_limite_carencia=None))

    assert resultado["status"] == "offline_valid"
    assert resultado["em_carencia"] is True


def test_ct05_carencia_sem_data_limite_nao_vale():
    token = _token(
        dataVencimento=(AGORA - timedelta(days=2)).isoformat(),
        emCarencia=True,
        dataLimiteCarencia=None,
    )

    with pytest.raises(HTTPException) as erro:
        _offline(_licenca(token))

    assert _codigo(erro) == "LICENCA_EXPIRADA"


def test_ct18_coluna_editada_para_o_futuro_nao_engana_a_claim_vencida():
    token = _token(dataVencimento=(AGORA - timedelta(days=1)).isoformat())
    licenca = _licenca(token, data_vencimento=AGORA + timedelta(days=365))   # coluna "editada"

    with pytest.raises(HTTPException) as erro:
        _offline(licenca)

    assert _codigo(erro) == "LICENCA_EXPIRADA"


def test_ct18b_coluna_carencia_editada_nao_cria_carencia():
    """Colunas de carencia preenchidas a mao nao valem: so o token decide."""
    token = _token(dataVencimento=(AGORA - timedelta(days=1)).isoformat())
    licenca = _licenca(token, em_carencia=True, data_limite_carencia=AGORA + timedelta(days=30))

    with pytest.raises(HTTPException) as erro:
        _offline(licenca)

    assert _codigo(erro) == "LICENCA_EXPIRADA"


# ===========================================================================
# CT-08 e CT-09: validade do token e prazo offline
# ===========================================================================

def test_ct08_token_vencido_e_recusado_offline():
    token = _token(exp=int((AGORA - timedelta(minutes=1)).timestamp()))

    with pytest.raises(HTTPException) as erro:
        _offline(_licenca(token))

    assert _codigo(erro) == "REQUISITA_CONEXAO_INTERNET"


def test_token_com_assinatura_falsa_e_recusado():
    outra_privada, _ = _gerar_par_de_chaves()
    falso = jwt.encode({"licencaId": LICENCA_ID}, outra_privada, algorithm="RS256")

    with pytest.raises(HTTPException) as erro:
        _offline(_licenca(falso))

    assert _codigo(erro) == "REQUISITA_CONEXAO_INTERNET"


def test_ct09_prazo_offline_do_token_estourado_exige_internet():
    licenca = _licenca(_token(gracePeriodDias=3), ultima_sinc=AGORA - timedelta(days=4))

    with pytest.raises(HTTPException) as erro:
        _offline(licenca)

    assert _codigo(erro) == "REQUISITA_CONEXAO_INTERNET"


def test_offline_marca_os_dias_como_estimativa():
    resultado = _offline(_licenca(_token()))

    assert resultado["estimativa"] is True
    assert "aviso" not in resultado


def test_offline_com_relogio_recuado_avisa_e_segue():
    licenca = _licenca(_token(), ultimo_horario_visto=AGORA + timedelta(hours=2))

    resultado = _offline(licenca)

    assert resultado["status"] == "offline_valid"
    assert resultado["aviso"] == "relogio_recuou"


# ===========================================================================
# Caminho COM internet: CT-06, CT-07, CT-10 a CT-12, CT-17
# ===========================================================================

class _Resposta:
    def __init__(self, status_code: int, corpo: dict):
        self.status_code = status_code
        self._corpo = corpo
        self.text = str(corpo)

    def json(self):
        return self._corpo


def _resposta_conectar(token: str, **extra) -> _Resposta:
    corpo = {
        "msg": "Conexão autorizada.",
        "licencaId": LICENCA_ID,
        "limite": 3,
        "dataVencimento": (AGORA + timedelta(days=30)).isoformat(),
        "token": token,
        "ultimaSincronizacao": AGORA.isoformat(),
        "gracePeriodDias": 7,
        "proximaValidacaoEm": (AGORA + timedelta(days=5)).isoformat(),
    }
    corpo.update(extra)
    return _Resposta(201, corpo)


def _nuvem(monkeypatch, resposta: _Resposta) -> None:
    """Finge o POST /licenca/conectar devolvendo `resposta`."""

    class _Cliente:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, json=None, **kwargs):
            return resposta

    monkeypatch.setattr(httpx, "Client", _Cliente)
    monkeypatch.setattr(licenca_validacao, "obter_hwid", lambda: HWID)


@pytest.fixture
def banco_com_licenca(db_session):
    """Licenca gravada no banco de teste, com a chave publica ILEGIVEL."""
    licenca = _licenca(_token(), public_key="lixo-que-nao-decifra")
    db_session.add(licenca)
    db_session.commit()
    return db_session


def test_ct06_chave_publica_ilegivel_com_internet_e_resgatada(banco_com_licenca, monkeypatch):
    _nuvem(monkeypatch, _resposta_conectar(_token(modulos=["NFE", "NFSE"])))
    resgates = []

    def _buscar_na_api():
        resgates.append(True)
        return PUBLICA

    # Usa o resgate de verdade (que grava a chave boa no banco); so a busca
    # HTTP da chave publica e simulada.
    monkeypatch.setattr(cadastro, "_buscar_chave_publica_online", _buscar_na_api)

    resultado = licenca_validacao.verificar_licenca_ativa(banco_com_licenca)

    assert resgates == [True]
    assert resultado["modulos"] == ["NFE", "NFSE"]     # lidos com a chave resgatada
    banco_com_licenca.expire_all()
    licenca = banco_com_licenca.query(ConfiguracaoLicenca).one()
    assert licenca_validacao._decifrar_public_key(licenca, HWID) == PUBLICA


def test_ct07_chave_publica_ilegivel_e_resgate_falha_da_chave_corrompida(banco_com_licenca, monkeypatch):
    _nuvem(monkeypatch, _resposta_conectar(_token()))

    def _falha(*args, **kwargs):
        raise httpx.ConnectError("API da chave fora do ar")

    monkeypatch.setattr(licenca_validacao, "resgatar_chave_publica_online", _falha)

    with pytest.raises(HTTPException) as erro:
        licenca_validacao.verificar_licenca_ativa(banco_com_licenca)

    assert _codigo(erro) == "CHAVE_CORROMPIDA"


@pytest.fixture
def banco_com_chave_boa(db_session):
    db_session.add(_licenca(_token()))
    db_session.commit()
    return db_session


def test_ct10_dias_restantes_vem_da_api_mesmo_com_o_relogio_errado(banco_com_chave_boa, monkeypatch):
    # O vencimento mandado da 30 dias pelo relogio local; a API diz 3.
    _nuvem(monkeypatch, _resposta_conectar(_token(), diasRestantes=3))

    resultado = licenca_validacao.verificar_licenca_ativa(banco_com_chave_boa)

    assert resultado["dias_restantes"] == 3
    assert resultado["estimativa"] is False


def test_api_sem_dias_restantes_calcula_e_marca_estimativa(banco_com_chave_boa, monkeypatch):
    _nuvem(monkeypatch, _resposta_conectar(_token()))

    resultado = licenca_validacao.verificar_licenca_ativa(banco_com_chave_boa)

    assert resultado["dias_restantes"] in (29, 30)
    assert resultado["estimativa"] is True


def test_ct11_recusa_sem_codigo_cai_na_leitura_do_texto(banco_com_chave_boa, monkeypatch):
    _nuvem(monkeypatch, _Resposta(400, {"message": "Licença vencida."}))

    with pytest.raises(HTTPException) as erro:
        licenca_validacao.verificar_licenca_ativa(banco_com_chave_boa)

    assert _codigo(erro) == "LICENCA_EXPIRADA"   # como antes: pelo texto


def test_recusa_402_licenca_vencida_vira_licenca_expirada(banco_com_chave_boa, monkeypatch):
    _nuvem(monkeypatch, _Resposta(402, {"codigo": "LICENCA_VENCIDA", "message": "Vencida"}))

    with pytest.raises(HTTPException) as erro:
        licenca_validacao.verificar_licenca_ativa(banco_com_chave_boa)

    assert _codigo(erro) == "LICENCA_EXPIRADA"


def test_ct12_recusa_licenca_transferida_chega_com_esse_codigo(banco_com_chave_boa, monkeypatch):
    _nuvem(monkeypatch, _Resposta(400, {
        "codigo": "LICENCA_TRANSFERIDA",
        "message": "Licença transferida para outro dispositivo.",
    }))

    with pytest.raises(HTTPException) as erro:
        licenca_validacao.verificar_licenca_ativa(banco_com_chave_boa)

    assert erro.value.status_code == 403
    assert _codigo(erro) == "LICENCA_TRANSFERIDA"


def test_ct17_token_valido_sem_a_claim_modulos_da_none():
    token = _token(modulos=_SEM)

    assert licenca_validacao.ler_modulos_liberados(token, PUBLICA) is None
