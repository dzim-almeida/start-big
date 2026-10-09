# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/orcamento_detalhe.py
# DESCRICAO: As SAIDAS do orcamento (detalhe, item da lista, simulacao), com o
#            recorte de custos por permissao (Spec 06A, §6.2, §6.3, D23).
# ---------------------------------------------------------------------------
"""
Recorte de custos (P4, D23): sem `view_custos_marcenaria`, a resposta NAO TRAZ
custo de insumo, origem do custo, material, perda, mao de obra, custos,
margens, RT (% e valores), markup, perda %, custo/hora e instalacao. Traz
precos, quantidades, medidas, desconto, total, sinal e saldo.

"Nao traz" = a CHAVE nao existe (e nao `null`), como na configuracao da 04A.
Por isso tudo aqui e montado em dicionario: e mais facil nao escrever a chave
do que tira-la depois.
"""

from typing import Any, Optional

from app.db.models.marcenaria.ambiente import MarcenariaMovel
from app.db.models.marcenaria.orcamento import MarcenariaOrcamento, StatusOrcamento
from app.services.marcenaria.calculo import (
    AVISO_MARGEM_NEGATIVA,
    MovelResultado,
    OrcamentoResultado,
    arredondar,
    repartir_maior_resto,
)
from app.services.marcenaria.aprovacao_bloqueios import os_cancelada
from app.services.marcenaria.permissoes import (
    PERMISSOES_EXCLUIR_ORCAMENTOS,
    PERMISSOES_GERIR_ORCAMENTOS,
    tem_alguma,
)

# Status em que cada acao faz sentido (secao 6.1, D11-D19).
_PODE_RECUSAR = (StatusOrcamento.ENVIADO, StatusOrcamento.VENCIDO)
_PODE_NOVA_VERSAO = (StatusOrcamento.ENVIADO, StatusOrcamento.VENCIDO, StatusOrcamento.RECUSADO)
_PODE_APROVAR = (StatusOrcamento.RASCUNHO, StatusOrcamento.ENVIADO, StatusOrcamento.VENCIDO)


# ===========================================================================
# PEDACOS (cliente, vendedor, endereco)
# ===========================================================================

def _formatar_cep(cep: Optional[str]) -> str:
    """'60000000' -> '60000-000' (mesmo formato do frontend)."""
    digitos = "".join(c for c in (cep or "") if c.isdigit())
    return f"{digitos[:5]}-{digitos[5:]}" if len(digitos) == 8 else (cep or "")


def endereco_em_uma_linha(endereco) -> str:
    """Endereco no formato do `getClienteEndereco` do frontend (Revisao 2):
    'Rua X, 123 (Sala 2) - Aldeota, Fortaleza - CE, CEP 60000-000'."""
    if endereco is None or not endereco.logradouro:
        return ""
    rua = ", ".join(p for p in (endereco.logradouro, endereco.numero) if p)
    complemento = f" ({endereco.complemento})" if endereco.complemento else ""
    uf = getattr(endereco.estado, "value", endereco.estado) or ""   # enum State -> "CE"
    cidade_uf = f"{endereco.cidade} - {uf}" if endereco.cidade and uf else (endereco.cidade or uf)
    local = ", ".join(p for p in (endereco.bairro, cidade_uf) if p)
    cep = f", CEP {_formatar_cep(endereco.cep)}" if endereco.cep else ""
    return " - ".join(p for p in (rua + complemento, local) if p) + cep


def nome_do_cliente(cliente) -> str:
    """PF: nome. PJ: razao social (o que vai na proposta)."""
    if cliente is None:
        return ""
    return getattr(cliente, "nome", None) or getattr(cliente, "razao_social", None) or ""


def _cliente(cliente) -> Optional[dict]:
    """Contato do cliente para a tela e a proposta (Revisao 2). Nao e custo."""
    if cliente is None:
        return None
    enderecos = list(cliente.endereco or [])
    return {
        "id": cliente.id,
        "nome": nome_do_cliente(cliente),
        "documento": getattr(cliente, "cpf", None) or getattr(cliente, "cnpj", None),
        "telefone": cliente.celular or cliente.telefone,            # celular, senao o fixo
        "email": cliente.email,
        "endereco": endereco_em_uma_linha(enderecos[0]) if enderecos else "",
    }


