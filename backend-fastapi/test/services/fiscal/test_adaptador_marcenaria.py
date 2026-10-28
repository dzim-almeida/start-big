# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_adaptador_marcenaria.py
# DESCRICAO: A entrega da marcenaria vista como venda (F3 do plano
#            docs/marcenaria-faturamento-plano.md).
#
# As decisoes nao obvias, cada uma com um teste:
#   - so os moveis escolhidos entram, com o nome do movel na descricao;
#   - desconto, acrescimo, taxa de entrega e instalacao entram pela FATIA
#     acumulada: somadas as notas de todas as entregas, fecham ao centavo;
#   - instalacao FORA nao entra, e o desconto dela tambem nao;
#   - o que ja foi pago entra pela proporcao, o resto vai como "a receber" (99).
# ---------------------------------------------------------------------------

from app.core.enum import OrdemServicoItemAprovacao, OrdemServicoItemTipo
from app.services.fiscal.emissoes.adaptador_marcenaria import MovelParaNota, adaptar_entrega, fatia_acumulada

from test.services.fiscal.test_payload_builder import _calcular, _empresa, _endereco_empresa, _fiscal_settings, _produto
from app.services.fiscal.payload.builder import montar_payload_nfe


class _Item:
    def __init__(self, nome, valor, quantidade=1):
        self.nome, self.quantidade = nome, quantidade
        self.valor_unitario, self.valor_total = valor // quantidade, valor
        self.tipo = OrdemServicoItemTipo.SERVICO
        self.status_aprovacao = OrdemServicoItemAprovacao.APROVADO


class _Forma:
    def __init__(self, codigo):
        self.codigo_sefaz, self.tipo_integracao = codigo, None


class _Pagamento:
    def __init__(self, valor, codigo="17"):
        self.valor, self.forma_pagamento = valor, _Forma(codigo)


class _Objeto:
    cliente = None


class _OS:
    def __init__(self, valor_bruto, desconto=0, acrescimo=0, taxa_entrega=0, pagamentos=()):
        self.numero_os, self.id = "OS-2026-000009", 9
        self.valor_bruto, self.desconto, self.acrescimo, self.taxa_entrega = valor_bruto, desconto, acrescimo, taxa_entrega
        self.valor_total = valor_bruto - desconto + acrescimo + taxa_entrega
        self.pagamentos, self.objeto, self.nota_fiscal = list(pagamentos), _Objeto(), None


def _movel(nome, valor, produto_id=1):
    return MovelParaNota(item_os=_Item(nome, valor), produto=_produto(produto_id, "Móvel planejado"),
                         quantidade=1, terceirizado=False)


def test_fatia_acumulada_fecha_ao_centavo_em_tres_entregas():
    """R$ 100,00 de desconto em tres entregas de R$ 333,33 / 333,33 / 333,34."""
    base, total = 100000, 10000
    partes, antes = [], 0
    for nesta in (33333, 33333, 33334):
        partes.append(fatia_acumulada(total, antes, nesta, base))
        antes += nesta
    assert sum(partes) == total


def test_so_os_moveis_escolhidos_com_o_nome_do_movel():
    os_ = _OS(valor_bruto=1_000_000)
    balcao = _movel("Balcão — Cozinha", 600_000)

    adaptado = adaptar_entrega(os_, [balcao], valor_moveis_total=1_000_000, valor_moveis_ja_faturados=0)

    assert [i.descricao_nota for i in adaptado.itens] == ["Balcão — Cozinha"]
    assert adaptado.total == 600_000


def test_instalacao_embutida_entra_como_acrescimo_pela_fatia():
    # Moveis 9.000 + instalacao 1.000. Esta entrega leva 60% dos moveis.
    os_ = _OS(valor_bruto=1_000_000)
    adaptado = adaptar_entrega(os_, [_movel("Balcão", 540_000)], valor_moveis_total=900_000,
                               valor_moveis_ja_faturados=0, instalacao_valor=100_000, instalacao_modo="EMBUTIDA")
    assert adaptado.acrescimo == 60_000
    assert adaptado.total == 600_000


