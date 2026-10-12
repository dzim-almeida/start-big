# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/marcenaria/test_separacao_api.py
# DESCRICAO: Separacao de material da OS da marcenaria pela API (Spec 10A,
#            secao 11, casos 01-20 e 23).
#
#            O que nao pode errar:
#              - uma linha por peca embutida, com planejado e sugerido do orcamento;
#              - retirar/devolver passam pelo livro de estoque ligados a OS;
#              - a reserva do Compras acompanha cada acao, sem mudar o Compras;
#              - dois cliques ao mesmo tempo nao tiram a mesma chapa duas vezes;
#              - nenhum preco na separacao, para ninguem.
# ---------------------------------------------------------------------------

import pytest

from app.core.enum import MovimentacaoOrigem, MovimentacaoTipo, OrdemServicoItemAprovacao
from app.db.models.marcenaria import MarcenariaEvento
from app.db.models.marcenaria.ambiente import MarcenariaMovelInsumo
from app.db.models.movimentacao_estoque import MovimentacaoEstoque
from app.db.models.ordem_servico import OrdemServico
from app.db.models.ordem_servico_item import OrdemServicoItem
from app.db.models.produto import Produto
from app.db.models.produto_embalagem import ProdutoEmbalagem
from app.services.compras import demanda_os

from test.apoio_orcamento_marcenaria import URL_MARCENARIA, aprovar, aprovar_simples, montar_cenario_b

OS_URL = "/api/v1/ordens-servico"


# =========================
# Ajudantes
# =========================

@pytest.fixture
def aprovada(api, produto, fornecedor, cliente_id) -> str:
    """O cenario B aprovado inteiro; devolve o numero da OS."""
    d = aprovar(api, montar_cenario_b(api, produto, fornecedor, cliente=cliente_id))
    return d["os"]["numero_os"]


def _estoque(db, produto_id: int) -> float:
    db.expire_all()
    return db.get(Produto, produto_id).estoque.quantidade


def _definir_estoque(db, produto_id: int, quantidade: float) -> None:
    db.get(Produto, produto_id).estoque.quantidade = quantidade
    db.commit()


def _item(db, item_id: int) -> OrdemServicoItem:
    db.expire_all()
    return db.get(OrdemServicoItem, item_id)


def _chaves(valor) -> set[str]:
    """Todas as chaves de um JSON, em qualquer nivel."""
    if isinstance(valor, dict):
        return set(valor) | {k for v in valor.values() for k in _chaves(v)}
    if isinstance(valor, list):
        return {k for v in valor for k in _chaves(v)}
    return set()


def _cancelar(api, numero: str) -> None:
    r = api.client.put(f"{OS_URL}/{numero}/cancelar", json={"motivo": "Cliente desistiu"}, headers=api.header)
    assert r.status_code == 200, r.text


# =========================
# Leitura (01-04)
# =========================

def test_01_cenario_b_uma_linha_por_peca_embutida(separacao, aprovada):
    sep = separacao.ler(aprovada)

    assert [linha["descricao"] for linha in sep["linhas"]] == ["Corrediça Tandem", "MDF Branco TX 18mm"]  # sem a Torre
    mdf = next(linha for linha in sep["linhas"] if linha["descricao"].startswith("MDF"))
    assert (mdf["planejado_milesimos"], mdf["sugerido_milesimos"], mdf["quantidade_milesimos"]) == (2200, 3000, 3000)
    assert (mdf["separada_milesimos"], mdf["falta_milesimos"], mdf["concluida"]) == (0, 3000, False)
    assert mdf["moveis"] == [{"nome": "Balcão", "ambiente": "Cozinha Gourmet", "planejado_milesimos": 2200}]
    assert mdf["no_estoque_milesimos"] == 3000 and mdf["sem_cobertura_milesimos"] == 0   # estoque 10 cobre
    assert mdf["estoque_milesimos"] == 10000 and mdf["alertas"] == [] and mdf["diferenca_bp"] is None
    corredica = next(linha for linha in sep["linhas"] if linha["descricao"].startswith("Corrediça"))
    assert (corredica["unidade"], corredica["planejado_milesimos"], corredica["sugerido_milesimos"]) == ("PAR", 6000, 6000)
    assert sep["os"] == {"numero_os": aprovada, "status": "ABERTA", "editavel": True}
    assert sep["resumo"] == {"linhas": 2, "concluidas": 0, "com_falta": 0}
    assert sep["sem_cadastro"] == []


