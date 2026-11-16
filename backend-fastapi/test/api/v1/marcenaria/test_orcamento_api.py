# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/marcenaria/test_orcamento_api.py
# DESCRICAO: API do orcamento de marcenaria (Spec 06A, §11, casos 18 a 33).
#
#            O que nao pode errar:
#              - fora da marcenaria, nada existe (404);
#              - quem nao ve custo nao recebe NENHUMA chave de custo, e nao
#                consegue escrever custo (403);
#              - revisao antiga e status errado nao gravam nada (409);
#              - so a versao mais recente aparece na lista, por padrao.
# ---------------------------------------------------------------------------

from datetime import timedelta

import pytest

from app.core.tempo import hoje_local
from app.db.models.marcenaria import MarcenariaOrcamento

from test.apoio_orcamento_marcenaria import montar_cenario_b

GERIR = {"manage_orcamentos_marcenaria": True}           # cargo: orcamentos sim, custos nao

# Chaves de custo que NAO podem aparecer para quem nao ve custo (caso 20).
CHAVES_DE_CUSTO = {
    "custo_unit_centavos", "custo_origem", "custo_total_centavos", "custo_centavos",
    "margem_bruta_centavos", "margem_liquida_centavos", "margem_liquida_bp",
    "rt_total_centavos", "rt_linha_centavos", "rt_bp", "rt_padrao_bp", "rt_modo",
    "valor_previsto_centavos", "markup_bp", "perda_bp", "custo_hora_centavos",
    "instalacao_custo_centavos", "material_centavos", "perda_centavos", "mao_obra_centavos",
    "mao_obra", "terceirizado_centavos", "resumo_margem_bp",
}


def _todas_as_chaves(valor) -> set[str]:
    """Todas as chaves de um JSON, em qualquer nivel."""
    if isinstance(valor, dict):
        return set(valor) | {k for v in valor.values() for k in _todas_as_chaves(v)}
    if isinstance(valor, list):
        return {k for v in valor for k in _todas_as_chaves(v)}
    return set()


def _enviar(api, d) -> dict:
    return api.ok("POST", f"/{d['id']}/enviar", rev=d["revisao"])


@pytest.fixture
def cenario(api, produto, fornecedor, cliente_id) -> dict:
    """O cenario B montado (detalhe), com cliente."""
    return montar_cenario_b(api, produto, fornecedor, cliente=cliente_id)


# =========================
# Capacidade e permissao (18, 19)
# =========================

def test_18_fora_da_marcenaria_tudo_e_404(api, mudar_segmento):
    orc = api.criar()
    mudar_segmento("serigrafia")

    for metodo, caminho, rev in (
        ("GET", "/", None), ("GET", "/contagens", None), ("GET", "/projetos?cliente_id=1", None),
        ("POST", "/", None), ("GET", f"/{orc['id']}", None), ("GET", f"/{orc['id']}/historico", None),
        ("POST", f"/{orc['id']}/ambientes", 1), ("GET", f"/{orc['id']}/anexos", None),
    ):
        corpo = {"json": {"nome": "Cozinha"}} if caminho.endswith("ambientes") else {}
        r = api.req(metodo, caminho, rev=rev, **corpo)
        assert r.status_code == 404, (metodo, caminho, r.text)


def test_19_cargo_sem_permissao_de_ver_recebe_403(api, como):
    orc = api.criar()
    como(view_clientes=True)                                    # outro modulo, nao orcamento

    assert api.req("GET", "/").status_code == 403
    assert api.req("GET", f"/{orc['id']}").status_code == 403
    como(view_orcamentos_marcenaria=True)                       # ver nao e gerir
    assert api.req("GET", f"/{orc['id']}").status_code == 200
    assert api.req("POST", "/").status_code == 403
    assert api.req("DELETE", f"/{orc['id']}", rev=1).status_code == 403   # excluir e outra chave


# =========================
# Recorte de custos (20, 21, 22)
# =========================

def test_20_sem_view_custos_nenhuma_chave_de_custo(api, cenario, como):
    como(**GERIR)
    d = api.detalhe(cenario["id"])

    assert d["inclui_custos"] is False
    assert _todas_as_chaves(d) & CHAVES_DE_CUSTO == set()
    c = d["calculo"]
    assert (c["total_centavos"], c["sinal_centavos"], c["saldo_centavos"]) == (923889, 369556, 554333)
    assert d["ambientes"][0]["moveis"][0]["calculo"] == {"preco_unit_centavos": 422275, "preco_total_centavos": 422275}
    assert d["parametros"] == {"validade_dias": 15, "prazo_entrega_dias": 30}
    assert d["arquitetos"] == [{"fornecedor_id": cenario["arquitetos"][0]["fornecedor_id"], "nome": "Studio Renascer"}]
    assert d["calculo"]["instalacao"] == {"preco_centavos": 142500}

    lista = api.ok("GET", "/")["items"]
    assert "resumo_margem_bp" not in lista[0]


