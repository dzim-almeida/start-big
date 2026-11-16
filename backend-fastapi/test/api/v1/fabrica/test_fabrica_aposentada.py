# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/fabrica/test_fabrica_aposentada.py
# DESCRIÇÃO: A fábrica foi APOSENTADA (SPEC-00 da marcenaria, Revisão 15, FB1;
#            Spec 03A, D13-D17). Casos 20 a 26 da Spec 03A.
#
# A marcenaria passou a seguir as specs de docs/marcenaria/ (orçamento
# técnico). O código da fábrica continua no projeto, mas INERTE: nenhuma OS
# nova entra no trilho de 10 fases, mesmo com a chave `modo_fabrica` gravada
# como ligada no banco.
#
# O que estes testes provam:
#   - a chave gravada não liga mais nada (casos 20 a 22);
#   - cancelar só devolve a separação de OS do trilho ANTIGO (casos 23 e 24);
#   - o Compras continua comprando para a OS da marcenaria (caso 25);
#   - informática segue com o mesmo estoque e o mesmo livro (caso 26).
#
# Os testes que montavam o trilho (test_orcamento_api, test_trilho_api,
# test_separacao_api: 50 testes) saíram no mesmo commit (Spec 03A, D17).
# ---------------------------------------------------------------------------

from app.core.enum import MovimentacaoTipo, OrdemServicoStatus
from app.db.models.movimentacao_estoque import MovimentacaoEstoque
from app.db.models.ordem_servico import OrdemServico
from app.db.models.produto import Produto
from app.services.compras.demanda_os import demandas_por_produto
from app.services.fabrica.modo import modo_fabrica_ligado

OS = "/api/v1/ordens-servico"  # rota comum de OS


# =========================
# Helpers
# =========================

def _item_chapa(produto_id: int, quantidade: float = 2) -> dict:
    """Item de produto (a chapa de MDF da fixture `chapa`) para pôr na OS."""
    return {
        "tipo": "PRODUTO",
        "item_id": produto_id,           # id do produto no catálogo
        "nome": "MDF Branco 15mm",
        "unidade_medida": "UN",
        "quantidade": quantidade,
        "valor_unitario": 30000,         # centavos
    }


def _estoque(db_session, produto_id: int) -> float:
    """Saldo do produto lido do banco (e não do cache da sessão)."""
    db_session.expire_all()
    return float(db_session.get(Produto, produto_id).estoque.quantidade)


def _entradas_da_os(db_session, os_id: int) -> list[MovimentacaoEstoque]:
    """Entradas de estoque que o livro registrou para esta OS."""
    db_session.expire_all()
    return (
        db_session.query(MovimentacaoEstoque)
        .filter(MovimentacaoEstoque.ordem_servico_id == os_id,
                MovimentacaoEstoque.tipo == MovimentacaoTipo.ENTRADA)
        .all()
    )


def _marcar_separado(db_session, os_: OrdemServico, quantidade: float) -> int:
    """Simula a separação de um item (o que a Spec 10A vai fazer) gravando a
    coluna `quantidade_separada` direto no banco. Devolve o id do item."""
    item = os_.itens[0]
    item.quantidade_separada = quantidade
    item.custo_real = 30000
    db_session.commit()
    return item.id


# =========================
# A chave gravada não liga mais nada (casos 20, 21 e 22)
# =========================

def test_chave_ligada_no_banco_nao_liga_a_fabrica(client, header_com_token, modo_fabrica, db_session):
    """Caso 20: a fixture grava `modo_fabrica = true` na marcenaria."""
    assert modo_fabrica_ligado(db_session) is False


def test_os_de_planejados_nasce_fora_do_trilho(client, header_com_token, modo_fabrica, abrir_os):
    """Caso 21: com a chave ligada, a OS nova continua sem fase."""
    os_ = abrir_os()
    assert os_.fase_fabrica is None


def test_status_da_os_troca_pela_rota_comum(client, header_com_token, modo_fabrica, abrir_os):
    """Caso 22: sem fase, o trilho não trava o status (assert_status_manual sai cedo)."""
    os_ = abrir_os()

    r = client.put(f"{OS}/{os_.numero_os}", json={"status": "EM_ANDAMENTO"}, headers=header_com_token)

    assert r.status_code == 200, r.text
    assert r.json()["status"] == "EM_ANDAMENTO"


# =========================
# Cancelamento (casos 23 e 24)
# =========================

def test_cancelar_os_sem_fase_nao_devolve_o_separado(client, header_com_token, modo_fabrica, abrir_os,
                                                     chapa, db_session):
    """
    Caso 23 (D15). A OS da marcenaria nova separa pela mesma coluna (Spec 10A),
    mas a regra dela é NÃO devolver sozinha: chapa cortada não volta à
    prateleira por um clique (E2a). Antes desta spec, o cancelamento chamava
    `devolver_tudo` em qualquer OS e criaria uma entrada aqui.
    """
    os_ = abrir_os(itens=[_item_chapa(chapa)])
    item_id = _marcar_separado(db_session, os_, 2)
    saldo_antes = _estoque(db_session, chapa)

    r = client.put(f"{OS}/{os_.numero_os}/cancelar", json={"motivo": "Cliente desistiu"},
                   headers=header_com_token)

    assert r.status_code == 200, r.text
    assert _entradas_da_os(db_session, os_.id) == []            # nenhuma entrada nova
    assert _estoque(db_session, chapa) == saldo_antes             # prateleira igual
    item = next(i for i in r.json()["itens"] if i["id"] == item_id)
    assert item["quantidade_separada"] == 2                       # separação intacta


