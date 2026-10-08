# ---------------------------------------------------------------------------
# ARQUIVO: test/core/test_regras_preco.py
# DESCRIÇÃO: A conta das regras de preço por quantidade (§6.1), sem banco.
# ---------------------------------------------------------------------------

from app.core.regras_preco import EmbalagemR1, FaixaR2, LevePagueR3, calcular, reais

FD15 = EmbalagemR1("FD", 15, 5000)


def test_r1_exemplo_do_plano_17_latas_sao_1_fardo_mais_2():
    r = calcular(17, 450, embalagens=[FD15])
    # 50,00 + 2 × 4,50 = 59,00; cheio 76,50 → desconto 17,50
    assert (r.regra, r.total, r.desconto, r.preco_unitario) == ("R1", 5900, 1750, None)
    assert r.descricao == "Preço de 1 FD (15 un)"


def test_r1_nao_completa_o_fardo_nao_aplica():
    assert calcular(14, 450, embalagens=[FD15]) is None


def test_r1_embalagem_mais_cara_que_as_unidades_nao_conta():
    assert calcular(15, 300, embalagens=[FD15]) is None


def test_r1_usa_primeiro_a_embalagem_de_melhor_preco_por_unidade():
    cx = EmbalagemR1("CX", 30, 9000)  # 3,00 a unidade — melhor que o FD (3,33)
    r = calcular(47, 450, embalagens=[FD15, cx])
    # 1 CX (30) + 1 FD (15) + 2 un = 90,00 + 50,00 + 9,00
    assert r.total == 14900
    assert r.descricao == "Preço de 1 CX (30 un) + 1 FD (15 un)"


def test_r2_faixa_em_escada_pega_a_maior_alcancada():
    faixas = [FaixaR2(6, 380), FaixaR2(24, 350)]
    assert calcular(5, 450, faixas=faixas) is None
    r = calcular(6, 450, faixas=faixas)
    assert (r.regra, r.preco_unitario, r.total, r.desconto) == ("R2", 380, 2280, 0)
    assert r.descricao == "A partir de 6 un: R$ 3,80"
    assert calcular(30, 450, faixas=faixas).preco_unitario == 350


def test_r3_leve_3_pague_2():
    r = calcular(7, 450, leve_pague=[LevePagueR3(3, 2)])
    # 2 grupos de 3 → 2 grátis
    assert (r.regra, r.desconto, r.total) == ("R3", 900, 2250)
    assert r.descricao == "Leve 3, pague 2: 2 grátis"
    assert calcular(2, 450, leve_pague=[LevePagueR3(3, 2)]) is None


def test_conflito_menor_preco_e_o_padrao():
    # 15 un: R1 = 50,00; R2 (a partir de 6 a 3,80) = 57,00; R3 (leve 3 pague 2) = 45,00
    todas = dict(embalagens=[FD15], faixas=[FaixaR2(6, 380)], leve_pague=[LevePagueR3(3, 2)])
    assert calcular(15, 450, **todas).regra == "R3"


def test_conflito_por_ordem_do_dono():
    todas = dict(embalagens=[FD15], faixas=[FaixaR2(6, 380)], leve_pague=[LevePagueR3(3, 2)])
    r = calcular(15, 450, conflito="ORDEM", ordem=["R2", "R1", "R3"], **todas)
    assert (r.regra, r.total) == ("R2", 5700)
    # A primeira da ordem que não serve é pulada.
    r = calcular(5, 450, conflito="ORDEM", ordem=["R2", "R3", "R1"], **todas)
    assert r.regra == "R3"


def test_ordem_incompleta_completa_com_a_padrao():
    r = calcular(15, 450, conflito="ORDEM", ordem=["R3"], embalagens=[FD15])
    assert r.regra == "R1"


def test_empate_no_menor_preco_segue_a_ordem():
    # FD de 3 por 9,00 e leve 3 pague 2 dão o mesmo total para 3 un.
    r = calcular(3, 450, embalagens=[EmbalagemR1("FD", 3, 900)], leve_pague=[LevePagueR3(3, 2)])
    assert r.regra == "R1"
    r = calcular(3, 450, ordem=["R3", "R1", "R2"],
                 embalagens=[EmbalagemR1("FD", 3, 900)], leve_pague=[LevePagueR3(3, 2)])
    assert r.regra == "R3"


def test_nada_ligado_ou_uma_unidade_nao_aplica():
    assert calcular(17, 450) is None
    assert calcular(1, 450, leve_pague=[LevePagueR3(1, 0)]) is None


def test_reais():
    assert reais(123456) == "R$ 1.234,56"
    assert reais(5) == "R$ 0,05"
