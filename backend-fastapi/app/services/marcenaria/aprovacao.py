# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/aprovacao.py
# DESCRICAO: Aprovacao do orcamento de marcenaria e geracao da OS; desfazer
#            a aprovacao (Spec 08A, secoes 4 e 7).
# ---------------------------------------------------------------------------
"""
Aprovar = transformar o orcamento aceito em ORDEM DE SERVICO sem digitar nada:

- um item de SERVICO por movel aprovado (preco do motor; custo + parte do RT);
- a instalacao como item proprio;
- os insumos dos moveis internos como PECAS EMBUTIDAS (item de produto de valor
  zero, que o cliente nao ve): e por elas que o Compras e a finalizacao veem o
  material;
- o desconto do motor sobre o aprovado, o vendedor como responsavel, a
  previsao de entrega e o projeto (objeto) do cliente;
- o sinal so entra na OS se foi RECEBIDO.

A OS nasce pelo servico de SEMPRE (`create_ordem_servico(..., origem_orcamento=True)`),
na mesma transacao que muda o orcamento: erro em qualquer passo desfaz tudo.
Os itens gerados recebem `origem = "ORCAMENTO_MARCENARIA"` e ficam travados na
OS (D18); para mudar, desfaz-se a aprovacao ou cria-se uma nova versao.
"""

from dataclasses import dataclass, replace
from datetime import datetime, time, timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enum import (
    OrdemServicoItemAprovacao,
    OrdemServicoItemTipo,
    OrdemServicoPrioridade,
    UnidadeMedida,
)
from app.core.regras_preco import reais
from app.core.tempo import agora_utc, hoje_local
from app.db.crud import ordem_servico as os_crud
from app.db.crud.marcenaria import evento as crud_evento
from app.db.crud.marcenaria import orcamento as crud
from app.db.models.marcenaria.orcamento import MarcenariaOrcamento, StatusOrcamento
from app.db.models.produto import Produto
from app.schemas.marcenaria.aprovacao import AprovacaoEntrada, DesfazerEntrada, SinalEntrada
from app.schemas.ordem_servico import OrdemServicoCancelar, OrdemServicoCreate, OSItemCreate, OSObjetoCreate
from app.services import ordem_servico as os_service
from app.services.marcenaria import erros
from app.services.marcenaria.calculo import AjusteCalc, OrcamentoResultado
from app.services.marcenaria.aprovacao_bloqueios import motivos_que_impedem_desfazer
from app.services.marcenaria.insumos_os import InsumoDaOS, insumos_da_os, ordenar_para_a_os
from app.services.marcenaria.orcamento import exigir_completo_para_enviar, registrar_envio
from app.services.marcenaria.orcamento_calculo import Selecao, calcular, montar_entrada_motor
from app.services.marcenaria.orcamento_comum import (
    carregar,
    conferir_revisao,
    exigir_orcamento_tecnico,
    fechar_escrita,
    registrar_evento,
)
from app.services.marcenaria.permissoes import pode_ver_custos_marcenaria

ORIGEM = "ORCAMENTO_MARCENARIA"            # o que vai em `ordem_servico_itens.origem` (D18)
NOME_INSTALACAO = "Instalação e montagem"   # o item da instalacao (D2)
AVISO_MOVEL_SEM_PRECO = "MOVEL_SEM_PRECO"   # aviso do simular (D4)

# De onde se pode aprovar (D13): de RASCUNHO o envio e registrado junto.
STATUS_APROVAVEIS = (StatusOrcamento.RASCUNHO, StatusOrcamento.ENVIADO, StatusOrcamento.VENCIDO)

# ===========================================================================
# ESCOLHA DO QUE FOI APROVADO
# ===========================================================================

def _todos_os_moveis(orc: MarcenariaOrcamento):
    """(ambiente, movel) na ordem da tela."""
    for ambiente in sorted(orc.ambientes, key=lambda a: (a.ordem, a.id)):
        for movel in sorted(ambiente.moveis, key=lambda m: (m.ordem, m.id)):
            yield ambiente, movel


