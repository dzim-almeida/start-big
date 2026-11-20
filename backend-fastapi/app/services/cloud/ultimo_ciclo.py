# ---------------------------------------------------------------------------
# ARQUIVO: services/cloud/ultimo_ciclo.py
# DESCRICAO: Lembra o resultado do último ciclo de envio para a nuvem, para a
#            tela de backup avisar o dono quando o backup na nuvem está parado
#            (LIC-08 §6.2).
#
# Não muda o comportamento do envio: só guarda o que aconteceu. O valor fica
# EM MEMÓRIA (sem tabela nova). O ciclo roda a cada hora; antes do primeiro
# ciclo depois do boot, a tela não mostra aviso de backup, e isso é esperado.
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Any, Optional

from app.schemas.backup.operacoes import SyncResponse
from app.services.cloud.flow import CloudSyncError

# None = o último ciclo não deixou nada a avisar.
# Senão: {"codigo": ..., "desde": datetime, "feito_em": str | None}
_ultimo: Optional[dict] = None

# Ciclos que provam que o backup na nuvem está em dia: enviou, ou não havia
# nada novo para enviar. Eles limpam o aviso.
_STATUS_EM_DIA = {"success", "skipped", "up_to_date"}


def registrar(codigo: Optional[str], feito_em: Optional[str] = None) -> None:
    """Guarda o código do ciclo. `None` = em dia: limpa o aviso.

    Se o mesmo código se repete, o `desde` não muda (o aviso continua sendo o
    mesmo desde aquele horário). `feito_em` é a data do backup do trial.
    """
    global _ultimo
    if codigo is None:
        _ultimo = None
    elif _ultimo is None or _ultimo["codigo"] != codigo:
        _ultimo = {"codigo": codigo, "desde": datetime.now(), "feito_em": feito_em}
    elif feito_em:
        _ultimo["feito_em"] = feito_em   # mesmo aviso; só atualiza a data, se veio


def registrar_resposta(resposta: SyncResponse) -> None:
    """Registra o fim normal de um ciclo (a resposta do `cloud_sync.sync`)."""
    if resposta.status in _STATUS_EM_DIA:
        registrar(None)
    elif resposta.status in ("blocked", "error") and resposta.code:
        # blocked: o /status disse que o plano não permite (codigoBloqueio);
        # error: a nuvem recusou com um código (ex.: BACKUP_MAQUINA_REVOGADA).
        registrar(resposta.code, resposta.feito_em)
    # Os outros (outro terminal enviando, nada local ainda, erro sem código)
    # não dizem nada sobre o backup estar parado: o aviso fica como está.


def registrar_erro(erro: CloudSyncError) -> None:
    """Registra um ciclo que terminou em erro. Sem código (rede) não vira aviso."""
    if erro.code:
        registrar(erro.code)


def ler() -> Optional[dict]:
    """O aviso do último ciclo, ou None."""
    return _ultimo


def data_do_ultimo_full(status: dict[str, Any]) -> Optional[str]:
    """Data do FULL confirmado mais recente no `historicoEventos` do /status.

    É o "feito em {data}" do aviso do trial (LIC-08 §6.3). Maiúsculas não importam
    ("FULL"/"full"), e a data é lida do primeiro campo que existir.
    """
    datas = []
    for evento in status.get("historicoEventos") or []:
        if str(evento.get("tipo", "")).upper() != "FULL":
            continue
        if str(evento.get("status", "")).upper() != "CONFIRMADO":
            continue
        for campo in ("confirmadoEm", "criadoEm", "dataHora", "data"):
            if evento.get(campo):
                datas.append(str(evento[campo]))
                break
    return max(datas) if datas else None   # datas ISO: a maior é a mais recente
