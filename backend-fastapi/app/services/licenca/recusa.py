# ---------------------------------------------------------------------------
# ARQUIVO: services/licenca/recusa.py
# DESCRICAO: Licenca - erro padrao, vencimento x outra recusa, bloqueio local e carencia.
# ---------------------------------------------------------------------------

import logging
import unicodedata
from datetime import datetime, timezone
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


# ===========================================================================
# Validação de Sessão (Etapa 2 — Boot Check)
# ===========================================================================

def _erro_licenca(codigo: str, mensagem: str) -> HTTPException:
    """
    Cria uma HTTPException 403 padronizada para erros de licença inválida.
    E um HTTPException 404 para licença não encontrada.
    """
    
    if codigo == "LICENCA_NAO_ENCONTRADA":
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": codigo, "mensagem": mensagem},
        )

    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"codigo": codigo, "mensagem": mensagem},
    )


# ===========================================================================
# Licença de outro computador (troca de servidor)
# ===========================================================================
# A licença local é cifrada com o HWID da máquina que a ativou. Se ela não
# decifra aqui, o banco veio de outro computador -- na vida real, quase sempre
# uma troca de servidor, e não uma fraude. Até 19/10/2026 isto se chamava
# CLONAGEM_DETECTADA e era levantado em dois lugares com textos próprios; só um
# deles (a tela de erro) oferecia saída, e o cliente que caía pelo login ficava
# preso. Agora há um código, uma frase e uma saída: transferir com a conta.

CODIGO_LICENCA_DE_OUTRA_MAQUINA = "LICENCA_DE_OUTRA_MAQUINA"


def erro_licenca_de_outra_maquina() -> HTTPException:
    """403 padrão de "a licença deste banco foi ativada em outro computador"."""
    return _erro_licenca(
        CODIGO_LICENCA_DE_OUTRA_MAQUINA,
        "A licença deste sistema está ativada em outro computador. "
        "Entre com a conta StartBig para transferi-la para este.",
    )


# ===========================================================================
# Recusa da nuvem: vencimento ou outra coisa?
# ===========================================================================
# A nuvem responde 4xx tanto para "o plano acabou" quanto para "esta licenca
# foi bloqueada". Ate 31/08/2026 os dois viravam LICENCA_RECUSADA, e o efeito
# pratico era este: quem so precisava PAGAR batia numa tela sem saida --
# "Tentar Novamente" e o suporte --, sem sequer conseguir logar. A tela de
# cobranca ja existia, e ninguem nunca chegava nela, porque ela so abre com o
# codigo LICENCA_EXPIRADA e esse codigo so nascia offline (ou na simulacao).
#
# Separar os dois casos aqui e o que liga o caminho: vencimento vira
# LICENCA_EXPIRADA, o frontend deixa entrar e leva para a renovacao; qualquer
# outra recusa continua exatamente como estava.

_CODIGOS_DE_VENCIMENTO = frozenset({
    "LICENCA_EXPIRADA",
    "LICENCA_VENCIDA",
    "ASSINATURA_EXPIRADA",
    "ASSINATURA_VENCIDA",
    "PLANO_EXPIRADO",
    "EXPIRED",
    "EXPIRED_LICENSE",
    "LICENSE_EXPIRED",
    "SUBSCRIPTION_EXPIRED",
    "PAYMENT_REQUIRED",
})


# A nuvem hoje nao manda codigo nenhum -- manda texto ("Licenca vencida. Acesso
# negado."). Ler o texto e fragil de proposito assumido: e o unico sinal que
# existe hoje, e a rede de baixo (o vencimento gravado aqui) cobre o dia em que
# a frase mudar.
_TERMOS_DE_VENCIMENTO = (
    "vencid",
    "expirad",
    "expired",
    "assinatura inativa",
    "plano inativo",
    "renove",
    "renovacao",
)