def _selecao(orc: MarcenariaOrcamento, dados: AprovacaoEntrada) -> Selecao:
    """Os moveis escolhidos tem de ser DESTE orcamento."""
    ids_do_orcamento = {m.id for _a, m in _todos_os_moveis(orc)}
    if any(mid not in ids_do_orcamento for mid in dados.movel_ids):
        erros.invalido("Móvel não encontrado neste orçamento.")
    return Selecao(frozenset(dados.movel_ids), dados.incluir_instalacao)


def _com_desconto_novo(entrada, dados: AprovacaoEntrada):
    """O desconto renegociado na aprovacao (D11), se veio."""
    if dados.desconto is None:
        return entrada
    return replace(entrada, desconto=AjusteCalc(dados.desconto.modo, dados.desconto.valor))


def _moveis_sem_preco(orc: MarcenariaOrcamento, resultado: OrcamentoResultado) -> list[str]:
    """Nomes dos moveis aprovados com preco zero (D4): sinal de movel incompleto."""
    nomes = {str(m.id): m.nome for _a, m in _todos_os_moveis(orc)}
    return [nomes[mr.id] for amb in resultado.ambientes for mr in amb.moveis if mr.preco_unit_centavos <= 0]


def _previsao(orc: MarcenariaOrcamento):
    """Data da aprovacao + prazo de entrega (O7)."""
    return hoje_local() + timedelta(days=orc.prazo_entrega_dias)


# ===========================================================================
# SIMULAR (D12)
# ===========================================================================

def simular(db: Session, orcamento_id: int, dados: AprovacaoEntrada, usuario_token: dict) -> dict:
    """Os numeros do que SERIA aprovado, sem gravar nada (mesmo recorte de custos da 06A)."""
    orc = carregar(db, orcamento_id)
    if orc.status not in STATUS_APROVAVEIS:
        erros.transicao_invalida(orc.status)
    selecao = _selecao(orc, dados)
    resultado = calcular(_com_desconto_novo(montar_entrada_motor(orc, selecao=selecao), dados))
    custos = pode_ver_custos_marcenaria(usuario_token)

    avisos = [a for a in resultado.avisos if custos or a != "MARGEM_NEGATIVA"]
    if _moveis_sem_preco(orc, resultado):
        avisos.append(AVISO_MOVEL_SEM_PRECO)
    total_moveis = sum(1 for _ in _todos_os_moveis(orc))
    saida = {
        "moveis_aprovados": len(selecao.movel_ids),
        "moveis_recusados": total_moveis - len(selecao.movel_ids),
        "bruto_centavos": resultado.bruto_centavos,
        "desconto_centavos": resultado.desconto_centavos,
        "total_centavos": resultado.total_centavos,
        "sinal_centavos": resultado.sinal_centavos,
        "saldo_centavos": resultado.saldo_centavos,
        "desconto_bp_efetivo": resultado.desconto_bp_efetivo,
        "sinal_bp_efetivo": resultado.sinal_bp_efetivo,
        # Para a tela oferecer o credito do cliente no sinal (D16).
        "credito_cliente_centavos": (orc.cliente.saldo_credito or 0) if orc.cliente else 0,
        "previsao_entrega": _previsao(orc).isoformat(),
        "avisos": avisos,
    }
    if custos:
        saida.update({
            "custo_total_centavos": resultado.custo_total_centavos,
            "margem_bruta_centavos": resultado.margem_bruta_centavos,
            "rt_total_centavos": resultado.rt_total_centavos,
            "margem_liquida_centavos": resultado.margem_liquida_centavos,
            "margem_liquida_bp": resultado.margem_liquida_bp,
        })
    return saida


# ===========================================================================
# APROVAR
# ===========================================================================

@dataclass(frozen=True)
class SinalResolvido:
    """O que entra na OS como adiantamento (D15)."""
    valor_entrada: int                    # 0 quando ainda nao recebido
    forma_pagamento_id: Optional[int]
    usar_credito: bool