def test_02_mesmo_produto_em_3_moveis_uma_linha_arredondada_uma_vez(api, separacao, produto, cliente_id):
    chapa = produto("Chapa MDP 15mm", valor_entrada=15000, sofre_perda=False)
    _d, numero = aprovar_simples(api, cliente_id, [
        [{"produto_id": chapa, "quantidade_milesimos": q}] for q in (1400, 1200, 600)
    ])
    (linha,) = separacao.ler(numero)["linhas"]
    assert (linha["planejado_milesimos"], linha["sugerido_milesimos"]) == (3200, 4000)    # e nao 2 + 2 + 1
    assert [m["planejado_milesimos"] for m in linha["moveis"]] == [1400, 1200, 600]


def test_03_fita_em_metros_nao_arredonda(api, separacao, produto, cliente_id):
    fita = produto("Fita de borda branca", valor_entrada=350, sofre_perda=False, unidade="M")
    _d, numero = aprovar_simples(api, cliente_id, [[{"produto_id": fita, "quantidade_milesimos": 26350}]])
    (linha,) = separacao.ler(numero)["linhas"]
    assert (linha["unidade"], linha["sugerido_milesimos"]) == ("M", 26350)


def test_04_insumo_de_produto_excluido_vai_para_sem_cadastro(api, separacao, produto, cliente_id, db_session):
    chapa = produto("Chapa MDP 15mm", valor_entrada=15000, sofre_perda=False)
    puxador = produto("Puxador perfil antigo", valor_entrada=900, sofre_perda=False)
    orc = api.criar(cliente_id=cliente_id, projeto_nome="Projeto")
    d = api.ok("POST", f"/{orc['id']}/ambientes", rev=orc["revisao"], esperado=201, json={"nome": "Sala"})
    d = api.ok("POST", f"/{orc['id']}/ambientes/{d['ambientes'][0]['id']}/moveis", rev=d["revisao"], esperado=201, json={
        "nome": "Rack", "quantidade": 1, "mao_obra": {"modo": "FIXA", "centavos": 10000, "horas_centesimos": 0},
        "insumos": [{"produto_id": chapa, "quantidade_milesimos": 1000},
                    {"produto_id": puxador, "quantidade_milesimos": 2000}],
    })
    # O produto do puxador "some" do cadastro depois de copiado no orcamento (08A D1c).
    db_session.query(MarcenariaMovelInsumo).filter_by(produto_id=puxador).update({"produto_id": None})
    db_session.commit()
    numero = aprovar(api, api.detalhe(orc["id"]))["os"]["numero_os"]

    sep = separacao.ler(numero)
    assert [linha["descricao"] for linha in sep["linhas"]] == ["Chapa MDP 15mm"]   # o puxador nao tem linha (nem acao)
    assert sep["sem_cadastro"] == [{"descricao": "Puxador perfil antigo", "planejado_milesimos": 2000}]


# =========================
# Retirar e devolver (05-09)
# =========================

def test_05_retirar_da_baixa_ligada_a_os(separacao, aprovada, db_session):
    mdf = separacao.linha(aprovada, "MDF")
    _definir_estoque(db_session, mdf["produto_id"], 6)

    sep = separacao.acao(aprovada, mdf, "retirar", 3000)

    assert _estoque(db_session, mdf["produto_id"]) == 3
    mov = db_session.query(MovimentacaoEstoque).filter_by(produto_id=mdf["produto_id"]).order_by(MovimentacaoEstoque.id.desc()).first()
    os_id = db_session.query(OrdemServico.id).filter_by(numero_os=aprovada).scalar()
    assert (mov.tipo, mov.origem, mov.ordem_servico_id, mov.quantidade) == (
        MovimentacaoTipo.SAIDA, MovimentacaoOrigem.ORDEM_SERVICO.value, os_id, 3)
    linha = next(linha for linha in sep["linhas"] if linha["item_id"] == mdf["item_id"])
    assert (linha["separada_milesimos"], linha["falta_milesimos"], linha["concluida"]) == (3000, 0, True)
    assert linha["diferenca_bp"] == 3636                       # 3 chapas sobre 2,2 planejadas: +36,36%
    assert _item(db_session, mdf["item_id"]).custo_real == 28000   # custo do instante (fica gravado, nao aparece)
    evento = db_session.query(MarcenariaEvento).filter_by(tipo="MATERIAL_RETIRADO").one()
    assert evento.descricao == "Retirado do estoque: 3 UN de MDF Branco TX 18mm." and evento.os_id == os_id


