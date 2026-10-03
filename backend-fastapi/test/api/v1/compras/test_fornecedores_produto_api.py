# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/compras/test_fornecedores_produto_api.py
# DESCRIÇÃO: Aba Fornecedores do produto (docs/compras-plano.md, fase 1).
#
# O que não pode errar: loja sem o módulo não acessa (nem por rota direta);
# quem não pode ver custo não vê — nem o ranking de "mais barato"; o
# fornecedor principal é o do cadastro do produto (uma verdade só); salvar sem
# ver o preço não apaga o preço.
# ---------------------------------------------------------------------------

from app.db.models.produto import Produto
from app.db.models.produto_fornecedor import ProdutoFornecedor
from app.schemas.compras import FornecedorDoProdutoEscrita, FornecedoresDoProdutoSalvar
from app.services.compras import fornecedores_produto as service

URL = "/api/v1/compras"


def url_produto(produto_id: int) -> str:
    return f"{URL}/produtos/{produto_id}/fornecedores"


def salvar(client, headers, produto_id, fornecedores):
    return client.put(url_produto(produto_id), json={"fornecedores": fornecedores}, headers=headers)


# --- trava do módulo (D2) -------------------------------------------------------

def test_licenca_sem_resposta_nao_libera_compras(client, header_com_token, cadastro, licenca):
    licenca()  # lista vazia = "não sei" → para COMPRAS, NÃO
    r = client.get(url_produto(cadastro["produto_id"]), headers=header_com_token)
    assert r.status_code == 403
    assert r.json()["detail"]["codigo"] == "MODULO_NAO_CONTRATADO"


def test_licenca_com_outros_modulos_e_sem_compras_nao_libera(client, header_com_token, cadastro, licenca):
    licenca("FINANCEIRO", "NFE")
    assert client.get(f"{URL}/fornecedores", headers=header_com_token).status_code == 403
    assert salvar(client, header_com_token, cadastro["produto_id"], []).status_code == 403


def test_sem_o_modulo_as_outras_rotas_continuam_iguais(client, header_com_token, cadastro, licenca):
    # Não-regressão (C11): o cadastro de produto não depende de COMPRAS.
    licenca()
    assert client.get(f"/api/v1/produtos/{cadastro['produto_id']}", headers=header_com_token).status_code == 200


# --- permissões da linha "Compras" ------------------------------------------------

def test_sem_permissao_de_compras_nao_acessa(client, cadastro, como):
    como(produto=True, view_products=True, manage_products=True)
    assert client.get(url_produto(cadastro["produto_id"])).status_code == 403


def test_visualizar_le_mas_nao_salva(client, cadastro, como):
    como(compra=True, view_purchases=True)
    assert client.get(url_produto(cadastro["produto_id"])).status_code == 200
    assert salvar(client, {}, cadastro["produto_id"], []).status_code == 403


def test_so_a_chave_generica_le_sem_preco(client, db_session, header_com_token, cadastro, como):
    # Quem só recebe mercadoria (fase 3) terá só `compra`: vê a lista, sem custo (D14).
    assert salvar(client, header_com_token, cadastro["produto_id"], [
        {"fornecedor_id": cadastro["ambev"], "ultimo_preco": 4000, "fator": 12},
        {"fornecedor_id": cadastro["atacado"], "ultimo_preco": 350},
    ]).status_code == 200

    como(compra=True)
    linhas = client.get(url_produto(cadastro["produto_id"])).json()
    assert len(linhas) == 2
    assert all(l["ultimo_preco"] is None and l["preco_unidade"] is None for l in linhas)
    assert not any(l["mais_barato"] for l in linhas)  # o ranking também revela preço
    assert all(l["acima_do_menor_bp"] == 0 for l in linhas)


# --- listar e salvar --------------------------------------------------------------

def test_produto_sem_fornecedor_lista_vazia(client, header_com_token, cadastro):
    r = client.get(url_produto(cadastro["produto_id"]), headers=header_com_token)
    assert r.status_code == 200 and r.json() == []