def _vendedor(funcionario) -> Optional[dict]:
    if funcionario is None:
        return None
    return {
        "id": funcionario.id,
        "nome": funcionario.nome,
        "telefone": funcionario.celular or funcionario.telefone,    # celular, senao o fixo
    }


# ===========================================================================
# ACOES (o que o usuario pode fazer AGORA)
# ===========================================================================

def montar_acoes(orc: MarcenariaOrcamento, usuario_token: dict, pode_desfazer: bool = False) -> dict[str, bool]:
    """Status + permissao. A tela so mostra botao a partir daqui (06B D13).

    `pode_desfazer` vem do servico (08A, secao 7.6): so liga o botao quando
    nada impede, para a tela nao oferecer o que vai falhar.
    """
    gerir = tem_alguma(usuario_token, PERMISSOES_GERIR_ORCAMENTOS)
    excluir = tem_alguma(usuario_token, PERMISSOES_EXCLUIR_ORCAMENTOS)
    s = orc.status
    # 08A D21: aprovado com a OS cancelada pela tela de OS -> o caminho e nova versao.
    aprovado_com_os_cancelada = s == StatusOrcamento.APROVADO and os_cancelada(orc)
    return {
        "editar": gerir and s == StatusOrcamento.RASCUNHO,
        "enviar": gerir and s == StatusOrcamento.RASCUNHO,
        "voltar_a_editar": gerir and s == StatusOrcamento.ENVIADO,
        "recusar": gerir and s in _PODE_RECUSAR,
        "renovar": gerir and s == StatusOrcamento.VENCIDO,
        "nova_versao": gerir and (s in _PODE_NOVA_VERSAO or aprovado_com_os_cancelada),
        # D18: so a versao 1, em rascunho, que nunca foi enviada.
        "excluir": excluir and s == StatusOrcamento.RASCUNHO and orc.versao == 1 and orc.data_envio is None,
        # D31: anexos em qualquer status, menos SUBSTITUIDO e APROVADO.
        "anexos": gerir and s not in (StatusOrcamento.SUBSTITUIDO, StatusOrcamento.APROVADO),
        # 08A D13: aprova de RASCUNHO (registra o envio junto), ENVIADO ou VENCIDO.
        "aprovar": gerir and s in _PODE_APROVAR,
        "desfazer_aprovacao": gerir and s == StatusOrcamento.APROVADO and pode_desfazer,
    }


# ===========================================================================
# DETALHE
# ===========================================================================

def _calculo_do_movel(r: MovelResultado, custos: bool) -> dict:
    """Calculo de uma linha. Precos sempre; custos so com permissao."""
    saida = {
        "preco_unit_centavos": r.preco_unit_centavos,
        "preco_total_centavos": r.preco_total_centavos,
    }
    if custos:
        saida.update({
            # Material, perda e mao de obra vem do motor sem arredondar
            # (Decimal); para a tela, centavos inteiros.
            "material_centavos": arredondar(r.material_centavos),
            "perda_centavos": arredondar(r.perda_centavos),
            "mao_obra_centavos": arredondar(r.mao_obra_centavos),
            "custo_unit_centavos": r.custo_unit_centavos,
            "custo_total_centavos": r.custo_total_centavos,
            "rt_linha_centavos": r.rt_linha_centavos,
        })
    return saida


