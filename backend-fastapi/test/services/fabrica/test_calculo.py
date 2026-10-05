# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fabrica/test_calculo.py
# DESCRIÇÃO: Conversão consumo → unidade de compra (docs/marcenaria-fabrica-plano.md, §5).
#
# Os exemplos da §5 do plano, um por teste. Erro aqui compra a menos ou a mais
# em silêncio (RNC04).
# ---------------------------------------------------------------------------

import pytest

from app.services.fabrica.calculo import (
    LinhaDeMaterial,
    consumo_com_perda,
    custo_do_material,
    quantidade_de_compra,
    quantidades_por_insumo,
)

CHAPA = 2750 * 1850          # 5.087.500 mm²
M2 = 1_000_000               # mm² em 1 m²
ROLO_50M = 50_000            # mm
PERDA_10 = 1000              # pontos-base


def test_exemplo_do_resumo_12m2_com_10pct_da_3_chapas():
    usado = consumo_com_perda(12 * M2, PERDA_10, sofre_perda=True)
    assert usado == 13_200_000
    assert quantidade_de_compra(usado, CHAPA) == 3


def test_soma_antes_de_arredondar_tres_moveis_de_1m2_cabem_numa_chapa():
    linhas = [LinhaDeMaterial(produto_id=1, consumo=M2, sofre_perda=True, consumo_por_unidade=CHAPA)] * 3
    assert quantidades_por_insumo(linhas, PERDA_10) == {1: 1}


def test_insumo_sem_perda_nao_ganha_perda():
    assert consumo_com_perda(24, PERDA_10, sofre_perda=False) == 24
    assert quantidade_de_compra(24, 1) == 24


def test_fita_37_5m_com_perda_cabe_num_rolo_de_50m():
    usado = consumo_com_perda(37_500, PERDA_10, sofre_perda=True)
    assert usado == 41_250
    assert quantidade_de_compra(usado, ROLO_50M) == 1


def test_consumo_exato_nao_arredonda_para_cima():
    assert quantidade_de_compra(2 * CHAPA, CHAPA) == 2
    assert quantidade_de_compra(2 * CHAPA + 1, CHAPA) == 3


def test_custo_do_movel_usa_a_fracao_de_chapa():
    # 1 m² + 10% de uma chapa de R$ 300,00 (5,0875 m²) = 0,2162 chapa = R$ 64,86
    assert custo_do_material(M2, PERDA_10, True, CHAPA, 30000) == 6486


def test_perda_arredonda_o_consumo_para_cima():
    # 1 mm² com 10% = 1,1 → 2: nunca some material no arredondamento
    assert consumo_com_perda(1, PERDA_10, sofre_perda=True) == 2


def test_quantidades_por_insumo_separa_os_produtos():
    linhas = [
        LinhaDeMaterial(1, 12 * M2, True, CHAPA),
        LinhaDeMaterial(2, 24, False, 1),
        LinhaDeMaterial(1, M2, True, CHAPA),
    ]
    # MDF: 13 m² × 1,1 = 14,3 m² → 2,81 → 3 chapas; dobradiça: 24
    assert quantidades_por_insumo(linhas, PERDA_10) == {1: 3, 2: 24}


@pytest.mark.parametrize("perda", [-1, 5001])
def test_perda_fora_da_faixa_e_erro(perda):
    with pytest.raises(ValueError):
        consumo_com_perda(M2, perda, sofre_perda=True)


def test_rendimento_zero_e_erro():
    with pytest.raises(ValueError):
        quantidade_de_compra(M2, 0)
    with pytest.raises(ValueError):
        custo_do_material(M2, 0, False, 0, 100)
