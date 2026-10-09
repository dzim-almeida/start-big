# ---------------------------------------------------------------------------
# ARQUIVO: test/services/marcenaria/test_calculo.py
# DESCRICAO: Motor de calculo do orcamento de marcenaria (Spec 05, §11).
#
#            Os numeros dos cenarios A, B e C foram conferidos a mao e por um
#            prototipo (06/10/2026). Se um deles mudar, e o PRECO que a loja
#            cobra do cliente que mudou: nao ajuste o teste sem entender por que.
# ---------------------------------------------------------------------------

import inspect
import random
import time
from dataclasses import replace
from decimal import Decimal

import pytest

from app.services.marcenaria import calculo
from app.services.marcenaria.calculo import (
    AVISO_HORAS_SEM_CUSTO_HORA,
    AVISO_INSUMO_SEM_CUSTO,
    AVISO_MARGEM_NEGATIVA,
    AVISO_ORCAMENTO_VAZIO,
    AjusteCalc,
    AmbienteCalc,
    InsumoCalc,
    MovelCalc,
    OrcamentoCalc,
    arredondar,
    calcular_orcamento,
    fator_preco,
    repartir_maior_resto,
)

# =========================
# Dados do exemplo (§11.1)
# =========================

# Torre Quente (Figma): mao de obra fixa R$ 300,00, terceirizado R$ 380,00.
INSUMOS_TORRE = (
    InsumoCalc(1400, 28000, True),     # MDF Branco TX 18mm: 1,4 chapa x R$ 280,00
    InsumoCalc(900, 38000, True),      # MDF Freijo 18mm: 0,9 chapa x R$ 380,00
    InsumoCalc(26000, 350, True),      # Fita PVC: 26 m x R$ 3,50
    InsumoCalc(2000, 19500, False),    # Corredica Tandem: 2 pares x R$ 195,00 (ferragem: sem perda)
    InsumoCalc(2800, 8750, False),     # Perfil gola: 2,8 barras x R$ 87,50
)
TORRE = MovelCalc("torre", 1, INSUMOS_TORRE, "FIXA", mao_obra_centavos=30000, terceirizado_centavos=38000)

# Balcao: 2 unidades, mao de obra 4,00 h x R$ 45,00, sem terceirizado.
BALCAO = MovelCalc(
    "balcao", 2,
    (InsumoCalc(1000, 28000, True), InsumoCalc(3000, 19500, False)),
    "HORAS", mao_obra_horas_centesimos=400,
)

COZINHA = AmbienteCalc("cozinha-gourmet", (TORRE, BALCAO))


def _orcamento(rt_modo="MARGEM", desconto=AjusteCalc("PERCENTUAL", 0), **extra) -> OrcamentoCalc:
    """Markup 90%, perda 10%, custo/hora R$ 45,00, RT 8%, instalacao R$ 750,00, sinal 40%."""
    base = dict(
        ambientes=(COZINHA,), markup_bp=9000, perda_bp=1000, custo_hora_centavos=4500,
        rt_bp=800, rt_modo=rt_modo, instalacao_custo_centavos=75000,
        desconto=desconto, sinal=AjusteCalc("PERCENTUAL", 4000),
    )
    base.update(extra)
    return OrcamentoCalc(**base)


def _linhas(r):
    """(custo_unit, preco_unit, preco_total, rt_linha, custo_os_unit) de cada movel."""
    return [
        (m.custo_unit_centavos, m.preco_unit_centavos, m.preco_total_centavos, m.rt_linha_centavos, m.custo_os_unit_centavos)
        for a in r.ambientes for m in a.moveis
    ]


# =========================
# Cenarios (§11.2)
# =========================

