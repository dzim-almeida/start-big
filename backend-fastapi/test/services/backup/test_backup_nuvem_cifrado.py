# ---------------------------------------------------------------------------
# ARQUIVO: test/services/backup/test_backup_nuvem_cifrado.py
# DESCRICAO: LIC-01 (CT-12 a CT-16) -- o snapshot do backup sai sem o token, e
#            a copia que vai para a nuvem sai cifrada com a chave de ativacao.
#
# A rede e o disco do backup sao simulados: o que interessa aqui e o que sai
# do computador (envio) e o que e salvo (download).
# ---------------------------------------------------------------------------

import asyncio
import importlib
import io
import sqlite3
import zipfile
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.db.models.configuracao_licenca import ConfiguracaoLicenca
from app.schemas.backup.operacoes import BackupInfo, FlowDecision
from app.services import backup as backup_service
from app.services.backup import _utils as backup_utils
from app.services.cloud import cifra_backup
from app.services.cloud import download as cloud_download
# O pacote `cloud` reexporta a FUNCAO sync com o mesmo nome do modulo; o
# import_module pega o MODULO, onde os testes trocam as funcoes de rede.
cloud_sync = importlib.import_module("app.services.cloud.sync")
from app.services.licenca import segredos_licenca
from app.services.licenca.cripto import encriptar_valor

HWID = "HWID-DO-SERVIDOR"
CHAVE = "CHAVE-ATIVACAO-DO-CLIENTE"
TOKEN = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJ4In0.assinatura"
AGORA = datetime.now(timezone.utc)


# ===========================================================================
# Apoio
# ===========================================================================

def _zip_de_backup() -> bytes:
    """Um ZIP pequeno, no formato dos backups locais (banco + manifest)."""
    memoria = io.BytesIO()
    with zipfile.ZipFile(memoria, "w") as z:
        z.writestr("start_big.db", b"dados-da-loja")
        z.writestr("manifest.json", b'{"arquivos": {}}')
    return memoria.getvalue()


def _licenca_no_banco(db) -> None:
    """Licenca ja migrada para o cofre (o estado depois da LIC-01)."""
    db.add(ConfiguracaoLicenca(
        cliente_id="cliente-abc",
        hwid=HWID,
        licenca_id="lic-abc",
        chave_ativacao=segredos_licenca.guardar_chave_ativacao(CHAVE),
        public_key=encriptar_valor("PEM-FALSO", HWID),
        limite=3,
        data_vencimento=AGORA + timedelta(days=30),
        token=segredos_licenca.guardar_token(TOKEN),
        ultima_sinc=AGORA,
        grace_period=7,
        proxima_validacao=AGORA + timedelta(days=1),
    ))
    db.commit()


# ===========================================================================
# CT-12: snapshot sem token
# ===========================================================================

def test_ct12_snapshot_sai_sem_token_e_o_banco_real_nao_muda(tmp_path, monkeypatch):
    banco_real = tmp_path / "start_big.db"
    snapshot = tmp_path / "snapshot.db"
    conexao = sqlite3.connect(banco_real)
    # Mesma restricao do model: a coluna token e NOT NULL no banco de verdade.
    conexao.execute("CREATE TABLE configuracoes_licenca (id INTEGER PRIMARY KEY, token TEXT NOT NULL)")
    conexao.execute("INSERT INTO configuracoes_licenca (id, token) VALUES (1, 'dpapi:v1:abc')")
    conexao.commit()
    conexao.close()
    monkeypatch.setattr(backup_utils, "database_path", str(banco_real))

    backup_utils._create_snapshot_db(str(snapshot))

    def _token(caminho):
        c = sqlite3.connect(caminho)
        try:
            return c.execute("SELECT token FROM configuracoes_licenca").fetchone()[0]
        finally:
            c.close()

    assert _token(snapshot) == ""                   # o snapshot (que vira backup) nao leva o token
    assert _token(banco_real) == "dpapi:v1:abc"     # o banco da loja nao foi tocado