def test_06_retirar_sem_saldo_acontece_e_avisa(separacao, aprovada, db_session):
    mdf = separacao.linha(aprovada, "MDF")
    _definir_estoque(db_session, mdf["produto_id"], 1)

    sep = separacao.acao(aprovada, mdf, "retirar", 3000)

    assert _estoque(db_session, mdf["produto_id"]) == -2
    linha = next(linha for linha in sep["linhas"] if linha["item_id"] == mdf["item_id"])
    assert "ESTOQUE_NEGATIVO" in linha["alertas"] and linha["estoque_milesimos"] == -2000


def test_07_retirar_acima_do_sugerido_sobe_a_quantidade(separacao, aprovada, db_session):
    mdf = separacao.linha(aprovada, "MDF")
    sep = separacao.acao(aprovada, mdf, "retirar", 4000)
    linha = next(linha for linha in sep["linhas"] if linha["item_id"] == mdf["item_id"])
    assert (linha["quantidade_milesimos"], linha["separada_milesimos"]) == (4000, 4000)
    assert "ACIMA_DO_SUGERIDO" in linha["alertas"]
    assert _item(db_session, mdf["item_id"]).quantidade == 4


def test_08_devolver_a_sobra_reduz_a_necessidade(separacao, aprovada, db_session):
    mdf = separacao.linha(aprovada, "MDF")
    sep = separacao.acao(aprovada, mdf, "retirar", 3000)
    mdf = next(linha for linha in sep["linhas"] if linha["item_id"] == mdf["item_id"])

    sep = separacao.acao(aprovada, mdf, "devolver", 1000)

    assert _estoque(db_session, mdf["produto_id"]) == 8          # 10 - 3 + 1
    linha = next(linha for linha in sep["linhas"] if linha["item_id"] == mdf["item_id"])
    assert (linha["separada_milesimos"], linha["quantidade_milesimos"], linha["concluida"]) == (2000, 2000, True)
    ultimo = db_session.query(MovimentacaoEstoque).order_by(MovimentacaoEstoque.id.desc()).first()
    assert (ultimo.tipo, ultimo.origem) == (MovimentacaoTipo.ENTRADA, MovimentacaoOrigem.ORDEM_SERVICO.value)


def test_09_devolver_mais_que_o_retirado_e_422(separacao, aprovada, db_session):
    mdf = separacao.linha(aprovada, "MDF")
    sep = separacao.acao(aprovada, mdf, "retirar", 3000)
    mdf = next(linha for linha in sep["linhas"] if linha["item_id"] == mdf["item_id"])
    r = separacao.acao(aprovada, mdf, "devolver", 4000, esperado=422)
    assert r.json()["detail"] == "Não é possível devolver mais do que foi retirado (3)."
    assert _estoque(db_session, mdf["produto_id"]) == 7         # nada mudou


def test_devolver_tudo_vira_nao_usado(separacao, aprovada, db_session):
    mdf = separacao.linha(aprovada, "MDF")
    sep = separacao.acao(aprovada, mdf, "retirar", 3000)
    mdf = next(linha for linha in sep["linhas"] if linha["item_id"] == mdf["item_id"])
    sep = separacao.acao(aprovada, mdf, "devolver", 3000)
    linha = next(linha for linha in sep["linhas"] if linha["item_id"] == mdf["item_id"])
    assert (linha["nao_usado"], linha["concluida"], linha["separada_milesimos"]) == (True, True, 0)
    item = _item(db_session, mdf["item_id"])
    assert item.status_aprovacao == OrdemServicoItemAprovacao.REPROVADO and item.quantidade == 3   # coluna > 0


def test_quantidade_zero_e_422(separacao, aprovada):
    mdf = separacao.linha(aprovada, "MDF")
    for acao in ("retirar", "devolver"):
        r = separacao.acao(aprovada, mdf, acao, 0, esperado=422)
        assert r.json()["detail"] == "A quantidade deve ser maior que zero."


# =========================
# Concluir e reabrir (10-12)
# =========================

