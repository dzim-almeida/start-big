# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/embalagens/test_venda_por_embalagem.py
# DESCRIÇÃO: Venda e orçamento por embalagem (plano de embalagens, fase 3).
#
# O que não pode regredir: com a chave `usar_embalagens` DESLIGADA (o padrão),
# a venda é exatamente a de antes — e ligada, a baixa, o estorno e a conversão
# do orçamento usam quantidade × fator congelado na linha.
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.contador_venda import ContadorVenda
from app.db.models.estoque import Estoque
from app.db.models.produto import Produto


@pytest.fixture
def loja(client: TestClient, db_session: Session, header_com_token) -> dict:
    """Cerveja com 100 un, FD 12 (preço próprio) e CX 24 (5% de desconto)."""
    if not db_session.query(ContadorVenda).first():
        db_session.add(ContadorVenda(id=1, proximo_numero=1))
    produto = Produto(nome="Cerveja Lata 350ml", codigo_produto="CERV-350", codigo_barras="7891000000001",
                      unidade_medida="UN", ativo=True)
    produto.estoque = Estoque(quantidade=100, valor_varejo=450, custo_medio=300)
    db_session.add(produto)
    db_session.commit()

    embalagens = client.put(
        f"/api/v1/produtos/{produto.id}/embalagens",
        json={"embalagens": [
            {"sigla": "FD", "fator": 12, "preco": 4800, "codigo_barras": "17891000000008"},
            {"sigla": "CX", "fator": 24, "desconto_bp": 500},
            {"sigla": "DP", "fator": 6, "vende_no_pdv": False},
        ]},
        headers=header_com_token,
    )
    assert embalagens.status_code == 200, embalagens.text
    ids = {e["sigla"]: e["id"] for e in embalagens.json()}

    funcionario = client.post("/api/v1/funcionarios/", json={
        "nome": "Vendedor Teste", "cpf": "11122233344", "contato": "11999999999",
        "usuario": {"nome": "vendedor1", "email": "vend1@empresa.com", "senha": "SenhaForte123!"},
        "endereco": [{"logradouro": "Rua X", "numero": "1", "cep": "12345-678",
                      "bairro": "Centro", "cidade": "Lab City", "estado": "SP"}],
    }, headers=header_com_token)
    assert funcionario.status_code in (200, 201), funcionario.text
    fp = client.post("/api/v1/formas-pagamento/", json={"nome": "Dinheiro", "ativo": True}, headers=header_com_token)
    assert fp.status_code == 201, fp.text
    return {"produto_id": produto.id, "funcionario_id": funcionario.json()["id"], "fp_id": fp.json()["id"], **ids}


def ligar_embalagens(client, headers, ligado=True):
    r = client.put("/api/v1/configuracoes/produtos", json={"usar_embalagens": ligado}, headers=headers)
    assert r.status_code == 200, r.text


