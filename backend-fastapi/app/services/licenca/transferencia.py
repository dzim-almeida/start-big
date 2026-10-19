# ---------------------------------------------------------------------------
# ARQUIVO: services/licenca/transferencia.py
# DESCRICAO: Licenca - ativar este computador com a conta StartBig e trocar o
#            servidor de computador.
#
# O MODELO (o mesmo de JetBrains, Adobe, LicenseSpring, Keygen):
#
#   - A licença é UMA e mora na nuvem. O que fica neste banco é só a ATIVAÇÃO
#     dela nesta máquina, cifrada com o HWID -- por isso não decifra em outra.
#   - Trocar de computador = desativar no antigo (libera a vaga) e ativar no
#     novo. Quem autoriza é o login da conta, nunca o arquivo do banco.
#   - Se o computador antigo morreu e não dá para desativá-lo, o login da conta
#     no novo basta: a nuvem derruba a sessão antiga e manda e-mail de aviso.
#
# Três portas usam o mesmo núcleo (`_entrar_na_conta` + `_gravar_ativacao`):
#   reconnect_licenca            -> assistente de primeiro acesso (banco sem licença)
#   transferir_para_esta_maquina -> banco copiado de outro computador
#   desativar_esta_maquina       -> computador que vai deixar de ser o servidor
#
# Até 19/10/2026 o reconectar morava em cadastro.py e a troca de computador era
# um remendo dentro dele, com saída só na tela de erro de licença. O cliente
# que descobria a troca pelo LOGIN (o caso comum: o servidor sobe devagar e a
# checagem do boot passa direto) ficava preso sem botão nenhum.
# ---------------------------------------------------------------------------

import logging

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.hwid import obter_hwid
from app.db.crud.configuracao import licenca as licenca_crud
from app.db.crud.terminal import conectados as terminal_crud
from app.db.models.configuracao_licenca import ConfiguracaoLicenca
from app.schemas.licenca import AutoCadastroResponse, DesconectarPayload
from app.services.licenca import cadastro
from app.services.licenca.constantes import (
    API_DESCONECTAR_URL,
    API_ERP_LOGIN_URL,
    DESCONECTAR_TIMEOUT,
    TIMEOUT_SECONDS,
)
from app.services.licenca.cripto import decriptar_valor, encriptar_valor
from app.services.licenca.recusa import _detalhe_da_recusa

logger = logging.getLogger(__name__)


def _erro(http_status: int, codigo: str, mensagem: str) -> HTTPException:
    return HTTPException(status_code=http_status, detail={"codigo": codigo, "mensagem": mensagem})


# ===========================================================================
# Em que computador esta licença foi ativada?
# ===========================================================================

def licenca_ativada_nesta_maquina(licenca: ConfiguracaoLicenca, hwid: str) -> bool:
    """A ativação gravada no banco é DESTE computador?

    Decifrar é a prova; a coluna `hwid` sozinha não basta, porque é texto puro
    e pode ser editada. Mesma regra do boot (`verificar_licenca_ativa`).
    """
    try:
        decriptar_valor(licenca.chave_ativacao, hwid)
        return True
    except Exception:  # noqa: BLE001 - qualquer falha = não decifra aqui
        return False


# ===========================================================================
# Login na conta StartBig
# ===========================================================================

def _entrar_na_conta(email: str, senha: str, hwid: str) -> AutoCadastroResponse:
    """Pede à nuvem a ativação deste HWID com o login da conta.

    A nuvem trata este login como autenticado: se o plano já estiver no limite
    de computadores, ela encerra as sessões antigas para abrir vaga a este
    (e avisa o dono por e-mail). Não muda nada local -- quem grava é o chamador,
    e só depois daqui.

    Cada falha vira um código próprio, porque a tela precisa dizer coisas
    diferentes: senha errada se corrige ali; licença vencida, não.
    """
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            resposta = client.post(
                API_ERP_LOGIN_URL,
                json={"email": email, "senha": senha, "hwid": hwid},
            )
    except httpx.RequestError as e:
        logger.warning("[licenca] Login na conta sem conexão: %s", e)
        raise _erro(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "SEM_CONEXAO",
            "Sem conexão com a StartBig. Ativar a licença precisa de internet.",
        ) from e

    if resposta.status_code >= 500:
        logger.warning("[licenca] Login na conta: nuvem respondeu %d", resposta.status_code)
        raise _erro(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "NUVEM_INDISPONIVEL",
            "O servidor da StartBig não respondeu. Tente de novo em alguns minutos.",
        )

    if resposta.status_code >= 400:
        detalhe, _ = _detalhe_da_recusa(resposta)
        if resposta.status_code == 401:
            raise _erro(
                status.HTTP_401_UNAUTHORIZED,
                "CREDENCIAIS_INVALIDAS",
                "E-mail ou senha da conta StartBig incorretos.",
            )
        # 400 da nuvem: conta sem licença ativa, licença vencida ou bloqueada,
        # senha ainda não criada. A frase dela é a melhor explicação que há.
        raise _erro(
            status.HTTP_403_FORBIDDEN,
            "CONTA_RECUSADA",
            detalhe or "A StartBig recusou a ativação desta conta.",
        )

    try:
        dados = AutoCadastroResponse(**resposta.json())
    except (ValueError, ValidationError) as e:
        logger.error("[licenca] Login na conta: resposta fora do contrato: %s", e)
        raise _erro(
            status.HTTP_502_BAD_GATEWAY,
            "RESPOSTA_INVALIDA",
            "A StartBig respondeu num formato inesperado. Fale com o suporte.",
        ) from e

    if not dados.chaveAtivacao:
        logger.error("[licenca] Login na conta: resposta sem chaveAtivacao.")
        raise _erro(
            status.HTTP_502_BAD_GATEWAY,
            "RESPOSTA_INVALIDA",
            "A StartBig não devolveu a chave de ativação. Fale com o suporte.",
        )

    return dados