def test_21_sem_view_custos_insumo_novo_recebe_o_custo_do_produto(api, cenario, produto, como):
    como(**GERIR)
    amb = cenario["ambientes"][0]["id"]
    pid = produto("Puxador", valor_entrada=1200)

    api.ok("POST", f"/{cenario['id']}/ambientes/{amb}/moveis", rev=cenario["revisao"], esperado=201, json={
        "nome": "Gaveteiro", "insumos": [{"produto_id": pid, "quantidade_milesimos": 4000}],
    })

    _limpar_override()                        # volta ao master (ve custos)
    d = api.detalhe(cenario["id"])
    gaveteiro = d["ambientes"][0]["moveis"][-1]
    assert (gaveteiro["insumos"][0]["custo_unit_centavos"], gaveteiro["insumos"][0]["custo_origem"]) == (1200, "ULTIMA_COMPRA")


def _limpar_override():
    """Tira o usuario simulado: as proximas chamadas usam o token do master."""
    from app.core.depends import get_current_active_user
    from app.main import app
    app.dependency_overrides.pop(get_current_active_user, None)


def test_22_sem_view_custos_custo_manual_e_403(api, cenario, produto, como):
    como(**GERIR)
    amb = cenario["ambientes"][0]["id"]
    pid = produto("Puxador", valor_entrada=1200)

    r = api.req("POST", f"/{cenario['id']}/ambientes/{amb}/moveis", rev=cenario["revisao"], json={
        "nome": "Gaveteiro", "insumos": [{"produto_id": pid, "quantidade_milesimos": 4000, "custo_unit_centavos": 1}],
    })
    assert r.status_code == 403, r.text
    # Outros campos de custo, pelo cabecalho, tambem.
    assert api.req("PATCH", f"/{cenario['id']}", rev=cenario["revisao"], json={"markup_bp": 1}).status_code == 403
    _limpar_override()
    assert api.detalhe(cenario["id"])["revisao"] == cenario["revisao"]     # nada gravado


# =========================
# Trava e status (23, 24, 25, 26)
# =========================

def test_23_revisao_antiga_responde_409_e_nao_grava(api):
    orc = api.criar()
    api.ok("PATCH", f"/{orc['id']}", rev=1, json={"projeto_nome": "Cozinha"})   # revisao vai a 2

    r = api.req("PATCH", f"/{orc['id']}", rev=1, json={"projeto_nome": "Outro computador"})

    assert r.status_code == 409
    assert r.json()["detail"]["mensagem"] == (
        "Este orçamento foi alterado em outro computador. Recarregue para ver a versão atual."
    )
    assert api.detalhe(orc["id"])["projeto"]["nome"] == "Cozinha"


def test_24_patch_num_enviado(api, cenario):
    d = _enviar(api, cenario)

    r = api.req("PATCH", f"/{d['id']}", rev=d["revisao"], json={"projeto_nome": "x"})

    assert r.status_code == 409
    assert r.json()["detail"] == {"codigo": "STATUS_NAO_EDITAVEL",
                                  "mensagem": "Só é possível editar orçamentos em rascunho."}


def test_25_voltar_a_editar(api, cenario):
    d = _enviar(api, cenario)

    d = api.ok("POST", f"/{d['id']}/voltar-a-editar", rev=d["revisao"])

    assert d["status"] == "RASCUNHO"
    tipos = [e["tipo"] for e in api.ok("GET", f"/{d['id']}/historico")]
    assert tipos[0] == "ORCAMENTO_VOLTOU_A_EDITAR"


def test_26_recusar_exige_motivo(api, cenario):
    d = _enviar(api, cenario)

    r = api.req("POST", f"/{d['id']}/recusar", rev=d["revisao"], json={"motivo": "   "})
    assert r.status_code == 422
    assert r.json()["detail"][0]["message"] == "Informe o motivo da recusa."

    d = api.ok("POST", f"/{d['id']}/recusar", rev=d["revisao"], json={"motivo": "Fechou com outro"})
    assert (d["status"], d["motivo_recusa"]) == ("RECUSADO", "Fechou com outro")
    assert d["datas"]["recusa"] is not None


