# ---------------------------------------------------------------------------
# ARQUIVO: test_licenca_transferencia.py
# DESCRICAO: Troca de servidor -- transferir a licenca para o computador novo
#            e desativar no antigo.
#
#            O CASO REAL (19/10/2026): o servidor do escritorio passou para um
#            notebook. O start_big.db foi copiado para o AppData do notebook, o
#            sistema subiu e o erro de "banco copiado de outro PC" apareceu NO
#            LOGIN -- onde nao havia botao nenhum. A correcao de 17/10 so tinha
#            saida na tela de erro de licenca, que esse caminho nunca alcanca.
#
#            As invariantes:
#              1. Boot e login devolvem o MESMO codigo (LICENCA_DE_OUTRA_MAQUINA),
#                 para o frontend levar os dois a mesma tela.
#              2. A ativacao antiga so sai DEPOIS que a nuvem aprova o login.
#                 Senha errada, conta recusada, sem internet: nada muda.
#              3. Desativar exige a nuvem confirmar; sem ela, nada muda.
# ---------------------------------------------------------------------------

import asyncio
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi import HTTPException

from app.db.models.configuracao_licenca import ConfiguracaoLicenca
from app.db.models.terminal_conectado import TerminalConectado
from app.services import licenca as licenca_service
from app.services.licenca import cadastro as licenca_cadastro
from app.services.licenca import terminal as licenca_terminal
from app.services.licenca import transferencia
from app.services.licenca import validacao as licenca_validacao
from app.services.licenca import decriptar_valor, encriptar_valor


HWID_ANTIGO = "HWID-DO-SERVIDOR-QUE-SAIU"
HWID_NOVO = "HWID-DO-NOTEBOOK-NOVO"
CHAVE_DO_CLIENTE = "CHAVE-ATIVACAO-DO-CLIENTE"
AGORA = datetime.now(timezone.utc)


class _Resposta:
    def __init__(self, status_code: int, corpo=None):
        self.status_code = status_code
        self._corpo = corpo
        self.text = str(corpo)

    def json(self):
        return self._corpo


def _nuvem(monkeypatch, *, resposta: _Resposta | None = None, offline: bool = False):
    """Finge a nuvem: o POST de login devolve `resposta` (ou cai, se offline)."""
    chamadas: list[dict] = []

    class _Cliente:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, json=None, **kwargs):
            chamadas.append({"url": url, "json": json})
            if offline:
                raise httpx.ConnectError("sem internet")
            return resposta

    monkeypatch.setattr(httpx, "Client", _Cliente)
    monkeypatch.setattr(licenca_cadastro, "_buscar_chave_publica_online", lambda: "PEM-FALSO")
    return chamadas


def _login_aprovado(licenca_id: str = "lic-abc") -> _Resposta:
    return _Resposta(201, {
        "msg": "Conexão autorizada.",
        "licencaId": licenca_id,  # a MESMA licenca: e a mesma conta
        "chaveAtivacao": CHAVE_DO_CLIENTE,
        "limite": 3,
        "dataVencimento": (AGORA + timedelta(days=30)).isoformat(),
        "token": "token-novo",
        "ultimaSincronizacao": AGORA.isoformat(),
        "gracePeriodDias": 7,
        "proximaValidacaoEm": (AGORA + timedelta(days=1)).isoformat(),
    })


def _ativacao(hwid: str, token: str = "token-antigo") -> ConfiguracaoLicenca:
    return ConfiguracaoLicenca(
        cliente_id="cliente-abc",
        hwid=hwid,
        licenca_id="lic-abc",
        chave_ativacao=encriptar_valor(CHAVE_DO_CLIENTE, hwid),
        public_key=encriptar_valor("PEM-FALSO", hwid),
        limite=3,
        data_vencimento=AGORA + timedelta(days=30),
        token=token,
        ultima_sinc=AGORA,
        grace_period=7,
        proxima_validacao=AGORA + timedelta(days=1),
    )


def _estar_no(monkeypatch, hwid: str) -> None:
    """Roda o backend "neste" computador."""
    for modulo in (transferencia, licenca_terminal, licenca_validacao):
        monkeypatch.setattr(modulo, "obter_hwid", lambda: hwid)