# ===========================================================================
# Gravação da ativação
# ===========================================================================

def _gravar_ativacao(db: Session, resposta: AutoCadastroResponse, hwid: str) -> ConfiguracaoLicenca:
    """Troca o que houver de licença no banco pela ativação deste computador.

    Só roda depois de a nuvem aprovar. Sai junto:
      - a licença de outra máquina, que não decifra aqui e prende o
        `licenca_id` (unique) que a nova vai usar;
      - os terminais conectados que vieram no banco copiado: são sessões do
        servidor antigo, e contariam contra o limite de computadores.
    Flush sem commit -- o commit é do endpoint (`_handle_db_transaction`).
    """
    public_key_pem = cadastro._buscar_chave_publica_online()

    removidas = licenca_crud.remover_licencas_de_outras_maquinas(db, hwid)
    terminal_crud.limpar_todos_terminais(db)

    licenca = ConfiguracaoLicenca(
        cliente_id=resposta.clienteId or "000000000-0000000000-0000000000",
        hwid=hwid,
        licenca_id=resposta.licencaId,
        chave_ativacao=encriptar_valor(resposta.chaveAtivacao, hwid),
        public_key=encriptar_valor(public_key_pem, hwid),
        limite=resposta.limite,
        data_vencimento=resposta.dataVencimento,
        token=resposta.token,
        ultima_sinc=resposta.ultimaSincronizacao,
        grace_period=resposta.gracePeriodDias,
        proxima_validacao=resposta.proximaValidacaoEm,
        em_carencia=resposta.emCarencia,
        data_limite_carencia=resposta.dataLimiteCarencia,
    )
    criada = licenca_crud.create_licenca(db, licenca)

    logger.info(
        "[licenca] Ativação gravada neste computador (licença %s; %d ativação(ões) de outra máquina substituída(s)).",
        resposta.licencaId[:8], removidas,
    )
    return criada


# ===========================================================================
# Primeiro acesso: banco sem licença
# ===========================================================================

def reconnect_licenca(db: Session, email: str, senha: str) -> ConfiguracaoLicenca:
    """Assistente de primeiro acesso: liga uma conta que já existe a este banco.

    Se o banco já tiver a licença DESTE computador, não há o que reconectar
    (409). Se tiver a de OUTRO, é uma troca de servidor -- e é tratada aqui
    também, porque o assistente é por onde muita gente chega depois de copiar
    o banco.
    """
    hwid = obter_hwid()

    if licenca_crud.get_licenca_by_hwid(db, hwid):
        raise _erro(
            status.HTTP_409_CONFLICT,
            "LICENCA_JA_ATIVADA",
            "Este computador já está com a licença ativada.",
        )

    resposta = _entrar_na_conta(email, senha, hwid)
    return _gravar_ativacao(db, resposta, hwid)


# ===========================================================================
# Troca de servidor: banco copiado de outro computador
# ===========================================================================