def test_snapshot_de_banco_sem_tabela_de_licenca_nao_quebra(tmp_path, monkeypatch):
    banco_real = tmp_path / "start_big.db"
    sqlite3.connect(banco_real).close()             # banco vazio: loja antes do setup
    monkeypatch.setattr(backup_utils, "database_path", str(banco_real))

    backup_utils._create_snapshot_db(str(tmp_path / "snapshot.db"))   # nao pode lancar


# ===========================================================================
# CT-13: o que vai para a nuvem
# ===========================================================================

@pytest.fixture
def envio(db_session, tmp_path, monkeypatch):
    """Monta um ciclo de envio com a rede simulada; devolve o que foi enviado."""
    _licenca_no_banco(db_session)
    zip_local = _zip_de_backup()
    (tmp_path / "backup_full.zip").write_bytes(zip_local)
    capturado: dict = {}

    async def _status(db, metodo, url, payload=None):
        return SimpleNamespace(status_code=200, json=lambda: {"planoPermiteBackup": True})

    async def _url_upload(db, payload):
        capturado["pedido"] = payload
        return {"acao": "ENVIAR", "uploadId": "up-1", "url": "https://r2/x", "headers": {}}

    async def _put(url, headers, caminho):
        with open(caminho, "rb") as f:
            capturado["enviado"] = f.read()

    async def _confirmar(db, payload):
        capturado["confirmar"] = payload
        return {"confirmado": True}

    monkeypatch.setattr(cloud_sync, "_request", _status)
    monkeypatch.setattr(cloud_sync, "flow", lambda *a: FlowDecision(
        action="upload", backup_type="full", cycle="2026-W47", force_full_local=False))
    monkeypatch.setattr(cloud_sync, "get_url_upload", _url_upload)
    monkeypatch.setattr(cloud_sync, "send_zip_to_cloud", _put)
    monkeypatch.setattr(cloud_sync, "confirm_upload", _confirmar)
    monkeypatch.setattr(cloud_sync.journal, "update_journal_entry", lambda *a, **k: {})
    monkeypatch.setattr(cloud_sync.journal, "code_content", lambda m: "codigo-do-manifest")
    monkeypatch.setattr(backup_service, "LOCAL_BACKUP", str(tmp_path))
    monkeypatch.setattr(backup_service, "get_last_backup", lambda: BackupInfo(
        arquivo="backup_full.zip", criado_em=AGORA.isoformat(),
        tamanho_bytes=len(zip_local), completo=True))
    monkeypatch.setattr(backup_service, "load_manifest", lambda caminho: {"arquivos": {}})
    import app.core.hwid as hwid_mod
    monkeypatch.setattr(hwid_mod, "obter_hwid", lambda: HWID)
    capturado["zip_local"] = zip_local
    return capturado


def test_ct13_copia_para_nuvem_sai_cifrada_sem_token(db_session, envio):
    resposta = asyncio.run(cloud_sync.sync(db_session))

    enviado = envio["enviado"]
    assert resposta.status == "success"
    assert enviado.startswith(b"SBKC1")                       # marca de cifrado
    assert b"eyJ" not in enviado                              # nenhum JWT a vista
    assert TOKEN.encode() not in enviado
    assert b"dados-da-loja" not in enviado                    # o conteudo nao vai em claro
    assert envio["pedido"]["tamanhoBytes"] == len(enviado)    # o tamanho e o da copia cifrada
    assert envio["confirmar"]["tamanhoBytes"] == len(enviado)
    assert envio["pedido"]["codigoConteudo"] == "codigo-do-manifest"
    assert cifra_backup.decifrar_da_nuvem(enviado, CHAVE) == envio["zip_local"]


def test_envio_com_chave_que_nao_abre_nao_manda_nada(db_session, envio):
    from test.apoio import cofre_falso
    cofre_falso.maquina = "outro-computador"     # banco copiado: a chave nao abre aqui

    resposta = asyncio.run(cloud_sync.sync(db_session))

    assert resposta.status == "error"
    assert "pedido" not in envio and "enviado" not in envio    # nem pediu URL, nem enviou