@pytest.fixture
def banco_copiado(db_session, monkeypatch):
    """O banco que veio do servidor antigo, aberto no notebook novo."""
    db_session.add(_ativacao(HWID_ANTIGO))
    # Sessões do servidor antigo que vieram junto no arquivo.
    db_session.add(TerminalConectado(hwid=HWID_ANTIGO))
    db_session.add(TerminalConectado(hwid="HWID-CAIXA-01"))
    db_session.commit()
    _estar_no(monkeypatch, HWID_NOVO)
    return db_session


def _licencas(db):
    db.expire_all()
    return db.query(ConfiguracaoLicenca).all()


def _codigo(erro: pytest.ExceptionInfo) -> str:
    return erro.value.detail["codigo"]


# ===========================================================================
# 1. Um codigo so, nas duas portas
# ===========================================================================

def test_boot_com_banco_copiado_pede_transferencia(banco_copiado):
    with pytest.raises(HTTPException) as erro:
        licenca_service.verificar_licenca_ativa(banco_copiado)

    assert erro.value.status_code == 403
    assert _codigo(erro) == "LICENCA_DE_OUTRA_MAQUINA"


def test_login_com_banco_copiado_pede_a_mesma_transferencia(banco_copiado):
    """O caso de 19/10: o erro apareceu no LOGIN, nao no boot."""
    banco_copiado.query(TerminalConectado).delete()  # o boot limpa os terminais
    banco_copiado.commit()

    with pytest.raises(HTTPException) as erro:
        licenca_service.conectar_terminal(banco_copiado, HWID_NOVO)

    assert erro.value.status_code == 403
    assert _codigo(erro) == "LICENCA_DE_OUTRA_MAQUINA"


# ===========================================================================
# 2. Transferir
# ===========================================================================

def test_transferir_troca_a_ativacao_antiga_pela_deste_computador(banco_copiado, monkeypatch):
    chamadas = _nuvem(monkeypatch, resposta=_login_aprovado())

    licenca_service.transferir_para_esta_maquina(banco_copiado, "dono@loja.com", "senha-certa")
    banco_copiado.commit()

    licencas = _licencas(banco_copiado)
    assert len(licencas) == 1, "a ativacao do servidor antigo sobreviveu ao lado da nova"
    assert licencas[0].hwid == HWID_NOVO
    assert licencas[0].token == "token-novo"
    # A nuvem recebeu o HWID do computador NOVO.
    assert chamadas[0]["json"]["hwid"] == HWID_NOVO


def test_ativacao_transferida_decifra_e_destrava_o_boot(banco_copiado, monkeypatch):
    _nuvem(monkeypatch, resposta=_login_aprovado())
    licenca_service.transferir_para_esta_maquina(banco_copiado, "dono@loja.com", "senha-certa")
    banco_copiado.commit()

    licenca = _licencas(banco_copiado)[0]
    assert decriptar_valor(licenca.chave_ativacao, HWID_NOVO) == CHAVE_DO_CLIENTE
    assert transferencia.licenca_ativada_nesta_maquina(licenca, HWID_NOVO)


def test_transferir_descarta_as_sessoes_do_servidor_antigo(banco_copiado, monkeypatch):
    """Sessões copiadas contariam contra o limite de computadores do plano."""
    _nuvem(monkeypatch, resposta=_login_aprovado())
    licenca_service.transferir_para_esta_maquina(banco_copiado, "dono@loja.com", "senha-certa")
    banco_copiado.commit()

    assert banco_copiado.query(TerminalConectado).count() == 0


