# ---------------------------------------------------------------------------
# ARQUIVO: services/cloud/cifra_backup.py
# DESCRICAO: Cifra a COPIA do backup que vai para a nuvem (LIC-01 §6.7,
#            ACORDO D-03 revista no conflito 3).
#
# Os backups LOCAIS nao mudam: o incremental, a limpeza, a verificacao e a
# restauracao em cadeia leem o manifest de dentro do ZIP, como sempre. So a
# copia que sai do computador e cifrada.
#
# A chave da cifra sai da CHAVE DE ATIVACAO da licenca. Ela e a mesma em todas
# as maquinas da licenca, entao um backup enviado pelo servidor antigo abre no
# computador novo depois do re-login. Quem nao tem a chave (por exemplo, quem
# conseguiu o arquivo direto do armazenamento da nuvem) nao abre.
#
# Formato do arquivo enviado:
#   b"SBKC1" (5 bytes) + nonce (12 bytes) + ZIP cifrado com AES-GCM
#   (o "tag" de 16 bytes, que prova que nada foi alterado, vai no fim).
# Um ZIP comum comeca com b"PK\x03\x04": e assim que o download sabe se o
# arquivo e cifrado ou e um backup antigo, sem precisar abrir nada.
# ---------------------------------------------------------------------------

import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# "StartBig Backup Cifrado", versao 1.
MARCA_CIFRADO = b"SBKC1"
_TAMANHO_NONCE = 12   # o AES-GCM usa um numero unico (nonce) de 12 bytes por cifra


def chave_do_backup(chave_ativacao: str) -> bytes:
    """Transforma a chave de ativacao numa chave AES-256 so para backup.

    HKDF e uma receita padrao para "derivar" chaves: a mesma entrada sempre da
    a mesma saida, e o rotulo `info` garante que esta chave nao serve para
    nenhum outro uso.
    """
    return HKDF(
        algorithm=hashes.SHA256(),       # funcao de resumo usada pelo HKDF
        length=32,                       # 32 bytes = AES-256
        salt=None,                       # sem sal: a chave precisa ser igual em todas as maquinas
        info=b"startbig-backup-v2",      # rotulo: separa esta chave de qualquer outra
    ).derive(chave_ativacao.encode("utf-8"))


def esta_cifrado(primeiros_bytes: bytes) -> bool:
    """True se o arquivo comeca com a marca de backup cifrado."""
    return primeiros_bytes.startswith(MARCA_CIFRADO)


def cifrar_para_nuvem(zip_bytes: bytes, chave_ativacao: str) -> bytes:
    """Cifra o ZIP inteiro e devolve marca + nonce + dados cifrados."""
    nonce = os.urandom(_TAMANHO_NONCE)        # sorteado a cada cifra (exigencia do AES-GCM)
    # A marca entra como "dado associado": nao e cifrada, mas e conferida na
    # hora de abrir, entao ninguem consegue troca-la sem a cifra perceber.
    cifrado = AESGCM(chave_do_backup(chave_ativacao)).encrypt(nonce, zip_bytes, MARCA_CIFRADO)
    return MARCA_CIFRADO + nonce + cifrado


def decifrar_da_nuvem(conteudo: bytes, chave_ativacao: str) -> bytes:
    """Abre um arquivo cifrado por `cifrar_para_nuvem` e devolve o ZIP.

    Se a chave nao confere (outra licenca) ou o arquivo foi alterado, o AES-GCM
    lanca `cryptography.exceptions.InvalidTag`; quem chama transforma isso em
    BACKUP_CHAVE_INVALIDA.
    """
    inicio_dados = len(MARCA_CIFRADO) + _TAMANHO_NONCE
    nonce = conteudo[len(MARCA_CIFRADO):inicio_dados]
    cifrado = conteudo[inicio_dados:]
    return AESGCM(chave_do_backup(chave_ativacao)).decrypt(nonce, cifrado, MARCA_CIFRADO)
