# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/marcenaria/test_arquitetos_api.py
# DESCRICAO: GET /marcenaria/orcamentos/arquitetos -- o select "Quem indicou"
#            do orcamento (Spec 09B D1, D4).
#
#            O que nao pode errar:
#              - o vendedor so com a permissao de ver orcamentos consegue a
#                lista (sem ela, nao escolheria o arquiteto, D1);
#              - so arquitetos ATIVOS, em ordem de nome;
#              - nada de PIX e dados bancarios (so id, nome e escritorio);
#              - fora da marcenaria, 404 (como o resto do orcamento).
# ---------------------------------------------------------------------------

from app.db.models.fornecedor import Fornecedor


def _cadastrar(db_session, *fornecedores: Fornecedor) -> None:
    """Grava os fornecedores do teste direto no banco."""
    db_session.add_all(fornecedores)
    db_session.commit()


def test_vendedor_ve_so_arquitetos_ativos_em_ordem_e_sem_dados_bancarios(api, db_session, como):
    _cadastrar(
        db_session,
        Fornecedor(nome="Studio Renascer", nome_fantasia="Renascer Arquitetura", tipo="arquiteto",
                   pix="studio@renascer.com", banco="Banco do Brasil", agencia="1234", conta="99999"),
        Fornecedor(nome="Ana Projetos", tipo="arquiteto"),
        Fornecedor(nome="Arquiteta Inativa", tipo="arquiteto", ativo=False),   # inativo: fora
        Fornecedor(nome="Madeireira Central", tipo="produto"),                 # outro tipo: fora
    )
    como(view_orcamentos_marcenaria=True)            # sem a permissao de fornecedores/produtos

    lista = api.ok("GET", "/arquitetos")

    assert [a["nome"] for a in lista] == ["Ana Projetos", "Studio Renascer"]
    assert lista[1]["nome_fantasia"] == "Renascer Arquitetura"
    assert lista[0]["nome_fantasia"] is None
    for arquiteto in lista:                          # so o necessario para escolher
        assert set(arquiteto) == {"id", "nome", "nome_fantasia"}


def test_sem_permissao_de_ver_orcamento_e_403(api, como):
    como(view_clientes=True)                         # outro modulo, nao orcamento
    assert api.req("GET", "/arquitetos").status_code == 403


def test_fora_da_marcenaria_e_404(api, mudar_segmento):
    mudar_segmento("serigrafia")
    assert api.req("GET", "/arquitetos").status_code == 404


def test_nao_confunde_a_rota_com_um_id_de_orcamento(api):
    # "/arquitetos" e rota fixa: vem antes de "/{orcamento_id}" (senao seria 422).
    assert api.ok("GET", "/arquitetos") == []