def _resolver_sinal(sinal: Optional[SinalEntrada], resultado: OrcamentoResultado) -> SinalResolvido:
    """So o sinal RECEBIDO vira `valor_entrada` (dinheiro que entrou)."""
    if sinal is None or not sinal.recebido:
        return SinalResolvido(0, None, False)       # combinado fica guardado no orcamento
    valor = sinal.valor_centavos if sinal.valor_centavos is not None else resultado.sinal_centavos
    if valor > resultado.total_centavos:
        erros.invalido("O sinal não pode ser maior que o total aprovado.")
    if valor == 0:
        return SinalResolvido(0, None, False)
    if sinal.usar_credito_cliente:
        return SinalResolvido(valor, None, True)     # D16: o servico da OS baixa o credito
    if sinal.forma_pagamento_id is None:
        erros.invalido("Informe a forma de pagamento do sinal.")
    return SinalResolvido(valor, sinal.forma_pagamento_id, False)


def _nome_item(movel: str, ambiente: str) -> str:
    """'Torre Quente — Cozinha Gourmet', cortando o movel para caber em 255."""
    sufixo = f" — {ambiente}"
    return movel[: 255 - len(sufixo)] + sufixo


def _unidade_do_item(unidade: str) -> UnidadeMedida:
    """O item da OS exige o enum; a unidade do produto e texto livre ("CH", "PAR")."""
    try:
        return UnidadeMedida((unidade or "UN").upper())
    except ValueError:
        return UnidadeMedida.OUTROS


def _descricao_os(orc: MarcenariaOrcamento) -> str:
    """O 'defeito relatado' da OS (D5): de que orcamento ela veio."""
    texto = f"Móveis planejados conforme orçamento {orc.codigo} v{orc.versao}"
    if orc.projeto_nome:
        texto += f" — {orc.projeto_nome}"
    return texto[:500]


def _objeto_do_projeto(orc: MarcenariaOrcamento) -> OSObjetoCreate:
    """O projeto (D6): o objeto que ja existe (pelo PRJ-...) ou um novo."""
    dados = {"endereco_obra": orc.endereco_obra} if orc.endereco_obra else {}
    if orc.objeto_id is not None and orc.objeto is not None:
        # Mesmo numero_serie = o servico da OS reaproveita o objeto e atualiza
        # o nome e o endereco da obra se mudaram.
        return OSObjetoCreate(
            numero_serie=orc.objeto.numero_serie,
            modelo=(orc.projeto_nome or orc.objeto.modelo)[:100],
            dados_adicionais=dados,
        )
    # Novo: o codigo PRJ-... e gerado pelo servico da OS, como sempre.
    return OSObjetoCreate(modelo=(orc.projeto_nome or "Projeto")[:100], dados_adicionais=dados)


def _itens_da_os(orc: MarcenariaOrcamento, resultado: OrcamentoResultado, pecas: list[InsumoDaOS]):
    """Os itens da OS e, lado a lado, de onde cada um veio (para gravar os vinculos).

    Ordem (D1e): moveis (por ambiente e ordem), a instalacao, as pecas embutidas.
    """
    por_movel = {mr.id: mr for amb in resultado.ambientes for mr in amb.moveis}
    itens: list[OSItemCreate] = []
    fontes: list[tuple[str, object]] = []                    # ("movel", movel) | ("instalacao", None) | ("peca", insumo)
    for ambiente, movel in _todos_os_moveis(orc):
        calc = por_movel.get(str(movel.id))
        if calc is None:                                    # movel fora da aprovacao
            continue
        itens.append(OSItemCreate(
            tipo=OrdemServicoItemTipo.SERVICO,              # comissao sobre a margem (C5)
            nome=_nome_item(movel.nome, ambiente.nome),
            unidade_medida=UnidadeMedida.UNIDADE,
            quantidade=movel.quantidade,
            valor_unitario=calc.preco_unit_centavos,         # preco de venda (F2)
            custo_unitario=calc.custo_os_unit_centavos,      # custo + parte do RT (C5d)
            status_aprovacao=OrdemServicoItemAprovacao.APROVADO,
            visivel_cliente=True,
        ))
        fontes.append(("movel", movel))
    if resultado.instalacao is not None:                     # D2
        itens.append(OSItemCreate(
            tipo=OrdemServicoItemTipo.SERVICO,
            nome=NOME_INSTALACAO,
            unidade_medida=UnidadeMedida.UNIDADE,
            quantidade=1,
            valor_unitario=resultado.instalacao.preco_centavos,
            custo_unitario=resultado.instalacao.custo_os_centavos,
            status_aprovacao=OrdemServicoItemAprovacao.APROVADO,
            visivel_cliente=True,
        ))
        fontes.append(("instalacao", None))
    for peca in pecas:                                       # D1a: pecas embutidas
        nome = peca.nome if len(peca.nome) >= 3 else f"{peca.nome} (insumo)"   # a OS pede 3 letras
        itens.append(OSItemCreate(
            tipo=OrdemServicoItemTipo.PRODUTO,
            item_id=peca.produto_id,                         # vira o produto_id do item
            nome=nome[:255],
            unidade_medida=_unidade_do_item(peca.unidade),
            quantidade=peca.sugerido_milesimos / 1000,       # o item da OS e Float, como o estoque
            valor_unitario=0,                                # o cliente paga na linha do movel
            custo_unitario=peca.custo_unitario_centavos,
            status_aprovacao=OrdemServicoItemAprovacao.APROVADO,
            visivel_cliente=False,                           # embutida: nao sai na via do cliente
        ))
        fontes.append(("peca", peca))
    return itens, fontes


