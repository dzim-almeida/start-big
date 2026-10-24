# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/marcenaria/test_faturamento_estoque_api.py
# DESCRICAO: F2 do faturamento dos moveis (docs/marcenaria-faturamento-
#            plano.md): o movel pronto entra no estoque como produto acabado.
#
#            O que nao pode errar:
#              - desligado, nada acontece (R1);
#              - pronto entra, deixou de estar pronto estorna (idempotente);
#              - terceirizado entra no produto de revenda, pelo valor da central;
#              - origem PRODUCAO: o CMV nao conta o acabado (R3);
#              - cancelar a OS estorna, e movel faturado barra o cancelamento.
# ---------------------------------------------------------------------------

from datetime import datetime, timedelta

import pytest

from app.core.enum import MovimentacaoOrigem, OrdemServicoStatus
from app.db.crud.relatorio.custo import get_cmv_os
from app.db.models.configuracao_marcenaria import ConfiguracaoMarcenaria
from app.db.models.marcenaria.faturamento import MarcenariaMovelFaturamento
from app.db.models.movimentacao_estoque import MovimentacaoEstoque
from app.db.models.ordem_servico import OrdemServico
from app.db.models.produto import Produto

from test.api.v1.marcenaria.test_producao_api import OS_URL, Producao, _aprovar_obra, _terceirizado, _todas

URL_CONFIG = "/api/v1/configuracoes/marcenaria"


@pytest.fixture
def obra(api, fornecedor, cliente_id) -> Producao:
    _d, numero = _aprovar_obra(api, cliente_id, fornecedor("Madeiranit"))
    return Producao(api, numero)


@pytest.fixture
def ligado(api, db_session) -> ConfiguracaoMarcenaria:
    """Os dois produtos acabados criados e o faturamento ligado (nota na entrega)."""
    r = api.client.post(f"{URL_CONFIG}/produtos-acabados", headers=api.header)
    assert r.status_code == 200, r.text
    r = api.client.put(URL_CONFIG, json={"faturamento_modo": "NOTA_NA_ENTREGA"}, headers=api.header)
    assert r.status_code == 200, r.text
    db_session.expire_all()
    return db_session.query(ConfiguracaoMarcenaria).one()


def _estoque(db, produto_id: int) -> float:
    db.expire_all()
    return db.get(Produto, produto_id).estoque.quantidade


def _movs_producao(db) -> list[MovimentacaoEstoque]:
    db.expire_all()
    return (db.query(MovimentacaoEstoque)
            .filter(MovimentacaoEstoque.origem == MovimentacaoOrigem.PRODUCAO.value)
            .order_by(MovimentacaoEstoque.id).all())


def _concluir_tudo(obra, *moveis: str) -> dict:
    return obra.concluir(*_todas(obra.ler(), *moveis))


def test_desligado_nada_entra_no_estoque(obra, db_session):
    producao = _concluir_tudo(obra, "Balcão")

    assert obra.movel("Balcão", producao)["pronto"] is True
    assert obra.movel("Balcão", producao)["faturamento"] is None
    assert db_session.query(MarcenariaMovelFaturamento).count() == 0
    assert _movs_producao(db_session) == []


def test_pronto_entra_e_reaberto_estorna(obra, ligado, db_session):
    padrao = ligado.produto_acabado_padrao_id

    producao = _concluir_tudo(obra, "Balcão")

    assert obra.movel("Balcão", producao)["faturamento"] == "NO_ESTOQUE"
    assert obra.movel("Aéreo", producao)["faturamento"] is None            # ainda nao esta pronto
    assert _estoque(db_session, padrao) == 1
    (entrada,) = _movs_producao(db_session)
    assert (entrada.tipo.value, entrada.quantidade, entrada.produto_id) == ("ENTRADA", 1, padrao)

    # Concluir de novo (idempotente) nao duplica a entrada.
    _concluir_tudo(obra, "Balcão")
    assert _estoque(db_session, padrao) == 1

    # Reabrir uma etapa: o movel deixou de estar pronto, a entrada e estornada.
    corte = obra.etapa("Balcão", "Corte")
    producao = obra.escrever("POST", f"/etapas/{corte['id']}/reabrir")
    assert obra.movel("Balcão", producao)["faturamento"] is None
    assert _estoque(db_session, padrao) == 0
    assert [m.tipo.value for m in _movs_producao(db_session)] == ["ENTRADA", "SAIDA"]

    # Pronto de novo: entra de novo, na MESMA linha (movel_id e unico).
    obra.concluir(corte["id"])
    assert _estoque(db_session, padrao) == 1
    assert db_session.query(MarcenariaMovelFaturamento).count() == 1