def test_cenario_a_rt_sai_da_margem_sem_desconto():
    r = calcular_orcamento(_orcamento())

    assert _linhas(r) == [
        (222250, 422275, 422275, 33782, 256032),    # Torre Quente
        (107300, 203870, 407740, 32619, 123609),    # Balcao (sobra 0,01 do RT fora do custo da OS)
    ]
    inst = r.instalacao
    assert (inst.custo_centavos, inst.preco_centavos, inst.rt_linha_centavos, inst.custo_os_centavos) == (75000, 142500, 11400, 86400)
    assert r.ambientes[0].subtotal_centavos == 830015
    assert (r.bruto_centavos, r.desconto_centavos, r.total_centavos) == (972515, 0, 972515)
    assert (r.custo_total_centavos, r.margem_bruta_centavos, r.rt_total_centavos) == (511850, 460665, 77801)
    assert (r.margem_liquida_centavos, r.margem_liquida_bp) == (382864, 3937)
    assert (r.sinal_centavos, r.saldo_centavos) == (389006, 583509)


def test_cenario_b_rt_sai_da_margem_desconto_5():
    r = calcular_orcamento(_orcamento(desconto=AjusteCalc("PERCENTUAL", 500)))

    assert [(l[3], l[4]) for l in _linhas(r)] == [(32093, 254343), (30988, 122794)]
    assert (r.instalacao.rt_linha_centavos, r.instalacao.custo_os_centavos) == (10830, 85830)
    assert (r.bruto_centavos, r.desconto_centavos, r.total_centavos) == (972515, 48626, 923889)
    assert (r.custo_total_centavos, r.margem_bruta_centavos, r.rt_total_centavos) == (511850, 412039, 73911)
    assert (r.margem_liquida_centavos, r.margem_liquida_bp) == (338128, 3660)
    assert (r.sinal_centavos, r.saldo_centavos) == (369556, 554333)


def test_cenario_c_rt_embutido_no_preco_desconto_5():
    r = calcular_orcamento(_orcamento(rt_modo="PRECO", desconto=AjusteCalc("PERCENTUAL", 500)))

    assert [(l[1], l[2], l[3], l[4]) for l in _linhas(r)] == [
        (458995, 458995, 34883, 257133),
        (221598, 443196, 33683, 124141),
    ]
    assert (r.instalacao.preco_centavos, r.instalacao.rt_linha_centavos, r.instalacao.custo_os_centavos) == (154891, 11772, 86772)
    assert (r.bruto_centavos, r.desconto_centavos, r.total_centavos) == (1057082, 52854, 1004228)
    assert (r.margem_bruta_centavos, r.rt_total_centavos) == (492378, 80338)
    assert (r.margem_liquida_centavos, r.margem_liquida_bp) == (412040, 4103)
    assert (r.sinal_centavos, r.saldo_centavos) == (401691, 602537)


# =========================
# Unidade e bordas (§11.3)
# =========================

def test_01_torre_quente_do_figma_sem_mao_de_obra():
    """O PDF do Figma, corrigido: custo R$ 1.922,50 e preco R$ 3.652,75."""
    torre = replace(TORRE, mao_obra_modo="NENHUMA", mao_obra_centavos=0)
    r = calcular_orcamento(_orcamento(ambientes=(AmbienteCalc("a", (torre,)),), instalacao_custo_centavos=None))
    movel = r.ambientes[0].moveis[0]
    assert (movel.custo_unit_centavos, movel.preco_unit_centavos) == (192250, 365275)


def test_02_arredondar_meio_para_cima():
    assert arredondar(Decimal("10.5")) == 11
    assert arredondar(Decimal("10.4999")) == 10
    assert arredondar(Decimal("-0")) == 0


def test_03_meio_centavo_no_preco_arredonda_para_cima():
    """Custo 5 x 1,9 = 9,5 centavos -> 10."""
    movel = MovelCalc("m", 1, (), "FIXA", mao_obra_centavos=5)
    r = calcular_orcamento(_orcamento(ambientes=(AmbienteCalc("a", (movel,)),), instalacao_custo_centavos=None))
    assert r.ambientes[0].moveis[0].preco_unit_centavos == 10


def test_04_maior_resto_empate_vai_para_o_primeiro():
    assert repartir_maior_resto(10, [1, 1, 1]) == [4, 3, 3]


def test_05_maior_resto_sem_nada_a_repartir():
    assert repartir_maior_resto(0, [5, 5]) == [0, 0]
    assert repartir_maior_resto(7, [0, 0]) == [0, 0]