def _pecas_embutidas(db: Session, orc: MarcenariaOrcamento) -> list[InsumoDaOS]:
    """Insumos dos moveis aprovados internos, um por produto, na ordem da separacao."""
    ids = sorted({
        i.produto_id for _a, m in _todos_os_moveis(orc)
        if m.aprovado and m.tipo_producao == "INTERNA" for i in m.insumos if i.produto_id
    })
    produtos = crud.buscar_por_ids(db, Produto, ids)          # uma consulta so
    unidades = {pid: p.unidade_medida or "UN" for pid, p in produtos.items()}
    localizacoes = {pid: p.localizacao_estoque or "" for pid, p in produtos.items()}
    return ordenar_para_a_os(insumos_da_os(orc, unidades), localizacoes)


def _erro_interno(mensagem: str):
    """500 que NUNCA deve acontecer (o endpoint desfaz tudo)."""
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=mensagem)


def aprovar(db: Session, orcamento_id: int, revisao: int, dados: AprovacaoEntrada, usuario_token: dict) -> int:
    """Aprova o orcamento (todo ou em parte) e cria a OS, numa transacao so.

    Devolve o id do orcamento. Qualquer erro sobe ANTES do commit e o endpoint
    desfaz tudo: nenhuma OS fica pela metade.
    """
    orc = carregar(db, orcamento_id)
    conferir_revisao(orc, revisao)
    if orc.status not in STATUS_APROVAVEIS:
        erros.transicao_invalida(orc.status)
    # D14: so uma versao do codigo pode estar aprovada.
    outra = next((v for v in crud.listar_versoes(db, orc.codigo)
                  if v.id != orc.id and v.status == StatusOrcamento.APROVADO), None)
    if outra is not None:
        erros.conflito("VERSAO_JA_APROVADA", f"A versão {outra.versao} deste orçamento já foi aprovada.")
    selecao = _selecao(orc, dados)
    if orc.funcionario_id is None:
        erros.invalido("Informe o vendedor do orçamento antes de aprovar.")      # D5

    if orc.status == StatusOrcamento.RASCUNHO:                # D13: fecha na loja, na hora
        exigir_completo_para_enviar(orc, verbo="aprovar")
        registrar_envio(db, orc, usuario_token)
    if dados.desconto is not None:                            # D11: renegociado
        orc.desconto_modo, orc.desconto_valor = dados.desconto.modo, dados.desconto.valor

    # D9: true/false em cada movel; a instalacao so entra se existe e foi escolhida.
    for _a, movel in _todos_os_moveis(orc):
        movel.aprovado = movel.id in selecao.movel_ids
    orc.instalacao_aprovada = bool(selecao.incluir_instalacao and orc.instalacao_custo_centavos is not None)

    resultado = calcular(montar_entrada_motor(orc, so_aprovados=True))   # D10 (422 com `campo`)
    sem_preco = _moveis_sem_preco(orc, resultado)
    if sem_preco:
        erros.invalido(f"O móvel {sem_preco[0]} está sem preço. Complete o móvel ou deixe-o de fora.")
    sinal = _resolver_sinal(dados.sinal, resultado)

    itens, fontes = _itens_da_os(orc, resultado, _pecas_embutidas(db, orc))
    os_criada = os_service.create_ordem_servico(
        db,
        OrdemServicoCreate(
            cliente_id=orc.cliente_id,
            funcionario_id=orc.funcionario_id,                  # responsavel = vendedor (O7)
            prioridade=OrdemServicoPrioridade.NORMAL,
            defeito_relatado=_descricao_os(orc),
            observacoes=(orc.observacoes_proposta or "")[:500] or None,
            dados_adicionais={"tipo_trabalho": "planejados"},   # 03A D9; vinculo NAO vai aqui (D7)
            objeto=_objeto_do_projeto(orc),
            itens=itens,
            desconto=resultado.desconto_centavos,               # C9
            valor_entrada=sinal.valor_entrada,                  # D15: so o recebido
            forma_pagamento_entrada_id=sinal.forma_pagamento_id,
            usar_credito_cliente=sinal.usar_credito,            # D16
            data_previsao=datetime.combine(_previsao(orc), time(0, 0)),
        ),
        origem_orcamento=True,                                  # 03A D7: o caminho legitimo
    )
    # D3: a OS confere com o motor (as pecas embutidas somam zero).
    if os_criada.valor_bruto != resultado.bruto_centavos or os_criada.valor_total != resultado.total_centavos:
        _erro_interno("A OS gerada não confere com o orçamento. Nada foi gravado.")

    # D7: vinculos so nas tabelas da marcenaria; a trava (origem) em cada item.
    itens_criados = sorted(os_criada.itens, key=lambda i: i.id)    # mesma ordem em que foram enviados
    if len(itens_criados) != len(fontes):
        _erro_interno("A OS gerada não confere com o orçamento. Nada foi gravado.")
    for item, (tipo, fonte) in zip(itens_criados, fontes):
        item.origem = ORIGEM
        if tipo == "movel":
            fonte.os_item_id = item.id

    orc.status = StatusOrcamento.APROVADO
    orc.data_aprovacao = agora_utc()
    orc.os_id = os_criada.id
    orc.objeto_id = os_criada.objeto_id                         # D6: o projeto do cliente
    orc.resumo_aprovado_total_centavos = resultado.total_centavos
    orc.resumo_aprovado_sinal_centavos = resultado.sinal_centavos
    orc.sinal_recebido_centavos = sinal.valor_entrada

    aprovados = [m.id for _a, m in _todos_os_moveis(orc) if m.aprovado]
    recusados = [m.id for _a, m in _todos_os_moveis(orc) if not m.aprovado]
    registrar_evento(
        db, orc, "ORCAMENTO_APROVADO",
        f"Aprovado: {os_criada.numero_os} com {len(aprovados)} móvel(is), total de {reais(resultado.total_centavos)}.",
        usuario_token,
        {
            "os_numero": os_criada.numero_os,
            "moveis_aprovados": aprovados,
            "moveis_recusados": recusados,
            "instalacao": orc.instalacao_aprovada,
            "total_centavos": resultado.total_centavos,
            "desconto_centavos": resultado.desconto_centavos,
            "sinal_combinado_centavos": resultado.sinal_centavos,
            "sinal_recebido_centavos": sinal.valor_entrada,
        },
        os_id=os_criada.id,
    )
    fechar_escrita(db, orc)
    return orc.id


