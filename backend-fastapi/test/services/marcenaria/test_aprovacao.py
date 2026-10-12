# ---------------------------------------------------------------------------
# ARQUIVO: test/services/marcenaria/test_aprovacao.py
# DESCRICAO: Spec 08A -- a funcao pura das pecas embutidas (casos 37-39) e a
#            propriedade "a OS sempre bate com o motor" (caso 23).
# ---------------------------------------------------------------------------

import random

from app.core.enum import UnidadeMedida
from app.db.models.marcenaria import (
    MarcenariaAmbiente,
    MarcenariaMovel,
    MarcenariaMovelInsumo,
    MarcenariaOrcamento,
)
from app.db.models.ordem_servico import OrdemServico
from app.schemas.marcenaria.aprovacao import AprovacaoEntrada
from app.services.marcenaria import aprovacao
from app.services.marcenaria.insumos_os import insumos_da_os, ordenar_para_a_os, sugerido
from app.services.marcenaria.orcamento_calculo import calcular, montar_entrada_motor


def _insumo(produto_id, quantidade_milesimos, custo=10000, sofre_perda=False, descricao="MDF 15mm", ordem=1):
    return MarcenariaMovelInsumo(
        produto_id=produto_id, descricao=descricao, quantidade_milesimos=quantidade_milesimos,
        custo_unit_centavos=custo, custo_origem="ULTIMA_COMPRA", sofre_perda=sofre_perda, ordem=ordem,
    )


def _orcamento_em_memoria(moveis, perda_bp=1000) -> MarcenariaOrcamento:
    """Orcamento so em memoria (sem banco): a funcao pura nao le nada."""
    orc = MarcenariaOrcamento(perda_bp=perda_bp)
    amb = MarcenariaAmbiente(id=1, nome="Cozinha", ordem=1)
    amb.moveis = moveis
    orc.ambientes = [amb]
    return orc


def _movel(id_, insumos, quantidade=1, tipo="INTERNA", aprovado=True):
    m = MarcenariaMovel(id=id_, nome=f"Móvel {id_}", quantidade=quantidade, tipo_producao=tipo, aprovado=aprovado, ordem=id_)
    m.insumos = insumos
    return m


# =========================
# Pecas embutidas (37, 38, 39 e bordas)
# =========================

def test_37_arredonda_uma_vez_por_produto():
    """1,4 + 1,2 + 0,6 chapa = 3,2 -> 4 (e nao 2 + 2 + 1 = 5)."""
    orc = _orcamento_em_memoria([_movel(1, [_insumo(9, 1400)]), _movel(2, [_insumo(9, 1200)]), _movel(3, [_insumo(9, 600)])])

    (peca,) = insumos_da_os(orc, {9: "UN"})

    assert (peca.planejado_milesimos, peca.sugerido_milesimos) == (3200, 4000)
    assert [m[2] for m in peca.moveis] == [1400, 1200, 600]


def test_38_unidade_fracionavel_nao_arredonda():
    orc = _orcamento_em_memoria([_movel(1, [_insumo(5, 26350, descricao="Fita de borda")])])

    (peca,) = insumos_da_os(orc, {5: "M"})

    assert peca.sugerido_milesimos == 26350


def test_39_unidade_fora_do_enum_vira_outros_e_arredonda_para_cima():
    orc = _orcamento_em_memoria([_movel(1, [_insumo(7, 1500)])])

    (peca,) = insumos_da_os(orc, {7: "CH"})

    assert peca.sugerido_milesimos == 2000
    assert aprovacao._unidade_do_item("CH") == UnidadeMedida.OUTROS
    assert aprovacao._unidade_do_item("m2") == UnidadeMedida.METRO_QUADRADO


def test_perda_so_onde_sofre_perda_e_quantidade_do_movel():
    orc = _orcamento_em_memoria([_movel(1, [_insumo(1, 1000, sofre_perda=True), _insumo(2, 1000, sofre_perda=False)], quantidade=3)])

    pecas = {p.produto_id: p for p in insumos_da_os(orc, {1: "UN", 2: "UN"})}

    assert pecas[1].planejado_milesimos == 3300 and pecas[2].planejado_milesimos == 3000


def test_so_aprovados_internos_e_com_produto():
    orc = _orcamento_em_memoria([
        _movel(1, [_insumo(1, 1000)]),                          # entra
        _movel(2, [_insumo(2, 1000)], aprovado=False),          # recusado (O4)
        _movel(3, [_insumo(3, 1000)], tipo="TERCEIRIZADA"),     # material da central (D1d)
        _movel(4, [_insumo(None, 1000)]),                       # produto excluido (D1c)
    ])

    assert [p.produto_id for p in insumos_da_os(orc, {})] == [1]


