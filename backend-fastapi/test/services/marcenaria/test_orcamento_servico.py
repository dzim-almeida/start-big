# ---------------------------------------------------------------------------
# ARQUIVO: test/services/marcenaria/test_orcamento_servico.py
# DESCRICAO: Orcamento de marcenaria, regras do servico (Spec 06A, §11,
#            casos 01 a 17).
#
#            O que nao pode errar:
#              - o orcamento COPIA parametros e custos: mudar a configuracao ou
#                o produto depois nao muda nada sem aviso (D2-D4, O3);
#              - o motor da Spec 05 da os mesmos numeros pelo banco;
#              - uma escrita que o motor recusa nao grava nada pela metade;
#              - versoes, renovacao e vencimento seguem D14-D16.
# ---------------------------------------------------------------------------

from datetime import timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.tempo import hoje_local
from app.db.crud.marcenaria import orcamento as crud
from app.db.models.configuracao_marcenaria import ConfiguracaoMarcenaria
from app.db.models.estoque import Estoque
from app.db.models.marcenaria import (
    MarcenariaEvento,
    MarcenariaMovel,
    MarcenariaMovelInsumo,
    MarcenariaOrcamento,
)
from app.db.models.produto import Produto
from app.schemas.marcenaria.orcamento import AmbienteEntrada, AtualizarPrecosEntrada, MovelEntrada, OrcamentoCriar
from app.services.marcenaria import orcamento as servico
from app.services.marcenaria import orcamento_arvore as arvore

from test.apoio_orcamento_marcenaria import montar_cenario_b


def _orcamento(db: Session, orcamento_id: int) -> MarcenariaOrcamento:
    """O orcamento relido do banco (sem o que estiver em memoria)."""
    db.expire_all()
    return db.get(MarcenariaOrcamento, orcamento_id)


def _eventos(db: Session, orcamento_id: int, tipo: str) -> list[MarcenariaEvento]:
    return db.query(MarcenariaEvento).filter_by(orcamento_id=orcamento_id, tipo=tipo).all()


# =========================
# Criacao e copia dos parametros (01, 02)
# =========================

def test_01_criar_com_a_configuracao_padrao(db_session, token_master):
    oid = servico.criar_orcamento(db_session, OrcamentoCriar(), token_master)
    orc = _orcamento(db_session, oid)

    assert (orc.markup_bp, orc.perda_bp, orc.validade_dias, orc.prazo_entrega_dias) == (9000, 1000, 15, 30)
    assert (orc.status, orc.revisao, orc.versao) == ("RASCUNHO", 1, 1)
    assert orc.codigo == f"ORC-{hoje_local().year}-000001"
    assert len(_eventos(db_session, oid, "ORCAMENTO_CRIADO")) == 1


def test_02_mudar_a_configuracao_nao_altera_o_orcamento(db_session, token_master):
    oid = servico.criar_orcamento(db_session, OrcamentoCriar(), token_master)

    config = db_session.query(ConfiguracaoMarcenaria).first()
    config.markup_padrao_bp = 15000                     # o dono sobe o markup depois
    db_session.commit()

    assert _orcamento(db_session, oid).markup_bp == 9000
    # O proximo orcamento ja nasce com o markup novo.
    novo = servico.criar_orcamento(db_session, OrcamentoCriar(), token_master)
    assert _orcamento(db_session, novo).markup_bp == 15000


# =========================
# Custo do insumo pela regra O3a (03, 04, 05)
# =========================

def _orcamento_com_um_movel(db, token, produto_id: int, quantidade: int = 1000) -> int:
    """Orcamento com um ambiente e um movel com um insumo do produto.

    Fica na revisao 3 (criar = 1, ambiente = 2, movel = 3).
    """
    oid = servico.criar_orcamento(db, OrcamentoCriar(projeto_nome="Cozinha"), token)
    arvore.criar_ambiente(db, oid, 1, AmbienteEntrada(nome="Cozinha"))
    amb = _orcamento(db, oid).ambientes[0].id
    arvore.criar_movel(db, oid, amb, 2, MovelEntrada(
        nome="Armário", insumos=[{"produto_id": produto_id, "quantidade_milesimos": quantidade}],
    ), token)
    return oid