def test_06_aprovacao_parcial_so_a_torre_sem_instalacao():
    """O4: a aprovacao parcial recalcula tudo so com o que foi aceito."""
    r = calcular_orcamento(_orcamento(ambientes=(AmbienteCalc("a", (TORRE,)),), instalacao_custo_centavos=None))
    assert r.total_centavos == 422275
    assert r.rt_total_centavos == 33782
    assert r.ambientes[0].moveis[0].rt_linha_centavos == 33782
    assert r.instalacao is None


def test_07_desconto_em_valor_igual_ao_bruto():
    r = calcular_orcamento(_orcamento(desconto=AjusteCalc("VALOR", 972515)))
    assert r.total_centavos == 0
    assert r.margem_liquida_bp == 0                      # sem divisao por zero
    assert r.rt_total_centavos == 0


def test_08_desconto_em_valor_maior_que_o_bruto():
    with pytest.raises(ValueError, match="O desconto não pode ser maior que o total do orçamento."):
        calcular_orcamento(_orcamento(desconto=AjusteCalc("VALOR", 972516)))


def test_09_sinal_em_valor():
    r = calcular_orcamento(_orcamento(sinal=AjusteCalc("VALOR", 100000)))
    assert (r.sinal_centavos, r.saldo_centavos) == (100000, 872515)


def test_10_sinal_zero():
    r = calcular_orcamento(_orcamento(sinal=AjusteCalc("PERCENTUAL", 0)))
    assert r.saldo_centavos == r.total_centavos


def test_11_insumo_sem_custo_e_aviso():
    movel = MovelCalc("m", 1, (InsumoCalc(1000, 0, True),), "NENHUMA")
    r = calcular_orcamento(_orcamento(ambientes=(AmbienteCalc("a", (movel,)),)))
    assert AVISO_INSUMO_SEM_CUSTO in r.avisos
    assert r.ambientes[0].moveis[0].custo_unit_centavos == 0     # calculo normal


def test_12_horas_sem_custo_hora_e_aviso():
    r = calcular_orcamento(_orcamento(custo_hora_centavos=0))
    assert AVISO_HORAS_SEM_CUSTO_HORA in r.avisos
    assert r.ambientes[0].moveis[1].mao_obra_centavos == 0       # o balcao fica sem mao de obra


def test_13_margem_negativa_e_aviso():
    r = calcular_orcamento(_orcamento(markup_bp=0, desconto=AjusteCalc("PERCENTUAL", 1000)))
    assert r.margem_liquida_centavos < 0
    assert AVISO_MARGEM_NEGATIVA in r.avisos


def test_14_orcamento_vazio():
    r = calcular_orcamento(_orcamento(ambientes=(), instalacao_custo_centavos=None))
    assert (r.bruto_centavos, r.total_centavos, r.rt_total_centavos, r.sinal_centavos, r.saldo_centavos) == (0, 0, 0, 0, 0)
    assert r.avisos == (AVISO_ORCAMENTO_VAZIO,)


@pytest.mark.parametrize(
    "orcamento, mensagem",
    [
        (_orcamento(ambientes=(AmbienteCalc("a", (replace(TORRE, quantidade=0),)),)),
         "A quantidade do móvel deve ser pelo menos 1."),
        (_orcamento(ambientes=(AmbienteCalc("a", (replace(TORRE, insumos=(InsumoCalc(0, 100, True),)),)),)),
         "A quantidade do insumo deve ser maior que zero."),
        (_orcamento(ambientes=(AmbienteCalc("a", (replace(TORRE, terceirizado_centavos=-1),)),)),
         "Valores não podem ser negativos."),
        (_orcamento(markup_bp=100_001), "O markup deve ficar entre 0% e 1000%."),
        (_orcamento(perda_bp=5_001), "A perda deve ficar entre 0% e 50%."),
        (_orcamento(rt_bp=3_001), "O RT deve ficar entre 0% e 30%."),
        (_orcamento(desconto=AjusteCalc("PERCENTUAL", 10_001)), "O percentual não pode passar de 100%."),
        (_orcamento(sinal=AjusteCalc("VALOR", 972516)), "O sinal não pode ser maior que o total do orçamento."),
        (_orcamento(ambientes=(AmbienteCalc("a", (replace(TORRE, mao_obra_modo="POR_PECA"),)),)),
         "Forma de mão de obra inválida."),
    ],
    ids=["movel_qtd_0", "insumo_qtd_0", "negativo", "markup", "perda", "rt", "percentual", "sinal_valor", "mao_obra"],
)
def test_15_validacoes(orcamento, mensagem):
    with pytest.raises(ValueError, match=mensagem.replace("(", r"\(").replace(")", r"\)")):
        calcular_orcamento(orcamento)


