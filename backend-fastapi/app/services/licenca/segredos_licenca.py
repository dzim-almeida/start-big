# ---------------------------------------------------------------------------
# ARQUIVO: services/licenca/segredos_licenca.py
# DESCRICAO: Licenca - UNICO lugar que le e grava os dois segredos da licenca:
#            o TOKEN e a CHAVE DE ATIVACAO (LIC-01, ACORDO D-30).
#
# Os dois ficam no banco trancados pelo cofre do Windows (cofre.py, DPAPI no
# escopo da maquina). O valor guardado ganha o prefixo "dpapi:v1:", que diz
# "este valor ja esta no cofre". Valores sem o prefixo sao do formato antigo:
#   - token antigo: texto puro (um JWT, que comeca com "eyJ");
#   - chave antiga: cifrada com um resumo do HWID (cripto.py).
# Os antigos continuam legiveis ate a migracao do startup (migrar_segredos)
# passar por eles. A chave PUBLICA nao vem para ca: ela e publica por definicao.
#
# ATENCAO: chame sempre `cofre.proteger(...)` pelo nome do modulo (e nao
# `from cofre import proteger`). E assim que o teste consegue trocar a DPAPI
# pelo cofre falso.
# ---------------------------------------------------------------------------

import base64                       # transforma bytes em texto seguro para gravar no banco
import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.crud.configuracao import licenca as licenca_crud
from app.db.models.configuracao_licenca import ConfiguracaoLicenca
from app.services.licenca import cofre
from app.services.licenca.cripto import decriptar_valor   # formato antigo da chave (pelo HWID)

logger = logging.getLogger(__name__)

PREFIXO = "dpapi:v1:"               # marca de que o valor ja esta no cofre
_INICIO_DE_JWT = "eyJ"              # todo JWT comeca assim ('{"' em base64)


# ===========================================================================
# Trancar e abrir (uso interno)
# ===========================================================================

def _guardar(texto: str) -> str:
    """Tranca o texto no cofre e devolve o que deve ir para a coluna do banco."""
    cifrado = cofre.proteger(texto.encode("utf-8"))           # pode lancar CofreIndisponivel
    return PREFIXO + base64.b64encode(cifrado).decode("ascii")


def _abrir(guardado: str) -> str:
    """Abre um valor com o prefixo do cofre e devolve o texto original."""
    cifrado = base64.b64decode(guardado[len(PREFIXO):])
    return cofre.desproteger(cifrado).decode("utf-8")         # pode lancar SegredoIlegivel


def esta_no_cofre(guardado: str | None) -> bool:
    """True quando o valor ja foi trancado no cofre (tem o prefixo)."""
    return bool(guardado) and guardado.startswith(PREFIXO)


# ===========================================================================
# Token da licenca
# ===========================================================================

def guardar_token(token: str) -> str:
    """Devolve o texto que deve ir para a coluna `token`."""
    return _guardar(token)


def ler_token(guardado: str | None) -> str | None:
    """Abre o token guardado.

    - None ou vazio: devolve None (nao ha token).
    - Formato antigo (texto puro): devolve como esta, ate a migracao passar.
    - Formato novo: abre pelo cofre. Lanca cofre.SegredoIlegivel quando o valor
      foi trancado em outro computador, e cofre.CofreIndisponivel quando o
      Windows recusa.
    """
    if not guardado:
        return None
    if not esta_no_cofre(guardado):
        return guardado
    return _abrir(guardado)


def gravar_token_na_licenca(licenca: ConfiguracaoLicenca, token: str) -> bool:
    """Tranca o token novo e o coloca na licenca (sem dar commit).

    Se o cofre falhar, MANTEM o token anterior (que ainda vale ate 7 dias),
    registra no log e devolve False: a validacao continua "licenca valida" e a
    gravacao e tentada de novo na proxima validacao (LIC-01 §6.4).
    """
    try:
        licenca.token = guardar_token(token)
        return True
    except cofre.CofreIndisponivel as e:
        logger.warning(
            "[licenca] COFRE_INDISPONIVEL ao gravar o token novo; o anterior foi mantido: %s", e
        )
        return False


# ===========================================================================
# Chave de ativacao
# ===========================================================================

def guardar_chave_ativacao(chave: str) -> str:
    """Devolve o texto que deve ir para a coluna `chave_ativacao`."""
    return _guardar(chave)


def ler_chave_ativacao(guardado: str, hwid: str) -> str:
    """Abre a chave de ativacao.

    - Formato novo: abre pelo cofre (pode lancar SegredoIlegivel ou
      CofreIndisponivel).
    - Formato antigo: abre pelo HWID, como sempre foi. Se o HWID nao confere
      (banco de outro computador), a biblioteca de cifra lanca um erro, e quem
      chamou trata como "licenca de outra maquina".

    `hwid` e o desta maquina: quem chama ja o tem em maos (e e assim que os
    testes simulam "outro computador" no formato antigo).
    """
    if not esta_no_cofre(guardado):
        return decriptar_valor(guardado, hwid)
    return _abrir(guardado)


# ===========================================================================
# Migracao no startup (LIC-01 §6.3)
# ===========================================================================