def _insumo(db, oid) -> MarcenariaMovelInsumo:
    return _orcamento(db, oid).ambientes[0].moveis[0].insumos[0]


@pytest.mark.parametrize("valor_entrada, custo_medio, custo, origem", [
    (28000, 25000, 28000, "ULTIMA_COMPRA"),   # 03: ultima compra vence
    (None, 25000, 25000, "CUSTO_MEDIO"),      # 04: reserva = custo medio
    (0, 25000, 25000, "CUSTO_MEDIO"),         # valor_entrada 0 conta como "sem" (secao 7.3)
    (None, None, 0, "SEM_CUSTO"),             # 05: nenhum dos dois
])
def test_03_04_05_custo_copiado_pela_regra_o3a(db_session, token_master, produto, valor_entrada, custo_medio, custo, origem):
    pid = produto("MDF Branco", valor_entrada=valor_entrada, custo_medio=custo_medio, codigo="MDF-BR", unidade="CH")
    oid = _orcamento_com_um_movel(db_session, token_master, pid)

    insumo = _insumo(db_session, oid)
    assert (insumo.custo_unit_centavos, insumo.custo_origem) == (custo, origem)
    # Copia de descricao, codigo, unidade e sofre_perda (D2).
    assert (insumo.descricao, insumo.codigo, insumo.unidade, insumo.sofre_perda) == ("MDF Branco", "MDF-BR", "CH", True)


def test_05_sem_custo_gera_aviso_no_detalhe(db_session, token_master, produto):
    pid = produto("Puxador novo")
    oid = _orcamento_com_um_movel(db_session, token_master, pid)

    assert "INSUMO_SEM_CUSTO" in servico.detalhe(db_session, oid, token_master)["avisos"]


# =========================
# O motor pelo banco (06)
# =========================

def test_06_cenario_b_da_spec_05_pelo_banco(api, produto, fornecedor, cliente_id):
    d = montar_cenario_b(api, produto, fornecedor, cliente=cliente_id)
    c = d["calculo"]

    assert (c["bruto_centavos"], c["desconto_centavos"], c["total_centavos"]) == (972515, 48626, 923889)
    assert (c["custo_total_centavos"], c["margem_bruta_centavos"], c["rt_total_centavos"]) == (511850, 412039, 73911)
    assert (c["margem_liquida_centavos"], c["margem_liquida_bp"]) == (338128, 3660)
    assert (c["sinal_centavos"], c["saldo_centavos"]) == (369556, 554333)
    torre, balcao = d["ambientes"][0]["moveis"]
    assert (torre["calculo"]["custo_unit_centavos"], torre["calculo"]["preco_unit_centavos"]) == (222250, 422275)
    assert (balcao["calculo"]["preco_total_centavos"], balcao["calculo"]["rt_linha_centavos"]) == (407740, 30988)
    assert d["ambientes"][0]["subtotal_centavos"] == 830015


# =========================
# Copia do custo (07, 08, 09)
# =========================

def _mudar_produto(db: Session, produto_id: int, valor_entrada=None, sofre_perda=None) -> None:
    p = db.get(Produto, produto_id)
    if valor_entrada is not None:
        p.estoque.valor_entrada = valor_entrada
    if sofre_perda is not None:
        p.sofre_perda = sofre_perda
    db.commit()