@pytest.mark.parametrize(
    "resposta, http_status, codigo",
    [
        (_Resposta(401, {"message": "E-mail ou senha incorretos."}), 401, "CREDENCIAIS_INVALIDAS"),
        (_Resposta(400, {"message": "Licença vencida."}), 403, "CONTA_RECUSADA"),
        (_Resposta(400, {"message": "Nenhuma licença ativa encontrada para este e-mail."}), 403, "CONTA_RECUSADA"),
        (_Resposta(502, {"message": "Bad gateway"}), 503, "NUVEM_INDISPONIVEL"),
        (_Resposta(201, {"msg": "ok"}), 502, "RESPOSTA_INVALIDA"),
    ],
)
def test_recusa_da_nuvem_nao_mexe_no_banco(banco_copiado, monkeypatch, resposta, http_status, codigo):
    _nuvem(monkeypatch, resposta=resposta)

    with pytest.raises(HTTPException) as erro:
        licenca_service.transferir_para_esta_maquina(banco_copiado, "dono@loja.com", "x")

    assert erro.value.status_code == http_status
    assert _codigo(erro) == codigo
    assert [l.hwid for l in _licencas(banco_copiado)] == [HWID_ANTIGO]
    assert banco_copiado.query(TerminalConectado).count() == 2


def test_recusa_por_vencimento_mostra_a_frase_da_nuvem(banco_copiado, monkeypatch):
    """Antes saia "Credenciais inválidas: Licença vencida." -- a pessoa ia
    redigitar a senha certa para sempre."""
    _nuvem(monkeypatch, resposta=_Resposta(400, {"message": "Licença vencida."}))

    with pytest.raises(HTTPException) as erro:
        licenca_service.transferir_para_esta_maquina(banco_copiado, "dono@loja.com", "senha-certa")

    assert erro.value.detail["mensagem"] == "Licença vencida."


def test_sem_internet_nao_mexe_no_banco(banco_copiado, monkeypatch):
    _nuvem(monkeypatch, offline=True)

    with pytest.raises(HTTPException) as erro:
        licenca_service.transferir_para_esta_maquina(banco_copiado, "dono@loja.com", "senha-certa")

    assert erro.value.status_code == 503
    assert _codigo(erro) == "SEM_CONEXAO"
    assert [l.hwid for l in _licencas(banco_copiado)] == [HWID_ANTIGO]


def test_transferir_no_proprio_computador_e_recusado_sem_chamar_a_nuvem(banco_copiado, monkeypatch):
    """Transferir para si mesmo derrubaria os caixas na nuvem a troco de nada."""
    _estar_no(monkeypatch, HWID_ANTIGO)
    chamadas = _nuvem(monkeypatch, resposta=_login_aprovado())

    with pytest.raises(HTTPException) as erro:
        licenca_service.transferir_para_esta_maquina(banco_copiado, "dono@loja.com", "senha-certa")

    assert erro.value.status_code == 409
    assert _codigo(erro) == "LICENCA_JA_ATIVADA"
    assert chamadas == []


# ===========================================================================
# Primeiro acesso (assistente) continua igual
# ===========================================================================

def test_reconectar_em_banco_sem_licenca_ativa_este_computador(db_session, monkeypatch):
    _estar_no(monkeypatch, HWID_NOVO)
    _nuvem(monkeypatch, resposta=_login_aprovado())

    licenca_service.reconnect_licenca(db_session, "dono@loja.com", "senha-certa")
    db_session.commit()

    assert [l.hwid for l in _licencas(db_session)] == [HWID_NOVO]


def test_reconectar_com_banco_copiado_tambem_transfere(banco_copiado, monkeypatch):
    """Muita gente chega pelo assistente depois de copiar o banco."""
    _nuvem(monkeypatch, resposta=_login_aprovado())

    licenca_service.reconnect_licenca(banco_copiado, "dono@loja.com", "senha-certa")
    banco_copiado.commit()

    assert [l.hwid for l in _licencas(banco_copiado)] == [HWID_NOVO]


def test_reconectar_com_licenca_deste_computador_continua_409(banco_copiado, monkeypatch):
    _estar_no(monkeypatch, HWID_ANTIGO)
    _nuvem(monkeypatch, resposta=_login_aprovado())

    with pytest.raises(HTTPException) as erro:
        licenca_service.reconnect_licenca(banco_copiado, "dono@loja.com", "senha-certa")

    assert erro.value.status_code == 409
    assert [l.token for l in _licencas(banco_copiado)] == ["token-antigo"]


# ===========================================================================
# 3. Desativar no servidor que vai sair
# ===========================================================================