def test_principal_do_cadastro_aparece_mesmo_sem_linha(client, db_session, header_com_token, cadastro):
    db_session.get(Produto, cadastro["produto_id"]).fornecedor_id = cadastro["ambev"]
    db_session.commit()
    [linha] = client.get(url_produto(cadastro["produto_id"]), headers=header_com_token).json()
    assert (linha["id"], linha["fornecedor_id"], linha["fornecedor_nome"], linha["padrao"]) == (
        None, cadastro["ambev"], "Ambev", True)


def test_salva_com_embalagem_e_compara_por_unidade(client, header_com_token, cadastro, fardo):
    r = salvar(client, header_com_token, cadastro["produto_id"], [
        # Fardo de 12 a R$ 40,00 = 3,33/un. O fator enviado (1) é ignorado: a embalagem manda.
        {"fornecedor_id": cadastro["ambev"], "embalagem_id": fardo, "fator": 1, "ultimo_preco": 4000,
         "codigo_fornecedor": "  CERV-CX12 ", "prazo_dias": 3},
        # Unidade a R$ 3,50: 4,76% mais cara que o fardo.
        {"fornecedor_id": cadastro["atacado"], "ultimo_preco": 350},
    ])
    assert r.status_code == 200, r.text
    ambev, atacado = sorted(r.json(), key=lambda l: l["fornecedor_id"] != cadastro["ambev"])
    assert (ambev["embalagem_sigla"], ambev["fator"], ambev["codigo_fornecedor"], ambev["prazo_dias"]) == (
        "FD", 12, "CERV-CX12", 3)
    assert round(ambev["preco_unidade"], 2) == 333.33
    assert (ambev["mais_barato"], ambev["acima_do_menor_bp"]) == (True, 0)
    assert (atacado["mais_barato"], atacado["acima_do_menor_bp"]) == (False, 476)


def test_marcar_principal_muda_o_fornecedor_do_cadastro(client, db_session, header_com_token, cadastro):
    db_session.get(Produto, cadastro["produto_id"]).fornecedor_id = cadastro["ambev"]
    db_session.commit()
    r = salvar(client, header_com_token, cadastro["produto_id"], [
        {"fornecedor_id": cadastro["ambev"]},
        {"fornecedor_id": cadastro["atacado"], "padrao": True},
    ])
    assert r.status_code == 200, r.text
    db_session.expire_all()
    assert db_session.get(Produto, cadastro["produto_id"]).fornecedor_id == cadastro["atacado"]
    assert {l["fornecedor_id"]: l["padrao"] for l in r.json()} == {cadastro["ambev"]: False, cadastro["atacado"]: True}


def test_salvar_sem_marcar_principal_nao_apaga_o_do_cadastro(client, db_session, header_com_token, cadastro):
    db_session.get(Produto, cadastro["produto_id"]).fornecedor_id = cadastro["ambev"]
    db_session.commit()
    assert salvar(client, header_com_token, cadastro["produto_id"], [
        {"fornecedor_id": cadastro["atacado"]}]).status_code == 200
    db_session.expire_all()
    assert db_session.get(Produto, cadastro["produto_id"]).fornecedor_id == cadastro["ambev"]


def test_replace_all_apaga_o_que_nao_veio(client, db_session, header_com_token, cadastro):
    pid = cadastro["produto_id"]
    salvar(client, header_com_token, pid, [{"fornecedor_id": cadastro["ambev"]}, {"fornecedor_id": cadastro["atacado"]}])
    r = salvar(client, header_com_token, pid, [{"fornecedor_id": cadastro["atacado"]}])
    assert [l["fornecedor_id"] for l in r.json()] == [cadastro["atacado"]]
    db_session.expire_all()
    assert db_session.query(ProdutoFornecedor).count() == 1


def test_fornecedores_de_um_produto_nao_vazam_para_outro(client, header_com_token, cadastro):
    salvar(client, header_com_token, cadastro["produto_id"], [{"fornecedor_id": cadastro["ambev"]}])
    assert client.get(url_produto(cadastro["outro_id"]), headers=header_com_token).json() == []


