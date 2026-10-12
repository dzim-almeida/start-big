# ---------------------------------------------------------------------------
# ARQUIVO: test/services/marcenaria/test_rt.py
# DESCRICAO: Conta a pagar do RT do arquiteto (Spec 09A, §12, casos 01-12,
#            17-23).
#
#            O que nao pode errar:
#              - uma conta por arquiteto na FINALIZACAO, somando o RT do aprovado;
#              - reabrir/refinalizar nunca duplica, e conta paga nunca e mexida;
#              - cancelar OS finalizada com RT pago deixa o aviso no historico.
# ---------------------------------------------------------------------------

from datetime import timedelta

import pytest

from app.core.tempo import hoje_local
from app.db.models.configuracao_marcenaria import ConfiguracaoMarcenaria
from app.db.models.conta_pagar import ContaPagar
from app.db.models.marcenaria import MarcenariaEvento
from app.db.models.ordem_servico import OrdemServico
from app.db.models.plano_conta import PlanoConta

from test.apoio_orcamento_marcenaria import aprovar, montar_cenario_b

OS_URL = "/api/v1/ordens-servico"


@pytest.fixture
def pix(forma_pagamento) -> int:
    return forma_pagamento("PIX")


def _finalizar(api, numero: str, pix: int, valor: int, **extra):
    r = api.client.put(f"{OS_URL}/{numero}/finalizar", json={
        "situacao_equipamento": "REPARADO", "pagamentos": [{"forma_pagamento_id": pix, "valor": valor}], **extra,
    }, headers=api.header)
    assert r.status_code == 200, r.text
    return r.json()


def _reabrir(api, numero: str):
    """Reabre com o pagamento mantido como credito da OS (o caso comum)."""
    r = api.client.put(f"{OS_URL}/{numero}/reabrir", json={"cliente_pagou": True}, headers=api.header)
    assert r.status_code == 200, r.text


def _refinalizar(api, numero: str):
    """Finaliza de novo: o credito da finalizacao anterior ja cobre o total."""
    r = api.client.put(f"{OS_URL}/{numero}/finalizar", json={"situacao_equipamento": "REPARADO", "pagamentos": []},
                       headers=api.header)
    assert r.status_code == 200, r.text


def _pagar(db, conta: ContaPagar) -> None:
    """Marca a conta como paga ao arquiteto (com data e valor, como o banco exige)."""
    conta.status, conta.pago_em, conta.valor_pago = "PAGA", hoje_local(), conta.valor
    db.commit()


def _contas(db) -> list[ContaPagar]:
    db.expire_all()
    return db.query(ContaPagar).order_by(ContaPagar.id).all()


def _aprovada(api, produto, fornecedor, cliente_id, arquitetos=None, movel_ids=None, incluir_instalacao=True):
    """Cenario B aprovado; devolve (detalhe, numero da OS)."""
    d = montar_cenario_b(api, produto, fornecedor, cliente=cliente_id, arquitetos=arquitetos)
    d = aprovar(api, d, movel_ids=movel_ids, incluir_instalacao=incluir_instalacao)
    return d, d["os"]["numero_os"]


# =========================
# Criacao (01, 02, 03, 04, 18, 19, 20)
# =========================

def test_01_uma_conta_com_o_rt_do_aprovado(api, produto, fornecedor, cliente_id, pix, db_session):
    d, numero = _aprovada(api, produto, fornecedor, cliente_id)
    assert api.detalhe(d["id"])["arquitetos"][0]["conta"] is None              # 19: antes de finalizar

    _finalizar(api, numero, pix, 923889)

    (conta,) = _contas(db_session)
    assert (conta.valor, conta.status, conta.fornecedor_id) == (73911, "PENDENTE", d["arquitetos"][0]["fornecedor_id"])
    assert conta.vencimento == hoje_local() + timedelta(days=30)
    assert conta.descricao == f"RT arquiteto — Studio Renascer — {numero} ({d['codigo']})"
    assert db_session.get(PlanoConta, conta.plano_conta_id).nome == "Comissão de arquitetos (RT)"
    assert conta.observacao is None                                             # total igual ao aprovado
    linha = api.detalhe(d["id"])["arquitetos"][0]                               # 20
    assert linha["conta"] == {"id": conta.id, "status": "PENDENTE", "valor_centavos": 73911,
                              "vencimento": conta.vencimento.isoformat()}
    (evento,) = db_session.query(MarcenariaEvento).filter_by(tipo="RT_CONTAS_CRIADAS").all()
    assert evento.os_id == d["os"]["id"] and "R$ 739,11" in evento.descricao


def test_02_dois_arquitetos_somam_o_rt(api, produto, fornecedor, cliente_id, pix, db_session):
    arquitetos = [{"fornecedor_id": fornecedor("Studio A"), "rt_bp": 500},
                  {"fornecedor_id": fornecedor("Studio B"), "rt_bp": 300}]
    _d, numero = _aprovada(api, produto, fornecedor, cliente_id, arquitetos=arquitetos)

    _finalizar(api, numero, pix, 923889)

    assert [c.valor for c in _contas(db_session)] == [46194, 27717]            # maior resto, soma 73.911