def test_26b_transicao_invalida_diz_o_status(api, cenario):
    r = api.req("POST", f"/{cenario['id']}/recusar", rev=cenario["revisao"], json={"motivo": "x"})

    assert r.status_code == 409
    assert r.json()["detail"] == {"codigo": "TRANSICAO_INVALIDA",
                                  "mensagem": "Ação não permitida para um orçamento em rascunho."}


# =========================
# Excluir (27)
# =========================

def test_27_excluir_rascunho_nunca_enviado(api, db_session):
    orc = api.criar()

    r = api.req("DELETE", f"/{orc['id']}", rev=orc["revisao"])

    assert r.status_code == 204
    assert api.req("GET", f"/{orc['id']}").status_code == 404
    assert db_session.query(MarcenariaOrcamento).count() == 0


def test_27b_nao_exclui_o_que_ja_foi_enviado(api, cenario):
    d = _enviar(api, cenario)
    d = api.ok("POST", f"/{d['id']}/voltar-a-editar", rev=d["revisao"])     # rascunho de novo, mas ja enviado

    r = api.req("DELETE", f"/{d['id']}", rev=d["revisao"])

    assert r.status_code == 409
    assert r.json()["detail"]["codigo"] == "EXCLUSAO_NAO_PERMITIDA"
    assert d["acoes"]["excluir"] is False


# =========================
# Lista (28, 29)
# =========================

def test_28_lista_padrao_so_a_versao_mais_recente(api, cenario):
    d = _enviar(api, cenario)
    v2 = api.ok("POST", f"/{d['id']}/nova-versao", rev=d["revisao"], esperado=201)

    padrao = api.ok("GET", "/")
    assert [(i["codigo"], i["versao"]) for i in padrao["items"]] == [(v2["codigo"], 2)]
    assert padrao["total_items"] == 1

    todas = api.ok("GET", "/", params={"incluir_versoes_antigas": "true"})
    assert sorted(i["versao"] for i in todas["items"]) == [1, 2]
    assert padrao["items"][0]["resumo_total_centavos"] == v2["calculo"]["total_centavos"]   # resumo bate


def test_28b_busca_por_cliente_e_projeto(api, cenario):
    assert api.ok("GET", "/", params={"busca": "marta"})["total_items"] == 1
    assert api.ok("GET", "/", params={"busca": "alpha ville"})["total_items"] == 1
    assert api.ok("GET", "/", params={"busca": "inexistente"})["total_items"] == 0


def test_29_vence_em_dias(api, cenario, db_session):
    d = _enviar(api, cenario)
    orc = db_session.get(MarcenariaOrcamento, d["id"])

    orc.data_validade = hoje_local() + timedelta(days=3)
    db_session.commit()
    assert api.ok("GET", "/", params={"vence_em_dias": 3})["total_items"] == 1

    orc.data_validade = hoje_local() + timedelta(days=4)
    db_session.commit()
    assert api.ok("GET", "/", params={"vence_em_dias": 3})["total_items"] == 0


# =========================
# Anexos (30, 31)
# =========================

PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"


@pytest.fixture
def pasta_uploads(tmp_path, monkeypatch):
    """Os arquivos vao para uma pasta temporaria, nunca para a do projeto."""
    from app.core import imagem
    monkeypatch.setattr(imagem, "BASE_DIR", str(tmp_path))
    return tmp_path


def _anexar(api, oid, nome, conteudo, tipo="application/pdf", legenda=None):
    dados = {"legenda": legenda} if legenda is not None else {}
    return api.req("POST", f"/{oid}/anexos", files={"arquivo": (nome, conteudo, tipo)}, data=dados)


def _png(tamanho_extra: int = 0) -> bytes:
    """Uma imagem PNG valida (opcionalmente com lixo no fim para pesar mais)."""
    from io import BytesIO
    from PIL import Image
    buffer = BytesIO()
    Image.new("RGB", (40, 30), "white").save(buffer, format="PNG")
    return buffer.getvalue() + b"\0" * tamanho_extra