def _nuvem_assincrona(monkeypatch, *, status_code: int = 201, offline: bool = False):
    chamadas: list[dict] = []

    class _ClienteAsync:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, json=None, **kwargs):
            chamadas.append({"url": url, "json": json})
            if offline:
                raise httpx.ConnectError("sem internet")
            return _Resposta(status_code, {"msg": "Desconectado."})

    monkeypatch.setattr(httpx, "AsyncClient", _ClienteAsync)
    return chamadas


@pytest.fixture
def servidor_antigo(db_session, monkeypatch):
    """O servidor que vai sair, ainda com a própria licença e um caixa."""
    db_session.add(_ativacao(HWID_ANTIGO))
    db_session.add(TerminalConectado(hwid="HWID-CAIXA-01"))
    db_session.commit()
    _estar_no(monkeypatch, HWID_ANTIGO)
    return db_session


def test_desativar_libera_as_vagas_na_nuvem_e_apaga_a_ativacao(servidor_antigo, monkeypatch):
    chamadas = _nuvem_assincrona(monkeypatch)

    asyncio.run(licenca_service.desativar_esta_maquina(servidor_antigo, HWID_ANTIGO))

    assert _licencas(servidor_antigo) == []
    assert servidor_antigo.query(TerminalConectado).count() == 0
    liberados = {c["json"]["hwid"] for c in chamadas}
    assert liberados == {HWID_ANTIGO, "HWID-CAIXA-01"}
    assert all(c["json"]["chave"] == CHAVE_DO_CLIENTE for c in chamadas)


def test_desativar_sem_internet_nao_mexe_em_nada(servidor_antigo, monkeypatch):
    _nuvem_assincrona(monkeypatch, offline=True)

    with pytest.raises(HTTPException) as erro:
        asyncio.run(licenca_service.desativar_esta_maquina(servidor_antigo, HWID_ANTIGO))

    assert _codigo(erro) == "SEM_CONEXAO"
    assert [l.hwid for l in _licencas(servidor_antigo)] == [HWID_ANTIGO]


def test_desativar_com_recusa_da_nuvem_nao_mexe_em_nada(servidor_antigo, monkeypatch):
    _nuvem_assincrona(monkeypatch, status_code=500)

    with pytest.raises(HTTPException):
        asyncio.run(licenca_service.desativar_esta_maquina(servidor_antigo, HWID_ANTIGO))

    assert [l.hwid for l in _licencas(servidor_antigo)] == [HWID_ANTIGO]


def test_caixa_nao_desativa_a_licenca_do_servidor(servidor_antigo, monkeypatch):
    chamadas = _nuvem_assincrona(monkeypatch)

    with pytest.raises(HTTPException) as erro:
        asyncio.run(licenca_service.desativar_esta_maquina(servidor_antigo, "HWID-CAIXA-01"))

    assert erro.value.status_code == 403
    assert _codigo(erro) == "SOMENTE_NO_SERVIDOR"
    assert chamadas == []
    assert [l.hwid for l in _licencas(servidor_antigo)] == [HWID_ANTIGO]


# ===========================================================================
# Situacao (Configuracoes › Licenca)
# ===========================================================================

def test_situacao_diz_se_a_licenca_e_deste_computador(banco_copiado, monkeypatch):
    assert licenca_service.situacao_desta_maquina(banco_copiado)["ativada_nesta_maquina"] is False

    _estar_no(monkeypatch, HWID_ANTIGO)
    situacao = licenca_service.situacao_desta_maquina(banco_copiado)
    assert situacao["ativada_nesta_maquina"] is True
    assert situacao["limite_computadores"] == 3
    assert HWID_ANTIGO not in situacao["computador"], "o HWID inteiro não sai na tela"


# ===========================================================================
# Rota
# ===========================================================================

def test_rota_transferir_responde_sem_login(client, banco_copiado, monkeypatch):
    _nuvem(monkeypatch, resposta=_login_aprovado())

    resposta = client.post(
        "/api/v1/licenca/transferir",
        json={"email": "dono@loja.com", "senha": "senha-certa"},
    )

    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["transferida"] is True
    assert [l.hwid for l in _licencas(banco_copiado)] == [HWID_NOVO]
