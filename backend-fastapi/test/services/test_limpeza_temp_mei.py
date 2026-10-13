# ---------------------------------------------------------------------------
# ARQUIVO: test/services/test_limpeza_temp_mei.py
# DESCRICAO: A limpeza das pastas _MEI* do boot so apaga o que sobrou de
#            execucao ENCERRADA do StartBig. Ver `limpar_temp_data`.
# ---------------------------------------------------------------------------
import os
import sys

import pytest

from app.services.sistema.limpeza_temporal import limpar_temp_data


def _pasta_mei(raiz, nome, *, do_startbig=True):
    pasta = raiz / nome
    pasta.mkdir()
    if do_startbig:
        (pasta / "alembic").mkdir()
        (pasta / "dist").mkdir()
        (pasta / "alembic" / "env.py").write_text("# migracoes", encoding="utf-8")
    else:
        (pasta / "outro_app.dll").write_text("x", encoding="utf-8")
    return pasta


@pytest.fixture
def como_exe(monkeypatch):
    """Simula o .exe do PyInstaller: `sys.frozen` e a propria pasta de extracao."""
    def _ligar(propria=None):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", str(propria) if propria else None, raising=False)
    return _ligar


def test_fora_do_exe_nao_apaga_nada(tmp_path, monkeypatch):
    """Desenvolvimento e testes: a suite derrubava os sidecars de teste."""
    monkeypatch.delattr(sys, "frozen", raising=False)
    sobra = _pasta_mei(tmp_path, "_MEI111")
    assert limpar_temp_data(str(tmp_path)) == 0
    assert sobra.exists()


def test_apaga_sobra_do_startbig_encerrado(tmp_path, como_exe):
    como_exe()
    sobra = _pasta_mei(tmp_path, "_MEI222")
    assert limpar_temp_data(str(tmp_path)) == 1
    assert not sobra.exists()
    assert not (tmp_path / "_MEI222.removendo").exists()


def test_nunca_mexe_na_pasta_de_outro_programa(tmp_path, como_exe):
    como_exe()
    alheia = _pasta_mei(tmp_path, "_MEI333", do_startbig=False)
    assert limpar_temp_data(str(tmp_path)) == 0
    assert alheia.exists()


def test_nunca_apaga_a_propria_pasta(tmp_path, como_exe):
    propria = _pasta_mei(tmp_path, "_MEI444")
    como_exe(propria)
    assert limpar_temp_data(str(tmp_path)) == 0
    assert propria.exists()


@pytest.mark.skipif(sys.platform != "win32", reason="a trava por renomear e do Windows")
def test_pasta_em_uso_por_outro_processo_fica(tmp_path, como_exe):
    """Segunda instancia viva: arquivo aberto la dentro impede renomear a pasta."""
    como_exe()
    viva = _pasta_mei(tmp_path, "_MEI555")
    with open(viva / "alembic" / "env.py", encoding="utf-8"):
        assert limpar_temp_data(str(tmp_path)) == 0
        assert (viva / "alembic" / "env.py").exists()
    assert os.path.isdir(viva)
