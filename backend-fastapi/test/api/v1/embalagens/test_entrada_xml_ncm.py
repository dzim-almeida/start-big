# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/embalagens/test_entrada_xml_ncm.py
# DESCRIÇÃO: O NCM da nota de compra contra o cadastro do produto.
#
# O que não pode errar: a prévia não grava nada; produto sem NCM recebe o da
# nota; NCM diferente só muda se a pessoa marcar; NCM inválido nunca entra.
# ---------------------------------------------------------------------------

from app.db.models.produto_fiscal import ProdutoFiscal
from test.api.v1.embalagens.test_venda_por_embalagem import loja  # noqa: F401 — `loja` é fixture
from test.core.nfe_exemplo import nota

URL = "/api/v1/estoque/nfe-entrada"
NCM_DA_NOTA = "22030000"  # o da cerveja em test/core/nfe_exemplo.py


def _ler(client, headers, xml: str) -> dict:
    r = client.post(f"{URL}/ler", files={"arquivo": ("nota.xml", xml.encode(), "text/xml")}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def _importar(client, headers, loja, xml: str | None = None, **decisao_extra):
    itens = [
        {"indice": 1, "acao": "vincular", "produto_id": loja["produto_id"], "embalagem_id": loja["FD"], "fator": 12,
         **decisao_extra},
        {"indice": 2, "acao": "ignorar", "fator": 1},
    ]
    r = client.post(f"{URL}/importar", json={"xml": xml or nota(), "itens": itens}, headers=headers)
    assert r.status_code == 201, r.text


def _fiscal(db, produto_id) -> ProdutoFiscal | None:
    db.expire_all()
    return db.query(ProdutoFiscal).filter_by(produto_id=produto_id).first()


def _com_ncm(db, produto_id, ncm: str) -> None:
    db.add(ProdutoFiscal(produto_id=produto_id, ncm=ncm, cfop_padrao="5405"))
    db.commit()


def test_produto_sem_ncm_avisa_na_previa_sem_gravar(client, db_session, header_com_token, loja):
    item = _ler(client, header_com_token, nota())["itens"][0]

    assert (item["ncm_situacao"], item["ncm_cadastro"]) == ("vazio", None)
    assert _fiscal(db_session, loja["produto_id"]) is None


def test_produto_sem_ncm_recebe_o_da_nota(client, db_session, header_com_token, loja):
    _importar(client, header_com_token, loja)

    assert _fiscal(db_session, loja["produto_id"]).ncm == NCM_DA_NOTA


def test_ncm_igual_nao_avisa(client, db_session, header_com_token, loja):
    _com_ncm(db_session, loja["produto_id"], NCM_DA_NOTA)

    item = _ler(client, header_com_token, nota())["itens"][0]

    assert (item["ncm_situacao"], item["ncm_cadastro"]) == ("igual", NCM_DA_NOTA)


def test_ncm_diferente_nao_muda_sem_marcar(client, db_session, header_com_token, loja):
    _com_ncm(db_session, loja["produto_id"], "22021000")

    item = _ler(client, header_com_token, nota())["itens"][0]
    assert (item["ncm_situacao"], item["ncm_cadastro"]) == ("divergente", "22021000")

    _importar(client, header_com_token, loja)
    assert _fiscal(db_session, loja["produto_id"]).ncm == "22021000"


def test_ncm_diferente_muda_so_o_ncm_quando_marca(client, db_session, header_com_token, loja):
    _com_ncm(db_session, loja["produto_id"], "22021000")

    _importar(client, header_com_token, loja, atualizar_ncm=True)

    fiscal = _fiscal(db_session, loja["produto_id"])
    assert fiscal.ncm == NCM_DA_NOTA
    assert fiscal.cfop_padrao == "5405"


def test_ncm_invalido_avisa_e_nao_entra(client, db_session, header_com_token, loja):
    xml = nota().replace(f"<NCM>{NCM_DA_NOTA}</NCM>", "<NCM>123</NCM>")

    item = _ler(client, header_com_token, xml)["itens"][0]
    assert item["ncm_situacao"] == "invalido"

    _importar(client, header_com_token, loja, xml=xml, atualizar_ncm=True)
    assert _fiscal(db_session, loja["produto_id"]) is None


def test_produto_novo_com_ncm_valido_nao_tem_aviso(client, header_com_token, loja):
    biscoito = _ler(client, header_com_token, nota())["itens"][1]

    assert biscoito["produto"] is None
    assert biscoito["ncm_situacao"] is None