def test_10_concluir_com_menos_solta_a_reserva(separacao, aprovada, db_session):
    mdf = separacao.linha(aprovada, "MDF")
    sep = separacao.acao(aprovada, mdf, "retirar", 2000)
    mdf = next(linha for linha in sep["linhas"] if linha["item_id"] == mdf["item_id"])
    assert demanda_os.reservado(demanda_os.demandas_por_produto(db_session, [mdf["produto_id"]])[mdf["produto_id"]]) == 1

    sep = separacao.acao(aprovada, mdf, "concluir")

    linha = next(linha for linha in sep["linhas"] if linha["item_id"] == mdf["item_id"])
    assert (linha["quantidade_milesimos"], linha["concluida"], linha["nao_usado"]) == (2000, True, False)
    assert mdf["produto_id"] not in demanda_os.demandas_por_produto(db_session, [mdf["produto_id"]])   # reserva 0


def test_11_concluir_sem_retirar_marca_nao_usado(separacao, aprovada, db_session):
    mdf = separacao.linha(aprovada, "MDF")
    sep = separacao.acao(aprovada, mdf, "concluir")
    linha = next(linha for linha in sep["linhas"] if linha["item_id"] == mdf["item_id"])
    assert (linha["nao_usado"], linha["concluida"], linha["falta_milesimos"]) == (True, True, 0)
    assert _item(db_session, mdf["item_id"]).status_aprovacao == OrdemServicoItemAprovacao.REPROVADO
    assert mdf["produto_id"] not in demanda_os.demandas_por_produto(db_session, [mdf["produto_id"]])
    # Nao usado nao se retira: primeiro reabrir.
    r = separacao.acao(aprovada, linha, "retirar", 1000, esperado=409)
    assert r.json()["detail"]["codigo"] == "ITEM_NAO_USADO"


def test_12_reabrir_volta_ao_sugerido(separacao, aprovada, db_session):
    mdf = separacao.linha(aprovada, "MDF")
    sep = separacao.acao(aprovada, mdf, "concluir")
    mdf = next(linha for linha in sep["linhas"] if linha["item_id"] == mdf["item_id"])
    sep = separacao.acao(aprovada, mdf, "reabrir")
    linha = next(linha for linha in sep["linhas"] if linha["item_id"] == mdf["item_id"])
    assert (linha["nao_usado"], linha["quantidade_milesimos"], linha["falta_milesimos"]) == (False, 3000, 3000)
    assert _item(db_session, mdf["item_id"]).status_aprovacao == OrdemServicoItemAprovacao.APROVADO


def test_concluir_duas_vezes_nao_muda_nada(separacao, aprovada, db_session):
    mdf = separacao.linha(aprovada, "MDF")
    sep = separacao.acao(aprovada, mdf, "concluir")
    mdf = next(linha for linha in sep["linhas"] if linha["item_id"] == mdf["item_id"])
    separacao.acao(aprovada, mdf, "concluir")
    assert db_session.query(MarcenariaEvento).filter_by(tipo="SEPARACAO_CONCLUIDA").count() == 1


# =========================
# Concorrencia e OS fechada (13, 14)
# =========================

def test_13_trava_velha_e_409_e_nada_muda(separacao, aprovada, db_session):
    mdf = separacao.linha(aprovada, "MDF")
    separacao.acao(aprovada, mdf, "retirar", 1000)              # outra pessoa retirou 1

    r = separacao.acao(aprovada, mdf, "retirar", 3000, esperado=409)   # a tela ainda achava 0

    assert r.json()["detail"]["codigo"] == "REVISAO_DESATUALIZADA"
    assert r.json()["detail"]["mensagem"] == "Outra pessoa alterou este item. A lista foi atualizada."
    assert _estoque(db_session, mdf["produto_id"]) == 9          # so a primeira retirada
    assert _item(db_session, mdf["item_id"]).quantidade_separada == 1


def test_14_os_finalizada_so_leitura(api, separacao, aprovada, db_session, forma_pagamento):
    mdf = separacao.linha(aprovada, "MDF")
    os_ = db_session.query(OrdemServico).filter_by(numero_os=aprovada).one()
    r = api.client.put(f"{OS_URL}/{aprovada}/finalizar", json={
        "situacao_equipamento": "REPARADO",
        "pagamentos": [{"forma_pagamento_id": forma_pagamento("PIX"), "valor": os_.valor_total}],
    }, headers=api.header)
    assert r.status_code == 200, r.text

    assert separacao.ler(aprovada)["os"]["editavel"] is False
    for acao, quantidade in (("retirar", 1000), ("devolver", 1000), ("concluir", None), ("reabrir", None)):
        r = separacao.acao(aprovada, mdf, acao, quantidade, esperado=409)
        assert r.json()["detail"]["codigo"] == "OS_FECHADA"