# ===========================================================================
# DESFAZER (D20). As regras que impedem estao em aprovacao_bloqueios.py
# (o detalhe tambem usa, para montar `acoes.desfazer_aprovacao`).
# ===========================================================================

def desfazer_aprovacao(db: Session, orcamento_id: int, revisao: int, dados: DesfazerEntrada, usuario_token: dict) -> None:
    """Cancela a OS pelas regras de sempre (PIN, credito) e volta o orcamento a ENVIADO.

    Os itens da OS cancelada continuam com `origem`: mostram de onde vieram, e
    a OS cancelada nao se edita mesmo.
    """
    orc = carregar(db, orcamento_id)
    conferir_revisao(orc, revisao)
    if orc.status != StatusOrcamento.APROVADO:
        erros.transicao_invalida(orc.status)
    motivos = motivos_que_impedem_desfazer(db, orc)
    if motivos:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
            "codigo": "DESFAZER_BLOQUEADO",
            "mensagem": "Não é possível desfazer a aprovação.",
            "motivos": motivos,
        })

    os_ = orc.os
    numero_os, os_id, sinal = os_.numero_os, os_.id, os_.valor_entrada or 0
    os_service.cancelar_ordem_servico(                          # PIN, credito e cobranca como sempre
        db, numero_os,
        OrdemServicoCancelar(
            motivo=f"Aprovação desfeita no orçamento {orc.codigo}: {dados.motivo}",
            zerar_adiantamento=(dados.destino_sinal == "DEVOLVIDO"),
            codigo_gerente=dados.codigo_gerente,
        ),
        usuario_token=usuario_token,
    )

    for _a, movel in _todos_os_moveis(orc):
        movel.aprovado, movel.os_item_id = None, None
    orc.os_id = None
    orc.data_aprovacao = None
    orc.instalacao_aprovada = None
    orc.resumo_aprovado_total_centavos = None
    orc.resumo_aprovado_sinal_centavos = None
    orc.sinal_recebido_centavos = None
    destino = "crédito do cliente" if dados.destino_sinal == "CREDITO" else "devolvido ao cliente"
    registrar_evento(
        db, orc, "APROVACAO_DESFEITA",
        f"Aprovação desfeita ({numero_os} cancelada): {dados.motivo}",
        usuario_token,
        {"motivo": dados.motivo, "os_numero": numero_os, "sinal_centavos": sinal,
         "destino_sinal": dados.destino_sinal if sinal else None, "destino_texto": destino if sinal else None},
        os_id=os_id,
    )
    # Volta a ENVIADO. Se a validade ja passou, a regra preguicosa da 06A (D14)
    # o marca VENCIDO na proxima leitura -- que e a resposta desta mesma chamada.
    orc.status = StatusOrcamento.ENVIADO
    fechar_escrita(db, orc)