def test_instalacao_fora_nao_entra_e_o_desconto_dela_tambem_nao():
    # Moveis 9.000 + instalacao 1.000, desconto de 1.000 na OS inteira: a parte
    # dos moveis e 900 (90%). A nota com TODOS os moveis leva 900, nao 1.000.
    os_ = _OS(valor_bruto=1_000_000, desconto=100_000)
    adaptado = adaptar_entrega(os_, [_movel("Balcão", 900_000)], valor_moveis_total=900_000,
                               valor_moveis_ja_faturados=0, instalacao_valor=100_000, instalacao_modo="FORA")
    assert adaptado.acrescimo == 0
    assert sum(i.desconto for i in adaptado.itens) == 90_000
    assert adaptado.total == 810_000


def test_taxa_de_entrega_vira_frete():
    os_ = _OS(valor_bruto=500_000, taxa_entrega=20_000)
    adaptado = adaptar_entrega(os_, [_movel("Balcão", 500_000)], valor_moveis_total=500_000,
                               valor_moveis_ja_faturados=0)
    assert adaptado.entrega == 20_000 and adaptado.total == 520_000


def test_pago_entra_pela_proporcao_e_o_resto_a_receber():
    # OS de 10.000 com sinal de 3.000 em PIX; a nota e de 6.000 (60%): 1.800 PIX + 4.200 a receber.
    os_ = _OS(valor_bruto=1_000_000, pagamentos=[_Pagamento(300_000, "17")])
    adaptado = adaptar_entrega(os_, [_movel("Balcão", 600_000)], valor_moveis_total=1_000_000,
                               valor_moveis_ja_faturados=0)
    assert [(p.forma_pagamento.codigo_sefaz, p.valor) for p in adaptado.pagamentos] == [("17", 180_000), ("99", 420_000)]


def test_payload_fecha_os_pagamentos_e_leva_o_nome_do_movel():
    """A costura com o builder: Σ pagamentos == total da nota (Rejeição 767)."""
    os_ = _OS(valor_bruto=1_000_000, desconto=50_000, pagamentos=[_Pagamento(200_000, "01")])
    adaptado = adaptar_entrega(os_, [_movel("Torre Quente — Cozinha", 400_000), _movel("Aéreo — Cozinha", 200_000, 2)],
                               valor_moveis_total=900_000, valor_moveis_ja_faturados=0,
                               instalacao_valor=100_000, instalacao_modo="EMBUTIDA")

    payload = montar_payload_nfe(
        empresa=_empresa("Lucro Presumido"), endereco_empresa=_endereco_empresa(), fiscal_settings=_fiscal_settings(),
        venda=adaptado, nota_fiscal=None, resultado_calculo=_calcular(adaptado),
    )

    assert [i["descricao"] for i in payload["items"]] == ["Torre Quente — Cozinha", "Aéreo — Cozinha"]
    soma = round(sum(p["valor_pagamento"] for p in payload["formas_pagamento"]), 2)
    assert soma == payload["totais"]["valor_total"] == adaptado.total / 100


# =========================
# Entrega futura (F4): simples faturamento e remessa
# =========================

import pytest


@pytest.fixture
def sp(db_session):
    """A aliquota padrao de SP (a seed do startup nao roda nos testes)."""
    from app.db.models.aliquota_uf import AliquotaUF

    db_session.add(AliquotaUF(uf="SP", aliquota_icms_interna=1800, aliquota_pis_padrao=165, aliquota_cofins_padrao=760))
    db_session.commit()
    return db_session


def _payload(db, adaptado, regime="Lucro Presumido"):
    return montar_payload_nfe(
        empresa=_empresa(regime), endereco_empresa=_endereco_empresa(), fiscal_settings=_fiscal_settings(),
        venda=adaptado, nota_fiscal=adaptado.nota_fiscal, resultado_calculo=_calcular_com_resolver(db, adaptado, regime),
    )