# =========================
# Leitor (15)
# =========================

def test_15_leitor_codigo_de_barras_codigo_do_produto_e_embalagem(api, separacao, aprovada, produto, db_session):
    mdf = separacao.linha(aprovada, "MDF")
    corredica = separacao.linha(aprovada, "Corrediça")
    db_session.get(Produto, mdf["produto_id"]).codigo_barras = "7891000000018"
    db_session.add(ProdutoEmbalagem(produto_id=corredica["produto_id"], sigla="CX", fator=10, codigo_barras="17891000000025"))
    outro = produto("Dobradiça 35mm", codigo="DOB-35")              # de nenhuma linha desta OS
    db_session.commit()

    def ler(codigo):
        return separacao.req("GET", aprovada, "/ler", params={"codigo": codigo})

    r = ler("7891000000018")
    assert r.status_code == 200 and (r.json()["fator"], r.json()["linha"]["item_id"]) == (1, mdf["item_id"])
    codigo_corredica = db_session.get(Produto, corredica["produto_id"]).codigo_produto
    assert (ler(codigo_corredica).json()["fator"], ler(codigo_corredica).json()["linha"]["item_id"]) == (1, corredica["item_id"])
    assert (ler("17891000000025").json()["fator"], ler("17891000000025").json()["linha"]["item_id"]) == (10, corredica["item_id"])
    r = ler("DOB-35")
    assert r.status_code == 404 and r.json()["detail"] == "Este produto não faz parte desta OS."
    assert outro and ler("").status_code == 422


def test_15_leitor_acha_a_linha_concluida(separacao, aprovada, db_session):
    mdf = separacao.linha(aprovada, "MDF")
    separacao.acao(aprovada, mdf, "concluir")
    codigo = db_session.get(Produto, mdf["produto_id"]).codigo_produto
    r = separacao.req("GET", aprovada, "/ler", params={"codigo": codigo})
    assert r.status_code == 200 and r.json()["linha"]["concluida"] is True


# =========================
# Disponivel e faltas, na fila do Compras (16-18)
# =========================

@pytest.fixture
def duas_os(api, produto, cliente_id, db_session, fornecedor) -> tuple[str, str, int]:
    """Duas OS abertas precisando de 4 e 3 chapas; estoque 5. Devolve (1a, 2a, produto)."""
    madeireira = fornecedor("Madeireira Central")
    chapa = produto("MDF Branco TX 18mm", valor_entrada=28000, sofre_perda=False)
    p = db_session.get(Produto, chapa)
    p.fornecedor_id, p.localizacao_estoque, p.estoque.quantidade = madeireira, "Corredor A", 5
    db_session.commit()
    _d, primeira = aprovar_simples(api, cliente_id, [[{"produto_id": chapa, "quantidade_milesimos": 4000}]])
    _d, segunda = aprovar_simples(api, cliente_id, [[{"produto_id": chapa, "quantidade_milesimos": 3000}]])
    return primeira, segunda, chapa


def test_16_a_segunda_os_so_tem_o_que_sobrou(separacao, duas_os):
    primeira, segunda, _chapa = duas_os
    (linha_1,) = separacao.ler(primeira)["linhas"]
    (linha_2,) = separacao.ler(segunda)["linhas"]
    assert (linha_1["no_estoque_milesimos"], linha_1["sem_cobertura_milesimos"]) == (4000, 0)
    assert (linha_2["no_estoque_milesimos"], linha_2["sem_cobertura_milesimos"]) == (1000, 2000)
    assert "SEM_COBERTURA" in linha_2["alertas"]
    assert separacao.ler(segunda)["resumo"]["com_falta"] == 1


def test_17_disponivel_desconta_todas_as_os_abertas(api, duas_os):
    _primeira, _segunda, chapa = duas_os
    r = api.client.get(f"{URL_MARCENARIA}/estoque/disponivel", params={"produto_ids": f"{chapa},{chapa},999999"},
                       headers=api.header)
    assert r.status_code == 200, r.text
    assert r.json() == {str(chapa): {"estoque_milesimos": 5000, "reservado_milesimos": 7000, "disponivel_milesimos": -2000}}


def test_17_disponivel_valida_os_ids(api):
    for texto in ("", "1,a", ",".join(["1"] * 201)):
        r = api.client.get(f"{URL_MARCENARIA}/estoque/disponivel", params={"produto_ids": texto}, headers=api.header)
        assert r.status_code == 422, texto


