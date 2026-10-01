# ---------------------------------------------------------------------------
# ARQUIVO: test/core/test_nfe_xml.py
# DESCRIÇÃO: Leitura da XML da NF-e do fornecedor (entrada por XML, fase 1).
# ---------------------------------------------------------------------------

from datetime import date
from decimal import Decimal

import pytest

from app.core.nfe_xml import NotaInvalida, custo_por_unidade, ler_nfe
from test.core.nfe_exemplo import CHAVE, CNPJ_FORNECEDOR, CNPJ_LOJA, item_caixa_sem_fator, nota


def test_le_cabecalho_fornecedor_e_parcelas():
    lida = ler_nfe(nota())
    assert (lida.chave, lida.numero, lida.serie, lida.emissao) == (CHAVE, "1234", "1", date(2026, 9, 30))
    assert lida.valor_total == 13000
    assert lida.destinatario_documento == CNPJ_LOJA
    e = lida.emitente
    assert (e.documento, e.nome, e.fantasia, e.ie, e.cidade, e.uf) == (
        CNPJ_FORNECEDOR, "DISTRIBUIDORA DE BEBIDAS LTDA", "DISTRIBEB", "123456789110", "SAO PAULO", "SP")
    assert [(d.numero, d.vencimento, d.valor) for d in lida.duplicatas] == [
        ("001", date(2026, 10, 31), 6300), ("002", date(2026, 11, 30), 6300)]


def test_caixa_com_st_e_frete_vira_custo_por_unidade():
    cerveja = ler_nfe(nota()).itens[0]
    assert (cerveja.codigo, cerveja.ean, cerveja.ean_tributavel) == ("CERV-CX12", "17891000000008", "7891000000001")
    assert (cerveja.unidade, cerveja.quantidade, cerveja.fator_sugerido()) == ("CX", Decimal("2.0000"), 12)
    assert (cerveja.ncm, cerveja.cest, cerveja.cst_icms, cerveja.tinha_st, cerveja.monofasico) == (
        "22030000", "0302100", "10", True, True)
    # 96,00 − 6,00 + 2,00 + 12,00 de ST = 104,00 ÷ 24 latas = 4,333…
    assert cerveja.custo_total == 10400
    assert custo_por_unidade(cerveja, 12) == 433


def test_sem_gtin_ipi_e_simples_sem_st():
    biscoito = ler_nfe(nota()).itens[1]
    assert (biscoito.ean, biscoito.ean_tributavel, biscoito.fator_sugerido()) == (None, None, 1)
    assert (biscoito.cst_icms, biscoito.tinha_st, biscoito.monofasico) == ("102", False, False)
    assert biscoito.custo_total == 2600  # 25,00 + 1,00 de IPI
    assert custo_por_unidade(biscoito, 1) == 260


def test_nota_sem_protocolo_e_sem_duplicata():
    lida = ler_nfe(nota(proc=False, duplicatas=False))
    assert lida.chave == CHAVE and lida.duplicatas == []


@pytest.mark.parametrize("xml, trecho", [
    (nota(modelo="65"), "NFC-e"),
    (nota(tp_nf="0"), "entrada emitida pela própria loja"),
    (nota(itens=""), "não tem itens"),
    (nota(chave="123"), "chave de acesso"),
    ("<nao é xml", "XML válido"),
    ("<raiz/>", "não é uma NF-e"),
    ('<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><NFe>&a;</NFe>', "não permitidas"),
])
def test_recusa_o_que_nao_e_nota_de_compra(xml, trecho):
    with pytest.raises(NotaInvalida, match=trecho):
        ler_nfe(xml)


def test_caixa_sem_fator_na_nota_e_duzia():
    [caixa] = ler_nfe(nota(item_caixa_sem_fator())).itens
    assert (caixa.unidade_de_embalagem, caixa.fator_sugerido()) == (True, 1)  # a nota não diz
    [duzia] = ler_nfe(nota(item_caixa_sem_fator(unidade="DZ"))).itens
    assert duzia.fator_sugerido() == 12
    biscoito = ler_nfe(nota()).itens[1]
    assert biscoito.unidade_de_embalagem is False
