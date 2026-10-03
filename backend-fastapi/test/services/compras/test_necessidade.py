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
    PRAZO_PADRAO_DIAS,
    OfertaFornecedor,
    dividir_para_cima,
    economia_percentual,
    mais_barato,
    preco_por_unidade,
    sugerir_compra,
    sugerir_por_vendas,
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


# --- fase 5: pela média de vendas ---------------------------------------------------


def test_vende_10_por_dia_prazo_3_cobre_30_dias():
    # Ponto de pedido = 10 × 3 = 30; alvo = 10 × 33 = 330. Saldo 25 → faltam 305 → 26 fardos de 12.
    assert sugerir_por_vendas(saldo=25, em_pedido=0, media_diaria=10, prazo_dias=3, cobertura_dias=30,
                              minimo=None, fator=12) == 26


def test_acima_do_ponto_de_pedido_nao_compra():
    assert sugerir_por_vendas(saldo=31, em_pedido=0, media_diaria=10, prazo_dias=3, cobertura_dias=30,
                              minimo=None, fator=1) == 0


def test_o_que_esta_a_caminho_conta_tambem_aqui():
    assert sugerir_por_vendas(saldo=10, em_pedido=300, media_diaria=10, prazo_dias=3, cobertura_dias=30,
                              minimo=None, fator=1) == 0


def test_minimo_vira_estoque_de_seguranca():
    # Ponto = 10 × 3 + 20 = 50; alvo = 10 × 33 + 20 = 350. Saldo 45 → 305.
    assert sugerir_por_vendas(saldo=45, em_pedido=0, media_diaria=10, prazo_dias=3, cobertura_dias=30,
                              minimo=20, fator=1) == 305


def test_sem_prazo_conta_uma_semana():
    # Ponto = 2 × 7 = 14; alvo = 2 × (7 + 30) = 74. Saldo 14 → 60.
    assert PRAZO_PADRAO_DIAS == 7
    assert sugerir_por_vendas(saldo=14, em_pedido=0, media_diaria=2, prazo_dias=None, cobertura_dias=30,
                              minimo=None, fator=1) == 60


def test_sem_venda_nao_sugere():
    assert sugerir_por_vendas(saldo=0, em_pedido=0, media_diaria=0, prazo_dias=3, cobertura_dias=30,
                              minimo=10, fator=1) == 0


def test_media_fracionada_arredonda_para_cima():
    # 0,5/dia, prazo 2 → ponto 1; alvo 0,5 × 32 = 16. Saldo 1 → 15.
    assert sugerir_por_vendas(saldo=1, em_pedido=0, media_diaria=0.5, prazo_dias=2, cobertura_dias=30,
                              minimo=None, fator=1) == 15