def _movel(m: MarcenariaMovel, r: Optional[MovelResultado], custos: bool) -> dict:
    """Um movel: dados de sempre + (com permissao) os de custo + o calculo."""
    saida: dict[str, Any] = {
        "id": m.id,
        "ambiente_id": m.ambiente_id,
        "nome": m.nome,
        "descricao": m.descricao,
        "largura_mm": m.largura_mm,
        "altura_mm": m.altura_mm,
        "profundidade_mm": m.profundidade_mm,
        "quantidade": m.quantidade,
        "ordem": m.ordem,
        "tipo_producao": m.tipo_producao,
        "central": (
            {"fornecedor_id": m.central.id, "nome": m.central.nome} if m.central is not None else None
        ),
        "aprovado": m.aprovado,
        "os_item_id": m.os_item_id,       # o item da OS que o movel virou (08A)
    }
    if custos:
        saida["terceirizado_centavos"] = m.terceirizado_centavos
        saida["mao_obra"] = {
            "modo": m.mao_obra_modo,
            "centavos": m.mao_obra_centavos,
            "horas_centesimos": m.mao_obra_horas_centesimos,
        }
    insumos = []
    for i in m.insumos:
        item = {
            "id": i.id,
            "produto_id": i.produto_id,
            "descricao": i.descricao,
            "codigo": i.codigo,
            "unidade": i.unidade,
            "quantidade_milesimos": i.quantidade_milesimos,
            "sofre_perda": i.sofre_perda,
        }
        if custos:
            item["custo_unit_centavos"] = i.custo_unit_centavos
            item["custo_origem"] = i.custo_origem
        insumos.append(item)
    saida["insumos"] = insumos
    saida["calculo"] = _calculo_do_movel(r, custos) if r is not None else None
    return saida


def _arquitetos(orc: MarcenariaOrcamento, resultado: OrcamentoResultado, custos: bool) -> list[dict]:
    """Os arquitetos. Com custos, o % e o valor previsto (Revisao 3).

    Valor previsto = RT total repartido entre eles pelo MAIOR RESTO, com peso
    = rt_bp de cada um (a mesma conta da 09A na finalizacao).
    """
    rts = list(orc.rts)
    previstos = repartir_maior_resto(resultado.rt_total_centavos, [rt.rt_bp for rt in rts]) if rts else []
    lista = []
    for rt, previsto in zip(rts, previstos):
        item = {"fornecedor_id": rt.fornecedor_id, "nome": rt.fornecedor.nome if rt.fornecedor else ""}
        if custos:
            item["rt_bp"] = rt.rt_bp
            item["valor_previsto_centavos"] = previsto
            # Spec 09A (Revisao 1): a conta a pagar ATUAL deste arquiteto, que
            # nasce na finalizacao da OS. Antes disso, null.
            conta = rt.conta_pagar
            item["conta"] = None if conta is None else {
                "id": conta.id,
                "status": conta.status,
                "valor_centavos": conta.valor,
                "vencimento": conta.vencimento,
            }
        lista.append(item)
    return lista


def calculo_geral(resultado: OrcamentoResultado, custos: bool) -> dict:
    """Totais. Desconto, total, sinal e saldo sempre; custos e margens so com permissao."""
    saida: dict[str, Any] = {
        "bruto_centavos": resultado.bruto_centavos,
        "desconto_centavos": resultado.desconto_centavos,
        "total_centavos": resultado.total_centavos,
        "sinal_centavos": resultado.sinal_centavos,
        "saldo_centavos": resultado.saldo_centavos,
        # O % equivalente do valor digitado (so exibicao; Revisao 3): nao e custo.
        "desconto_bp_efetivo": resultado.desconto_bp_efetivo,
        "sinal_bp_efetivo": resultado.sinal_bp_efetivo,
    }
    if custos:
        saida.update({
            "custo_total_centavos": resultado.custo_total_centavos,
            "margem_bruta_centavos": resultado.margem_bruta_centavos,
            "rt_total_centavos": resultado.rt_total_centavos,
            "margem_liquida_centavos": resultado.margem_liquida_centavos,
            "margem_liquida_bp": resultado.margem_liquida_bp,
        })
    inst = resultado.instalacao
    if inst is None:
        saida["instalacao"] = None
    else:
        saida["instalacao"] = {"preco_centavos": inst.preco_centavos}
        if custos:
            saida["instalacao"]["custo_centavos"] = inst.custo_centavos
    return saida