def test_18_faltas_da_segunda_os_com_o_fornecedor(separacao, duas_os):
    _primeira, segunda, chapa = duas_os
    r = separacao.req("GET", segunda, "/faltas")
    assert r.status_code == 200, r.text
    faltas = r.json()
    assert (faltas["numero_os"], faltas["cliente"]) == (segunda, "Dona Marta")
    assert faltas["itens"] == [{
        "produto_id": chapa, "descricao": "MDF Branco TX 18mm", "unidade": "UN", "faltam_milesimos": 2000,
        "localizacao": "Corredor A", "fornecedor": {"id": faltas["itens"][0]["fornecedor"]["id"],
                                                    "nome": "Madeireira Central", "telefone": None},
    }]
    assert faltas["gerado_em"]


# =========================
# Desfazer e cancelar (19, 20)
# =========================

def test_19_desfazer_bloqueado_com_material_retirado(api, separacao, aprovada):
    mdf = separacao.linha(aprovada, "MDF")
    separacao.acao(aprovada, mdf, "retirar", 1000)
    resumo = api.ok("GET", f"/por-os/{aprovada}")
    assert resumo["pode_desfazer"] is False
    assert ("Já há material retirado do estoque para esta OS. "
            "Devolva o material ao estoque antes de desfazer a aprovação.") in resumo["motivos_desfazer"]


def test_20_cancelar_nao_devolve_e_registra_o_aviso(api, separacao, aprovada, db_session):
    mdf = separacao.linha(aprovada, "MDF")
    separacao.acao(aprovada, mdf, "retirar", 3000)

    _cancelar(api, aprovada)

    assert _estoque(db_session, mdf["produto_id"]) == 7          # a chapa nao volta sozinha (03A D15)
    evento = db_session.query(MarcenariaEvento).filter_by(tipo="MATERIAL_FORA_DO_ESTOQUE").one()
    assert evento.descricao == "Material retirado para esta OS continua fora do estoque: 3 UN MDF Branco TX 18mm."
    sep = separacao.ler(aprovada)
    assert sep["os"]["editavel"] is False


def test_cancelar_sem_retirado_nao_registra_aviso(api, aprovada, db_session):
    _cancelar(api, aprovada)
    assert db_session.query(MarcenariaEvento).filter_by(tipo="MATERIAL_FORA_DO_ESTOQUE").count() == 0


# =========================
# Nenhum preco (23), permissao e capacidade
# =========================

def test_23_nenhum_campo_de_preco_com_ou_sem_custos(separacao, aprovada, como):
    for permissoes in ({"servico": True}, {"servico": True, "view_custos_marcenaria": True}):
        como(**permissoes)
        sep = separacao.ler(aprovada)
        palavras = {"custo", "preco", "valor", "margem", "centavos"}
        assert not [k for k in _chaves(sep) if any(p in k for p in palavras)], _chaves(sep)


def test_permissao_de_os_e_capacidade(separacao, aprovada, como, mudar_segmento, api):
    como(view_orcamentos_marcenaria=True)                     # orcamento sim, OS nao
    assert separacao.req("GET", aprovada).status_code == 403
    como(servico=True)
    assert separacao.req("GET", aprovada).status_code == 200
    r = api.client.get(f"{URL_MARCENARIA}/estoque/disponivel", params={"produto_ids": "1"}, headers=api.header)
    assert r.status_code == 403                               # o disponivel e da busca do orcamento

    mudar_segmento("serigrafia")
    r = separacao.req("GET", aprovada)
    assert r.status_code == 404 and r.json()["detail"] == "Esta OS não tem separação de material."


def test_os_que_nao_existe_e_404(separacao, loja):
    r = separacao.req("GET", "OS-2026-999999")
    assert r.status_code == 404 and r.json()["detail"] == "Esta OS não tem separação de material."


def test_item_de_outra_os_e_404(api, separacao, aprovada, produto, cliente_id):
    chapa = produto("Chapa MDP 15mm", valor_entrada=15000, sofre_perda=False)
    _d, outra = aprovar_simples(api, cliente_id, [[{"produto_id": chapa, "quantidade_milesimos": 1000}]])
    (linha_da_outra,) = separacao.ler(outra)["linhas"]
    r = separacao.acao(aprovada, linha_da_outra, "retirar", 1000, esperado=404)
    assert r.json()["detail"] == "Este produto não faz parte desta OS."
