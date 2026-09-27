# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/etiquetas/test_permissoes_etiquetas.py
# DESCRIÇÃO: Linha "Etiquetas" da tela de Cargos — o que cada caixa libera, e
#            a migração que a concede a quem já tinha Produtos.
# ---------------------------------------------------------------------------

import importlib.util
import json
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi.testclient import TestClient

from app.core.depends import get_current_active_user
from app.main import app

URL = "/api/v1/etiquetas"
DEFINICAO = {
    "pagina": {"tipo": "bobina", "largura_mm": 50, "altura_mm": 30},
    "elementos": [{"tipo": "texto", "x": 2, "y": 2, "w": 40, "h": 6}],
}


@pytest.fixture
def como(header_com_token):
    """Troca o usuário logado por um funcionário com as permissões dadas."""
    def _como(**permissoes):
        token = {"sub": "99", "empresa_id": 1, "cargo": "Estoquista", "is_master": False, "permissoes": permissoes}
        app.dependency_overrides[get_current_active_user] = lambda: token
    yield _como
    app.dependency_overrides.pop(get_current_active_user, None)


def test_so_produtos_nao_da_mais_acesso_as_etiquetas(client: TestClient, como):
    como(produto=True, view_products=True)
    assert client.get(f"{URL}/modelos").status_code == 403
    assert client.get(f"{URL}/envio/remetente").status_code == 403


def test_visualizar_lista_e_imprime_mas_nao_cria(client: TestClient, como):
    como(etiqueta=True, view_labels=True)
    assert client.get(f"{URL}/modelos").status_code == 200
    assert client.get(f"{URL}/envio/remetente").status_code == 200
    assert client.post(f"{URL}/modelos", json={"nome": "X", "definicao": DEFINICAO}).status_code == 403


def test_gerenciar_cria_mas_so_excluir_apaga(client: TestClient, como):
    como(etiqueta=True, manage_labels=True)
    criado = client.post(f"{URL}/modelos", json={"nome": "Gôndola", "definicao": DEFINICAO})
    assert criado.status_code == 201, criado.text
    assert client.delete(f"{URL}/modelos/{criado.json()['id']}").status_code == 403

    como(etiqueta=True, delete_labels=True)
    assert client.delete(f"{URL}/modelos/{criado.json()['id']}").status_code == 204


def test_envio_de_venda_continua_exigindo_permissao_de_venda(client: TestClient, como):
    como(etiqueta=True, view_labels=True)
    assert client.get(f"{URL}/envio/venda/1").status_code == 403
    assert client.get(f"{URL}/envio/os/1").status_code == 403
    assert client.get(f"{URL}/envio/origens").json() == []


# --- migração -------------------------------------------------------------

def _migracao():
    caminho = Path(__file__).parents[4] / "alembic" / "versions" / "z9a0b1c2d3e4_permissao_etiquetas.py"
    spec = importlib.util.spec_from_file_location("migracao_etiquetas", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_migracao_concede_a_quem_tinha_produtos_e_nao_toca_o_resto():
    m = _migracao()
    engine = sa.create_engine("sqlite://")
    cargos = {
        1: {"produto": True, "view_products": True},        # tinha Produtos → ganha
        2: {"view_products": True},                          # só a caixa → ganha
        3: {"venda": True},                                  # sem Produtos → nada
        4: {"produto": True, "etiqueta": False},             # já configurado na tela nova → nada
        5: {"all": True},                                    # administrador → nada
    }
    with engine.begin() as conexao:
        conexao.exec_driver_sql("CREATE TABLE cargos (id INTEGER PRIMARY KEY, permissoes JSON NOT NULL)")
        for cargo_id, perms in cargos.items():
            conexao.execute(sa.text("INSERT INTO cargos VALUES (:i, :p)"), {"i": cargo_id, "p": json.dumps(perms)})
        with Operations.context(MigrationContext.configure(conexao)):
            m.upgrade()
            m.upgrade()  # rodar de novo não muda nada
        resultado = {i: json.loads(p) for i, p in conexao.execute(sa.text("SELECT id, permissoes FROM cargos"))}

    for cargo_id in (1, 2):
        assert all(resultado[cargo_id][k] is True for k in m.CHAVES_ETIQUETAS), resultado[cargo_id]
    assert "etiqueta" not in resultado[3]
    assert resultado[4] == cargos[4]
    assert resultado[5] == cargos[5]
