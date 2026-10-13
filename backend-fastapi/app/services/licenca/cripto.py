# ---------------------------------------------------------------------------
# ARQUIVO: services/licenca/cripto.py
# DESCRICAO: Licenca - criptografia AES-256-GCM com chave derivada do HWID.
# ---------------------------------------------------------------------------

import base64
import hashlib
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# ===========================================================================
# Criptografia AES-256-GCM
# ===========================================================================

def _derivar_chave(hwid: str) -> bytes:
    """
    Deriva uma chave AES-256 (32 bytes) a partir do HWID usando SHA-256.
    Determinístico: mesmo HWID sempre gera a mesma chave.
    """
    return hashlib.sha256(hwid.encode("utf-8")).digest()


def encriptar_valor(valor: str, hwid: str) -> str:
    """
    Encripta um valor usando AES-256-GCM com chave derivada do HWID.
    Retorna: base64(nonce + ciphertext + tag)
    """
    chave = _derivar_chave(hwid)
    aesgcm = AESGCM(chave)
    nonce = os.urandom(12)  # 96-bit nonce para GCM
    ciphertext = aesgcm.encrypt(nonce, valor.encode("utf-8"), None)
    # nonce (12 bytes) + ciphertext (inclui tag de 16 bytes)
    return base64.b64encode(nonce + ciphertext).decode("utf-8")


def decriptar_valor(valor_encriptado: str, hwid: str) -> str:
    """
    Decripta um valor previamente encriptado com encriptar_valor.
    """
    chave = _derivar_chave(hwid)
    dados = base64.b64decode(valor_encriptado)
    nonce = dados[:12]
    ciphertext = dados[12:]
    aesgcm = AESGCM(chave)
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")
