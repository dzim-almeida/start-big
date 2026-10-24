# ---------------------------------------------------------------------------
# ARQUIVO: test/services/marcenaria/test_faturamento_tipo_fiscal.py
# DESCRICAO: O "tipo fiscal" do movel no orcamento (docs/marcenaria-faturamento-
#            plano.md, D3): o produto acabado que o movel vira na nota.
#
#            O que nao pode errar:
#              - AUSENTE no PUT mantem o gravado (a tela antiga nao manda o
#                campo e nao pode apagar a escolha);
#              - null volta ao padrao da configuracao;
#              - a nova versao do orcamento leva a escolha junto.
# ---------------------------------------------------------------------------

import pytest
from fastapi import HTTPException

from app.db.models.marcenaria import MarcenariaOrcamento
from app.schemas.marcenaria.orcamento import AmbienteEntrada, MovelEntrada, OrcamentoCriar
from app.services.marcenaria import orcamento as servico
from app.services.marcenaria import orcamento_arvore as arvore


def _orcamento(db, orcamento_id: int) -> MarcenariaOrcamento:
    db.expire_all()
    return db.get(MarcenariaOrcamento, orcamento_id)


def _movel(db, oid):
    return _orcamento(db, oid).ambientes[0].moveis[0]


def _com_movel(db, token, **campos_do_movel) -> int:
    """Orcamento com um ambiente e um movel (revisao 3 no fim)."""
    oid = servico.criar_orcamento(db, OrcamentoCriar(projeto_nome="Cozinha"), token)
    arvore.criar_ambiente(db, oid, 1, AmbienteEntrada(nome="Cozinha"))
    amb = _orcamento(db, oid).ambientes[0].id
    arvore.criar_movel(db, oid, amb, 2, MovelEntrada(nome="Armário", **campos_do_movel), token)
    return oid


def test_movel_novo_sem_o_campo_fica_no_padrao(db_session, token_master):
    oid = _com_movel(db_session, token_master)
    assert _movel(db_session, oid).produto_acabado_id is None


def test_gravado_ausente_mantem_e_null_volta_ao_padrao(db_session, token_master, produto):
    cozinha = produto("Cozinha planejada")
    oid = _com_movel(db_session, token_master, produto_acabado_id=cozinha)
    movel = _movel(db_session, oid)
    assert movel.produto_acabado_id == cozinha

    # PUT sem o campo (a tela de antes): a escolha fica.
    arvore.atualizar_movel(db_session, oid, movel.id, 3, MovelEntrada(nome="Armário aéreo"), token_master)
    assert _movel(db_session, oid).produto_acabado_id == cozinha

    # PUT com null: volta ao padrao da configuracao.
    arvore.atualizar_movel(db_session, oid, movel.id, 4, MovelEntrada(nome="Armário aéreo", produto_acabado_id=None),
                           token_master)
    assert _movel(db_session, oid).produto_acabado_id is None


def test_produto_inexistente_e_recusado(db_session, token_master):
    with pytest.raises(HTTPException) as erro:
        _com_movel(db_session, token_master, produto_acabado_id=999_999)
    assert "Tipo fiscal do móvel" in str(erro.value.detail)


def test_detalhe_mostra_e_nova_versao_copia(db_session, token_master, produto, cliente_id):
    cozinha = produto("Cozinha planejada")
    oid = _com_movel(db_session, token_master, produto_acabado_id=cozinha)
    orc = _orcamento(db_session, oid)
    orc.cliente_id = cliente_id
    db_session.commit()

    detalhe = servico.detalhe(db_session, oid, token_master)
    assert detalhe["ambientes"][0]["moveis"][0]["produto_acabado_id"] == cozinha

    servico.enviar(db_session, oid, 3, token_master)
    servico.recusar(db_session, oid, 4, "Preço", token_master)
    novo = servico.nova_versao(db_session, oid, 5, token_master)
    assert _movel(db_session, novo).produto_acabado_id == cozinha
