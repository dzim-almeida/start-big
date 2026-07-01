# ---------------------------------------------------------------------------
# ARQUIVO: app/core/hwid.py
# DESCRIÇÃO: Obtém o identificador único da máquina (HWID) de forma nativa.
#            No Windows, lê o MachineGuid do registro (compatível com machine-uid).
#            No Linux, lê /etc/machine-id.
# ---------------------------------------------------------------------------

import functools
import logging
import platform

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def obter_hwid() -> str:
    """
    Retorna o Hardware ID da máquina.

    - Windows: lê HKLM\\SOFTWARE\\Microsoft\\Cryptography\\MachineGuid
      (mesmo valor que o crate Rust `machine-uid` retornava).
    - Linux: lê /etc/machine-id.

    O resultado é cacheado (imutável durante o processo).

    Raises:
        RuntimeError: Se o SO não for suportado ou o HWID não puder ser lido.
    """
    sistema = platform.system()

    if sistema == "Windows":
        return _obter_hwid_windows()
    elif sistema == "Linux":
        return _obter_hwid_linux()

    raise RuntimeError(f"Sistema operacional '{sistema}' não suportado para leitura de HWID.")


def _obter_hwid_windows() -> str:
    """Lê o MachineGuid do registro do Windows."""
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
        ) as key:
            valor, _ = winreg.QueryValueEx(key, "MachineGuid")
            hwid = valor.strip()
            logger.debug("[hwid] MachineGuid obtido com sucesso.")
            return hwid
    except OSError as e:
        raise RuntimeError(f"Falha ao ler MachineGuid do registro Windows: {e}") from e


def _obter_hwid_linux() -> str:
    """Lê o machine-id do Linux."""
    try:
        with open("/etc/machine-id") as f:
            hwid = f.read().strip()
            logger.debug("[hwid] machine-id obtido com sucesso.")
            return hwid
    except OSError as e:
        raise RuntimeError(f"Falha ao ler /etc/machine-id: {e}") from e
