# ---------------------------------------------------------------------------
# ARQUIVO: services/licenca/relogio.py
# DESCRICAO: Licenca - relogio do computador que voltou no tempo (LIC-02 §6.5,
#            ACORDO D-05). UNICO ponto de decisao sobre o relogio.
#
# O problema: sem internet, a licenca confere os prazos com o relogio do
# computador. Quem atrasa o relogio "ganha" dias. A regra decidida com o dono:
# AVISAR e continuar, usando o maior horario ja visto nas contas offline.
# Bloquear pararia o PDV no meio do expediente, o que custa mais que o risco.
#
# O "maior horario ja visto" fica na coluna `ultimo_horario_visto` da licenca.
# ---------------------------------------------------------------------------

from datetime import datetime, timedelta, timezone

# Pequenos acertos de relogio (sincronizacao do Windows, horario de verao mal
# configurado por minutos) nao geram aviso.
TOLERANCIA = timedelta(minutes=5)


def _em_utc(momento: datetime | None) -> datetime | None:
    """Datas sem fuso vindas do SQLite foram gravadas em UTC: marca o fuso."""
    if momento is not None and momento.tzinfo is None:
        return momento.replace(tzinfo=timezone.utc)
    return momento


def verificar_relogio(licenca, agora: datetime) -> tuple[datetime, bool]:
    """Devolve (horario a usar nas contas offline, se o relogio recuou).

    - Sem horario guardado (primeira vez): usa o agora, sem aviso.
    - Agora mais de 5 min ANTES do maior horario visto: o relogio recuou; usa o
      horario guardado e avisa.
    - Senao: usa o agora.
    """
    visto = _em_utc(licenca.ultimo_horario_visto)
    if visto is None:
        return agora, False
    if agora + TOLERANCIA < visto:
        return visto, True
    return agora, False


def registrar_horario(licenca, agora: datetime) -> None:
    """Guarda sempre o MAIOR horario ja visto (nunca anda para tras)."""
    visto = _em_utc(licenca.ultimo_horario_visto)
    if visto is None or agora > visto:
        licenca.ultimo_horario_visto = agora