def transferir_para_esta_maquina(db: Session, email: str, senha: str) -> ConfiguracaoLicenca:
    """Transfere para este computador a licença que veio no banco copiado.

    Recusa (409) quando a licença já é desta máquina: transferir aqui seria
    só gastar uma troca à toa e derrubar os caixas da loja na nuvem.
    Sem licença no banco, faz o mesmo que o primeiro acesso.
    """
    hwid = obter_hwid()

    licenca = licenca_crud.get_licenca(db)
    if licenca and licenca_ativada_nesta_maquina(licenca, hwid):
        raise _erro(
            status.HTTP_409_CONFLICT,
            "LICENCA_JA_ATIVADA",
            "A licença já está ativada neste computador. Não há o que transferir.",
        )

    resposta = _entrar_na_conta(email, senha, hwid)
    if licenca and licenca.licenca_id != resposta.licencaId:
        # Conta diferente da que estava no banco. Não é erro -- a conta manda --,
        # mas é o tipo de coisa que o suporte precisa achar no log depois.
        logger.warning(
            "[licenca] Transferência com OUTRA conta: banco era da licença %s, conta é da %s.",
            licenca.licenca_id[:8], resposta.licencaId[:8],
        )

    return _gravar_ativacao(db, resposta, hwid)


# ===========================================================================
# Situação deste computador (Configurações › Licença)
# ===========================================================================

def _parcial(valor: str) -> str:
    """Começo do identificador: o bastante para o suporte, sem expor o todo."""
    return f"{valor[:8]}…" if valor and len(valor) > 8 else (valor or "")


def situacao_desta_maquina(db: Session) -> dict:
    licenca = licenca_crud.get_licenca(db)
    if not licenca:
        raise _erro(
            status.HTTP_404_NOT_FOUND,
            "LICENCA_NAO_ENCONTRADA",
            "Nenhuma licença ativada neste computador.",
        )

    hwid = obter_hwid()
    return {
        "ativada_nesta_maquina": licenca_ativada_nesta_maquina(licenca, hwid),
        "licenca_id": _parcial(licenca.licenca_id),
        "computador": _parcial(hwid),
        "limite_computadores": licenca.limite,
        "computadores_conectados": len(terminal_crud.get_todos_terminais(db)),
        "data_vencimento": licenca.data_vencimento,
        "ultima_sincronizacao": licenca.ultima_sinc,
    }


# ===========================================================================
# Desativar este computador (o servidor que vai sair)
# ===========================================================================

async def desativar_esta_maquina(db: Session, hwid_solicitante: str) -> None:
    """Libera a licença deste computador antes de trocar de servidor.

    É o "desativar antes de ativar" que o mercado inteiro pede: a vaga volta
    para a conta na hora, e o computador novo ativa sem precisar derrubar
    nada. Depois disto este servidor fica sem licença -- se o desligamento foi
    engano, basta entrar com a conta de novo (assistente de primeiro acesso).

    Ordem: nuvem primeiro, banco depois. Sem internet nada muda aqui, para não
    deixar a vaga presa na nuvem com o computador já sem licença.
    """
    hwid = obter_hwid()
    if hwid_solicitante.strip() != hwid:
        raise _erro(
            status.HTTP_403_FORBIDDEN,
            "SOMENTE_NO_SERVIDOR",
            "A licença só pode ser desativada no próprio computador servidor.",
        )

    licenca = licenca_crud.get_licenca(db)
    if not licenca:
        raise _erro(
            status.HTTP_404_NOT_FOUND,
            "LICENCA_NAO_ENCONTRADA",
            "Nenhuma licença ativada neste computador.",
        )

    if not licenca_ativada_nesta_maquina(licenca, hwid):
        raise _erro(
            status.HTTP_409_CONFLICT,
            "LICENCA_DE_OUTRA_MAQUINA",
            "A licença deste banco não é deste computador; não há o que desativar aqui.",
        )

    chave = decriptar_valor(licenca.chave_ativacao, hwid)
    hwids = {hwid} | {t.hwid for t in terminal_crud.get_todos_terminais(db)}

    try:
        async with httpx.AsyncClient(timeout=DESCONECTAR_TIMEOUT) as client:
            for alvo in hwids:
                resposta = await client.post(
                    API_DESCONECTAR_URL,
                    json=DesconectarPayload(chave=chave, hwid=alvo).model_dump(),
                )
                if resposta.status_code >= 400:
                    logger.warning(
                        "[licenca] Desativação: nuvem recusou %s (%d).", alvo[:8], resposta.status_code
                    )
                    raise _erro(
                        status.HTTP_503_SERVICE_UNAVAILABLE,
                        "NUVEM_INDISPONIVEL",
                        "A StartBig não confirmou a desativação. Nada foi alterado; tente de novo.",
                    )
    except httpx.RequestError as e:
        logger.warning("[licenca] Desativação sem conexão: %s", e)
        raise _erro(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "SEM_CONEXAO",
            "Sem conexão com a StartBig. Desativar a licença precisa de internet; nada foi alterado.",
        ) from e

    terminal_crud.limpar_todos_terminais(db)
    db.delete(licenca)
    db.commit()
    logger.info("[licenca] Licença desativada neste computador (%d sessão(ões) liberada(s)).", len(hwids))