# --- recusas ----------------------------------------------------------------------

def test_recusa_fornecedor_repetido_e_dois_principais(client, header_com_token, cadastro):
    pid, a, b = cadastro["produto_id"], cadastro["ambev"], cadastro["atacado"]
    assert salvar(client, header_com_token, pid, [{"fornecedor_id": a}, {"fornecedor_id": a}]).status_code == 422
    assert salvar(client, header_com_token, pid, [
        {"fornecedor_id": a, "padrao": True}, {"fornecedor_id": b, "padrao": True}]).status_code == 422


def test_recusa_transportadora(client, header_com_token, cadastro):
    r = salvar(client, header_com_token, cadastro["produto_id"], [{"fornecedor_id": cadastro["frete"]}])
    assert r.status_code == 422 and "transportadora" in r.json()["detail"]


def test_recusa_embalagem_de_outro_produto(client, header_com_token, cadastro, fardo):
    r = salvar(client, header_com_token, cadastro["outro_id"], [{"fornecedor_id": cadastro["ambev"], "embalagem_id": fardo}])
    assert r.status_code == 422


def test_erro_no_meio_nao_grava_nada(client, db_session, header_com_token, cadastro):
    pid = cadastro["produto_id"]
    salvar(client, header_com_token, pid, [{"fornecedor_id": cadastro["ambev"], "ultimo_preco": 4000}])
    r = salvar(client, header_com_token, pid, [{"fornecedor_id": cadastro["atacado"]}, {"fornecedor_id": 9999}])
    assert r.status_code == 404
    db_session.expire_all()
    [linha] = db_session.query(ProdutoFornecedor).all()
    assert (linha.fornecedor_id, linha.ultimo_preco) == (cadastro["ambev"], 4000)


def test_produto_inexistente(client, header_com_token, cadastro):
    assert client.get(url_produto(9999), headers=header_com_token).status_code == 404


# --- seletor ----------------------------------------------------------------------

def test_seletor_so_traz_quem_vende_e_esta_ativo(client, header_com_token, cadastro):
    nomes = [f["nome"] for f in client.get(f"{URL}/fornecedores", headers=header_com_token).json()]
    assert nomes == ["Ambev SA", "Atacado Central LTDA"]


# --- sem permissão de custo, o preço salvo fica (service) ---------------------------

def test_salvar_sem_ver_custo_preserva_o_preco(db_session, cadastro):
    pid = cadastro["produto_id"]
    service.salvar(db_session, pid, FornecedoresDoProdutoSalvar(fornecedores=[
        FornecedorDoProdutoEscrita(fornecedor_id=cadastro["ambev"], ultimo_preco=4000)]), ver_custos=True)
    service.salvar(db_session, pid, FornecedoresDoProdutoSalvar(fornecedores=[
        FornecedorDoProdutoEscrita(fornecedor_id=cadastro["ambev"], ultimo_preco=None, prazo_dias=2),
        FornecedorDoProdutoEscrita(fornecedor_id=cadastro["atacado"], ultimo_preco=1)]), ver_custos=False)
    db_session.commit()
    precos = {l.fornecedor_id: (l.ultimo_preco, l.prazo_dias) for l in db_session.query(ProdutoFornecedor)}
    assert precos == {cadastro["ambev"]: (4000, 2), cadastro["atacado"]: (None, None)}


# --- busca de produto para o pedido ----------------------------------------------------

def test_busca_produto_sem_precisar_da_permissao_de_produtos(client, cadastro, fardo, como):
    como(compra=True, view_purchases=True)
    r = client.get(f"{URL}/produtos", params={"busca": "cerv"})
    assert r.status_code == 200, r.text
    [produto] = r.json()
    assert (produto["nome"], produto["saldo"], produto["embalagens"]) == (
        "Cerveja Lata 350ml", 10, [{"id": fardo, "sigla": "FD", "fator": 12}])
    assert client.get(f"{URL}/produtos", params={"busca": ""}).json() == []
