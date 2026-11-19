# ---------------------------------------------------------------------------
# ARQUIVO: services/licenca/cofre.py
# DESCRICAO: Licenca - guarda e le segredos pela DPAPI do Windows, no escopo
#            da MAQUINA (ADR-001, ACORDO D-02, D-25, D-26).
#
# O que e a DPAPI: um "cofre" que o proprio Windows oferece. Voce entrega bytes,
# ele devolve os mesmos bytes cifrados; so o Windows consegue abrir de novo.
#
# Por que escopo de MAQUINA (e nao de usuario): o backend da loja roda com duas
# contas sobre o mesmo banco -- a tarefa StartBigServer (SYSTEM) e o sidecar de
# reserva (o usuario logado). No escopo de usuario, uma conta nao abriria o que
# a outra gravou. No de maquina, qualquer conta DESTE computador abre, e nenhum
# OUTRO computador abre: e exatamente o que protege uma copia do banco.
#
# Este arquivo NAO tem "modo de teste" e nao le variavel de ambiente (D-26).
# A tarefa do Windows nao recebe APP_ENV, entao uma regra pelo ambiente ligaria
# a cifra fraca na loja. Os testes trocam estas funcoes por um cofre falso que
# mora na pasta test/apoio/ e por isso nunca entra no .exe.
# ---------------------------------------------------------------------------

import ctypes                      # biblioteca para chamar funcoes de DLLs do Windows
import sys                         # para saber em qual sistema operacional estamos
from ctypes import wintypes        # tipos que o Windows usa (inteiros, ponteiros)

# 0x4 = CRYPTPROTECT_LOCAL_MACHINE: a chave do cofre e do computador, nao do usuario.
CRYPTPROTECT_LOCAL_MACHINE = 0x4


class CofreIndisponivel(Exception):
    """A DPAPI nao pode ser usada (o sistema nao e Windows, ou o Windows recusou)."""


class SegredoIlegivel(Exception):
    """O valor guardado nao abre neste computador (foi gravado em outro)."""


class _DataBlob(ctypes.Structure):
    """Estrutura que a DPAPI usa para receber e devolver bytes."""
    _fields_ = [("cbData", wintypes.DWORD),                 # quantos bytes existem
                ("pbData", ctypes.POINTER(ctypes.c_byte))]  # endereco onde os bytes estao


def _blob_de(dados: bytes) -> tuple[_DataBlob, ctypes.Array]:
    """Monta o blob de entrada a partir dos bytes do Python.

    Devolve tambem o buffer: enquanto alguem guarda uma referencia a ele, o
    Python nao libera a memoria antes de a DPAPI terminar de ler.
    """
    buffer = ctypes.create_string_buffer(dados, len(dados))
    blob = _DataBlob(len(dados), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
    return blob, buffer


def _ler_e_liberar(saida: _DataBlob) -> bytes:
    """Copia os bytes que a DPAPI devolveu e devolve a memoria ao Windows.

    A DPAPI aloca a memoria da saida por conta propria. Se nao chamarmos o
    LocalFree, cada chamada deixa um pedaco de memoria perdido (vazamento).
    """
    try:
        return ctypes.string_at(saida.pbData, saida.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(saida.pbData)


def proteger(dados: bytes) -> bytes:
    """Cifra os bytes. Depois disso, so este computador consegue abri-los."""
    # Fora do Windows a DPAPI nao existe: quem chamou decide o que fazer.
    if sys.platform != "win32":
        raise CofreIndisponivel("A DPAPI so existe no Windows.")
    entrada, _buffer = _blob_de(dados)   # _buffer fica vivo ate o fim da funcao
    saida = _DataBlob()                  # a DPAPI preenche este blob com o resultado
    ok = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(entrada),            # bytes a cifrar
        None,                             # descricao (nao usamos)
        None,                             # entropia extra (nao usamos)
        None, None,                       # reservado e janela de aviso (nao usamos)
        CRYPTPROTECT_LOCAL_MACHINE,       # escopo de maquina (D-25)
        ctypes.byref(saida),              # onde o Windows escreve o resultado
    )
    if not ok:
        raise CofreIndisponivel("O Windows recusou a cifra.")
    return _ler_e_liberar(saida)


def desproteger(dados: bytes) -> bytes:
    """Abre os bytes. Falha se eles foram cifrados em outro computador."""
    if sys.platform != "win32":
        raise CofreIndisponivel("A DPAPI so existe no Windows.")
    entrada, _buffer = _blob_de(dados)
    saida = _DataBlob()
    ok = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(entrada), None, None, None, None, 0, ctypes.byref(saida))
    if not ok:
        # O caso tipico: o banco foi copiado de outro computador.
        raise SegredoIlegivel("Este valor nao abre neste computador.")
    return _ler_e_liberar(saida)