def _parametros(orc: MarcenariaOrcamento, custos: bool) -> dict:
    """Parametros copiados (D4). Sem custos: so validade e prazo."""
    saida = {"validade_dias": orc.validade_dias, "prazo_entrega_dias": orc.prazo_entrega_dias}
    if custos:
        saida.update({
            "markup_bp": orc.markup_bp,
            "perda_bp": orc.perda_bp,
            "custo_hora_centavos": orc.custo_hora_centavos,
            "rt_padrao_bp": orc.rt_padrao_bp,
            "rt_modo": orc.rt_modo,
        })
    return saida


def _os_resumo(orc: MarcenariaOrcamento) -> Optional[dict]:
    """A OS da aprovacao (08A): numero e status, para o link e a faixa."""
    if orc.os is None:
        return None
    return {"id": orc.os.id, "numero_os": orc.os.numero_os, "status": getattr(orc.os.status, "value", orc.os.status)}


def _aprovacao(orc: MarcenariaOrcamento, resultado_aprovado: Optional[OrcamentoResultado], custos: bool) -> Optional[dict]:
    """O que virou OS (08A, secao 6.4). `calculo` aqui e SO o aprovado; o de
    fora (o orcamento inteiro) continua sendo o que foi proposto."""
    if orc.status != StatusOrcamento.APROVADO:
        return None
    return {
        "data": orc.data_aprovacao,
        "instalacao_aprovada": orc.instalacao_aprovada,
        "total_centavos": orc.resumo_aprovado_total_centavos,
        "sinal_combinado_centavos": orc.resumo_aprovado_sinal_centavos,
        "sinal_recebido_centavos": orc.sinal_recebido_centavos,
        "calculo": calculo_geral(resultado_aprovado, custos) if resultado_aprovado is not None else None,
    }


def montar_detalhe(
    orc: MarcenariaOrcamento,
    resultado: OrcamentoResultado,
    usuario_token: dict,
    custos: bool,
    resultado_aprovado: Optional[OrcamentoResultado] = None,
    pode_desfazer: bool = False,
) -> dict:
    """O detalhe completo (secao 6.2), ja recortado.

    `resultado_aprovado` e `pode_desfazer` so importam no orcamento APROVADO (08A).
    """
    # Resultado do motor por id do movel (o motor devolve o id como texto).
    por_movel = {mr.id: mr for amb in resultado.ambientes for mr in amb.moveis}
    por_ambiente = {ar.id: ar for ar in resultado.ambientes}

    ambientes = []
    for amb in sorted(orc.ambientes, key=lambda a: (a.ordem, a.id)):
        ar = por_ambiente.get(str(amb.id))
        item: dict[str, Any] = {
            "id": amb.id,
            "nome": amb.nome,
            "ordem": amb.ordem,
            "subtotal_centavos": ar.subtotal_centavos if ar else 0,   # bruto (T5)
        }
        if custos:
            item["custo_centavos"] = ar.custo_centavos if ar else 0
        item["moveis"] = [
            _movel(m, por_movel.get(str(m.id)), custos)
            for m in sorted(amb.moveis, key=lambda m: (m.ordem, m.id))
        ]
        ambientes.append(item)

    # MARGEM_NEGATIVA conta da margem: quem nao ve custo nao recebe esse aviso.
    avisos = [a for a in resultado.avisos if custos or a != AVISO_MARGEM_NEGATIVA]

    detalhe: dict[str, Any] = {
        "id": orc.id,
        "codigo": orc.codigo,
        "versao": orc.versao,
        "status": orc.status,
        "revisao": orc.revisao,
        "cliente": _cliente(orc.cliente),
        "vendedor": _vendedor(orc.funcionario),
        "projeto": {
            "objeto_id": orc.objeto_id,
            "nome": orc.projeto_nome,
            "endereco_obra": orc.endereco_obra,
        },
        "medicao_observacoes": orc.medicao_observacoes,
        "observacoes_proposta": orc.observacoes_proposta,
        "parametros": _parametros(orc, custos),
        # No APROVADO, o RT previsto e o do que virou OS (09A Revisao 1): o mesmo
        # numero da conta que a finalizacao vai criar.
        "arquitetos": _arquitetos(orc, resultado_aprovado or resultado, custos),
    }
    if custos:
        detalhe["instalacao_custo_centavos"] = orc.instalacao_custo_centavos
    detalhe.update({
        "desconto": {"modo": orc.desconto_modo, "valor": orc.desconto_valor},
        "sinal": {"modo": orc.sinal_modo, "valor": orc.sinal_valor},
        "ambientes": ambientes,
        "calculo": calculo_geral(resultado, custos),
        "avisos": avisos,
        "datas": {
            "criacao": orc.data_criacao,
            "atualizacao": orc.data_atualizacao,
            "envio": orc.data_envio,
            "validade": orc.data_validade,
            "recusa": orc.data_recusa,
            "aprovacao": orc.data_aprovacao,
        },
        "motivo_recusa": orc.motivo_recusa,
        "aprovacao": _aprovacao(orc, resultado_aprovado, custos),   # 08A
        "os": _os_resumo(orc),                                       # 08A
        "inclui_custos": custos,
        "acoes": montar_acoes(orc, usuario_token, pode_desfazer),
    })
    return detalhe


