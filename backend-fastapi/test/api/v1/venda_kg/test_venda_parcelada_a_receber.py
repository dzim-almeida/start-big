# ---------------------------------------------------------------------------
# ARQUIVO: test/api/v1/venda_kg/test_venda_parcelada_a_receber.py
# DESCRICAO: Pagamento parcelado com vencimento futuro vira uma conta a receber
#            por parcela. Cartao da maquininha e fiado sem parcela nao mudam.
# ---------------------------------------------------------------------------

from datetime import date
from types import SimpleNamespace

import pytest

from app.core.enum import JurosResponsavel
from app.core.tempo import hoje_local
from app.db.models.conta_receber import ContaReceber
from app.db.models.contador_venda import ContadorVenda
from app.db.models.forma_pagamento import FormaPagamento
from app.services.financeiro.comum import _somar_meses
from app.services.financeiro.promessas import _dividir_em_parcelas, registrar_promessas_de_os

NOVENTA_MIL = 9_000_000
CEM_MIL = 10_000_000


@pytest.fixture
def loja(client, db_session, header_com_token) -> dict:
    if not db_session.query(ContadorVenda).first():
        db_session.add(ContadorVenda(id=1, proximo_numero=1))
        db_session.commit()
    funcionario = client.post("/api/v1/funcionarios/", json={
        "nome": "Vendedor Teste", "cpf": "11122233344", "contato": "11999999999",
        "usuario": {"nome": "vendedor1", "email": "vend1@empresa.com", "senha": "SenhaForte123!"},
        "endereco": [{"logradouro": "Rua X", "numero": "1", "cep": "12345-678",
                      "bairro": "Centro", "cidade": "Lab City", "estado": "SP"}],
    }, headers=header_com_token)
    assert funcionario.status_code in (200, 201), funcionario.text
    formas = {}
    for nome in ("Dinheiro", "Boleto", "Cartao"):
        r = client.post("/api/v1/formas-pagamento/", json={"nome": nome, "ativo": True}, headers=header_com_token)
        assert r.status_code == 201, r.text
        formas[nome] = r.json()["id"]
    return {"funcionario_id": funcionario.json()["id"], **formas}


def _primeira_parcela() -> date:
    return _somar_meses(hoje_local(), 1)


def _pago(forma_id, valor) -> dict:
    return {"forma_pagamento_id": forma_id, "valor": valor, "parcelado": False, "qtd_parcelas": None}


def _parcelado(forma_id, valor, parcelas=4, vencimento=None) -> dict:
    return {
        "forma_pagamento_id": forma_id, "valor": valor, "parcelado": True, "qtd_parcelas": parcelas,
        "vencimento": vencimento.isoformat() if vencimento else None,
    }


def _vender(client, headers, loja, total, pagamentos) -> int:
    v = client.post("/api/v1/vendas/", json={"funcionario_id": loja["funcionario_id"]}, headers=headers).json()["id"]
    item = client.post(f"/api/v1/vendas/{v}/itens", json={
        "tipo_produto": "AVULSO", "descricao_avulsa": "Movel", "quantidade": 1, "valor_unitario": total,
    }, headers=headers)
    assert item.status_code == 201, item.text
    r = client.post(f"/api/v1/vendas/{v}/finalizar", json={"pagamentos": pagamentos}, headers=headers)
    assert r.status_code == 200, r.text
    return v


def _contas(db_session) -> list[ContaReceber]:
    db_session.expire_all()
    return db_session.query(ContaReceber).order_by(ContaReceber.vencimento, ContaReceber.id).all()


def test_90_mil_a_vista_e_100_mil_em_4x_gera_4_contas(client, db_session, header_com_token, loja):
    """O caso do cliente: as 4 parcelas caem todo mes, no mesmo dia."""
    primeira = _primeira_parcela()

    _vender(client, header_com_token, loja, NOVENTA_MIL + CEM_MIL, [
        _pago(loja["Dinheiro"], NOVENTA_MIL),
        _parcelado(loja["Boleto"], CEM_MIL, vencimento=primeira),
    ])

    contas = _contas(db_session)
    assert [c.valor for c in contas] == [2_500_000] * 4
    assert [c.vencimento for c in contas] == [_somar_meses(primeira, n) for n in range(4)]
    assert [c.descricao.rsplit(" ", 2)[-1] for c in contas] == ["1/4)", "2/4)", "3/4)", "4/4)"]
    assert not any(c.baixa_automatica for c in contas)


