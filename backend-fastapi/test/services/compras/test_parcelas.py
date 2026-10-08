# ---------------------------------------------------------------------------
# ARQUIVO: test/services/compras/test_parcelas.py
# DESCRIÇÃO: Condição de pagamento → parcelas do pedido (plano, D8a).
# ---------------------------------------------------------------------------

import pytest

from app.services.compras.parcelas import Parcela, dias_da_condicao, gerar_parcelas


def test_30_60_90_fecha_o_total_exato_com_o_resto_na_ultima():
    # R$ 100,00 em 3: 33,33 + 33,33 + 33,34.
    assert gerar_parcelas(10000, "30/60/90") == [
        Parcela(1, 30, 3333), Parcela(2, 60, 3333), Parcela(3, 90, 3334)]
    assert sum(p.valor for p in gerar_parcelas(10001, "30/60/90")) == 10001


@pytest.mark.parametrize("texto", ["", None, "0", "à vista", "A Vista", "avista"])
def test_a_vista_e_uma_parcela_no_dia(texto):
    assert gerar_parcelas(5000, texto) == [Parcela(1, 0, 5000)]


@pytest.mark.parametrize("texto, dias", [
    ("28 dd", [28]),
    ("30 60 90", [30, 60, 90]),
    ("30,60", [30, 60]),
    ("0/30", [0, 30]),
    (" 21 / 42 dias ", [21, 42]),
])
def test_entende_o_jeito_que_o_lojista_escreve(texto, dias):
    assert dias_da_condicao(texto) == dias


@pytest.mark.parametrize("texto", ["boleto", "30/abc", "60/30", "30/30", "400", "/".join(["30"] * 25)])
def test_recusa_o_que_nao_da_para_entender_em_vez_de_adivinhar(texto):
    with pytest.raises(ValueError):
        dias_da_condicao(texto)


def test_total_zero_gera_parcelas_zeradas():
    assert [p.valor for p in gerar_parcelas(0, "30/60")] == [0, 0]