def test_07_reenviar_insumo_com_id_mantem_o_custo_antigo(db_session, token_master, produto):
    pid = produto("MDF Branco", valor_entrada=28000)
    oid = _orcamento_com_um_movel(db_session, token_master, pid)
    insumo = _insumo(db_session, oid)
    movel_id = insumo.movel_id

    _mudar_produto(db_session, pid, valor_entrada=31500)    # o fornecedor aumentou
    arvore.atualizar_movel(db_session, oid, movel_id, 3, MovelEntrada(
        nome="Armário", insumos=[{"id": insumo.id, "quantidade_milesimos": 2000}],
    ), token_master)

    depois = _insumo(db_session, oid)
    assert (depois.custo_unit_centavos, depois.quantidade_milesimos) == (28000, 2000)


def test_08_mudar_sofre_perda_do_produto_nao_muda_o_orcamento(db_session, token_master, produto):
    pid = produto("Fita PVC", valor_entrada=350, sofre_perda=True)
    oid = _orcamento_com_um_movel(db_session, token_master, pid)
    total_antes = servico.detalhe(db_session, oid, token_master)["calculo"]["total_centavos"]

    _mudar_produto(db_session, pid, sofre_perda=False)

    assert _insumo(db_session, oid).sofre_perda is True
    assert servico.detalhe(db_session, oid, token_master)["calculo"]["total_centavos"] == total_antes
    itens = servico.precos_desatualizados(db_session, oid)["itens"]
    assert [(i["sofre_perda_orcamento"], i["sofre_perda_hoje"]) for i in itens] == [(True, False)]


def test_09_atualizar_precos_com_todos(db_session, token_master, produto):
    pid = produto("MDF Branco", valor_entrada=28000)
    oid = _orcamento_com_um_movel(db_session, token_master, pid)
    _mudar_produto(db_session, pid, valor_entrada=31500)
    previa = servico.precos_desatualizados(db_session, oid)
    assert previa["diferenca_centavos"] > 0

    servico.atualizar_precos(db_session, oid, 3, AtualizarPrecosEntrada(todos=True), token_master)

    assert _insumo(db_session, oid).custo_unit_centavos == 31500
    detalhe = servico.detalhe(db_session, oid, token_master)
    assert detalhe["calculo"]["total_centavos"] == previa["total_com_precos_novos_centavos"]
    (evento,) = _eventos(db_session, oid, "PRECOS_ATUALIZADOS")
    assert evento.dados == {"qtd_itens": 1, "diferenca_centavos": previa["diferenca_centavos"]}


# =========================
# Arvore (10, 11, 12)
# =========================

def test_10_duplicar_movel(db_session, token_master, produto):
    pid = produto("MDF Branco", valor_entrada=28000)
    oid = _orcamento_com_um_movel(db_session, token_master, pid)
    original = _orcamento(db_session, oid).ambientes[0].moveis[0]
    _mudar_produto(db_session, pid, valor_entrada=99999)    # a copia NAO pega o preco de hoje

    arvore.duplicar_movel(db_session, oid, original.id, 3)

    moveis = _orcamento(db_session, oid).ambientes[0].moveis
    assert [m.nome for m in moveis] == ["Armário", "Armário (cópia)"]
    assert [m.ordem for m in moveis] == [1, 2]
    assert moveis[1].insumos[0].custo_unit_centavos == 28000


def test_11_excluir_ambiente_leva_moveis_e_insumos(db_session, token_master, produto):
    pid = produto("MDF Branco", valor_entrada=28000)
    oid = _orcamento_com_um_movel(db_session, token_master, pid)
    amb = _orcamento(db_session, oid).ambientes[0].id

    arvore.remover_ambiente(db_session, oid, amb, 3)

    assert db_session.query(MarcenariaMovel).count() == 0
    assert db_session.query(MarcenariaMovelInsumo).count() == 0


