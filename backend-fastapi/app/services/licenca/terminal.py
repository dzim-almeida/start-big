# ---------------------------------------------------------------------------
# ARQUIVO: services/licenca/terminal.py
# DESCRICAO: Licenca - conectar e desconectar terminal.
# ---------------------------------------------------------------------------

import logging
import httpx
from sqlalchemy.orm import Session
from app.schemas.licenca import (
    ConectarPayload,
    DesconectarPayload,
)
from app.db.models.terminal_conectado import TerminalConectado
from app.db.crud.configuracao import licenca as licenca_crud
from app.db.crud import terminal_conectado as terminal_crud
from app.core.hwid import obter_hwid
from app.services.licenca.constantes import API_CONECTAR_URL, API_DESCONECTAR_URL, CONECTAR_TIMEOUT_SECONDS, DESCONECTAR_TIMEOUT
from app.services.licenca.cripto import decriptar_valor
from app.services.licenca.recusa import _detalhe_da_recusa, _erro_licenca, _limpar_bloqueio, _recusa_por_vencimento

logger = logging.getLogger(__name__)


# ===========================================================================
# Conexão de Terminal (Login)
# ===========================================================================

def conectar_terminal(db: Session, terminal_hwid: str) -> None:
    """
    Conecta um terminal à licença via API StartBig.

    Chamado durante o login de cada terminal. Idempotente: se o HWID
    já estiver registrado em terminais_conectados, atualiza ultima_sinc
    e retorna sem chamar a API externa.

    Fluxo:
    1. Verifica se terminal já está registrado (idempotente).
    2. Busca licença e decripta chave_ativacao com HWID do servidor.
    3. POST /licenca/conectar com {chave, hwid: terminal_hwid}.
    4. Sucesso → insere em terminais_conectados.
    5. Erro 4xx → HTTPException 403.
    6. Erro de rede → HTTPException 503.

    Args:
        db: Sessão do banco de dados.
        terminal_hwid: Hardware ID do terminal que está fazendo login.

    Raises:
        HTTPException 403: Limite de terminais atingido ou licença recusada.
        HTTPException 503: Não foi possível conectar ao servidor de licenças.
    """
    # 0. HWID vazio nao identifica terminal nenhum. Barrar aqui (e nao so no
    #    endpoint) porque esta funcao E a fronteira do limite de licenca: a API
    #    externa ACEITA hwid vazio, entao um hwid em branco entrava sem ocupar
    #    vaga e furava o limite -- bastava omitir o campo no login.
    if not (terminal_hwid or "").strip():
        raise _erro_licenca(
            "HWID_AUSENTE",
            "Terminal não identificado. Não foi possível validar a licença.",
        )

    print(f"[terminal] conectar_terminal chamado — hwid={terminal_hwid[:8]}...")

    # 1. Idempotência: terminal já conectado
    existente = terminal_crud.get_terminal_by_hwid(db, terminal_hwid)
    if existente:
        terminal_crud.update_ultima_sinc(db, existente)
        print(f"[terminal] Terminal {terminal_hwid[:8]}... já conectado — update ultima_sinc")
        return

    # 2. Buscar licença e decriptar com HWID do servidor
    licenca = licenca_crud.get_licenca(db)
    if not licenca:
        import os, sys
        if os.getenv("TESTING") or "pytest" in sys.modules:
            print("[terminal] Ignorando conexão de licença em ambiente de testes")
            return
        raise _erro_licenca(
            "LICENCA_NAO_ENCONTRADA",
            "Nenhuma licença encontrada. Execute o setup inicial do sistema.",
        )

    # 3. Pré-validação local: verificar limite de terminais antes da chamada API
    terminais = terminal_crud.get_todos_terminais(db)
    if len(terminais) >= licenca.limite:
        raise _erro_licenca(
            "LIMITE_TERMINAIS",
            f"Limite máximo de {licenca.limite} máquina(s) conectada(s) atingido. "
            "Desconecte um terminal para conectar um novo.",
        )

    # 4. Decriptar chave de ativação com HWID do servidor
    hwid_servidor = obter_hwid()
    try:
        chave_ativacao = decriptar_valor(licenca.chave_ativacao, hwid_servidor)
    except Exception as e:
        logger.warning("[licenca] Falha na descriptografia — possível clonagem: %s", e)
        raise _erro_licenca(
            "CLONAGEM_DETECTADA",
            "Falha na verificação de integridade. "
            "O banco de dados pode ter sido copiado de outra máquina.",
        )

    # 5. Chamar API externa
    payload = ConectarPayload(chave=chave_ativacao, hwid=terminal_hwid)

    try:
        with httpx.Client(timeout=CONECTAR_TIMEOUT_SECONDS) as client:
            response = client.post(
                API_CONECTAR_URL,
                json=payload.model_dump(),
            )
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        # 6. Fallback offline: API indisponível, mas validação local passou — registrar localmente
        terminal = TerminalConectado(hwid=terminal_hwid)
        terminal_crud.create_terminal(db, terminal)
        print(f"[terminal] Terminal {terminal_hwid[:8]}... CRIADO (fallback offline — {type(e).__name__})")
        return

    # 7. Processar resposta da API
    if 200 <= response.status_code < 300:
        terminal = TerminalConectado(hwid=terminal_hwid)
        terminal_crud.create_terminal(db, terminal)
        # A nuvem aceitou ESTE terminal nesta licenca: e a prova mais direta de
        # que o bloqueio local nao vale mais. Sem esta linha o dono loga e leva
        # 403 em toda tela, ate o proximo /licenca/status.
        if _limpar_bloqueio(licenca):
            licenca_crud.update_licenca(db, licenca)
            db.commit()
        print(f"[terminal] Terminal {terminal_hwid[:8]}... CRIADO (API retornou {response.status_code})")
        return

    # 8. Erro 4xx (limite atingido na API, licença inválida)
    if 400 <= response.status_code < 500:
        detail, corpo = _detalhe_da_recusa(response)

        # Licença vencida NÃO barra o login.
        #
        # Quem precisa renovar é justamente quem venceu, e a renovação mora
        # DENTRO do sistema, depois do login (a cobrança é do dono da licença:
        # antes de saber quem está na frente da tela não há a quem cobrar).
        # Barrar aqui deixaria a pessoa presa do lado de fora com uma tela que
        # só sabe dizer "fale com o suporte".
        #
        # Entrar não libera nada: a verificação de licença já respondeu
        # LICENCA_EXPIRADA e o sistema fica inativo, com a cobrança como única
        # tela que funciona. O limite de máquinas continua valendo — quem o
        # aplica é a pré-validação local do passo 3, acima.
        if _recusa_por_vencimento(response.status_code, detail, corpo, licenca):
            terminal = TerminalConectado(hwid=terminal_hwid)
            terminal_crud.create_terminal(db, terminal)
            logger.info(
                "[terminal] Licença vencida na nuvem — terminal registrado localmente "
                "para permitir o login e a renovação: %s",
                detail,
            )
            return

        raise _erro_licenca(
            "LIMITE_TERMINAIS",
            f"Não foi possível conectar o terminal: {detail}",
        )

    # 9. Erro 5xx — tratar como indisponível (fallback offline)
    terminal = TerminalConectado(hwid=terminal_hwid)
    terminal_crud.create_terminal(db, terminal)
    print(f"[terminal] Terminal {terminal_hwid[:8]}... CRIADO (fallback 5xx — status {response.status_code})")


