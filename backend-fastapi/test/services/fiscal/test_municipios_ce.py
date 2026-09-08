# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_municipios_ce.py
# DESCRIÇÃO: Base embarcada dos municípios do Ceará (cMun da NF-e).
#
# O `cMun` é obrigatório no XML e o payload nunca o enviava: mandava só o NOME
# do município, e quem resolvia era a integradora — que erra com homônimos.
# ---------------------------------------------------------------------------

import pytest

from app.services.fiscal.derivacao.bases.municipios_ce import (
    MUNICIPIOS_CE,
    UF,
    codigo_ibge,
)


def test_o_ceara_tem_184_municipios():
    """Conferência contra o número oficial — pega uma geração truncada."""
    assert len(MUNICIPIOS_CE) == 184


@pytest.mark.parametrize("cidade, esperado", [
    ("Fortaleza", "2304400"),
    ("Caucaia", "2303709"),
    ("Juazeiro do Norte", "2307304"),
    ("Sobral", "2312908"),
])
def test_codigos_conhecidos(cidade, esperado):
    assert codigo_ibge(cidade) == esperado


@pytest.mark.parametrize("variante", [
    "JUAZEIRO DO NORTE",
    "juazeiro do norte",
    "  Juazeiro do Norte  ",
    "Juazeiro  do   Norte",
])
def test_caixa_acento_e_espacos_nao_atrapalham(variante):
    assert codigo_ibge(variante) == "2307304"


def test_acento_e_normalizado():
    assert codigo_ibge("Itapajé") == codigo_ibge("Itapaje")


def test_todo_codigo_tem_7_digitos_e_prefixo_do_ceara():
    """Os códigos do CE começam em 23 — um prefixo errado é UF trocada."""
    for chave, cod in MUNICIPIOS_CE.items():
        assert len(cod) == 7, chave
        assert cod.startswith("23"), chave


def test_fora_do_ceara_devolve_nada_em_vez_de_adivinhar():
    """
    Uma tabela estadual respondendo sobre outro estado é PIOR que não
    responder: devolveria o código do homônimo errado, que é exatamente o
    problema que esta base existe para evitar.
    """
    assert codigo_ibge("Fortaleza", "SP") is None
    assert codigo_ibge("Fortaleza", "PE") is None
    assert codigo_ibge("Fortaleza", UF) == "2304400"


@pytest.mark.parametrize("cidade", ["", "   ", None, "Cidade Que Nao Existe"])
def test_cidade_desconhecida_nao_inventa_codigo(cidade):
    assert codigo_ibge(cidade) is None