def _calcular_com_resolver(db, adaptado, regime):
    """O resolver de verdade decide CFOP e CST (e e nele que o CFOP forcado entra)."""
    from app.services.fiscal.tax_engine import calcular_impostos
    from app.services.fiscal.tax_engine.resolver import resolver_aliquotas_venda

    itens, dados = resolver_aliquotas_venda(db, adaptado, "SP", regime == "Simples Nacional", regime_apuracao="cumulativo")
    return calcular_impostos(itens, dados)


def test_simples_faturamento_5922_sem_icms_e_com_o_pagamento(sp):
    os_ = _OS(valor_bruto=500_000, pagamentos=[_Pagamento(100_000, "17")])
    produto = _produto(1, "Móvel planejado")
    produto.fiscal.cfop_padrao = "5101"
    movel = MovelParaNota(item_os=_Item("Balcão — Cozinha", 500_000), produto=produto, quantidade=1, terceirizado=False)

    adaptado = adaptar_entrega(os_, [movel], valor_moveis_total=500_000, valor_moveis_ja_faturados=0,
                               papel="SIMPLES_FATURAMENTO")
    payload = _payload(sp, adaptado)

    (item,) = payload["items"]
    assert item["cfop"] == "5922"
    assert item["icms_situacao_tributaria"] == "41" and item.get("icms_valor", 0) == 0
    assert payload["natureza_operacao"] == "Simples faturamento - venda para entrega futura"
    assert [(p["forma_pagamento"], p["valor_pagamento"]) for p in payload["formas_pagamento"]] == [("17", 1000.0), ("99", 4000.0)]


def test_remessa_5116_com_icms_sem_pagamento_e_apontando_a_5922(sp):
    os_ = _OS(valor_bruto=500_000)
    produto = _produto(1, "Móvel planejado")
    produto.fiscal.cfop_padrao = "5101"
    movel = MovelParaNota(item_os=_Item("Balcão — Cozinha", 500_000), produto=produto, quantidade=1, terceirizado=False)
    terceirizado = MovelParaNota(item_os=_Item("Torre — Cozinha", 100_000), produto=_produto(2, "Revenda"),
                                 quantidade=1, terceirizado=True)

    adaptado = adaptar_entrega(os_, [movel, terceirizado], valor_moveis_total=600_000, valor_moveis_ja_faturados=0,
                               papel="REMESSA_ENTREGA_FUTURA", chaves_referenciadas=["3" * 44])
    payload = _payload(sp, adaptado)

    assert [i["cfop"] for i in payload["items"]] == ["5116", "5117"]
    assert payload["items"][0]["icms_valor"] > 0                          # o ICMS sai na remessa
    assert payload["formas_pagamento"] == [{"forma_pagamento": "90", "valor_pagamento": 0.0}]
    assert payload["notas_referenciadas"] == [{"chave_nfe": "3" * 44}]


def test_instalacao_em_nfse_fica_fora_da_nfe_igual_a_fora():
    """G5 (docs/nfse-fase2-plano.md): no modo NFSE a instalação sai na NFS-e da
    OS, então a NF-e dos móveis é EXATAMENTE a do modo FORA — sem cobrar duas vezes."""
    os_ = _OS(valor_bruto=1_000_000, desconto=100_000)
    kwargs = dict(valor_moveis_total=900_000, valor_moveis_ja_faturados=0, instalacao_valor=100_000)
    nfse = adaptar_entrega(os_, [_movel("Balcão", 900_000)], instalacao_modo="NFSE", **kwargs)
    fora = adaptar_entrega(os_, [_movel("Balcão", 900_000)], instalacao_modo="FORA", **kwargs)
    assert (nfse.acrescimo, nfse.total) == (fora.acrescimo, fora.total) == (0, 810_000)
