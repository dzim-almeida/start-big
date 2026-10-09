# ---------------------------------------------------------------------------
# ARQUIVO: test/services/test_cmv_origem.py
# DESCRICAO: ⚠️ CMV sem contagem dupla (Spec 09A, F2a, D12; casos 15 e 24).
#
#            O custo declarado nos itens que vieram do orcamento (custo + RT)
#            NAO entra no custo manual da OS: cada parte entra pelo registro
#            real (estoque, contas pagas, salarios). A comissao, que usa o
#            custo declarado, nao muda. Item sem origem (todas as lojas de
#            hoje) continua contando como sempre.
# ---------------------------------------------------------------------------

from app.core.tempo import hoje_local, intervalo_utc
from app.db.crud.relatorio import get_comissao_base
from app.db.crud.relatorio_custo import get_custo_manual_os
from app.db.models.movimentacao_estoque import MovimentacaoEstoque
from app.db.models.ordem_servico import OrdemServico
from app.db.models.ordem_servico_item import OrdemServicoItem

from test.apoio_orcamento_marcenaria import aprovar, montar_cenario_b
# Fixtures da marcenaria (este arquivo fica fora da pasta que as recebe pelo conftest).
from test.apoio_orcamento_marcenaria import (  # noqa: F401
    api, client, cliente_id, forma_pagamento, fornecedor, loja, produto,
)


def _os_finalizada(api, produto, fornecedor, cliente_id, forma_pagamento) -> str:
    d = aprovar(api, montar_cenario_b(api, produto, fornecedor, cliente=cliente_id))
    numero = d["os"]["numero_os"]
    r = api.client.put(f"/api/v1/ordens-servico/{numero}/finalizar", json={
        "situacao_equipamento": "REPARADO",
        "pagamentos": [{"forma_pagamento_id": forma_pagamento("PIX"), "valor": 923889}],
    }, headers=api.header)
    assert r.status_code == 200, r.text
    return numero


def _custo_manual_de_hoje(db) -> int:
    inicio, fim = intervalo_utc(hoje_local(), hoje_local())
    return get_custo_manual_os(db, inicio, fim, 1)


def _comissao_de_hoje(db) -> list[tuple]:
    inicio, fim = intervalo_utc(hoje_local(), hoje_local())
    return [tuple(l) for l in get_comissao_base(db, inicio, fim, 1)]


def test_15_item_com_origem_fora_do_custo_manual_e_comissao_igual(api, produto, fornecedor, cliente_id,
                                                                   forma_pagamento, db_session):
    _os_finalizada(api, produto, fornecedor, cliente_id, forma_pagamento)
    comissao_com_origem = _comissao_de_hoje(db_session)

    assert _custo_manual_de_hoje(db_session) == 0                       # moveis e instalacao fora

    # Sem a origem (o comportamento de antes da 09A), o custo declarado contava:
    for item in db_session.query(OrdemServicoItem).all():
        item.origem = None
    db_session.commit()
    assert _custo_manual_de_hoje(db_session) == 254343 + 2 * 122794 + 85830   # custo + RT dos 3 servicos
    assert _comissao_de_hoje(db_session) == comissao_com_origem              # a comissao nao depende da origem


def test_24_pecas_embutidas_saem_pelo_livro_de_estoque(api, produto, fornecedor, cliente_id, forma_pagamento, db_session):
    numero = _os_finalizada(api, produto, fornecedor, cliente_id, forma_pagamento)

    saidas = db_session.query(MovimentacaoEstoque).all()
    # A finalizacao baixou as pecas embutidas (regra de hoje da OS): MDF 3 e corredica 6.
    assert sorted(abs(m.quantidade) for m in saidas) == [3, 6]
    assert {m.ordem_servico_id for m in saidas} == {db_session.query(OrdemServico).filter_by(numero_os=numero).one().id}
    assert _custo_manual_de_hoje(db_session) == 0