def test_cancelar_os_do_trilho_antigo_devolve_como_antes(client, header_com_token, modo_fabrica, abrir_os,
                                                         chapa, db_session):
    """
    Caso 24. Uma OS que já estava no trilho (fase gravada antes da
    aposentadoria) continua com a regra antiga até fechar: cancelar devolve o
    separado (D6 do plano da fábrica).
    """
    os_ = abrir_os(itens=[_item_chapa(chapa)])
    item_id = _marcar_separado(db_session, os_, 2)
    os_.fase_fabrica = "EM_PRODUCAO"          # cenário do trilho antigo, gravado à mão
    db_session.commit()
    saldo_antes = _estoque(db_session, chapa)

    r = client.put(f"{OS}/{os_.numero_os}/cancelar", json={"motivo": "Cliente desistiu"},
                   headers=header_com_token)

    assert r.status_code == 200, r.text
    entradas = _entradas_da_os(db_session, os_.id)
    assert [float(m.quantidade) for m in entradas] == [2.0]      # uma entrada no livro
    assert _estoque(db_session, chapa) == saldo_antes + 2        # voltou à prateleira
    item = next(i for i in r.json()["itens"] if i["id"] == item_id)
    assert item["quantidade_separada"] is None                    # nada mais separado


# =========================
# Compras (caso 25)
# =========================

def test_compras_continua_comprando_para_a_os_da_marcenaria(client, header_com_token, modo_fabrica,
                                                            abrir_os, chapa, db_session):
    """Caso 25: OS sem fase -> `pode_comprar(None, ...)` responde True."""
    os_ = abrir_os(itens=[_item_chapa(chapa)])

    demandas = demandas_por_produto(db_session, [chapa])

    da_os = [d for d in demandas[chapa] if d.os_id == os_.id]    # a demanda desta OS
    assert len(da_os) == 1
    assert da_os[0].quantidade == 2
    assert da_os[0].pode_comprar is True


# =========================
# GUARDIÃO: informática com o mesmo estoque e o mesmo livro (caso 26)
# =========================

def test_informatica_finaliza_e_cancela_com_o_mesmo_estoque(client, header_com_token, segmento,
                                                            cliente_id, chapa, db_session):
    """
    Caso 26. Informática não tem `quantidade_separada` em item nenhum, então o
    cancelamento faz exatamente o de sempre: finalizar baixa a peça, cancelar a
    OS finalizada devolve. Uma saída e uma entrada no livro, saldo de volta.
    """
    segmento("assistencia_tecnica")
    saldo_inicial = _estoque(db_session, chapa)

    # Forma de pagamento para poder finalizar.
    r = client.post("/api/v1/formas-pagamento/", json={"nome": "Dinheiro", "ativo": True},
                    headers=header_com_token)
    assert r.status_code == 201, r.text
    forma_id = r.json()["id"]

    # Abre a OS de informática pela rota comum (o caminho de sempre).
    r = client.post(f"{OS}/", json={
        "cliente_id": cliente_id, "prioridade": "NORMAL", "defeito_relatado": "Não liga",
        "dados_adicionais": {},
        "objeto": {"marca": "Dell", "modelo": "Inspiron", "numero_serie": "SERIAL-03A-26",
                   "dados_adicionais": {}},
        "itens": [_item_chapa(chapa, quantidade=1)],
    }, headers=header_com_token)
    assert r.status_code == 201, r.text
    numero_os = r.json()["numero_os"]
    os_id = r.json()["id"]

    # Finaliza pagando o total (30000): a peça sai do estoque.
    r = client.put(f"{OS}/{numero_os}/finalizar", json={
        "situacao_equipamento": "REPARADO",
        "pagamentos": [{"forma_pagamento_id": forma_id, "valor": 30000}],
    }, headers=header_com_token)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == OrdemServicoStatus.FINALIZADA.value
    assert _estoque(db_session, chapa) == saldo_inicial - 1

    # Cancela a OS finalizada: a peça volta, como sempre voltou.
    r = client.put(f"{OS}/{numero_os}/cancelar", json={"motivo": "Teste"}, headers=header_com_token)
    assert r.status_code == 200, r.text
    assert _estoque(db_session, chapa) == saldo_inicial

    # O livro tem exatamente uma saída e uma entrada para esta OS.
    db_session.expire_all()
    tipos = sorted(
        m.tipo.value
        for m in db_session.query(MovimentacaoEstoque).filter(MovimentacaoEstoque.ordem_servico_id == os_id)
    )
    assert tipos == ["ENTRADA", "SAIDA"]
