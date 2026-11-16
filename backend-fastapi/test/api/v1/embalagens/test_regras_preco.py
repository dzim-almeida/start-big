# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/embalagens/test_regras_preco.py
# DESCRIÇÃO: Regras de preço por quantidade na venda (plano de embalagens, fase 5).
#
# O que não pode regredir: com as chaves DESLIGADAS (o padrão) a venda sai
# exatamente como antes, mesmo com regra cadastrada no produto. Ligadas: R1/R3
# vão em `desconto_regra` (fora do limite e do zeramento do desconto do
# operador), R2 muda o preço e guarda o cheio.
# ---------------------------------------------------------------------------

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from test.api.v1.embalagens.test_venda_por_embalagem import (  # noqa: F401 — `loja` é fixture
    estoque,
    finalizar,
    lancar,
    ligar_embalagens,
    linhas,
    loja,
    nova_venda,
)

# Unidade a R$ 4,50 (fixture `loja`). FD de 15 por R$ 50,00 aplicado às avulsas.


@pytest.fixture
def adega(client: TestClient, header_com_token, loja) -> dict:
    """A cerveja da `loja` com o fardo de 15 (R1), a faixa de 6 (R2) e o leve-3-pague-2 (R3) cadastrados."""
    r = client.put(f"/api/v1/produtos/{loja['produto_id']}/embalagens", json={"embalagens": [
        {"id": loja["FD"], "sigla": "FD", "fator": 15, "preco": 5000, "codigo_barras": "17891000000008",
         "aplica_as_avulsas": True},
    ]}, headers=header_com_token)
    assert r.status_code == 200, r.text
    assert r.json()[0]["aplica_as_avulsas"] is True
    return {**loja, "FD": r.json()[0]["id"]}


