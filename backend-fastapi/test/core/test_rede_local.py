"""
Testes da rede da loja (LIC-04 §6.5, D-21): a API local só aceita quem está nas
redes privadas da loja ou no próprio computador.

O `TestClient` permite escolher o endereço de quem "chama" (parâmetro `client`),
então dá para simular um caixa da loja ou alguém da internet sem rede de verdade.
"""
import os
import re

import pytest  # type: ignore
from fastapi.testclient import TestClient  # type: ignore

from app.core.rede_local import REDES_DA_LOJA
from app.main import app

# Caminho do instalador (hooks.nsh), que repete a lista de redes no firewall.
_HOOKS_NSH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..",
    "frontend", "src-tauri", "nsis", "extend", "hooks.nsh",
)


def _chamar_de(endereco: str):
    """Faz um GET na rota de saúde fingindo que a chamada veio de `endereco`."""
    # Sem o `with`, o TestClient não roda o startup (lifespan): mais rápido e
    # não abre banco nenhum. O middleware roda igual.
    cliente = TestClient(app, client=(endereco, 50000))
    return cliente.get("/api/health")


def test_ct12_caixa_da_rede_privada_passa():
    # Um caixa típico de loja, numa rede 192.168.x.x
    assert _chamar_de("192.168.1.20").status_code == 200


def test_ct13_endereco_publico_recebe_403_no_formato_do_projeto():
    resposta = _chamar_de("8.8.8.8")
    assert resposta.status_code == 403
    # Mesmo formato dos outros erros que a tela trata por código (D-29)
    assert resposta.json() == {
        "error": "Fora da rede da loja",
        "detail": {
            "codigo": "FORA_DA_REDE_DA_LOJA",
            "mensagem": "Esta API só aceita conexões da rede da loja.",
        },
    }


@pytest.mark.parametrize("endereco", ["127.0.0.1", "::1"])
def test_ct14_proprio_computador_passa(endereco):
    assert _chamar_de(endereco).status_code == 200


def test_ct14_texto_que_nao_e_ip_e_recusado():
    # "testclient" é o nome que o TestClient usa por padrão: não é um IP
    assert _chamar_de("nao-e-um-ip").status_code == 403


def test_ct15_endereco_automatico_do_windows_passa():
    # 169.254.x.x: o Windows se dá esse endereço quando o roteador não entrega IP
    assert _chamar_de("169.254.10.5").status_code == 200


@pytest.mark.parametrize("endereco", ["10.0.0.7", "172.16.4.1", "172.31.255.254"])
def test_outras_redes_privadas_passam(endereco):
    assert _chamar_de(endereco).status_code == 200


@pytest.mark.parametrize("endereco", ["172.32.0.1", "100.64.0.1", "2001:db8::1"])
def test_vizinhos_das_redes_privadas_sao_recusados(endereco):
    # Bordas: 172.32 já está fora do 172.16/12; 100.64 é rede de operadora
    assert _chamar_de(endereco).status_code == 403


def test_ct16_lista_do_instalador_igual_a_do_middleware():
    # O hooks.nsh define: !define REDES_DA_LOJA "10.0.0.0/8,..."
    with open(_HOOKS_NSH, encoding="utf-8") as arquivo:
        conteudo = arquivo.read()
    achado = re.search(r'!define\s+REDES_DA_LOJA\s+"([^"]+)"', conteudo)
    assert achado, "hooks.nsh não define REDES_DA_LOJA"
    redes_do_instalador = achado.group(1).split(",")
    assert redes_do_instalador == REDES_DA_LOJA


def test_firewall_do_backend_usa_a_mesma_lista(monkeypatch):
    # firewall_cfg chama o `netsh`. Aqui trocamos as chamadas por "gravadores",
    # para ver os comandos sem mexer no firewall de verdade.
    from app.core import system

    comandos = []
    monkeypatch.setattr(system, "_exec", lambda comando, descricao: comandos.append(comando) or True)
    monkeypatch.setattr(system.subprocess, "run", lambda *a, **k: None)

    system.firewall_cfg(8080)

    esperado = "remoteip=" + ",".join(REDES_DA_LOJA)
    # As duas regras criadas (API e mDNS) levam o remoteip da lista da loja
    assert len(comandos) == 2
    assert all(esperado in comando for comando in comandos)