def nova_venda(client, headers, loja) -> int:
    r = client.post("/api/v1/vendas/", json={"funcionario_id": loja["funcionario_id"]}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def lancar(client, headers, venda_id, produto_id, quantidade, embalagem_id=None):
    payload = {"tipo_produto": "CADASTRADO", "produto_id": produto_id, "quantidade": quantidade}
    if embalagem_id is not None:
        payload["embalagem_id"] = embalagem_id
    return client.post(f"/api/v1/vendas/{venda_id}/itens", json=payload, headers=headers)


def finalizar(client, headers, venda_id, loja):
    total = client.get(f"/api/v1/vendas/{venda_id}", headers=headers).json()["total"]
    r = client.post(f"/api/v1/vendas/{venda_id}/finalizar", json={
        "pagamentos": [{"forma_pagamento_id": loja["fp_id"], "valor": total, "parcelado": False, "qtd_parcelas": None}],
    }, headers=headers)
    assert r.status_code == 200, r.text


def estoque(db_session, produto_id) -> int:
    db_session.expire_all()
    return db_session.get(Estoque, produto_id).quantidade


def linhas(client, headers, venda_id) -> list[dict]:
    return client.get(f"/api/v1/vendas/{venda_id}", headers=headers).json()["produtos"]


# ── Chave desligada: nada muda ───────────────────────────────────────────────

def test_desligado_recusa_embalagem_e_vende_unidade_como_sempre(client, db_session, header_com_token, loja):
    venda = nova_venda(client, header_com_token, loja)
    r = lancar(client, header_com_token, venda, loja["produto_id"], 1, loja["FD"])
    assert r.status_code == 400 and "desligada" in r.text

    assert lancar(client, header_com_token, venda, loja["produto_id"], 3).status_code == 201
    [linha] = linhas(client, header_com_token, venda)
    assert (linha["fator_embalagem"], linha["sigla_embalagem"], linha["valor_unitario"]) == (1, None, 450)
    finalizar(client, header_com_token, venda, loja)
    assert estoque(db_session, loja["produto_id"]) == 97


def test_desligado_a_busca_nao_acha_o_codigo_do_fardo(client, header_com_token, loja):
    r = client.get("/api/v1/produtos/search", params={"search": "17891000000008"}, headers=header_com_token)
    assert r.status_code == 200
    assert all(p["id"] != loja["produto_id"] or p["embalagens"] == [] for p in r.json())
    assert all(p["id"] != loja["produto_id"] for p in r.json())


# ── Chave ligada ──────────────────────────────────────────────────────────────

def test_fardo_e_uma_linha_com_preco_do_fardo_e_baixa_por_fator(client, db_session, header_com_token, loja):
    ligar_embalagens(client, header_com_token)
    venda = nova_venda(client, header_com_token, loja)
    assert lancar(client, header_com_token, venda, loja["produto_id"], 2, loja["FD"]).status_code == 201
    assert lancar(client, header_com_token, venda, loja["produto_id"], 3).status_code == 201

    fardo, avulsa = sorted(linhas(client, header_com_token, venda), key=lambda l: -l["fator_embalagem"])
    assert (fardo["quantidade"], fardo["sigla_embalagem"], fardo["fator_embalagem"]) == (2, "FD", 12)
    assert fardo["valor_unitario"] == 4800 and fardo["subtotal"] == 9600
    assert (avulsa["quantidade"], avulsa["fator_embalagem"], avulsa["valor_unitario"]) == (3, 1, 450)

    finalizar(client, header_com_token, venda, loja)
    # 100 − (2 × 12) − 3 = 73
    assert estoque(db_session, loja["produto_id"]) == 73

    # O CMV vem do livro, em unidade: 27 un × custo 3,00.
    movs = client.get("/api/v1/produtos/movimentacoes", params={"produto_id": loja["produto_id"]},
                      headers=header_com_token).json()
    saidas = sorted(m["quantidade"] for m in movs if m["tipo"] == "SAIDA")
    assert saidas == [3, 24]
    assert all(m["custo_unitario"] == 300 for m in movs if m["tipo"] == "SAIDA")


def test_preco_da_caixa_com_desconto_percentual(client, header_com_token, loja):
    ligar_embalagens(client, header_com_token)
    venda = nova_venda(client, header_com_token, loja)
    assert lancar(client, header_com_token, venda, loja["produto_id"], 1, loja["CX"]).status_code == 201
    [linha] = linhas(client, header_com_token, venda)
    # 24 × 4,50 = 108,00 − 5% = 102,60
    assert linha["valor_unitario"] == 10260


def test_cancelar_estorna_pelo_fator_congelado(client, db_session, header_com_token, loja):
    ligar_embalagens(client, header_com_token)
    venda = nova_venda(client, header_com_token, loja)
    lancar(client, header_com_token, venda, loja["produto_id"], 2, loja["FD"])
    finalizar(client, header_com_token, venda, loja)
    assert estoque(db_session, loja["produto_id"]) == 76

    # Mudar o fator no cadastro depois NÃO pode mudar o estorno de hoje (D6).
    client.put(f"/api/v1/produtos/{loja['produto_id']}/embalagens", json={"embalagens": [
        {"id": loja["FD"], "sigla": "FD", "fator": 15, "preco": 4800, "codigo_barras": "17891000000008"},
    ]}, headers=header_com_token)

    r = client.post(f"/api/v1/vendas/{venda}/cancelar", json={"motivo": "cliente desistiu da compra"},
                    headers=header_com_token)
    assert r.status_code == 200, r.text
    assert estoque(db_session, loja["produto_id"]) == 100


def test_estoque_compara_unidades_da_embalagem(client, header_com_token, loja):
    ligar_embalagens(client, header_com_token)
    r = client.put("/api/v1/configuracoes/produtos", json={"permitir_venda_estoque_zerado": False}, headers=header_com_token)
    assert r.status_code == 200, r.text
    venda = nova_venda(client, header_com_token, loja)
    # 9 FD = 108 un > 100 — recusa (a loja não permite vender sem estoque).
    r = lancar(client, header_com_token, venda, loja["produto_id"], 9, loja["FD"])
    assert r.status_code == 400 and "insuficiente" in r.text
    assert lancar(client, header_com_token, venda, loja["produto_id"], 8, loja["FD"]).status_code == 201

    [linha] = linhas(client, header_com_token, venda)
    r = client.patch(f"/api/v1/vendas/{venda}/itens/{linha['id']}", json={"quantidade": 9}, headers=header_com_token)
    assert r.status_code == 400 and "insuficiente" in r.text


def test_embalagem_fora_do_pdv_ou_de_outro_produto_e_recusada(client, header_com_token, loja):
    ligar_embalagens(client, header_com_token)
    venda = nova_venda(client, header_com_token, loja)
    assert lancar(client, header_com_token, venda, loja["produto_id"], 1, loja["DP"]).status_code == 400
    assert lancar(client, header_com_token, venda, loja["produto_id"], 1, 99999).status_code == 400


def test_so_embalagem_fechada_recusa_a_unidade(client, header_com_token, loja):
    ligar_embalagens(client, header_com_token)
    r = client.put(f"/api/v1/produtos/{loja['produto_id']}/embalagens", json={
        "so_embalagem_fechada": True,
        "embalagens": [{"id": loja["FD"], "sigla": "FD", "fator": 12, "preco": 4800, "codigo_barras": "17891000000008"}],
    }, headers=header_com_token)
    assert r.status_code == 200, r.text

    venda = nova_venda(client, header_com_token, loja)
    r = lancar(client, header_com_token, venda, loja["produto_id"], 1)
    assert r.status_code == 400 and "embalagem fechada" in r.text
    assert lancar(client, header_com_token, venda, loja["produto_id"], 1, loja["FD"]).status_code == 201

    # Desligar a chave da loja desliga a trava junto.
    ligar_embalagens(client, header_com_token, False)
    assert lancar(client, header_com_token, venda, loja["produto_id"], 1).status_code == 201


def test_busca_do_pdv_acha_pelo_codigo_do_fardo_e_traz_os_precos(client, header_com_token, loja):
    ligar_embalagens(client, header_com_token)
    r = client.get("/api/v1/produtos/search", params={"search": "17891000000008"}, headers=header_com_token)
    assert r.status_code == 200, r.text
    [produto] = [p for p in r.json() if p["id"] == loja["produto_id"]]
    por_sigla = {e["sigla"]: e for e in produto["embalagens"]}
    # DP não é vendido no caixa: não aparece.
    assert set(por_sigla) == {"FD", "CX"}
    assert por_sigla["FD"]["preco"] == 4800 and por_sigla["FD"]["codigo_barras"] == "17891000000008"
    assert por_sigla["CX"]["preco"] == 10260


def test_orcamento_por_embalagem_vira_venda_por_embalagem(client, db_session, header_com_token, loja):
    ligar_embalagens(client, header_com_token)
    orc = client.post("/api/v1/orcamentos/", json={"funcionario_id": loja["funcionario_id"]}, headers=header_com_token)
    assert orc.status_code == 201, orc.text
    orc_id = orc.json()["id"]
    r = client.post(f"/api/v1/orcamentos/{orc_id}/itens", json={
        "tipo_produto": "CADASTRADO", "produto_id": loja["produto_id"], "quantidade": 2, "embalagem_id": loja["FD"],
    }, headers=header_com_token)
    assert r.status_code == 201, r.text

    cliente = client.post("/api/v1/clientes/cliente_pf", json={
        "nome": "João Pedro Silva", "cpf": "98765432101", "tipo": "PF", "celular": "11987654321",
        "endereco": [{"logradouro": "Rua das Flores", "numero": "100", "bairro": "Centro",
                      "cidade": "Campinas", "estado": "SP", "cep": "13010-000"}],
    }, headers=header_com_token)
    assert cliente.status_code == 201, cliente.text
    conv = client.post(f"/api/v1/orcamentos/{orc_id}/converter", json={"cliente_id": cliente.json()["id"]},
                       headers=header_com_token)
    assert conv.status_code in (200, 201), conv.text
    venda_id = conv.json()["id"]
    [linha] = linhas(client, header_com_token, venda_id)
    assert (linha["quantidade"], linha["sigla_embalagem"], linha["fator_embalagem"], linha["valor_unitario"]) == (2, "FD", 12, 4800)

    finalizar(client, header_com_token, venda_id, loja)
    assert estoque(db_session, loja["produto_id"]) == 76