def test_custo_e_a_media_ponderada_pelo_planejado():
    orc = _orcamento_em_memoria([_movel(1, [_insumo(1, 1000, custo=10000)]), _movel(2, [_insumo(1, 3000, custo=20000)])])

    (peca,) = insumos_da_os(orc, {1: "UN"})

    assert peca.custo_unitario_centavos == 17500            # (1 x 100 + 3 x 200) / 4


def test_ordem_pela_localizacao_e_depois_pelo_nome():
    orc = _orcamento_em_memoria([_movel(1, [
        _insumo(1, 1000, descricao="Parafuso"), _insumo(2, 1000, descricao="Cola"), _insumo(3, 1000, descricao="Chapa"),
    ])])

    pecas = ordenar_para_a_os(insumos_da_os(orc, {}), {1: "A1", 2: "B2", 3: "B2"})

    assert [p.nome for p in pecas] == ["Parafuso", "Chapa", "Cola"]


def test_planejado_arredonda_meio_para_cima():
    """Perda de 0,05%: 1000 x 1,0005 = 1000,5 milesimos -> 1001 (meio para cima, como o motor)."""
    orc = _orcamento_em_memoria([_movel(1, [_insumo(1, 1000, sofre_perda=True)])], perda_bp=5)

    (peca,) = insumos_da_os(orc, {1: "M"})

    assert peca.planejado_milesimos == 1001


def test_sugerido_exato_nao_sobe():
    assert sugerido(3000, "UN") == 3000 and sugerido(3001, "UN") == 4000


# =========================
# Propriedade (23): a OS sempre bate com o motor
# =========================

def _orcamento_aleatorio(db, rng: random.Random, cliente_id: int, funcionario_id: int, produtos: list[int]) -> MarcenariaOrcamento:
    """Orcamento valido qualquer, gravado direto no banco (semente fixa)."""
    orc = MarcenariaOrcamento(
        codigo=f"ORC-T-{rng.randint(0, 10**9):010d}", versao=1, status="ENVIADO", revisao=1,
        cliente_id=cliente_id, funcionario_id=funcionario_id, projeto_nome="Projeto",
        markup_bp=rng.randint(0, 20_000), perda_bp=rng.randint(0, 5_000), custo_hora_centavos=rng.randint(0, 10_000),
        rt_padrao_bp=0, rt_modo=rng.choice(["MARGEM", "PRECO"]), validade_dias=15, prazo_entrega_dias=30,
        instalacao_custo_centavos=rng.choice([None, rng.randint(1, 200_000)]),
        desconto_modo="PERCENTUAL", desconto_valor=rng.randint(0, 3000),
        sinal_modo="PERCENTUAL", sinal_valor=rng.randint(0, 10_000),
    )
    for a in range(rng.randint(1, 3)):
        amb = MarcenariaAmbiente(nome=f"Ambiente {a}", ordem=a + 1)
        for m in range(rng.randint(1, 4)):
            movel = MarcenariaMovel(
                nome=f"Movel {a}-{m}", quantidade=rng.randint(1, 5), ordem=m + 1,
                tipo_producao=rng.choice(["INTERNA", "INTERNA", "TERCEIRIZADA"]),
                terceirizado_centavos=rng.randint(0, 80_000),
                mao_obra_modo="FIXA", mao_obra_centavos=rng.randint(1, 50_000),   # >0: o movel sempre tem preco
            )
            movel.insumos = [
                _insumo(rng.choice(produtos), rng.randint(1, 50_000), rng.randint(0, 100_000), rng.random() < 0.5, ordem=i)
                for i in range(rng.randint(0, 4))
            ]
            amb.moveis.append(movel)
        orc.ambientes.append(amb)
    db.add(orc)
    db.commit()
    return orc


def test_23_propriedade_os_igual_ao_motor(db_session, token_master, cliente_id, produto):
    rng = random.Random(8023)                                       # semente fixa: reprodutivel
    produtos = [produto(f"Insumo {i}", valor_entrada=1000 + i) for i in range(5)]
    for _ in range(200):
        orc = _orcamento_aleatorio(db_session, rng, cliente_id, token_master["funcionario_id"], produtos)
        todos = [m.id for a in orc.ambientes for m in a.moveis]
        escolhidos = rng.sample(todos, rng.randint(1, len(todos)))   # parcial ou total
        dados = AprovacaoEntrada(movel_ids=escolhidos, incluir_instalacao=rng.random() < 0.7)

        aprovacao.aprovar(db_session, orc.id, 1, dados, token_master)

        db_session.expire_all()
        orc = db_session.get(MarcenariaOrcamento, orc.id)
        esperado = calcular(montar_entrada_motor(orc, so_aprovados=True))
        os_ = db_session.get(OrdemServico, orc.os_id)
        assert (os_.valor_bruto, os_.valor_total) == (esperado.bruto_centavos, esperado.total_centavos)
        assert os_.desconto == esperado.desconto_centavos