# ===========================================================================
# RESUMO A PARTIR DA OS (Revisao 1): a aba "Orcamento" da OS
# ===========================================================================

def resumo_por_os(db: Session, numero_os: str) -> dict:
    """O que foi vendido, para quem trabalha na OS. NUNCA traz custo, margem ou RT."""
    exigir_orcamento_tecnico(db)
    os_ = os_crud.get_ordem_servico_by_numero_os(db, numero_os)
    orc = crud.get_orcamento_por_os(db, os_.id) if os_ is not None else None
    if orc is None:
        erros.nao_encontrado("Esta OS não veio de um orçamento.")

    aprovado_por = next(
        (ev.usuario_nome for ev in crud_evento.listar_eventos_do_codigo(db, orc.codigo)
         if ev.tipo == "ORCAMENTO_APROVADO" and ev.os_id == os_.id),
        None,
    )
    moveis = [
        {
            "nome": m.nome, "ambiente": a.nome, "quantidade": m.quantidade,
            "medidas": {"largura_mm": m.largura_mm, "altura_mm": m.altura_mm, "profundidade_mm": m.profundidade_mm},
            "os_item_id": m.os_item_id,
        }
        for a, m in _todos_os_moveis(orc) if m.aprovado
    ]
    motivos = motivos_que_impedem_desfazer(db, orc)
    return {
        "orcamento_id": orc.id,
        "codigo": orc.codigo,
        "versao": orc.versao,
        "status": orc.status,
        "data_aprovacao": orc.data_aprovacao,
        "aprovado_por": aprovado_por,
        "projeto": orc.projeto_nome,
        "moveis": moveis,
        "moveis_nao_aprovados": sum(1 for _a, m in _todos_os_moveis(orc) if m.aprovado is False),
        "instalacao_aprovada": orc.instalacao_aprovada,
        "total_aprovado_centavos": orc.resumo_aprovado_total_centavos,
        "sinal_combinado_centavos": orc.resumo_aprovado_sinal_centavos,
        # Lido da OS: o adiantamento lancado DEPOIS na OS aparece aqui.
        "sinal_recebido_centavos": os_.valor_entrada or 0,
        "pode_desfazer": not motivos,
        "motivos_desfazer": motivos,
    }