def test_terceirizado_conferido_entra_no_produto_de_revenda(api, obra, ligado, db_session):
    revenda = ligado.produto_acabado_revenda_id

    _terceirizado(api, obra.numero_os, "CONFERIDO")

    assert _estoque(db_session, revenda) == 1
    linha = db_session.query(MarcenariaMovelFaturamento).one()
    assert (linha.produto_id, linha.custo_unitario_centavos, linha.situacao) == (revenda, 38000, "NO_ESTOQUE")


def test_movel_com_tipo_fiscal_proprio_entra_nele(api, obra, ligado, db_session, produto):
    cozinha = produto("Cozinha planejada")
    movel = obra.movel("Balcão")
    db_session.query(MarcenariaMovelFaturamento).delete()
    from app.db.models.marcenaria import MarcenariaMovel
    db_session.get(MarcenariaMovel, movel["movel_id"]).produto_acabado_id = cozinha
    db_session.commit()

    _concluir_tudo(obra, "Balcão")

    assert db_session.query(MarcenariaMovelFaturamento).one().produto_id == cozinha


def test_acabado_nao_entra_no_cmv(obra, ligado, db_session):
    """R3: o CMV da OS so le ORDEM_SERVICO. A entrada e a saida do acabado
    (origem PRODUCAO) nao podem aparecer nele."""
    _concluir_tudo(obra, "Balcão", "Aéreo")
    os_ = db_session.query(OrdemServico).filter_by(numero_os=obra.numero_os).one()
    os_.status = OrdemServicoStatus.FINALIZADA
    os_.data_finalizacao = datetime.now()
    db_session.commit()

    linhas = get_cmv_os(db_session, datetime.now() - timedelta(days=1), datetime.now() + timedelta(days=1),
                        ligado.empresa_id)

    assert sum(total for _tipo, total, _sem in linhas) == 0                # nenhuma separacao: CMV zero


def test_cancelar_a_os_estorna_o_que_esta_no_estoque(api, obra, ligado, db_session):
    _concluir_tudo(obra, "Balcão")

    r = api.client.put(f"{OS_URL}/{obra.numero_os}/cancelar", json={"motivo": "Cliente desistiu"}, headers=api.header)

    assert r.status_code == 200, r.text
    assert _estoque(db_session, ligado.produto_acabado_padrao_id) == 0
    assert db_session.query(MarcenariaMovelFaturamento).one().situacao == "ESTORNADO"


def test_movel_faturado_barra_o_cancelamento(api, obra, ligado, db_session):
    _concluir_tudo(obra, "Balcão")
    linha = db_session.query(MarcenariaMovelFaturamento).one()
    linha.situacao = "FATURADO"                              # como se a NF-e tivesse saido (F3)
    db_session.commit()

    r = api.client.put(f"{OS_URL}/{obra.numero_os}/cancelar", json={"motivo": "Cliente desistiu"}, headers=api.header)

    assert r.status_code == 409, r.text
    assert "Balcão" in r.json()["detail"] and "Cancele a nota" in r.json()["detail"]
    db_session.expire_all()
    assert db_session.query(OrdemServico).filter_by(numero_os=obra.numero_os).one().status != OrdemServicoStatus.CANCELADA
    assert _estoque(db_session, ligado.produto_acabado_padrao_id) == 1    # nada foi mexido


URL_SINCRONIZAR = "/api/v1/marcenaria/faturamento/sincronizar"


def test_ligar_com_obra_em_andamento_da_entrada_nos_ja_prontos(api, obra, db_session):
    """Moveis prontos ANTES de ligar: o botao da a entrada (e nao duplica)."""
    _concluir_tudo(obra, "Balcão")                                         # desligado: nada entrou
    assert db_session.query(MarcenariaMovelFaturamento).count() == 0
    assert api.client.post(URL_SINCRONIZAR, headers=api.header).status_code == 409   # ainda desligado

    api.client.post(f"{URL_CONFIG}/produtos-acabados", headers=api.header)
    api.client.put(URL_CONFIG, json={"faturamento_modo": "NOTA_NA_ENTREGA"}, headers=api.header)
    r = api.client.post(URL_SINCRONIZAR, headers=api.header)

    assert r.status_code == 200, r.text
    assert r.json() == {"os_conferidas": 1, "moveis_no_estoque": 1, "entraram_agora": 1}
    assert api.client.post(URL_SINCRONIZAR, headers=api.header).json()["entraram_agora"] == 0


def test_os_fechada_fica_de_fora_da_sincronizacao(api, obra, db_session):
    _concluir_tudo(obra, "Balcão")
    os_ = db_session.query(OrdemServico).filter_by(numero_os=obra.numero_os).one()
    os_.status = OrdemServicoStatus.FINALIZADA
    db_session.commit()
    api.client.post(f"{URL_CONFIG}/produtos-acabados", headers=api.header)
    api.client.put(URL_CONFIG, json={"faturamento_modo": "NOTA_NA_ENTREGA"}, headers=api.header)

    assert api.client.post(URL_SINCRONIZAR, headers=api.header).json()["entraram_agora"] == 0
