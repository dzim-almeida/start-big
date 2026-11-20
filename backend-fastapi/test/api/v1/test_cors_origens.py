"""
Testes do CORS com lista fechada de origens (LIC-04 §6.1, D-18).

"Preflight" é a pergunta que o navegador faz (método OPTIONS) antes de uma
chamada vinda de outra origem. Se a resposta não trouxer o cabeçalho
`Access-Control-Allow-Origin` com a origem dele, o navegador bloqueia a chamada.
"""
import pytest  # type: ignore
from fastapi.testclient import TestClient  # type: ignore

from app.main import app

# Chamada vinda do próprio computador, para passar pelo middleware de rede.
_cliente = TestClient(app, client=("127.0.0.1", 50000))


def _preflight(origem: str):
    """Simula o OPTIONS que o navegador manda antes de um POST com Authorization."""
    return _cliente.options(
        "/api/health",
        headers={
            "Origin": origem,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        },
    )


def test_ct01_origem_de_fora_nao_recebe_permissao():
    resposta = _preflight("http://evil.example")
    assert "access-control-allow-origin" not in resposta.headers


def test_ct02_origem_do_dev_e_devolvida():
    resposta = _preflight("http://localhost:1420")
    assert resposta.headers.get("access-control-allow-origin") == "http://localhost:1420"


def test_ct03_origem_curinga_nao_recebe_nada():
    resposta = _preflight("*")
    assert "access-control-allow-origin" not in resposta.headers


@pytest.mark.parametrize("origem", ["http://tauri.localhost", "https://tauri.localhost"])
def test_ct04_origem_da_janela_tauri_e_devolvida(origem):
    resposta = _preflight(origem)
    assert resposta.headers.get("access-control-allow-origin") == origem


def test_get_simples_de_fora_nao_recebe_permissao():
    # Mesmo sem preflight, a resposta não libera a leitura para outra origem
    resposta = _cliente.get("/api/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in resposta.headers


def test_cabecalho_do_caixa_continua_liberado():
    # O caixa manda o próprio HWID em "X-Terminal-HWID" (terminal.service.ts).
    # Se o CORS não listar esse cabeçalho, o navegador barra a chamada no preflight.
    resposta = _cliente.options(
        "/api/health",
        headers={
            "Origin": "http://tauri.localhost",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization, X-Terminal-HWID",
        },
    )
    assert resposta.status_code == 200
    assert "x-terminal-hwid" in resposta.headers.get("access-control-allow-headers", "").lower()