def test_12_desconto_maior_que_o_novo_total_nao_grava_nada(db_session, token_master, produto):
    pid = produto("MDF Branco", valor_entrada=28000)
    oid = _orcamento_com_um_movel(db_session, token_master, pid)
    total = servico.detalhe(db_session, oid, token_master)["calculo"]["total_centavos"]
    orc = _orcamento(db_session, oid)
    orc.desconto_modo, orc.desconto_valor = "VALOR", total - 100    # desconto quase do total
    db_session.commit()
    movel_id = orc.ambientes[0].moveis[0].id

    with pytest.raises(HTTPException) as erro:
        arvore.remover_movel(db_session, oid, movel_id, 3)    # sem o movel, o desconto passa do total
    db_session.rollback()                                    # o endpoint faz isso

    assert erro.value.status_code == 422
    assert erro.value.detail == {"codigo": "CALCULO_INVALIDO", "campo": "desconto",
                                 "mensagem": "O desconto não pode ser maior que o total do orçamento."}
    depois = _orcamento(db_session, oid)
    assert len(depois.ambientes[0].moveis) == 1 and depois.revisao == 3   # nada gravado


# =========================
# Versoes e status (13, 14, 15)
# =========================

def _enviado(db, token, produto, cliente) -> int:
    pid = produto("MDF Branco", valor_entrada=28000)
    oid = _orcamento_com_um_movel(db, token, pid)
    orc = _orcamento(db, oid)
    orc.cliente_id = cliente
    db.commit()
    servico.enviar(db, oid, 3, token)
    return oid


def test_13_nova_versao_de_um_recusado(db_session, token_master, produto, cliente_id):
    oid = _enviado(db_session, token_master, produto, cliente_id)
    servico.recusar(db_session, oid, 4, "Preço", token_master)
    v1 = _orcamento(db_session, oid)
    v1.ambientes[0].moveis[0].aprovado = True               # simula uma marca antiga
    db_session.commit()

    novo = servico.nova_versao(db_session, oid, 5, token_master)

    v1, v2 = _orcamento(db_session, oid), _orcamento(db_session, novo)
    assert (v1.status, v2.status, v2.versao, v2.codigo, v2.revisao) == ("SUBSTITUIDO", "RASCUNHO", 2, v1.codigo, 1)
    assert v2.data_envio is None and v2.data_validade is None and v2.motivo_recusa is None
    movel = v2.ambientes[0].moveis[0]
    assert movel.aprovado is None
    assert movel.insumos[0].custo_unit_centavos == 28000
    assert v2.resumo_total_centavos == v1.resumo_total_centavos
    assert len(_eventos(db_session, oid, "NOVA_VERSAO")) == 1 and len(_eventos(db_session, novo, "NOVA_VERSAO")) == 1


def _vencer(db, oid, dias_atras=1):
    """Poe a validade no passado (como se o tempo tivesse passado)."""
    orc = _orcamento(db, oid)
    orc.data_validade = hoje_local() - timedelta(days=dias_atras)
    db.commit()


def test_14_renovar_vencido(db_session, token_master, produto, cliente_id):
    oid = _enviado(db_session, token_master, produto, cliente_id)
    _vencer(db_session, oid)
    assert servico.detalhe(db_session, oid, token_master)["status"] == "VENCIDO"

    servico.renovar(db_session, oid, 4, token_master)

    orc = _orcamento(db_session, oid)
    assert (orc.status, orc.data_validade, orc.versao) == ("RASCUNHO", None, 1)
    assert len(_eventos(db_session, oid, "ORCAMENTO_RENOVADO")) == 1


def test_15_vencimento_preguicoso_na_lista(db_session, token_master, produto, cliente_id):
    oid = _enviado(db_session, token_master, produto, cliente_id)
    _vencer(db_session, oid)
    revisao = _orcamento(db_session, oid).revisao

    servico.listar(db_session, {}, 1, 20, token_master)
    servico.listar(db_session, {}, 1, 20, token_master)          # a segunda leitura nao duplica

    orc = _orcamento(db_session, oid)
    assert (orc.status, orc.revisao) == ("VENCIDO", revisao)
    (evento,) = _eventos(db_session, oid, "ORCAMENTO_VENCIDO")
    assert evento.usuario_nome == "Sistema"


