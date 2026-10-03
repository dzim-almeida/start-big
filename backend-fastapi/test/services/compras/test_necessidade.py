# ---------------------------------------------------------------------------
# ARQUIVO: test/services/compras/test_necessidade.py
# DESCRIÇÃO: Contas puras do módulo de Compras (docs/compras-plano.md, §6).
#
# Cada linha da tabela do §6 é um teste. Se alguém mudar a regra e quebrar o
# cálculo, a loja compra a mais ou deixa faltar em silêncio — daí a cobertura.
# ---------------------------------------------------------------------------

from decimal import Decimal

import pytest

from app.services.compras.necessidade import (
    OfertaFornecedor,
    dividir_para_cima,
    economia_percentual,
    mais_barato,
    preco_por_unidade,
    sugerir_compra,
)


# --- sugerir_compra: a tabela do §6 ------------------------------------------

def test_lata_em_fardo_de_12_vai_ate_o_ideal():
    # 5 latas, mínimo 24, ideal 60: faltam 55 → 4,58 fardos → 5 fardos.
    assert sugerir_compra(saldo=5, em_pedido=0, minimo=24, ideal=60, fator=12) == 5


def test_o_que_ja_esta_pedido_conta():
    # 5 + 24 a caminho = 29 > 24: não sugere de novo a cada abertura da tela.
    assert sugerir_compra(saldo=5, em_pedido=24, minimo=24, ideal=60, fator=12) == 0


def test_sem_ideal_repoe_ate_o_minimo():
    assert sugerir_compra(saldo=3, em_pedido=0, minimo=10, ideal=None, fator=1) == 7


def test_sem_minimo_o_produto_nao_participa():
    assert sugerir_compra(saldo=0, em_pedido=0, minimo=None, ideal=None, fator=1) == 0
    assert sugerir_compra(saldo=0, em_pedido=0, minimo=None, ideal=50, fator=1) == 0


def test_produto_por_kg_arredonda_para_cima():
    # 2,5 kg, mínimo 10, ideal 20: faltam 17,5 kg → 18 kg.
    assert sugerir_compra(saldo=2.5, em_pedido=0, minimo=10, ideal=20, fator=1) == 18


def test_exatamente_no_minimo_dispara():
    # "≤ mínimo": chegar no mínimo já é hora de repor.
    assert sugerir_compra(saldo=10, em_pedido=0, minimo=10, ideal=20, fator=1) == 10


def test_um_acima_do_minimo_nao_dispara():
    assert sugerir_compra(saldo=11, em_pedido=0, minimo=10, ideal=20, fator=1) == 0


def test_ideal_menor_que_o_minimo_e_ignorado():
    # Cadastro incoerente (ideal 5 < mínimo 10): vale o mínimo, não compra "menos que zero".
    assert sugerir_compra(saldo=2, em_pedido=0, minimo=10, ideal=5, fator=1) == 8


def test_resto_de_ponto_flutuante_nao_compra_um_fardo_a_mais():
    # O estoque é Float: 0,7 kg + 0,1 kg fica guardado como 0,7999999999999999.
    # Mínimo 12,8 → faltam 12 kg exatos. Sem arredondar no grama, a falta vira
    # 12,0000000000000001 e o teto pede 13 (caso achado ao escrever este teste).
    saldo = 0.7 + 0.1
    assert saldo != 0.8  # a premissa do teste: o resto existe
    assert sugerir_compra(saldo=saldo, em_pedido=0, minimo=12.8, ideal=None, fator=1) == 12


def test_saldo_negativo_compra_o_que_falta_de_verdade():
    # Estoque negativo acontece (venda sem estoque liberada): a falta inclui o buraco.
    assert sugerir_compra(saldo=-6, em_pedido=0, minimo=6, ideal=None, fator=12) == 1


def test_fator_invalido_e_erro_de_programacao():
    with pytest.raises(ValueError):
        sugerir_compra(saldo=0, em_pedido=0, minimo=1, ideal=None, fator=0)


def test_dividir_para_cima():
    assert (dividir_para_cima(7, 2), dividir_para_cima(8, 2), dividir_para_cima(0, 5)) == (4, 4, 0)


# --- mais barato (D18) ---------------------------------------------------------

def test_compara_por_unidade_e_nao_pelo_preco_da_embalagem():
    # Fardo de 12 a R$ 40,00 = 3,33/un; caixa de 24 a R$ 79,00 = 3,29/un → a caixa ganha,
    # mesmo custando quase o dobro por embalagem.
    ofertas = [OfertaFornecedor(1, 4000, 12), OfertaFornecedor(2, 7900, 24)]
    assert mais_barato(ofertas) == 2


def test_um_preco_so_nao_tem_disputa():
    assert mais_barato([OfertaFornecedor(1, 4000, 12), OfertaFornecedor(2, None, 1)]) is None


def test_empate_nao_elege_ninguem():
    # 12 × 3,00 e 24 × 3,00: mesmo preço por unidade.
    assert mais_barato([OfertaFornecedor(1, 3600, 12), OfertaFornecedor(2, 7200, 24)]) is None


def test_preco_zero_nao_conta_como_oferta():
    # Preço zerado é cadastro incompleto, não fornecedor de graça.
    assert mais_barato([OfertaFornecedor(1, 0, 1), OfertaFornecedor(2, 350, 1), OfertaFornecedor(3, 400, 1)]) == 2


def test_preco_por_unidade_nao_arredonda():
    assert preco_por_unidade(4000, 12) == Decimal(4000) / 12


def test_quanto_mais_caro_em_pontos_base():
    # 3,50 contra 3,3333…: 4,76% mais caro → 476 bp.
    assert economia_percentual(Decimal(350), Decimal(4000) / 12) == 476
    assert economia_percentual(Decimal(300), Decimal(300)) == 0
    assert economia_percentual(Decimal(0), Decimal(0)) == 0
