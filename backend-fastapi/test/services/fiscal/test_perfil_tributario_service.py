# ---------------------------------------------------------------------------
# ARQUIVO: test/services/fiscal/test_perfil_tributario_service.py
# DESCRIÇÃO: TASK005 — o serviço de perfis tributários sobre o SQLite em
#            memória (fixture db_session do conftest raiz).
# ---------------------------------------------------------------------------

import pytest
import sqlalchemy as sa
from fastapi import HTTPException

from app.db.models.empresa import Empresa
from app.db.models.regra_perfil_tributario import RegraPerfilTributario
from app.schemas.perfil_tributario import PerfilTributarioCreate
from app.services import perfil_tributario as service


@pytest.fixture
def empresas(db_session) -> tuple[Empresa, Empresa]:
    a = Empresa(razao_social="Loja A", documento="11111111000191", is_cnpj=True)
    b = Empresa(razao_social="Loja B", documento="22222222000192", is_cnpj=True)
    db_session.add_all([a, b])
    db_session.commit()
    return a, b


def regra(**campos) -> dict:
    base = {"aliquota_interestadual": 1200, "aliquota_interna_destino": 1800}
    base.update(campos)
    return base


def dados(descricao="Varejo", *regras_extras) -> PerfilTributarioCreate:
    return PerfilTributarioCreate(descricao=descricao, regras=[regra(), *regras_extras])


def test_criar_grava_perfil_e_regras_com_ids(db_session, empresas):
    a, _ = empresas
    perfil = service.criar_perfil(db_session, a.id, dados("Varejo", regra(uf_destino="SP", percentual_fcp=200)))

    assert perfil.id and perfil.empresa_id == a.id
    assert {r.uf_destino for r in perfil.regras} == {None, "SP"}
    assert all(r.id for r in perfil.regras)


def test_listar_devolve_so_os_da_empresa_com_contagem_e_ordem(db_session, empresas):
    a, b = empresas
    service.criar_perfil(db_session, a.id, dados("Zebra", regra(uf_destino="SP")))
    service.criar_perfil(db_session, a.id, dados("Alfa"))
    service.criar_perfil(db_session, b.id, dados("Da outra loja"))

    lista = service.listar_perfis(db_session, a.id)

    assert [p.descricao for p in lista] == ["Alfa", "Zebra"]
    assert [p.quantidade_regras for p in lista] == [1, 2]


def test_obter_de_outra_empresa_e_404(db_session, empresas):
    a, b = empresas
    perfil = service.criar_perfil(db_session, a.id, dados())

    with pytest.raises(HTTPException) as exc:
        service.obter_perfil(db_session, b.id, perfil.id)
    assert exc.value.status_code == 404


def test_obter_inexistente_e_404(db_session, empresas):
    a, _ = empresas
    with pytest.raises(HTTPException) as exc:
        service.obter_perfil(db_session, a.id, 999)
    assert exc.value.status_code == 404


def test_atualizar_faz_replace_all_das_regras(db_session, empresas):
    a, _ = empresas
    perfil = service.criar_perfil(db_session, a.id, dados("Antigo", regra(uf_destino="SP"), regra(uf_destino="RJ")))

    atualizado = service.atualizar_perfil(
        db_session, a.id, perfil.id, dados("Novo", regra(uf_destino="MG", calculo_base_dupla=True)),
    )
    db_session.commit()

    assert atualizado.descricao == "Novo"
    assert {r.uf_destino for r in atualizado.regras} == {None, "MG"}
    assert db_session.scalar(sa.select(sa.func.count()).select_from(RegraPerfilTributario)) == 2
    assert next(r for r in atualizado.regras if r.uf_destino == "MG").calculo_base_dupla is True


def test_atualizar_perfil_de_outra_empresa_e_404(db_session, empresas):
    a, b = empresas
    perfil = service.criar_perfil(db_session, a.id, dados())
    with pytest.raises(HTTPException) as exc:
        service.atualizar_perfil(db_session, b.id, perfil.id, dados("Outro"))
    assert exc.value.status_code == 404


def test_deletar_apaga_perfil_e_regras(db_session, empresas):
    a, _ = empresas
    perfil = service.criar_perfil(db_session, a.id, dados("Some", regra(uf_destino="SP")))

    service.deletar_perfil(db_session, a.id, perfil.id)
    db_session.commit()

    assert service.listar_perfis(db_session, a.id) == []
    assert db_session.scalar(sa.select(sa.func.count()).select_from(RegraPerfilTributario)) == 0


def test_deletar_perfil_em_uso_e_409_com_os_produtos(db_session, empresas, monkeypatch):
    a, _ = empresas
    perfil = service.criar_perfil(db_session, a.id, dados())
    monkeypatch.setattr(service.crud, "produtos_que_usam", lambda _db, _id: ["Celular X", "Tablet Y"])

    with pytest.raises(HTTPException) as exc:
        service.deletar_perfil(db_session, a.id, perfil.id)

    assert exc.value.status_code == 409
    assert exc.value.detail["codigo"] == "PERFIL_EM_USO"
    assert "Celular X" in exc.value.detail["mensagem"] and "Tablet Y" in exc.value.detail["mensagem"]


def test_sem_vinculo_com_produto_nenhum_perfil_esta_em_uso(db_session, empresas):
    a, _ = empresas
    perfil = service.criar_perfil(db_session, a.id, dados())
    assert service.crud.produtos_que_usam(db_session, perfil.id) == []


def test_atualizar_mantendo_a_mesma_uf_nao_colide_na_unique(db_session, empresas):
    """Editar a alíquota de SP reenvia (SP, NULL): a linha antiga tem que sair antes da nova entrar."""
    a, _ = empresas
    perfil = service.criar_perfil(db_session, a.id, dados("Varejo", regra(uf_destino="SP", ncm_excecao="85171200")))
    db_session.commit()

    atualizado = service.atualizar_perfil(
        db_session, a.id, perfil.id,
        dados("Varejo", regra(uf_destino="SP", ncm_excecao="85171200", aliquota_interna_destino=2000)),
    )
    db_session.commit()

    sp = next(r for r in atualizado.regras if r.uf_destino == "SP")
    assert sp.aliquota_interna_destino == 2000
    assert db_session.scalar(sa.select(sa.func.count()).select_from(RegraPerfilTributario)) == 2
