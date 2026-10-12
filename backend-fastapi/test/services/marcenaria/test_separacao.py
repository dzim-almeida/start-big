# ---------------------------------------------------------------------------
# ARQUIVO: test/services/marcenaria/test_separacao.py
# DESCRICAO: Separacao de material x finalizacao da OS e CMV (Spec 10A,
#            secao 11, casos 21, 22 e 24), sem mexer na finalizacao (FB2).
#
#            O que nao pode errar:
#              - a finalizacao baixa so o que a separacao NAO levou;
#              - cada chapa entra no custo do mes UMA vez (retiradas - devolucoes);
#              - OS de outro segmento: o gancho do cancelamento sai na hora.
# ---------------------------------------------------------------------------

from types import SimpleNamespace

import pytest

from app.core.enum import MovimentacaoOrigem, MovimentacaoTipo
from app.db.models.marcenaria import MarcenariaEvento
from app.db.models.movimentacao_estoque import MovimentacaoEstoque
from app.db.models.ordem_servico import OrdemServico
from app.services.marcenaria import separacao as servico

from test.apoio_orcamento_marcenaria import aprovar, montar_cenario_b

OS_URL = "/api/v1/ordens-servico"


@pytest.fixture
def aprovada(api, produto, fornecedor, cliente_id) -> str:
    """O cenario B aprovado inteiro; devolve o numero da OS."""
    return aprovar(api, montar_cenario_b(api, produto, fornecedor, cliente=cliente_id))["os"]["numero_os"]


def _finalizar(api, db, numero: str, forma_pagamento) -> None:
    os_ = db.query(OrdemServico).filter_by(numero_os=numero).one()
    r = api.client.put(f"{OS_URL}/{numero}/finalizar", json={
        "situacao_equipamento": "REPARADO",
        "pagamentos": [{"forma_pagamento_id": forma_pagamento("PIX"), "valor": os_.valor_total}],
    }, headers=api.header)
    assert r.status_code == 200, r.text


def _consumo_da_os(db, numero: str, produto_id: int) -> float:
    """Saidas - entradas do produto ligadas a OS: o que o CMV da OS conta (F2a)."""
    db.expire_all()
    os_id = db.query(OrdemServico.id).filter_by(numero_os=numero).scalar()
    total = 0.0
    for mov in db.query(MovimentacaoEstoque).filter_by(
        produto_id=produto_id, ordem_servico_id=os_id, origem=MovimentacaoOrigem.ORDEM_SERVICO.value,
    ):
        total += mov.quantidade if mov.tipo == MovimentacaoTipo.SAIDA else -mov.quantidade
    return round(total, 3)


def test_21_finalizar_com_linha_aberta_baixa_o_resto(api, separacao, aprovada, db_session, forma_pagamento):
    mdf = separacao.linha(aprovada, "MDF")
    separacao.acao(aprovada, mdf, "retirar", 2000)             # 2 de 3, linha ainda aberta

    _finalizar(api, db_session, aprovada, forma_pagamento)

    # A finalizacao baixou so 1 (a regra de hoje, `quantidade - separada`): 3 chapas no custo.
    assert _consumo_da_os(db_session, aprovada, mdf["produto_id"]) == 3
    baixa = db_session.query(MovimentacaoEstoque).filter_by(produto_id=mdf["produto_id"]).order_by(
        MovimentacaoEstoque.id.desc()).first()
    assert (baixa.tipo, baixa.quantidade) == (MovimentacaoTipo.SAIDA, 1)


def test_22_finalizar_com_linha_concluida_nao_baixa_de_novo(api, separacao, aprovada, db_session, forma_pagamento):
    mdf = separacao.linha(aprovada, "MDF")
    sep = separacao.acao(aprovada, mdf, "retirar", 2000)
    mdf = next(linha for linha in sep["linhas"] if linha["item_id"] == mdf["item_id"])
    separacao.acao(aprovada, mdf, "concluir")                  # usou 2: a quantidade cai para 2
    movimentos_antes = db_session.query(MovimentacaoEstoque).filter_by(produto_id=mdf["produto_id"]).count()

    _finalizar(api, db_session, aprovada, forma_pagamento)

    assert _consumo_da_os(db_session, aprovada, mdf["produto_id"]) == 2
    assert db_session.query(MovimentacaoEstoque).filter_by(produto_id=mdf["produto_id"]).count() == movimentos_antes


def test_devolucao_desconta_do_consumo(api, separacao, aprovada, db_session, forma_pagamento):
    mdf = separacao.linha(aprovada, "MDF")
    sep = separacao.acao(aprovada, mdf, "retirar", 3000)
    mdf = next(linha for linha in sep["linhas"] if linha["item_id"] == mdf["item_id"])
    separacao.acao(aprovada, mdf, "devolver", 1000)

    _finalizar(api, db_session, aprovada, forma_pagamento)

    assert _consumo_da_os(db_session, aprovada, mdf["produto_id"]) == 2   # 3 saem, 1 volta, nada mais baixa


def test_11_nao_usado_a_finalizacao_nao_baixa(api, separacao, aprovada, db_session, forma_pagamento):
    mdf = separacao.linha(aprovada, "MDF")
    separacao.acao(aprovada, mdf, "concluir")

    _finalizar(api, db_session, aprovada, forma_pagamento)

    assert _consumo_da_os(db_session, aprovada, mdf["produto_id"]) == 0


def test_24_gancho_do_cancelamento_sai_na_hora_sem_orcamento(db_session, loja):
    # OS de outro segmento (ou sem orcamento): nada e lido alem do indice, nada gravado.
    os_qualquer = SimpleNamespace(id=999_999, itens=[])
    servico.avisar_material_no_cancelamento(db_session, os_qualquer, None, {"status_anterior": "ABERTA"})
    assert db_session.query(MarcenariaEvento).count() == 0


def test_texto_das_quantidades():
    assert [servico._texto(m) for m in (3000, 26350, 500, 1, 0)] == ["3", "26,35", "0,5", "0,001", "0"]


def test_diferenca_em_bp():
    assert servico._diferenca_bp(0, 2200) is None                    # antes de retirar
    assert servico._diferenca_bp(3000, 2200) == 3636
    assert servico._diferenca_bp(2000, 2200) == -909
    assert servico._diferenca_bp(1000, None) is None
