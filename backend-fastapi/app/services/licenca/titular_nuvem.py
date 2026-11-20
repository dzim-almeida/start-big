# ---------------------------------------------------------------------------
# ARQUIVO: services/licenca/titular_nuvem.py
# DESCRICAO: Dados do titular da conta na nuvem StartBig (LIC-03 §6.6, D-22,
#            D-28, conflito 16) e a chamada autenticada à nuvem usada pelo
#            re-login.
#
# REDE DE SEGURANÇA (D-28): enquanto a API não tiver as rotas do titular (LIC-06),
# ela responde 404. Nesse caso `buscar_titular` devolve None e `atualizar_titular`
# devolve False, e o setup funciona como sempre funcionou: só local.
# ---------------------------------------------------------------------------

import logging

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.crud.configuracao import licenca as licenca_crud
from app.schemas.licenca.titular import AtualizarTitularCorpo, TitularNuvem
from app.services.licenca import segredos_licenca
from app.services.licenca.constantes import API_REENVIAR_LINK_URL, API_TITULAR_URL, TIMEOUT_SECONDS
from app.services.licenca.recusa import _detalhe_da_recusa

logger = logging.getLogger(__name__)


def _erro(http_status: int, codigo: str, mensagem: str) -> HTTPException:
    """Erro no formato que a tela trata por código (D-29)."""
    return HTTPException(status_code=http_status, detail={"codigo": codigo, "mensagem": mensagem})


def pedir_a_nuvem(db: Session, metodo: str, url: str, corpo: dict | None = None) -> httpx.Response:
    """Faz uma chamada à nuvem com o token da licença no cabeçalho `Authorization`.

    É síncrona de propósito: o setup e o re-login rodam fora do "loop" assíncrono
    do FastAPI (em rotas `def`), então não precisam do `await`.

    Falha de rede vira `SEM_CONEXAO`; qualquer resposta (até erro) volta para
    quem chamou decidir o que fazer com ela.
    """
    licenca = licenca_crud.get_licenca(db)
    # O token mora no cofre (LIC-01). Se não abrir, sai o erro certo (TOKEN_ILEGIVEL
    # ou COFRE_INDISPONIVEL) em vez de uma chamada sem autenticação.
    token = segredos_licenca.abrir_token_ou_erro(licenca.token if licenca else None)
    cabecalhos = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as cliente:
            return cliente.request(metodo, url, json=corpo, headers=cabecalhos)
    except httpx.RequestError as e:
        logger.warning("[licenca] %s %s sem conexão: %s", metodo, url, e)
        raise _erro(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "SEM_CONEXAO",
            "Sem conexão com a StartBig. Verifique a internet.",
        ) from e


def erro_da_resposta(resposta: httpx.Response) -> HTTPException:
    """Transforma uma resposta de erro da nuvem no erro local com o código certo.

    - 5xx: a nuvem caiu → NUVEM_INDISPONIVEL (503).
    - 4xx com `codigo` (ex.: LICENCA_HWID_REVOGADO, DOCUMENTO_TRAVADO): o mesmo
      código e o mesmo status, para a tela mostrar a mensagem da tabela (§6.4).
    - 4xx sem código (ex.: 400 de validação): RESPOSTA_INVALIDA, com a frase da nuvem.
    """
    if resposta.status_code >= 500:
        return _erro(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "NUVEM_INDISPONIVEL",
            "O servidor da StartBig não respondeu. Tente de novo em alguns minutos.",
        )
    frase, corpo = _detalhe_da_recusa(resposta)
    codigo = corpo.get("codigo")
    if codigo:
        return _erro(resposta.status_code, codigo, frase or "A StartBig recusou o pedido.")
    return _erro(
        resposta.status_code,
        "RESPOSTA_INVALIDA",
        frase or "A StartBig recusou os dados enviados.",
    )


def buscar_titular(db: Session) -> TitularNuvem | None:
    """Dados do titular na nuvem (GET /erp/usuario/titular). None = a API ainda não tem a rota."""
    resposta = pedir_a_nuvem(db, "GET", API_TITULAR_URL)
    if resposta.status_code == 404:
        return None  # rede de segurança: API sem a LIC-06
    if resposta.status_code >= 400:
        raise erro_da_resposta(resposta)
    try:
        return TitularNuvem(**resposta.json())
    except (ValueError, ValidationError) as e:
        logger.error("[licenca] Titular fora do contrato: %s", e)
        raise _erro(
            status.HTTP_502_BAD_GATEWAY,
            "RESPOSTA_INVALIDA",
            "A StartBig respondeu num formato inesperado. Tente de novo em instantes.",
        ) from e


def atualizar_titular(db: Session, corpo: AtualizarTitularCorpo) -> bool:
    """Atualiza o titular na nuvem (PUT). True = atualizado; False = a API não tem a rota (404).

    O corpo é um `AtualizarTitularCorpo`: o documento não existe nessa classe,
    então nunca sai daqui (conflito 16). Qualquer recusa levanta o erro com o
    código, e quem chama não cria nada local.
    """
    resposta = pedir_a_nuvem(db, "PUT", API_TITULAR_URL, corpo.model_dump(exclude_none=True))
    if resposta.status_code == 404:
        return False
    if resposta.status_code >= 400:
        raise erro_da_resposta(resposta)
    return True


def reenviar_link(email: str) -> None:
    """Pede à nuvem um novo link de confirmação ou de nova senha (LIC-06 §4.4).

    Não usa o token: quem pede ainda pode não ter licença (cadastro esperando a
    confirmação). A nuvem responde sempre 202, exista ou não o e-mail, e a rota
    local faz o mesmo, para ninguém descobrir quem é cliente (D-31). Sem a
    LIC-06 no ar (404), também segue como "pedido aceito". Só a falta de rede e
    a nuvem fora do ar viram erro, para a tela não dizer "enviamos" à toa.
    """
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as cliente:
            resposta = cliente.post(API_REENVIAR_LINK_URL, json={"email": email})
    except httpx.RequestError as e:
        logger.warning("[licenca] Reenviar link sem conexão: %s", e)
        raise _erro(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "SEM_CONEXAO",
            "Sem conexão com a StartBig. Verifique a internet.",
        ) from e
    if resposta.status_code >= 500:
        raise erro_da_resposta(resposta)   # NUVEM_INDISPONIVEL