# ===========================================================================
# CT-14 a CT-16: download
# ===========================================================================

@pytest.fixture
def download(db_session, monkeypatch):
    """Simula a nuvem devolvendo `arquivos`; devolve o que foi salvo/restaurado."""
    _licenca_no_banco(db_session)
    registro: dict = {"salvos": [], "restaurado": None, "arquivos": []}

    async def _plano(db, ciclo):
        lista = [{"url": f"https://r2/{i}", "chave": f"b/{i}.zip"} for i in range(len(registro["arquivos"]))]
        return SimpleNamespace(status="ok", plan={"arquivos": lista, "ciclo": ciclo}, details=None)

    class _Cliente:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url):
            indice = int(url.rsplit("/", 1)[1])
            return SimpleNamespace(status_code=200, content=registro["arquivos"][indice])

    monkeypatch.setattr(cloud_download, "get_cloud_plan", _plano)
    monkeypatch.setattr(cloud_download, "_client", lambda timeout: _Cliente())
    monkeypatch.setattr(backup_service, "save_backup",
                        lambda ciclo, nome, conteudo: registro["salvos"].append((nome, conteudo)))
    monkeypatch.setattr(backup_service, "restore_from_chain",
                        lambda ciclo, arquivos: registro.__setitem__("restaurado", arquivos))
    import app.core.hwid as hwid_mod
    monkeypatch.setattr(hwid_mod, "obter_hwid", lambda: HWID)
    return registro


def test_ct14_download_cifrado_com_a_chave_certa_salva_o_zip_e_restaura(db_session, download):
    zip_original = _zip_de_backup()
    download["arquivos"] = [cifra_backup.cifrar_para_nuvem(zip_original, CHAVE)]

    resposta = asyncio.run(cloud_download.download_chain(db_session, "2026-W47"))

    assert resposta.status == "success"
    assert download["salvos"] == [("0.zip", zip_original)]   # salvo ja decifrado
    assert download["restaurado"] == ["0.zip"]


def test_ct15_download_cifrado_com_outra_chave_responde_422_e_nao_salva(db_session, download):
    zip_original = _zip_de_backup()
    download["arquivos"] = [
        _zip_de_backup(),                                          # um antigo, valido
        cifra_backup.cifrar_para_nuvem(zip_original, "CHAVE-DE-OUTRA-LICENCA"),
    ]

    with pytest.raises(HTTPException) as erro:
        asyncio.run(cloud_download.download_chain(db_session, "2026-W47"))

    assert erro.value.status_code == 422
    assert erro.value.detail["codigo"] == "BACKUP_CHAVE_INVALIDA"
    assert download["salvos"] == []            # nada salvo, nem o primeiro da cadeia
    assert download["restaurado"] is None


def test_ct16_download_de_zip_antigo_salva_como_antes(db_session, download):
    zip_antigo = _zip_de_backup()
    assert zip_antigo.startswith(b"PK")
    download["arquivos"] = [zip_antigo]

    resposta = asyncio.run(cloud_download.download_chain(db_session, "2026-W47"))

    assert resposta.status == "success"
    assert download["salvos"] == [("0.zip", zip_antigo)]


# ===========================================================================
# A cifra em si
# ===========================================================================

def test_cifra_e_decifra_com_a_mesma_chave_em_qualquer_maquina():
    zip_original = _zip_de_backup()

    cifrado = cifra_backup.cifrar_para_nuvem(zip_original, CHAVE)

    assert cifra_backup.esta_cifrado(cifrado[:5])
    assert not cifra_backup.esta_cifrado(zip_original[:5])
    # A chave do backup depende so da chave de ativacao, nunca da maquina.
    assert cifra_backup.decifrar_da_nuvem(cifrado, CHAVE) == zip_original
