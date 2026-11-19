# ---------------------------------------------------------------------------
# ARQUIVO: test/apoio/cofre_falso.py
# DESCRICAO: Cofre FALSO, usado so nos testes no lugar da DPAPI (ACORDO D-26).
#
# Por que existe: a DPAPI so existe no Windows, e os testes rodam em qualquer
# sistema. Este arquivo imita o comportamento que importa do cofre de verdade:
#   - o que foi trancado "nesta maquina" abre de novo;
#   - o que foi trancado em OUTRA maquina nao abre (SegredoIlegivel);
#   - o Windows pode recusar a operacao (CofreIndisponivel).
#
# Ele mora em test/, fora de app/: o PyInstaller empacota so o app/, entao
# este codigo NUNCA entra no .exe da loja (o CT-11 confere isso).
#
# NAO e criptografia de verdade: so embaralha os bytes para o valor guardado
# nao ser igual ao original. Nunca use fora dos testes.
# ---------------------------------------------------------------------------

import base64

from app.services.licenca.cofre import CofreIndisponivel, SegredoIlegivel

# Marca que identifica um valor trancado por este cofre falso.
_MARCA = b"COFRE-FALSO"

# "Computador" em que os testes estao rodando. Um teste troca este valor para
# simular que o banco foi aberto em outra maquina (o caso da copia do banco).
maquina = "maquina-de-teste"

# Quando True, a PROXIMA operacao falha como se o Windows recusasse o cofre.
# Volta sozinho para False depois de falhar uma vez.
falhar_proxima = False

# Quando True, TODAS as operacoes falham (cofre fora do ar o tempo todo).
sempre_falhar = False


def reiniciar() -> None:
    """Volta o cofre falso ao estado inicial. Chamado antes de cada teste."""
    global maquina, falhar_proxima, sempre_falhar
    maquina = "maquina-de-teste"
    falhar_proxima = False
    sempre_falhar = False


def _verificar_falha() -> None:
    """Simula a recusa do Windows quando o teste pediu."""
    global falhar_proxima
    if sempre_falhar:
        raise CofreIndisponivel("Cofre falso: falha simulada (sempre).")
    if falhar_proxima:
        falhar_proxima = False           # so a proxima chamada falha
        raise CofreIndisponivel("Cofre falso: falha simulada.")


def proteger(dados: bytes) -> bytes:
    """Imita o CryptProtectData: marca + maquina + bytes invertidos."""
    _verificar_falha()
    # Inverter os bytes basta para o valor guardado nao ser o texto original.
    return _MARCA + b"|" + maquina.encode() + b"|" + base64.b64encode(dados[::-1])


def desproteger(dados: bytes) -> bytes:
    """Imita o CryptUnprotectData: so abre o que foi trancado nesta 'maquina'."""
    _verificar_falha()
    try:
        marca, dono, conteudo = dados.split(b"|", 2)
    except ValueError as e:
        raise SegredoIlegivel("Cofre falso: valor em formato desconhecido.") from e
    if marca != _MARCA or dono.decode() != maquina:
        raise SegredoIlegivel("Cofre falso: valor trancado em outra maquina.")
    return base64.b64decode(conteudo)[::-1]