def migrar_segredos(db: Session, hwid: str) -> None:
    """Passa o token e a chave do formato antigo para o cofre.

    Decide pelo CONTEUDO de cada coluna (nao ha mudanca de schema):
      - token sem prefixo e com cara de JWT -> tranca no cofre;
      - chave sem prefixo -> abre pelo HWID e tranca no cofre.
    Rodar de novo nao faz nada, porque o prefixo ja esta la (idempotente).

    NUNCA derruba o startup: se o cofre falhar (ou a chave antiga nao abrir
    aqui), registra no log, nao altera nada e tenta no proximo boot. Os valores
    antigos continuam legiveis pelo caminho antigo de ler_token e
    ler_chave_ativacao.

    Nao da commit (regra das camadas): quem chama, no startup, confirma.
    """
    licenca = licenca_crud.get_licenca(db)
    if not licenca:
        return   # banco sem licenca (primeira abertura): nada a migrar

    # Calcula os dois valores novos ANTES de mexer na licenca: ou os dois
    # entram juntos, ou nada muda (nunca fica metade migrado por erro no meio).
    novo_token = None
    nova_chave = None
    try:
        token = licenca.token
        if token and not esta_no_cofre(token) and token.startswith(_INICIO_DE_JWT):
            novo_token = guardar_token(token)

        if licenca.chave_ativacao and not esta_no_cofre(licenca.chave_ativacao):
            chave_aberta = decriptar_valor(licenca.chave_ativacao, hwid)
            nova_chave = guardar_chave_ativacao(chave_aberta)
    except cofre.CofreIndisponivel as e:
        logger.warning("[licenca] COFRE_INDISPONIVEL na migracao dos segredos; nada mudou: %s", e)
        return
    except Exception as e:  # noqa: BLE001 - chave antiga de outra maquina, formato estranho...
        # Sem detalhes do valor no log: so o tipo do erro.
        logger.warning(
            "[licenca] Migracao dos segredos adiada: a chave antiga nao abre aqui (%s).",
            type(e).__name__,
        )
        return

    if novo_token is None and nova_chave is None:
        return   # ja migrado (ou nada a migrar): nao toca no banco

    if novo_token is not None:
        licenca.token = novo_token
    if nova_chave is not None:
        licenca.chave_ativacao = nova_chave
    licenca_crud.update_licenca(db, licenca)   # flush: o commit e de quem chamou (tarefas.py)
    logger.info("[licenca] Segredos da licenca trancados no cofre do Windows.")


# ===========================================================================
# Leitura com o erro de tela pronto (LIC-01 §6.4)
# ===========================================================================
# As rotas de licenca precisam transformar cada falha do cofre num erro que o
# app entende. As regras ficam aqui, num lugar so, para todas as portas
# (boot, login do caixa, renovacao) responderem igual.

def abrir_chave_ou_erro(licenca: ConfiguracaoLicenca, hwid: str) -> str:
    """Abre a chave de ativacao ou levanta o erro de licenca certo.

    - Chave que nao abre neste computador (banco copiado, nos dois formatos):
      LICENCA_DE_OUTRA_MAQUINA, o codigo que o app ja leva para a tela de
      transferencia. (Revisao 2 da SPEC-01: o codigo CHAVE_ATIVACAO_ILEGIVEL
      deixou de ser emitido, para nao perder essa tela.)
    - O Windows recusou o cofre: 503 COFRE_INDISPONIVEL.
    """
    # Import local: recusa.py e cripto.py nao dependem deste arquivo, mas
    # assim evitamos qualquer ciclo de import no pacote da licenca.
    from app.services.licenca.recusa import erro_licenca_de_outra_maquina

    try:
        return ler_chave_ativacao(licenca.chave_ativacao, hwid)
    except cofre.CofreIndisponivel as e:
        logger.error("[licenca] COFRE_INDISPONIVEL ao abrir a chave de ativacao: %s", e)
        raise erro_cofre_indisponivel() from e
    except Exception as e:  # noqa: BLE001 - SegredoIlegivel ou chave antiga de outro HWID
        logger.warning("[licenca] Chave de ativacao nao abre neste computador (%s).", type(e).__name__)
        raise erro_licenca_de_outra_maquina() from e


def abrir_token_ou_erro(guardado: str | None) -> str | None:
    """Abre o token para a validacao OFFLINE, ou levanta o erro certo.

    So e usado quando nao ha internet: com internet, a validacao online pede
    um token novo com a chave e regrava, e o token antigo nem e lido.
    """
    try:
        return ler_token(guardado)
    except cofre.CofreIndisponivel as e:
        logger.error("[licenca] COFRE_INDISPONIVEL ao abrir o token: %s", e)
        raise erro_cofre_indisponivel() from e
    except cofre.SegredoIlegivel as e:
        logger.warning("[licenca] TOKEN_ILEGIVEL: o token guardado nao abre neste computador.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "codigo": "TOKEN_ILEGIVEL",
                "mensagem": "Não foi possível ler a licença guardada. "
                            "Conecte-se à internet ou entre de novo com a conta StartBig.",
            },
        ) from e


def erro_cofre_indisponivel() -> HTTPException:
    """503 padrao de "o Windows nao deixou usar o cofre da licenca"."""
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "codigo": "COFRE_INDISPONIVEL",
            "mensagem": "O Windows não permitiu acessar o cofre da licença. "
                        "Reinicie o computador e tente de novo.",
        },
    )