def test_16_rt_no_limite_no_modo_preco():
    """Fator = (1 + markup) / 0,7, sem erro."""
    assert fator_preco(9000, 3000, "PRECO") == Decimal("1.9") / Decimal("0.7")
    calcular_orcamento(_orcamento(rt_modo="PRECO", rt_bp=3000))


def test_17_movel_so_de_terceirizado():
    movel = MovelCalc("m", 1, (), "NENHUMA", terceirizado_centavos=10000)
    r = calcular_orcamento(_orcamento(ambientes=(AmbienteCalc("a", (movel,)),)))
    m = r.ambientes[0].moveis[0]
    assert m.custo_unit_centavos == 10000
    assert m.preco_unit_centavos == arredondar(Decimal(10000) * fator_preco(9000, 800, "MARGEM"))


def test_17a_percentuais_efetivos_no_cenario_b():
    r = calcular_orcamento(_orcamento(desconto=AjusteCalc("PERCENTUAL", 500)))
    assert (r.desconto_bp_efetivo, r.sinal_bp_efetivo) == (500, 4000)


def test_17b_desconto_em_valor_vira_percentual_para_exibir():
    r = calcular_orcamento(_orcamento(desconto=AjusteCalc("VALOR", 100000)))
    assert r.desconto_bp_efetivo == 1028          # arred(100000 / 972515 x 10000)


def test_17c_percentuais_efetivos_no_orcamento_vazio():
    r = calcular_orcamento(_orcamento(ambientes=(), instalacao_custo_centavos=None))
    assert (r.desconto_bp_efetivo, r.sinal_bp_efetivo) == (0, 0)


# =========================
# Propriedades (§11.4): 500 orcamentos aleatorios, semente fixa
# =========================

def _orcamento_aleatorio(rng: random.Random) -> OrcamentoCalc:
    """Um orcamento valido qualquer (semente fixa: o teste e reprodutivel)."""
    ambientes = []
    for a in range(rng.randint(0, 3)):
        moveis = []
        for m in range(rng.randint(0, 4)):
            insumos = tuple(
                InsumoCalc(rng.randint(1, 50_000), rng.randint(0, 100_000), rng.random() < 0.5)
                for _ in range(rng.randint(0, 6))
            )
            modo = rng.choice(["FIXA", "HORAS", "NENHUMA"])
            moveis.append(MovelCalc(
                f"{a}-{m}", rng.randint(1, 5), insumos, modo,
                mao_obra_centavos=rng.randint(0, 50_000), mao_obra_horas_centesimos=rng.randint(0, 2_000),
                terceirizado_centavos=rng.randint(0, 80_000),
            ))
        ambientes.append(AmbienteCalc(f"amb-{a}", tuple(moveis)))
    base = OrcamentoCalc(
        ambientes=tuple(ambientes), markup_bp=rng.randint(0, 20_000), perda_bp=rng.randint(0, 5_000),
        custo_hora_centavos=rng.randint(0, 10_000), rt_bp=rng.randint(0, 3_000),
        rt_modo=rng.choice(["MARGEM", "PRECO"]),
        instalacao_custo_centavos=rng.choice([None, rng.randint(0, 200_000)]),
    )
    # Desconto e sinal: percentual, ou valor dentro do possivel (calculado sem eles).
    bruto = calcular_orcamento(base).bruto_centavos
    desconto = (AjusteCalc("PERCENTUAL", rng.randint(0, 10_000)) if rng.random() < 0.5
                else AjusteCalc("VALOR", rng.randint(0, bruto)))
    com_desconto = replace(base, desconto=desconto)
    total = calcular_orcamento(com_desconto).total_centavos
    sinal = (AjusteCalc("PERCENTUAL", rng.randint(0, 10_000)) if rng.random() < 0.5
             else AjusteCalc("VALOR", rng.randint(0, total)))
    return replace(com_desconto, sinal=sinal)


