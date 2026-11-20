# ---------------------------------------------------------------------------
# ARQUIVO: core/permissoes.py
# DESCRICAO: Confere as permissoes da pasta de dados e AVISA no log quando ela
#            esta aberta demais (LIC-01 §6.8, ACORDO D-19 revista).
#
# A pasta padrao (%LOCALAPPDATA%\StartBigERP\data) fica no perfil do usuario,
# que o Windows ja restringe ao proprio usuario, a SYSTEM e aos administradores.
# Este arquivo so CONFERE e AVISA: nunca altera permissao nenhuma. Mudar a
# lista de acesso com o nome de quem esta rodando trancaria a outra conta do
# backend para fora (o servidor roda como SYSTEM e como o usuario; ver
# docs/_shared/learn/2026-11-18-backend-roda-com-duas-contas-windows.md).
#
# O aviso vai para o log com o codigo PASTA_DADOS_ABERTA. A LIC-08 o mostra
# no painel.
# ---------------------------------------------------------------------------

import logging
import os
import subprocess
import sys
from datetime import datetime

logger = logging.getLogger(__name__)

# Quando a verificação do startup achou a pasta aberta (None = não achou).
# Fica em memória para a tela de backup avisar (LIC-08, GET /backup/avisos).
_pasta_aberta_desde: datetime | None = None


def _marcar_pasta_aberta() -> None:
    """Guarda o horário em que a pasta foi vista aberta (só a primeira vez)."""
    global _pasta_aberta_desde
    if _pasta_aberta_desde is None:
        _pasta_aberta_desde = datetime.now()


def ler_aviso_pasta() -> datetime | None:
    """Desde quando a pasta de dados está aberta; None = sem aviso."""
    return _pasta_aberta_desde

# Grupos que NAO deveriam ter acesso a pasta dos dados da loja, pelo SID.
# O SID e o "numero de identidade" de uma conta ou grupo no Windows. Usamos o
# SID, e nao o nome, porque o nome muda com o idioma ("Todos" x "Everyone").
_SIDS_ABERTOS = {
    "S-1-1-0": "Todos",
    "S-1-5-32-545": "Usuários",
    "S-1-5-11": "Usuários autenticados",
}

# Script do PowerShell que lista o SID de cada conta com acesso a pasta.
# O caminho entra pela variavel de ambiente STARTBIG_PASTA, e nao no meio do
# texto do comando: assim um caminho com aspas ou simbolos nao vira comando.
_SCRIPT_LER_ACL = (
    "(Get-Acl -LiteralPath $env:STARTBIG_PASTA).Access | ForEach-Object { "
    "$_.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value }"
)

_SEM_JANELA = 0x08000000   # CREATE_NO_WINDOW: nao pisca uma janela preta na loja


def verificar_pasta_de_dados(caminho: str) -> None:
    """Confere a pasta de dados e registra PASTA_DADOS_ABERTA quando preciso.

    Nunca lanca erro e nunca altera nada: e chamada no startup, e o sistema
    precisa subir mesmo que a verificacao falhe.
    """
    # Fora do Windows (desenvolvimento, testes) nao ha lista de acesso a ler.
    if sys.platform != "win32":
        return

    try:
        sids = _ler_sids_com_acesso(caminho)
    except Exception as e:  # noqa: BLE001 - qualquer falha na leitura so vai para o log
        logger.warning("[permissoes] Nao foi possivel ler a lista de acesso da pasta de dados: %s", e)
        return

    abertos = sorted(nome for sid, nome in _SIDS_ABERTOS.items() if sid in sids)
    if abertos or not _esta_no_perfil(caminho):
        _marcar_pasta_aberta()   # a tela de backup mostra o aviso (LIC-08)
    if abertos:
        logger.warning(
            "[permissoes] PASTA_DADOS_ABERTA: a pasta de dados da loja da acesso a %s.",
            ", ".join(abertos),
        )
    if not _esta_no_perfil(caminho):
        logger.warning(
            "[permissoes] PASTA_DADOS_ABERTA: a pasta de dados fica fora do perfil do usuario."
        )


def _ler_sids_com_acesso(caminho: str) -> set[str]:
    """Pergunta ao PowerShell quem tem acesso a pasta e devolve os SIDs."""
    resultado = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", _SCRIPT_LER_ACL],
        capture_output=True,       # guarda a saida em vez de imprimir
        text=True,
        timeout=30,                # nunca deixa o startup esperando para sempre
        env={**os.environ, "STARTBIG_PASTA": caminho},
        creationflags=_SEM_JANELA,
    )
    if resultado.returncode != 0:
        raise OSError((resultado.stderr or "Get-Acl falhou").strip()[:200])
    # Uma linha por conta; linhas vazias sao descartadas.
    return {linha.strip() for linha in resultado.stdout.splitlines() if linha.strip()}


def _esta_no_perfil(caminho: str) -> bool:
    """True se a pasta fica dentro do perfil de algum usuario (C:\\Users\\<nome>).

    Olhamos a pasta dos perfis, e nao o perfil de quem esta rodando: como
    SYSTEM, o "perfil" e outro, mas a pasta de dados continua sendo a do
    usuario (o backend recebe --data-dir).
    """
    publico = os.environ.get("PUBLIC")   # ex.: C:\Users\Public
    if publico:
        raiz_perfis = os.path.dirname(publico)
    else:
        raiz_perfis = os.path.join(os.environ.get("SystemDrive", "C:") + os.sep, "Users")

    pasta = os.path.normcase(os.path.abspath(caminho))
    raiz = os.path.normcase(os.path.abspath(raiz_perfis))
    dentro_dos_perfis = pasta.startswith(raiz + os.sep)
    # A pasta "Public" fica em C:\Users, mas e de todos: nao conta como perfil.
    no_publico = bool(publico) and pasta.startswith(os.path.normcase(os.path.abspath(publico)))
    return dentro_dos_perfis and not no_publico