def _limpar_bloqueio(licenca) -> bool:
    """A nuvem acabou de aceitar esta licenca -> o bloqueio local caiu.

    O BECO SEM SAIDA QUE ISTO FECHA (visto na loja em 31/08/2026): o unico
    lugar que limpava `bloqueada` era o heartbeat, e so quando algum terminal
    respondia 200. Acontece que e o proprio heartbeat que bloqueia, e ao
    bloquear ele APAGA os terminais (400 -> delete). Sem terminal, o heartbeat
    seguinte retorna antes de perguntar qualquer coisa -- e a flag fica ligada
    para sempre. A plataforma dizia "Ativa, 15 dias restantes" e a maquina
    continuava em "Licenca bloqueada. Conexao encerrada pelo servidor.", em
    toda requisicao autenticada.

    O bloqueio e um eco de um estado passado. Quem manda e a nuvem, e a resposta
    dela agora vale mais que a conclusao que tiramos dela antes.
    """
    if not getattr(licenca, "bloqueada", False):
        return False

    licenca.bloqueada = False
    logger.info("[licenca] Bloqueio local limpo: a nuvem validou esta licenca.")
    return True


def _detalhe_da_recusa(response) -> tuple[str, dict]:
    """Mensagem legivel e corpo JSON (quando houver) de uma resposta 4xx."""
    corpo: dict = {}
    try:
        corpo = response.json() or {}
        if not isinstance(corpo, dict):
            corpo = {}
    except Exception:
        corpo = {}

    detalhe = corpo.get("msg") or corpo.get("message") or corpo.get("mensagem") or response.text
    return (detalhe or "").strip(), corpo


def _plano_vencido_localmente(licenca, agora: datetime | None = None) -> bool:
    """A data que ESTA MAQUINA guarda ja passou (e nao ha carencia vigente)?

    Serve de segunda opiniao quando a nuvem recusa sem dizer por que. E um dado
    que veio da propria nuvem na ultima sincronizacao bem-sucedida, entao nao e
    palpite -- e a ultima verdade conhecida sobre o plano.
    """
    agora = agora or datetime.now(timezone.utc)

    vencimento = getattr(licenca, "data_vencimento", None)
    if vencimento is None:
        return False
    if vencimento.tzinfo is None:
        vencimento = vencimento.replace(tzinfo=timezone.utc)

    return agora >= vencimento and not _carencia_vigente(licenca, agora)


def _recusa_por_vencimento(status_code: int, mensagem: str, corpo: dict, licenca) -> bool:
    """A recusa da nuvem e "falta pagar" (True) ou outra coisa (False)?

    Tres sinais, do mais confiavel para o menos:
      1. codigo estruturado no corpo -- o dia que a nuvem mandar um;
      2. HTTP 402 Payment Required, ou texto falando em vencimento;
      3. o vencimento gravado nesta maquina, que ja passou.

    Errar para MENOS (achar que nao e vencimento) devolve o comportamento
    antigo: tela de erro, cliente liga para o suporte. Errar para MAIS deixa a
    pessoa logar numa tela que so sabe cobrar. Nenhum dos dois libera o sistema.
    """
    codigo = (corpo.get("codigo") or corpo.get("code") or corpo.get("erro") or "")
    if isinstance(codigo, str) and codigo.strip().upper() in _CODIGOS_DE_VENCIMENTO:
        return True

    if status_code == 402:
        return True

    texto = _sem_acentos((mensagem or "").lower())
    if any(termo in texto for termo in _TERMOS_DE_VENCIMENTO):
        return True

    return _plano_vencido_localmente(licenca)


def _sem_acentos(texto: str) -> str:
    """"Licenca" e "Licença" tem que casar com o mesmo termo."""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def _carencia_vigente(licenca, agora: datetime) -> bool:
    """A licenca venceu, mas o pagamento ainda esta sendo re-tentado?

    So vale com as DUAS coisas: a flag ligada e uma data limite no futuro.
    Flag sozinha nao basta de proposito -- um servidor que mandasse
    `emCarencia` e esquecesse a data daria uso ilimitado de graca, e o sintoma
    seria o sistema funcionar, que ninguem reporta.

    Nulos (instalacao que ainda nao sincronizou depois da atualizacao, ou
    licenca no PIX) respondem False e o comportamento e o de sempre.
    """
    if not getattr(licenca, "em_carencia", None):
        return False

    limite = getattr(licenca, "data_limite_carencia", None)
    if limite is None:
        return False

    if limite.tzinfo is None:
        limite = limite.replace(tzinfo=timezone.utc)

    return agora < limite
