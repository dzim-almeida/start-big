# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_rota_reset_so_em_dev.py
# DESCRICAO: A rota que apaga o banco (GET /reset/, sem login) nao pode ir
#            para o instalador. Ver `rota_de_reset_liberada` em api.py.
# ---------------------------------------------------------------------------
import importlib
import sys

import pytest

from app.api.v1 import api as api_v1


def _caminhos_do_router(modulo) -> list[str]:
    return [getattr(r, "path", "") for r in modulo.router.routes]


@pytest.fixture
def recarregar_api(monkeypatch):
    """Recarrega api.py com o ambiente pedido e devolve o modulo novo.

    O app dos outros testes ja montou o router antigo; recarregar so cria um
    router novo para inspecionar, e no fim recarrega de novo no ambiente real.
    """
    def _recarregar(*, frozen: bool, app_env: str | None):
        if frozen:
            monkeypatch.setattr(sys, "frozen", True, raising=False)
        else:
            monkeypatch.delattr(sys, "frozen", raising=False)
        if app_env is None:
            monkeypatch.delenv("APP_ENV", raising=False)
        else:
            monkeypatch.setenv("APP_ENV", app_env)
        return importlib.reload(api_v1)

    yield _recarregar
    monkeypatch.undo()
    importlib.reload(api_v1)


def test_exe_empacotado_sem_app_env_nao_tem_reset(recarregar_api):
    """O servidor da loja: tarefa StartBigServer roda o .exe sem APP_ENV."""
    modulo = recarregar_api(frozen=True, app_env=None)
    assert modulo.rota_de_reset_liberada() is False
    assert not any(c.startswith("/reset") for c in _caminhos_do_router(modulo))


def test_sidecar_do_tauri_com_app_env_production_nao_tem_reset(recarregar_api):
    modulo = recarregar_api(frozen=True, app_env="production")
    assert modulo.rota_de_reset_liberada() is False
    assert not any(c.startswith("/reset") for c in _caminhos_do_router(modulo))


def test_producao_mesmo_sem_frozen_nao_tem_reset(recarregar_api):
    modulo = recarregar_api(frozen=False, app_env="production")
    assert modulo.rota_de_reset_liberada() is False
    assert not any(c.startswith("/reset") for c in _caminhos_do_router(modulo))


def test_desenvolvimento_continua_com_reset(recarregar_api):
    """`fastapi dev` na maquina do programador: a rota segue la."""
    modulo = recarregar_api(frozen=False, app_env=None)
    assert modulo.rota_de_reset_liberada() is True
    assert any(c.startswith("/reset") for c in _caminhos_do_router(modulo))