ORCAMENTOS_ALEATORIOS = [_orcamento_aleatorio(random.Random(semente)) for semente in range(500)]


def _conferir_propriedades(orcamento: OrcamentoCalc) -> None:
    """Propriedades 18 a 24 para UM orcamento."""
    r = calcular_orcamento(orcamento)
    preco_instalacao = r.instalacao.preco_centavos if r.instalacao else 0
    rt_instalacao = r.instalacao.rt_linha_centavos if r.instalacao else 0
    moveis = [m for a in r.ambientes for m in a.moveis]

    # 18: os subtotais + a instalacao fecham o bruto.
    assert sum(a.subtotal_centavos for a in r.ambientes) + preco_instalacao == r.bruto_centavos
    # 19: total = bruto - desconto, nunca negativo.
    assert r.total_centavos == r.bruto_centavos - r.desconto_centavos >= 0
    # 20: as partes do RT somam exatamente o RT total.
    assert sum(m.rt_linha_centavos for m in moveis) + rt_instalacao == r.rt_total_centavos
    # 21: margem liquida = total - custo - RT.
    assert r.margem_liquida_centavos == r.total_centavos - r.custo_total_centavos - r.rt_total_centavos
    # 22: saldo = total - sinal, nunca negativo.
    assert r.saldo_centavos == r.total_centavos - r.sinal_centavos >= 0
    # 23: o custo da OS por unidade nunca passa do custo + RT da linha, e a
    #     diferenca (o RT que nao coube por unidade) e menor que `qtd` centavos.
    for m in moveis:
        com_rt = m.custo_unit_centavos * m.quantidade + m.rt_linha_centavos
        assert 0 <= com_rt - m.custo_os_unit_centavos * m.quantidade < m.quantidade
    # 24: funcao pura, mesma entrada -> mesma saida.
    assert calcular_orcamento(orcamento) == r


def test_propriedades_18_a_24_em_500_orcamentos():
    for semente, orcamento in enumerate(ORCAMENTOS_ALEATORIOS):
        try:
            _conferir_propriedades(orcamento)
        except AssertionError as erro:                       # diz qual orcamento quebrou
            raise AssertionError(f"semente {semente}: {erro}") from erro


def test_propriedade_25_ordem_dos_ambientes_nao_muda_totais():
    campos = ("bruto_centavos", "desconto_centavos", "total_centavos", "custo_total_centavos",
              "rt_total_centavos", "margem_liquida_centavos", "sinal_centavos", "saldo_centavos")
    for semente, orcamento in enumerate(ORCAMENTOS_ALEATORIOS):
        invertido = replace(orcamento, ambientes=tuple(reversed(orcamento.ambientes)))
        a, b = calcular_orcamento(orcamento), calcular_orcamento(invertido)
        assert [getattr(a, c) for c in campos] == [getattr(b, c) for c in campos], f"semente {semente}"


# =========================
# Arquitetura e desempenho (§11.5)
# =========================

def test_26_sem_float_e_sem_banco_ou_http():
    fonte = inspect.getsource(calculo)
    for proibido in ("float(", "import sqlalchemy", "from sqlalchemy", "from app.db", "fastapi"):
        assert proibido not in fonte, proibido


def test_27_cem_moveis_com_trinta_insumos_em_menos_de_50_ms():
    insumos = tuple(InsumoCalc(1000 + i, 1000 + i, i % 2 == 0) for i in range(30))
    moveis = tuple(MovelCalc(str(i), 1 + i % 3, insumos, "HORAS", mao_obra_horas_centesimos=250) for i in range(100))
    orcamento = _orcamento(ambientes=(AmbienteCalc("grande", moveis),))
    calcular_orcamento(orcamento)                      # aquece (imports, caches)
    inicio = time.perf_counter()
    calcular_orcamento(orcamento)
    assert (time.perf_counter() - inicio) < 0.05
