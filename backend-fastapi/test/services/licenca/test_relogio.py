# ---------------------------------------------------------------------------
# ARQUIVO: test/services/licenca/test_relogio.py
# DESCRICAO: LIC-02 (CT-13 a CT-16) -- relogio do computador que voltou no tempo.
#
# Regra (ACORDO D-05): AVISAR e continuar, usando o maior horario ja visto nas
# contas offline. Bloquear pararia o PDV no meio do expediente.
# ---------------------------------------------------------------------------

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.services.licenca import relogio

AGORA = datetime(2026, 11, 19, 15, 0, tzinfo=timezone.utc)


def _licenca(visto):
    """Licenca de mentira: so o campo que o relogio usa."""
    return SimpleNamespace(ultimo_horario_visto=visto)


def test_ct13_primeiro_uso_usa_o_agora_sem_aviso():
    usado, recuou = relogio.verificar_relogio(_licenca(None), AGORA)

    assert usado == AGORA
    assert recuou is False


def test_ct14_relogio_recuado_10_min_avisa_e_usa_o_ultimo_horario_visto():
    visto = AGORA + timedelta(minutes=10)      # ja vimos um horario 10 min "a frente"

    usado, recuou = relogio.verificar_relogio(_licenca(visto), AGORA)

    assert recuou is True
    assert usado == visto


def test_ct15_relogio_recuado_2_min_fica_dentro_da_tolerancia():
    visto = AGORA + timedelta(minutes=2)

    usado, recuou = relogio.verificar_relogio(_licenca(visto), AGORA)

    assert recuou is False
    assert usado == AGORA


def test_ct16_horario_novo_maior_avanca_o_ultimo_visto():
    licenca = _licenca(AGORA)
    depois = AGORA + timedelta(hours=1)

    relogio.registrar_horario(licenca, depois)
    assert licenca.ultimo_horario_visto == depois

    relogio.registrar_horario(licenca, AGORA)      # horario menor: nao volta
    assert licenca.ultimo_horario_visto == depois


def test_horario_gravado_sem_fuso_e_tratado_como_utc():
    """O SQLite devolve datas sem fuso; elas foram gravadas em UTC."""
    visto_sem_fuso = (AGORA + timedelta(minutes=10)).replace(tzinfo=None)

    usado, recuou = relogio.verificar_relogio(_licenca(visto_sem_fuso), AGORA)

    assert recuou is True
    assert usado == AGORA + timedelta(minutes=10)