def test_15b_validade_hoje_ainda_nao_venceu(db_session, token_master, produto, cliente_id):
    oid = _enviado(db_session, token_master, produto, cliente_id)
    _vencer(db_session, oid, dias_atras=0)                         # vence HOJE: ainda vale

    servico.listar(db_session, {}, 1, 20, token_master)

    assert _orcamento(db_session, oid).status == "ENVIADO"


# =========================
# Numeracao e envio (16, 17)
# =========================

def test_16_disputa_pelo_mesmo_numero(db_session, token_master, monkeypatch):
    primeiro = servico.criar_orcamento(db_session, OrcamentoCriar(), token_master)
    original = crud.ultimo_codigo_com_prefixo
    chamadas = []

    def _atrasado(db, prefixo):
        """1a chamada: "nao vi o orcamento do outro computador" (devolve None)."""
        chamadas.append(prefixo)
        return None if len(chamadas) == 1 else original(db, prefixo)

    monkeypatch.setattr(crud, "ultimo_codigo_com_prefixo", _atrasado)
    segundo = servico.criar_orcamento(db_session, OrcamentoCriar(), token_master)

    assert len(chamadas) == 2                                     # tentou de novo
    codigos = [_orcamento(db_session, i).codigo for i in (primeiro, segundo)]
    assert codigos == [f"ORC-{hoje_local().year}-000001", f"ORC-{hoje_local().year}-000002"]


def test_17_enviar_sem_cliente_diz_so_o_que_falta(db_session, token_master, produto):
    pid = produto("MDF Branco", valor_entrada=28000)
    oid = _orcamento_com_um_movel(db_session, token_master, pid)

    with pytest.raises(HTTPException) as erro:
        servico.enviar(db_session, oid, 3, token_master)
    db_session.rollback()

    assert erro.value.status_code == 422
    assert erro.value.detail == "Para enviar, informe o cliente."
    assert _orcamento(db_session, oid).status == "RASCUNHO"


def test_17b_enviar_vazio_lista_tudo_que_falta(db_session, token_master):
    oid = servico.criar_orcamento(db_session, OrcamentoCriar(), token_master)

    with pytest.raises(HTTPException) as erro:
        servico.enviar(db_session, oid, 1, token_master)
    db_session.rollback()

    assert erro.value.detail == "Para enviar, informe o cliente, o nome do projeto e pelo menos um móvel."


def test_17c_enviar_grava_envio_validade_e_evento_com_valores(db_session, token_master, produto, cliente_id):
    oid = _enviado(db_session, token_master, produto, cliente_id)

    orc = _orcamento(db_session, oid)
    assert orc.status == "ENVIADO" and orc.data_envio is not None
    assert orc.data_validade == hoje_local() + timedelta(days=15)
    (evento,) = _eventos(db_session, oid, "ORCAMENTO_ENVIADO")
    assert evento.dados["total_centavos"] == orc.resumo_total_centavos
    assert evento.dados["qtd_moveis"] == 1
    assert evento.descricao.startswith("Enviado com total de R$ ")
    assert evento.descricao.endswith(f"válido até {orc.data_validade:%d/%m/%Y}.")


def test_custo_medio_ignora_estoque_sem_valores(db_session, token_master):
    """Produto sem linha de estoque: sem custo (nao quebra)."""
    p = Produto(nome="Servico avulso", codigo_produto="SV-1", ativo=True)
    db_session.add(p)
    db_session.commit()
    from app.services.marcenaria.orcamento_precos import custo_do_produto
    assert custo_do_produto(db_session.get(Produto, p.id)) == (0, "SEM_CUSTO")
    p.estoque = Estoque(quantidade=0, valor_varejo=0)
    db_session.commit()
    assert custo_do_produto(db_session.get(Produto, p.id)) == (0, "SEM_CUSTO")