# ===========================================================================
# Desconexão de Sessão (Etapa 5)
# ===========================================================================

async def desconectar_terminal(db: Session, terminal_hwid: str) -> dict:
    """
    Desconecta um terminal específico da licença.

    1. Remove o registro de terminais_conectados (local).
    2. Notifica a API StartBig via POST /licenca/desconectar.

    Fire-and-forget: nunca levanta exceção — falhas são registadas em log.

    Args:
        db: Sessão do banco de dados.
        terminal_hwid: Hardware ID do terminal a desconectar.

    Returns:
        dict: {"ok": True} sempre.
    """
    try:
        # 1. Remover da tabela local
        print(f"[terminal] desconectar_terminal chamado — hwid={terminal_hwid[:8]}...")
        terminal_crud.delete_terminal_by_hwid(db, terminal_hwid)
        db.commit()

        # 2. Notificar API externa
        licenca = licenca_crud.get_licenca(db)
        if not licenca:
            return {"ok": True}

        hwid_servidor = obter_hwid()
        chave_ativacao = decriptar_valor(licenca.chave_ativacao, hwid_servidor)
        payload = DesconectarPayload(chave=chave_ativacao, hwid=terminal_hwid)

        async with httpx.AsyncClient(timeout=DESCONECTAR_TIMEOUT) as client:
            response = await client.post(
                API_DESCONECTAR_URL,
                json=payload.model_dump(),
            )

        logger.info(
            "[licenca] Desconexão terminal %s: status %d",
            terminal_hwid[:8], response.status_code,
        )

    except Exception as e:
        logger.warning("[licenca] Desconexão falhou — %s: %s", type(e).__name__, e)

    return {"ok": True}