def test_03_aprovacao_parcial_rt_sobre_o_aprovado(api, produto, fornecedor, cliente_id, pix, db_session):
    d = montar_cenario_b(api, produto, fornecedor, cliente=cliente_id)
    torre = d["ambientes"][0]["moveis"][0]["id"]
    d = aprovar(api, d, movel_ids=[torre], incluir_instalacao=False)            # total 401.161
    assert d["arquitetos"][0]["valor_previsto_centavos"] == 32093               # 19: previsto sobre o aprovado

    _finalizar(api, d["os"]["numero_os"], pix, 401161)

    assert [c.valor for c in _contas(db_session)] == [32093]                    # 8% de 401.161


def test_04_sem_arquiteto_nada(api, produto, fornecedor, cliente_id, pix, db_session):
    _d, numero = _aprovada(api, produto, fornecedor, cliente_id, arquitetos=[])

    _finalizar(api, numero, pix, 923889)

    assert _contas(db_session) == []
    assert db_session.query(MarcenariaEvento).filter_by(tipo="RT_CONTAS_CRIADAS").count() == 0


def test_18_loja_sem_o_modulo_financeiro_cria_igual(api, produto, fornecedor, cliente_id, pix, db_session):
    """A conta nasce sempre (D7); o modulo so decide quem ve. Os testes rodam sem licenca."""
    _d, numero = _aprovada(api, produto, fornecedor, cliente_id)

    _finalizar(api, numero, pix, 923889)

    assert len(_contas(db_session)) == 1


def test_21_sem_view_custos_nao_ve_a_conta(api, produto, fornecedor, cliente_id, pix, como):
    d, numero = _aprovada(api, produto, fornecedor, cliente_id)
    _finalizar(api, numero, pix, 923889)
    como(view_orcamentos_marcenaria=True)

    (linha,) = api.detalhe(d["id"])["arquitetos"]

    assert set(linha) == {"fornecedor_id", "nome"}


# =========================
# Reabrir, refinalizar, cancelar (05-09, 22, 23)
# =========================

def test_05_06_reabrir_cancela_e_refinalizar_recria(api, produto, fornecedor, cliente_id, pix, db_session):
    _d, numero = _aprovada(api, produto, fornecedor, cliente_id)
    _finalizar(api, numero, pix, 923889)

    _reabrir(api, numero)
    assert [c.status for c in _contas(db_session)] == ["CANCELADA"]

    _refinalizar(api, numero)
    assert [c.status for c in _contas(db_session)] == ["CANCELADA", "PENDENTE"]   # uma so ativa


def test_07_conta_paga_fica_intacta(api, produto, fornecedor, cliente_id, pix, db_session):
    _d, numero = _aprovada(api, produto, fornecedor, cliente_id)
    _finalizar(api, numero, pix, 923889)
    (conta,) = _contas(db_session)
    _pagar(db_session, conta)                                # pago ao arquiteto

    _reabrir(api, numero)
    _refinalizar(api, numero)

    assert [c.status for c in _contas(db_session)] == ["PAGA"]                 # nada novo, nada cancelado


def test_08_22_cancelar_os_finalizada_com_rt_pago(api, produto, fornecedor, cliente_id, pix, db_session):
    d, numero = _aprovada(api, produto, fornecedor, cliente_id)
    _finalizar(api, numero, pix, 923889)
    (conta,) = _contas(db_session)
    _pagar(db_session, conta)

    r = api.client.put(f"{OS_URL}/{numero}/cancelar", json={"motivo": "Cliente desistiu"}, headers=api.header)
    assert r.status_code == 200, r.text

    (evento,) = db_session.query(MarcenariaEvento).filter_by(tipo="RT_PAGO_EM_OS_CANCELADA").all()
    assert evento.descricao == "RT já pago ao arquiteto Studio Renascer (R$ 739,11). Combine a devolução por fora."
    assert [c.status for c in _contas(db_session)] == ["PAGA"]


def test_09_23_cancelar_os_nao_finalizada_nao_mexe_no_rt(api, produto, fornecedor, cliente_id, db_session):
    _d, numero = _aprovada(api, produto, fornecedor, cliente_id)

    r = api.client.put(f"{OS_URL}/{numero}/cancelar", json={"motivo": "Desistiu"}, headers=api.header)
    assert r.status_code == 200, r.text

    assert _contas(db_session) == []
    assert db_session.query(MarcenariaEvento).filter(MarcenariaEvento.tipo.like("RT_%")).count() == 0


def test_cancelar_os_finalizada_com_rt_pendente_cancela_a_conta(api, produto, fornecedor, cliente_id, pix, db_session):
    _d, numero = _aprovada(api, produto, fornecedor, cliente_id)
    _finalizar(api, numero, pix, 923889)

    r = api.client.put(f"{OS_URL}/{numero}/cancelar", json={"motivo": "Erro"}, headers=api.header)
    assert r.status_code == 200, r.text

    assert [c.status for c in _contas(db_session)] == ["CANCELADA"]


