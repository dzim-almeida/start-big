# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/test_relatorio_acesso_comissoes.py
# DESCRICAO: O Master libera cargos para ver as comissoes (e o extrato) de toda
#            a equipe, pela tela de Relatorios (pedido do Alan, 13/10/2026).
#
#            Nasce desligado; o "all" do cargo nao conta; so o Master muda; e a
#            liberacao abre SO comissoes e extrato -- o resto da visao da loja
#            continua do dono.
# ---------------------------------------------------------------------------

from datetime import datetime

from starlette import status

from test.api.v1.test_relatorio import (
    _auth,
    _cargo_com_relatorio,
    _forma_pagamento,
    _funcionario_com_acesso,
    _login,
    _produto,
    _seed_contador_venda,
    _venda_finalizada,
)

ACESSO = "/api/v1/relatorios/comissoes/acesso"
HOJE = datetime.now().date().isoformat()
PERIODO = f"inicio={HOJE}&fim={HOJE}"


def _loja_com_gerente(client, db_session, permissoes=None):
    """Master + cargo "Gerente" (com acesso a Relatorios) + um funcionario nele."""
    _seed_contador_venda(db_session)
    header = _auth(client)
    r = client.post("/api/v1/cargos/", json={
        "nome": "Gerente", "permissoes": permissoes or {"relatorio": True, "venda": True},
    }, headers=header)
    assert r.status_code in (200, 201), r.text
    cargo_id = r.json()["id"]
    funcionario_id = _funcionario_com_acesso(
        client, header, nome="Gerente da Loja", cpf="11122266601",
        email="gerente.comissao@empresa.com", senha="SenhaForte123!", cargo_id=cargo_id,
    )
    h_gerente = _login(client, "gerente.comissao@empresa.com", "SenhaForte123!")
    return header, h_gerente, cargo_id, funcionario_id


def _comissoes(client, headers):
    return client.get(f"/api/v1/relatorios/comissoes?{PERIODO}", headers=headers)


def _extrato(client, headers, funcionario_id):
    return client.get(
        f"/api/v1/relatorios/extrato-funcionario?funcionario_id={funcionario_id}&{PERIODO}",
        headers=headers,
    )


def test_desligado_por_padrao(client, db_session):
    """Sem o Master liberar, nada muda: comissoes e extrato continuam so dele."""
    header, h_gerente, cargo_id, func_id = _loja_com_gerente(client, db_session)

    assert _comissoes(client, h_gerente).status_code == status.HTTP_403_FORBIDDEN
    assert _extrato(client, h_gerente, func_id).status_code == status.HTTP_403_FORBIDDEN

    acesso = client.get(ACESSO, headers=header).json()
    assert acesso["cargos"] == [
        {"id": cargo_id, "nome": "Gerente", "liberado": False, "abre_relatorios": True},
    ]


def test_master_libera_e_o_gerente_ve_as_comissoes_de_todos(client, db_session):
    header, h_gerente, cargo_id, func_id = _loja_com_gerente(client, db_session)
    fp_id = _forma_pagamento(client, header)
    produto_id = _produto(client, header, "P-COMISSAO", varejo=10000, entrada=4000, quantidade=100)
    colega = _funcionario_com_acesso(
        client, header, nome="Vendedor Colega", cpf="11122266602",
        email="colega.comissao@empresa.com", senha="SenhaForte123!",
    )
    _venda_finalizada(client, header, colega, produto_id, 2, fp_id)

    r = client.put(ACESSO, json={"cargo_ids": [cargo_id]}, headers=header)
    assert r.status_code == 200, r.text
    assert r.json()["cargos"][0]["liberado"] is True

    # Vale na hora, sem novo login: as permissoes sao relidas do banco a cada requisicao.
    dono = _comissoes(client, header)
    gerente = _comissoes(client, h_gerente)
    assert gerente.status_code == 200, gerente.text
    assert gerente.json() == dono.json()                      # a mesma tabela do dono
    assert any(i["funcionario_id"] == colega for i in gerente.json()["itens"])
    assert _extrato(client, h_gerente, colega).status_code == 200


