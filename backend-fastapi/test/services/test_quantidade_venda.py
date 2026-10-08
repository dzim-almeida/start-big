"""
Regras de quantidade da venda fracionada (docs/venda-fracionada-plano.md).

O último teste amarra a lista de unidades do backend à do frontend: as duas
precisam ser iguais, ou a tela oferece 3,5 onde o servidor recusa.
"""
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.helpers.exceptions import BadRequestException
from app.schemas.quantidade import normalizar_quantidade
from app.services.quantidade_venda import (
    UNIDADES_FRACIONAVEIS, eh_fracionavel, exigir_quantidade_permitida, subtotal_da_linha,
)


def produto(unidade, nome="Produto"):
    return SimpleNamespace(unidade_medida=unidade, nome=nome)


@pytest.mark.parametrize("valor,esperado", [(3, 3), (3.0, 3), (3.5, 3.5), (0.1234, 0.123), (0.1 + 0.2, 0.3), (2.0005, 2.001)])
def test_normalizar(valor, esperado):
    resultado = normalizar_quantidade(valor)
    assert resultado == esperado and type(resultado) is type(esperado)


@pytest.mark.parametrize("q,v,esperado", [(3, 450, 1350), (3.5, 3000, 10500), (3.5, 1001, 3504), (0.123, 3000, 369), (2.5, 1, 3)])
def test_subtotal(q, v, esperado):
    assert subtotal_da_linha(q, v) == esperado


def test_inteira_passa_em_qualquer_produto():
    exigir_quantidade_permitida(3, produto("UN"))
    exigir_quantidade_permitida(3.0, None)
    exigir_quantidade_permitida(2, produto("UN"), fator_embalagem=12)


@pytest.mark.parametrize("unidade", ["kg", " KG ", "m²", "M³", "cm", "ml"])
def test_fracionaveis(unidade):
    assert eh_fracionavel(produto(unidade))
    exigir_quantidade_permitida(1.5, produto(unidade))


@pytest.mark.parametrize("unidade", ["UN", "CX", "PC", None, ""])
def test_nao_fracionaveis(unidade):
    with pytest.raises(BadRequestException):
        exigir_quantidade_permitida(1.5, produto(unidade))


def test_embalagem_e_avulso_sao_inteiros():
    with pytest.raises(BadRequestException):
        exigir_quantidade_permitida(1.5, produto("KG"), fator_embalagem=12)
    with pytest.raises(BadRequestException):
        exigir_quantidade_permitida(1.5, None)


def test_lista_igual_a_do_frontend():
    ts = (Path(__file__).resolve().parents[3] / "frontend/src/shared/utils/quantidade.ts").read_text(encoding="utf-8")
    lista = re.search(r"UNIDADES_FRACIONADAS = new Set\(\[([^\]]*)\]\)", ts).group(1)
    assert set(re.findall(r"'([^']+)'", lista)) == set(UNIDADES_FRACIONAVEIS)