def test_centavos_que_sobram_vao_na_ultima_parcela(client, db_session, header_com_token, loja):
    _vender(client, header_com_token, loja, 10_000, [
        _parcelado(loja["Boleto"], 10_000, parcelas=3, vencimento=_primeira_parcela()),
    ])

    assert [c.valor for c in _contas(db_session)] == [3333, 3333, 3334]


def test_dia_31_nao_escorrega_ao_passar_por_mes_curto():
    assert [_somar_meses(date(2027, 1, 31), n) for n in range(3)] == [
        date(2027, 1, 31), date(2027, 2, 28), date(2027, 3, 31),
    ]


def test_divisao_sempre_fecha_a_soma():
    for total in (1, 99, 10_000, 10_000_001):
        for parcelas in (2, 3, 7, 12):
            assert sum(_dividir_em_parcelas(total, parcelas)) == total


def test_receber_uma_parcela_nao_mexe_nas_outras(client, db_session, header_com_token, loja):
    _vender(client, header_com_token, loja, CEM_MIL, [
        _parcelado(loja["Boleto"], CEM_MIL, vencimento=_primeira_parcela()),
    ])
    primeira, segunda = _contas(db_session)[:2]

    for conta in (primeira, segunda):
        r = client.post(f"/api/v1/financeiro/contas-receber/{conta.id}/receber",
                        json={"forma_pagamento_id": loja["Dinheiro"]}, headers=header_com_token)
        assert r.status_code == 200, r.text

    assert [c.status for c in _contas(db_session)] == ["RECEBIDA", "RECEBIDA", "PENDENTE", "PENDENTE"]


def test_cancelar_a_venda_derruba_todas_as_parcelas(client, db_session, header_com_token, loja):
    v = _vender(client, header_com_token, loja, CEM_MIL, [
        _parcelado(loja["Boleto"], CEM_MIL, vencimento=_primeira_parcela()),
    ])

    r = client.post(f"/api/v1/vendas/{v}/cancelar", json={"motivo": "Cliente desistiu"}, headers=header_com_token)

    assert r.status_code == 200, r.text
    assert [c.status for c in _contas(db_session)] == ["CANCELADA"] * 4


# --- O que nao muda -----------------------------------------------------------

def test_cartao_parcelado_sem_vencimento_nao_gera_conta(client, db_session, header_com_token, loja):
    _vender(client, header_com_token, loja, CEM_MIL, [_parcelado(loja["Cartao"], CEM_MIL)])

    assert _contas(db_session) == []


def test_cartao_com_prazo_da_operadora_continua_uma_conta_so(client, db_session, header_com_token, loja):
    forma = db_session.get(FormaPagamento, loja["Cartao"])
    forma.dias_para_receber = 30
    db_session.commit()

    _vender(client, header_com_token, loja, CEM_MIL, [_parcelado(loja["Cartao"], CEM_MIL)])

    [conta] = _contas(db_session)
    assert conta.valor == CEM_MIL
    assert conta.baixa_automatica is True
    assert "parcela" not in conta.descricao


def test_fiado_sem_parcela_continua_uma_conta_so(client, db_session, header_com_token, loja):
    _vender(client, header_com_token, loja, CEM_MIL, [{
        **_pago(loja["Dinheiro"], CEM_MIL), "vencimento": _primeira_parcela().isoformat(),
    }])

    [conta] = _contas(db_session)
    assert conta.valor == CEM_MIL
    assert "parcela" not in conta.descricao


# --- OS -----------------------------------------------------------------------

def _pagamento_os(parcelas: int) -> SimpleNamespace:
    return SimpleNamespace(
        id=None, valor=CEM_MIL, juros_valor=0, juros_responsavel=JurosResponsavel.CLIENTE,
        parcelas=parcelas, vencimento=_primeira_parcela(),
        forma_pagamento=SimpleNamespace(dias_para_receber=0, tipo="BOLETO"),
    )


def _os() -> SimpleNamespace:
    return SimpleNamespace(funcionario=SimpleNamespace(empresa_id=1), equipamento=None, numero_os="OS-1")


def test_os_parcelada_tambem_gera_uma_conta_por_parcela(client, db_session, header_com_token):
    registrar_promessas_de_os(db_session, _os(), [_pagamento_os(4)])
    db_session.commit()

    contas = _contas(db_session)
    assert [c.valor for c in contas] == [2_500_000] * 4
    assert contas[0].descricao == "OS OS-1 (parcela 1/4)"


def test_os_sem_parcela_continua_uma_conta_so(client, db_session, header_com_token):
    registrar_promessas_de_os(db_session, _os(), [_pagamento_os(1)])
    db_session.commit()

    [conta] = _contas(db_session)
    assert conta.descricao == "OS OS-1"