def test_30_anexos_pdf_exe_e_imagem_grande(api, pasta_uploads):
    orc = api.criar()

    r = _anexar(api, orc["id"], "planta.pdf", PDF, legenda="Planta baixa")
    assert r.status_code == 201, r.text
    anexo = r.json()
    assert (anexo["tipo"], anexo["legenda"], anexo["nome_arquivo"]) == ("PDF", "Planta baixa", "planta.pdf")
    assert (pasta_uploads / anexo["url"]).read_bytes() == PDF        # guardado como veio

    r = _anexar(api, orc["id"], "virus.pdf", b"MZ\x90\x00 executavel")
    assert r.status_code == 422
    assert r.json()["detail"] == "Arquivo não suportado. Envie JPG, PNG, WebP ou PDF."

    r = _anexar(api, orc["id"], "grande.png", _png(6 * 1024 * 1024), tipo="image/png")
    assert r.status_code == 422
    assert r.json()["detail"] == "Arquivo maior que 5 MB."

    r = _anexar(api, orc["id"], "parede.png", _png(), tipo="image/png")
    assert r.status_code == 201, r.text
    assert r.json()["tipo"] == "FOTO" and r.json()["url"].endswith(".webp")

    assert [a["nome_arquivo"] for a in api.ok("GET", f"/{orc['id']}/anexos")] == ["planta.pdf", "parede.png"]
    assert api.detalhe(orc["id"])["revisao"] == 1                     # anexo nao soma na revisao (D31)


def test_31_anexo_da_v1_aparece_na_v2(api, cenario, pasta_uploads):
    assert _anexar(api, cenario["id"], "planta.pdf", PDF).status_code == 201
    d = _enviar(api, cenario)
    v2 = api.ok("POST", f"/{d['id']}/nova-versao", rev=d["revisao"], esperado=201)

    assert [a["nome_arquivo"] for a in api.ok("GET", f"/{v2['id']}/anexos")] == ["planta.pdf"]


def test_31b_remover_anexo_apaga_o_arquivo(api, pasta_uploads):
    orc = api.criar()
    anexo = _anexar(api, orc["id"], "planta.pdf", PDF).json()

    assert api.req("DELETE", f"/{orc['id']}/anexos/{anexo['id']}").status_code == 204

    assert not (pasta_uploads / anexo["url"]).exists()
    assert api.ok("GET", f"/{orc['id']}/anexos") == []


# =========================
# Historico e acoes (32, 33)
# =========================

def test_32_historico_mais_novo_primeiro_com_usuario(api, cenario):
    d = _enviar(api, cenario)
    api.ok("POST", f"/{d['id']}/voltar-a-editar", rev=d["revisao"])

    eventos = api.ok("GET", f"/{d['id']}/historico")

    assert [e["tipo"] for e in eventos] == ["ORCAMENTO_VOLTOU_A_EDITAR", "ORCAMENTO_ENVIADO", "ORCAMENTO_CRIADO"]
    assert {e["usuario_nome"] for e in eventos} == {"Admin Master"}


def _acoes_ligadas(d) -> set[str]:
    return {nome for nome, pode in d["acoes"].items() if pode}


def test_33_acoes_por_status_e_permissao(api, cenario, como):
    # "aprovar" desde a Spec 08A: de RASCUNHO, ENVIADO e VENCIDO (08A D13).
    assert _acoes_ligadas(cenario) == {"editar", "enviar", "excluir", "anexos", "aprovar"}

    d = _enviar(api, cenario)
    assert _acoes_ligadas(d) == {"voltar_a_editar", "recusar", "nova_versao", "anexos", "aprovar"}

    d = api.ok("POST", f"/{d['id']}/recusar", rev=d["revisao"], json={"motivo": "Prazo"})
    assert _acoes_ligadas(d) == {"nova_versao", "anexos"}

    v2 = api.ok("POST", f"/{d['id']}/nova-versao", rev=d["revisao"], esperado=201)
    v1 = api.detalhe(d["id"])
    assert v1["status"] == "SUBSTITUIDO" and _acoes_ligadas(v1) == set()
    assert _acoes_ligadas(v2) == {"editar", "enviar", "anexos", "aprovar"}   # v2 nao se exclui (D18)

    como(view_orcamentos_marcenaria=True)                               # so ver: nenhum botao
    assert _acoes_ligadas(api.detalhe(v2["id"])) == set()


def test_33b_vencido_pode_renovar(api, cenario, db_session):
    d = _enviar(api, cenario)
    orc = db_session.get(MarcenariaOrcamento, d["id"])
    orc.data_validade = hoje_local() - timedelta(days=1)
    db_session.commit()

    d = api.detalhe(d["id"])

    assert d["status"] == "VENCIDO"
    assert _acoes_ligadas(d) == {"recusar", "renovar", "nova_versao", "anexos", "aprovar"}