# =========================
# Divergencia e categoria (10, 11, 12)
# =========================

def test_10_desconto_na_finalizacao_deixa_observacao(api, produto, fornecedor, cliente_id, pix, db_session):
    _d, numero = _aprovada(api, produto, fornecedor, cliente_id)

    _finalizar(api, numero, pix, 923889 - 10000, desconto=10000)               # mais R$ 100 de desconto (acumula)

    (conta,) = _contas(db_session)
    assert conta.valor == 73911                                                 # RT sobre o aprovado
    assert conta.observacao == "Total aprovado R$ 9.238,89; OS finalizada com R$ 9.138,89. RT calculado sobre o aprovado."


def test_11_categoria_renomeada_continua_sendo_usada(api, produto, fornecedor, cliente_id, pix, db_session):
    _d, n1 = _aprovada(api, produto, fornecedor, cliente_id)
    _finalizar(api, n1, pix, 923889)
    plano = db_session.get(PlanoConta, _contas(db_session)[0].plano_conta_id)
    plano.nome = "RT de arquitetos"
    db_session.commit()

    _d, n2 = _aprovada(api, produto, fornecedor, cliente_id)
    _finalizar(api, n2, pix, 923889)

    assert {c.plano_conta_id for c in _contas(db_session)} == {plano.id}
    assert db_session.query(PlanoConta).filter(PlanoConta.nome.like("%RT%")).count() == 1


def test_12_categoria_apagada_nasce_de_novo(api, produto, fornecedor, cliente_id, pix, db_session):
    """No sistema, "apagar" categoria e desativar. Renomeada e desativada: nasce outra."""
    _d, n1 = _aprovada(api, produto, fornecedor, cliente_id)
    _finalizar(api, n1, pix, 923889)
    plano = db_session.get(PlanoConta, _contas(db_session)[0].plano_conta_id)
    plano.nome, plano.ativo = "RT antigo", False
    db_session.commit()

    _d, n2 = _aprovada(api, produto, fornecedor, cliente_id)
    _finalizar(api, n2, pix, 923889)

    nova = db_session.get(PlanoConta, _contas(db_session)[-1].plano_conta_id)
    assert nova.id != plano.id and nova.nome == "Comissão de arquitetos (RT)" and nova.ativo
    db_session.expire_all()
    assert db_session.query(ConfiguracaoMarcenaria).first().rt_plano_conta_id == nova.id


def test_12b_categoria_desativada_com_o_nome_padrao_e_reativada(api, produto, fornecedor, cliente_id, pix, db_session):
    _d, n1 = _aprovada(api, produto, fornecedor, cliente_id)
    _finalizar(api, n1, pix, 923889)
    plano = db_session.get(PlanoConta, _contas(db_session)[0].plano_conta_id)
    plano.ativo = False
    db_session.commit()

    _d, n2 = _aprovada(api, produto, fornecedor, cliente_id)
    _finalizar(api, n2, pix, 923889)

    db_session.expire_all()
    assert db_session.get(PlanoConta, plano.id).ativo is True
    assert {c.plano_conta_id for c in _contas(db_session)} == {plano.id}


def test_categorias_padrao_do_financeiro_continuam_nascendo(api, produto, fornecedor, cliente_id, pix, db_session):
    """A categoria do RT nao pode fazer a loja parecer "ja configurada" (e ficar sem as padrao)."""
    _d, numero = _aprovada(api, produto, fornecedor, cliente_id)
    _finalizar(api, numero, pix, 923889)

    assert db_session.query(PlanoConta).filter(PlanoConta.padrao.is_(True)).count() > 0


# =========================
# Configuracao (17)
# =========================

def test_17_prazo_do_rt_na_configuracao(api, client, loja):
    r = client.put("/api/v1/configuracoes/marcenaria", json={"rt_vencimento_dias": 200}, headers=loja)
    assert r.status_code == 422
    assert r.json()["detail"][0]["message"] == "O prazo do RT deve ficar entre 0 e 180 dias."

    r = client.put("/api/v1/configuracoes/marcenaria", json={"rt_vencimento_dias": 45}, headers=loja)
    assert r.status_code == 200 and r.json()["rt_vencimento_dias"] == 45


def test_17b_prazo_configurado_vale_na_conta(api, produto, fornecedor, cliente_id, pix, db_session, client, loja):
    client.put("/api/v1/configuracoes/marcenaria", json={"rt_vencimento_dias": 0}, headers=loja)
    _d, numero = _aprovada(api, produto, fornecedor, cliente_id)

    _finalizar(api, numero, pix, 923889)

    assert _contas(db_session)[0].vencimento == hoje_local()


def test_os_cancelada_continua_no_banco(api, produto, fornecedor, cliente_id, db_session):
    """Sanidade: a OS da aprovacao existe e e a do orcamento."""
    d, numero = _aprovada(api, produto, fornecedor, cliente_id)
    assert db_session.query(OrdemServico).filter_by(numero_os=numero).count() == 1