# ===========================================================================
# LISTA E VERSOES
# ===========================================================================

def montar_item_lista(orc: MarcenariaOrcamento, custos: bool) -> dict:
    """Um item da lista (secao 6.3): o resumo do cabecalho, sem rodar o motor."""
    item = {
        "id": orc.id,
        "codigo": orc.codigo,
        "versao": orc.versao,
        "status": orc.status,
        "cliente_nome": nome_do_cliente(orc.cliente) or None,
        "projeto_nome": orc.projeto_nome,
        "vendedor_nome": orc.funcionario.nome if orc.funcionario else None,
        # Aprovado: o total que virou OS (08A, secao 5); senao, o proposto.
        "resumo_total_centavos": (
            orc.resumo_aprovado_total_centavos
            if orc.status == StatusOrcamento.APROVADO and orc.resumo_aprovado_total_centavos is not None
            else orc.resumo_total_centavos
        ),
        "resumo_qtd_moveis": orc.resumo_qtd_moveis,
        "data_validade": orc.data_validade,
        "data_atualizacao": orc.data_atualizacao,
        "os_numero": orc.os.numero_os if orc.status == StatusOrcamento.APROVADO and orc.os else None,
    }
    if custos:
        item["resumo_margem_bp"] = orc.resumo_margem_bp     # margem: so com permissao
    return item


def montar_versao(orc: MarcenariaOrcamento) -> dict:
    """Uma linha de GET /{id}/versoes (numero, status, total, datas)."""
    return {
        "id": orc.id,
        "versao": orc.versao,
        "status": orc.status,
        "resumo_total_centavos": orc.resumo_total_centavos,
        "data_criacao": orc.data_criacao,
        "data_envio": orc.data_envio,
        "data_validade": orc.data_validade,
        "data_recusa": orc.data_recusa,
    }


def recortar_simulacao(resultado: MovelResultado, insumos_novos: list[dict], avisos: list[str], custos: bool) -> dict:
    """Resposta do simular (secao 6.6): sem o RT da linha (depende do orcamento inteiro)."""
    calculo = _calculo_do_movel(resultado, custos)
    calculo.pop("rt_linha_centavos", None)
    calculo.pop("custo_total_centavos", None)
    if custos:
        insumos = insumos_novos
    else:
        # Sem custos: so o que nao e custo de cada insumo novo.
        insumos = [{"produto_id": i["produto_id"], "sofre_perda": i["sofre_perda"]} for i in insumos_novos]
    return {
        "calculo": calculo,
        "insumos": insumos,
        "avisos": [a for a in avisos if custos or a != AVISO_MARGEM_NEGATIVA],
    }