def test_liberacao_abre_so_comissoes_e_extrato(client, db_session):
    """Ranking, estoque, contador e o faturamento da loja continuam so do Master."""
    header, h_gerente, cargo_id, _ = _loja_com_gerente(client, db_session)
    client.put(ACESSO, json={"cargo_ids": [cargo_id]}, headers=header)

    for nome in ("ranking-funcionarios", "estoque", "os-performance", "regras-preco", "contador"):
        r = client.get(f"/api/v1/relatorios/{nome}?{PERIODO}", headers=h_gerente)
        assert r.status_code == status.HTTP_403_FORBIDDEN, (nome, r.status_code)

    fp_id = _forma_pagamento(client, header)
    produto_id = _produto(client, header, "P-LOJA", varejo=10000, entrada=4000, quantidade=100)
    outro = _funcionario_com_acesso(
        client, header, nome="Outro Vendedor", cpf="11122266603",
        email="outro.comissao@empresa.com", senha="SenhaForte123!",
    )
    _venda_finalizada(client, header, outro, produto_id, 3, fp_id)
    fat = client.get(f"/api/v1/relatorios/faturamento?{PERIODO}", headers=h_gerente).json()
    assert fat["faturamento_total"] == 0            # o recorte pessoal: ele nao vendeu nada


def test_master_retira_e_o_acesso_cai_na_hora(client, db_session):
    header, h_gerente, cargo_id, _ = _loja_com_gerente(client, db_session)
    client.put(ACESSO, json={"cargo_ids": [cargo_id]}, headers=header)
    assert _comissoes(client, h_gerente).status_code == 200

    r = client.put(ACESSO, json={"cargo_ids": []}, headers=header)
    assert r.status_code == 200, r.text
    assert _comissoes(client, h_gerente).status_code == status.HTTP_403_FORBIDDEN


def test_so_o_master_ve_e_muda_quem_esta_liberado(client, db_session):
    """O gerente liberado nao consegue se dar mais nem liberar os colegas."""
    header, h_gerente, cargo_id, _ = _loja_com_gerente(client, db_session)
    client.put(ACESSO, json={"cargo_ids": [cargo_id]}, headers=header)

    assert client.get(ACESSO, headers=h_gerente).status_code == status.HTTP_403_FORBIDDEN
    r = client.put(ACESSO, json={"cargo_ids": []}, headers=h_gerente)
    assert r.status_code == status.HTTP_403_FORBIDDEN


def test_cargo_com_all_nao_ganha_as_comissoes_sozinho(client, db_session):
    """O "marcar tudo" de hoje nao pode virar visao das comissoes na atualizacao."""
    header, h_gerente, cargo_id, _ = _loja_com_gerente(client, db_session, permissoes={"all": True})
    assert _comissoes(client, h_gerente).status_code == status.HTTP_403_FORBIDDEN

    client.put(ACESSO, json={"cargo_ids": [cargo_id]}, headers=header)
    assert _comissoes(client, h_gerente).status_code == 200


def test_liberar_nao_mexe_nas_outras_permissoes_do_cargo(client, db_session):
    header, _, cargo_id, _ = _loja_com_gerente(client, db_session)

    def _permissoes():
        cargos = client.get("/api/v1/cargos/", headers=header).json()
        return next(c for c in cargos if c["id"] == cargo_id)["permissoes"]

    client.put(ACESSO, json={"cargo_ids": [cargo_id]}, headers=header)
    assert _permissoes() == {"relatorio": True, "venda": True, "ver_comissoes_equipe": True}

    client.put(ACESSO, json={"cargo_ids": []}, headers=header)
    assert _permissoes() == {"relatorio": True, "venda": True}


def test_cargo_inexistente_nao_muda_nada(client, db_session):
    header, _, cargo_id, _ = _loja_com_gerente(client, db_session)
    r = client.put(ACESSO, json={"cargo_ids": [cargo_id, 9999]}, headers=header)
    assert r.status_code == status.HTTP_404_NOT_FOUND, r.text
    assert client.get(ACESSO, headers=header).json()["cargos"][0]["liberado"] is False


def test_cargo_sem_relatorios_aparece_avisado(client, db_session):
    """Liberado sem acesso a tela de Relatorios nao enxergaria nada: a tela avisa."""
    header = _auth(client)
    r = client.post("/api/v1/cargos/", json={"nome": "Caixa", "permissoes": {"venda": True}}, headers=header)
    caixa_id = r.json()["id"]
    relat_id = _cargo_com_relatorio(client, header, nome="Supervisor")
    cargos = {c["id"]: c for c in client.get(ACESSO, headers=header).json()["cargos"]}
    assert cargos[caixa_id]["abre_relatorios"] is False
    assert cargos[relat_id]["abre_relatorios"] is True