def cadastrar_regras(client, headers, produto_id, regras):
    r = client.put(f"/api/v1/produtos/{produto_id}/regras-preco", json={"regras": regras}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def configurar(client, headers, **campos):
    r = client.put("/api/v1/configuracoes/vendas", json=campos, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


FAIXA_6 = {"tipo": "FAIXA", "quantidade": 6, "preco": 380}
LEVE_3_PAGUE_2 = {"tipo": "LEVE_PAGUE", "quantidade": 3, "pague": 2}


def ler_venda(client, headers, venda_id) -> dict:
    return client.get(f"/api/v1/vendas/{venda_id}", headers=headers).json()


# ── Cadastro ──────────────────────────────────────────────────────────────────

def test_cadastro_replace_all_e_validacoes(client, header_com_token, loja):
    url = f"/api/v1/produtos/{loja['produto_id']}/regras-preco"
    salvas = cadastrar_regras(client, header_com_token, loja["produto_id"], [FAIXA_6, LEVE_3_PAGUE_2])
    assert {r["tipo"] for r in salvas} == {"FAIXA", "LEVE_PAGUE"}
    faixa = next(r for r in salvas if r["tipo"] == "FAIXA")
    assert faixa["pague"] is None

    # Replace-all: só a faixa, com o mesmo id, preço novo.
    salvas = cadastrar_regras(client, header_com_token, loja["produto_id"],
                              [{**FAIXA_6, "id": faixa["id"], "preco": 390}])
    assert [(r["id"], r["preco"]) for r in salvas] == [(faixa["id"], 390)]
    assert client.get(url, headers=header_com_token).json()[0]["preco"] == 390

    ruins = [
        [{"tipo": "FAIXA", "quantidade": 6}],  # sem preço
        [{"tipo": "LEVE_PAGUE", "quantidade": 3, "pague": 3}],  # pague ≥ leve
        [FAIXA_6, {**FAIXA_6, "preco": 300}],  # faixa repetida
        [{**LEVE_3_PAGUE_2, "inicio": "2026-10-10", "fim": "2026-10-01"}],
        [{"tipo": "FAIXA", "quantidade": 1, "preco": 100}],
    ]
    for regras in ruins:
        assert client.put(url, json={"regras": regras}, headers=header_com_token).status_code == 422, regras

    r = client.put("/api/v1/configuracoes/vendas", json={"regra_ordem": "R1,R1,R3"}, headers=header_com_token)
    assert r.status_code == 422


# ── Desligado: nada muda (B8) ────────────────────────────────────────────────

def test_desligado_com_regras_cadastradas_vende_como_sempre(client, db_session, header_com_token, adega):
    ligar_embalagens(client, header_com_token)
    cadastrar_regras(client, header_com_token, adega["produto_id"], [FAIXA_6, LEVE_3_PAGUE_2])
    config = client.get("/api/v1/configuracoes/vendas", headers=header_com_token).json()
    assert not (config["regra_embalagem_avulsas"] or config["regra_faixas_quantidade"] or config["regra_leve_pague"])

    v = nova_venda(client, header_com_token, adega)
    r = lancar(client, header_com_token, v, adega["produto_id"], 17)
    assert r.status_code == 201, r.text
    assert r.json()["itens_alterados"] == []
    [linha] = linhas(client, header_com_token, v)
    assert (linha["valor_unitario"], linha["subtotal"], linha["desconto_regra"], linha["regra_preco"]) == (450, 7650, 0, None)
    assert ler_venda(client, header_com_token, v)["total"] == 7650
    finalizar(client, header_com_token, v, adega)
    assert estoque(db_session, adega["produto_id"]) == 83


# ── R1 ────────────────────────────────────────────────────────────────────────

def test_r1_17_latas_cobram_1_fardo_mais_2_e_baixam_17(client, db_session, header_com_token, adega):
    ligar_embalagens(client, header_com_token)
    configurar(client, header_com_token, regra_embalagem_avulsas=True)
    v = nova_venda(client, header_com_token, adega)
    r = lancar(client, header_com_token, v, adega["produto_id"], 17)
    assert r.status_code == 201, r.text
    assert r.json()["financeiro_atualizado"]["descontos_regra"] == 1750
    assert r.json()["financeiro_atualizado"]["descontos"] == 0

    [linha] = linhas(client, header_com_token, v)
    # A linha continua UN, 17 × 4,50; a regra entra como desconto próprio.
    assert (linha["quantidade"], linha["fator_embalagem"], linha["valor_unitario"]) == (17, 1, 450)
    assert (linha["subtotal"], linha["desconto"], linha["desconto_regra"], linha["total"]) == (7650, 0, 1750, 5900)
    assert (linha["regra_preco"], linha["regra_descricao"]) == ("R1", "Preço de 1 FD (15 un)")
    venda_lida = ler_venda(client, header_com_token, v)
    assert (venda_lida["total"], venda_lida["descontos"], venda_lida["descontos_regra"]) == (5900, 0, 1750)

    finalizar(client, header_com_token, v, adega)
    assert estoque(db_session, adega["produto_id"]) == 83
    assert ler_venda(client, header_com_token, v)["total"] == 5900


def test_r1_so_com_a_embalagem_marcada_e_com_embalagens_ligadas(client, header_com_token, adega):
    configurar(client, header_com_token, regra_embalagem_avulsas=True)
    # Chave de embalagens desligada: a R1 não morde.
    v = nova_venda(client, header_com_token, adega)
    lancar(client, header_com_token, v, adega["produto_id"], 17)
    assert linhas(client, header_com_token, v)[0]["regra_preco"] is None


def test_linha_de_fardo_nao_entra_na_conta_das_avulsas(client, header_com_token, adega):
    ligar_embalagens(client, header_com_token)
    configurar(client, header_com_token, regra_embalagem_avulsas=True)
    v = nova_venda(client, header_com_token, adega)
    assert lancar(client, header_com_token, v, adega["produto_id"], 1, adega["FD"]).status_code == 201
    assert lancar(client, header_com_token, v, adega["produto_id"], 10).status_code == 201
    fardo, avulsa = sorted(linhas(client, header_com_token, v), key=lambda l: -l["fator_embalagem"])
    assert (fardo["valor_unitario"], fardo["regra_preco"]) == (5000, None)
    assert (avulsa["desconto_regra"], avulsa["regra_preco"]) == (0, None)


def test_quantidade_que_cai_tira_a_regra_e_outra_linha_vem_na_resposta(client, header_com_token, adega):
    ligar_embalagens(client, header_com_token)
    configurar(client, header_com_token, regra_embalagem_avulsas=True)
    v = nova_venda(client, header_com_token, adega)
    primeira = lancar(client, header_com_token, v, adega["produto_id"], 10).json()["produto_adicionado"]
    # A segunda linha completa o fardo: a regra passa a valer nas duas, e a
    # primeira volta na resposta para a tela trocar.
    r = lancar(client, header_com_token, v, adega["produto_id"], 7)
    corpo = r.json()
    assert corpo["financeiro_atualizado"]["descontos_regra"] == 1750
    assert [i["id"] for i in corpo["itens_alterados"]] == [primeira["id"]]
    assert sum(l["desconto_regra"] for l in linhas(client, header_com_token, v)) == 1750

    r = client.patch(f"/api/v1/vendas/{v}/itens/{primeira['id']}", json={"quantidade": 1}, headers=header_com_token)
    assert r.status_code == 200, r.text
    assert all(l["desconto_regra"] == 0 and l["regra_preco"] is None for l in linhas(client, header_com_token, v))
    assert ler_venda(client, header_com_token, v)["total"] == 8 * 450


# ── R2 ────────────────────────────────────────────────────────────────────────

def test_r2_muda_o_preco_e_volta_ao_cheio_abaixo_da_faixa(client, header_com_token, adega):
    configurar(client, header_com_token, regra_faixas_quantidade=True)
    cadastrar_regras(client, header_com_token, adega["produto_id"], [FAIXA_6])
    v = nova_venda(client, header_com_token, adega)
    item = lancar(client, header_com_token, v, adega["produto_id"], 6).json()["produto_adicionado"]
    assert (item["valor_unitario"], item["valor_unitario_tabela"], item["subtotal"]) == (380, 450, 2280)
    assert (item["desconto_regra"], item["regra_preco"]) == (0, "R2")
    assert item["regra_descricao"] == "A partir de 6 un: R$ 3,80"

    r = client.patch(f"/api/v1/vendas/{v}/itens/{item['id']}", json={"quantidade": 5}, headers=header_com_token)
    linha = r.json()["produto_adicionado"]
    assert (linha["valor_unitario"], linha["valor_unitario_tabela"], linha["regra_preco"]) == (450, None, None)
    assert ler_venda(client, header_com_token, v)["total"] == 2250


# ── R3 ────────────────────────────────────────────────────────────────────────

def test_r3_leve_3_pague_2_e_respeita_a_vigencia(client, header_com_token, adega):
    configurar(client, header_com_token, regra_leve_pague=True)
    ontem = (date.today() - timedelta(days=1)).isoformat()
    cadastrar_regras(client, header_com_token, adega["produto_id"], [{**LEVE_3_PAGUE_2, "fim": ontem}])
    v = nova_venda(client, header_com_token, adega)
    lancar(client, header_com_token, v, adega["produto_id"], 7)
    assert linhas(client, header_com_token, v)[0]["regra_preco"] is None

    cadastrar_regras(client, header_com_token, adega["produto_id"], [{**LEVE_3_PAGUE_2, "inicio": date.today().isoformat()}])
    v = nova_venda(client, header_com_token, adega)
    lancar(client, header_com_token, v, adega["produto_id"], 7)
    [linha] = linhas(client, header_com_token, v)
    assert (linha["desconto_regra"], linha["regra_preco"], linha["total"]) == (900, "R3", 2250)


# ── Conflito ──────────────────────────────────────────────────────────────────

def test_conflito_menor_preco_e_ordem_do_dono(client, header_com_token, adega):
    ligar_embalagens(client, header_com_token)
    configurar(client, header_com_token, regra_embalagem_avulsas=True, regra_faixas_quantidade=True,
               regra_leve_pague=True)
    cadastrar_regras(client, header_com_token, adega["produto_id"], [FAIXA_6, LEVE_3_PAGUE_2])
    # 15 un: R1 = 50,00 · R2 = 57,00 · R3 = 45,00
    v = nova_venda(client, header_com_token, adega)
    lancar(client, header_com_token, v, adega["produto_id"], 15)
    assert linhas(client, header_com_token, v)[0]["regra_preco"] == "R3"

    configurar(client, header_com_token, regra_conflito="ORDEM", regra_ordem="R2,R1,R3")
    v = nova_venda(client, header_com_token, adega)
    lancar(client, header_com_token, v, adega["produto_id"], 15)
    [linha] = linhas(client, header_com_token, v)
    assert (linha["regra_preco"], linha["valor_unitario"], linha["total"]) == ("R2", 380, 5700)


# ── Desconto do operador × regra ─────────────────────────────────────────────

def test_desconto_do_operador_vem_depois_da_regra_e_a_finalizacao_nao_zera_a_regra(client, header_com_token, adega):
    ligar_embalagens(client, header_com_token)
    configurar(client, header_com_token, regra_embalagem_avulsas=True, permitir_desconto=True,
               desconto_maximo_percent=10)
    v = nova_venda(client, header_com_token, adega)
    lancar(client, header_com_token, v, adega["produto_id"], 17)

    # 10% sobre o que sobrou depois da regra (59,00) = 5,90: dentro do limite.
    r = client.patch(f"/api/v1/vendas/{v}", json={"desconto": 590}, headers=header_com_token)
    assert r.status_code == 200, r.text
    venda_lida = ler_venda(client, header_com_token, v)
    assert (venda_lida["descontos"], venda_lida["descontos_regra"], venda_lida["total"]) == (590, 1750, 5310)

    # 7,00 é 11% de 59,00 — passa do limite. Se a regra de R$ 17,50 contasse
    # na base (76,50), seriam 9% e passaria.
    r = client.patch(f"/api/v1/vendas/{v}", json={"desconto": 700}, headers=header_com_token)
    assert r.status_code == 400

    finalizar(client, header_com_token, v, adega)
    venda_lida = ler_venda(client, header_com_token, v)
    assert (venda_lida["descontos"], venda_lida["descontos_regra"], venda_lida["total"]) == (590, 1750, 5310)


def test_finalizacao_zera_so_o_desconto_do_operador_quando_o_limite_baixa(client, header_com_token, adega):
    ligar_embalagens(client, header_com_token)
    configurar(client, header_com_token, regra_embalagem_avulsas=True, permitir_desconto=True,
               desconto_maximo_percent=50)
    v = nova_venda(client, header_com_token, adega)
    lancar(client, header_com_token, v, adega["produto_id"], 17)
    assert client.patch(f"/api/v1/vendas/{v}", json={"desconto": 1000}, headers=header_com_token).status_code == 200
    # O dono baixa o limite: o desconto do operador cai, o da regra fica.
    configurar(client, header_com_token, desconto_maximo_percent=5)
    venda_lida = ler_venda(client, header_com_token, v)
    assert (venda_lida["descontos"], venda_lida["descontos_regra"], venda_lida["total"]) == (0, 1750, 5900)


def test_trava_de_desconto_manual_em_item_com_regra(client, header_com_token, adega):
    ligar_embalagens(client, header_com_token)
    configurar(client, header_com_token, regra_embalagem_avulsas=True, bloquear_desconto_com_regra=True)
    v = nova_venda(client, header_com_token, adega)
    item = lancar(client, header_com_token, v, adega["produto_id"], 17).json()["produto_adicionado"]
    r = client.patch(f"/api/v1/vendas/{v}/itens/{item['id']}", json={"desconto": 100}, headers=header_com_token)
    assert r.status_code == 400 and "regra de preço" in r.text
    r = client.patch(f"/api/v1/vendas/{v}", json={"desconto": 100}, headers=header_com_token)
    assert r.status_code == 400 and "regra de preço" in r.text


def test_orcamento_convertido_nasce_com_a_regra(client, header_com_token, adega):
    ligar_embalagens(client, header_com_token)
    configurar(client, header_com_token, regra_embalagem_avulsas=True)
    orc = client.post("/api/v1/orcamentos/", json={"funcionario_id": adega["funcionario_id"]}, headers=header_com_token)
    orc_id = orc.json()["id"]
    r = client.post(f"/api/v1/orcamentos/{orc_id}/itens", json={
        "tipo_produto": "CADASTRADO", "produto_id": adega["produto_id"], "quantidade": 17,
    }, headers=header_com_token)
    assert r.status_code == 201, r.text
    cliente = client.post("/api/v1/clientes/cliente_pf", json={
        "nome": "Maria Souza", "cpf": "98765432101", "tipo": "PF", "celular": "11987654321",
        "endereco": [{"logradouro": "Rua A", "numero": "1", "bairro": "Centro",
                      "cidade": "Campinas", "estado": "SP", "cep": "13010-000"}],
    }, headers=header_com_token)
    assert cliente.status_code == 201, cliente.text
    conv = client.post(f"/api/v1/orcamentos/{orc_id}/converter", json={"cliente_id": cliente.json()["id"]},
                       headers=header_com_token)
    assert conv.status_code in (200, 201), conv.text
    venda_lida = ler_venda(client, header_com_token, conv.json()["id"])
    assert (venda_lida["total"], venda_lida["descontos_regra"]) == (5900, 1750)
