# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/aditivo.py
# DESCRICAO: ADITIVO do orcamento de marcenaria (remodelacao item 20): um
#            orcamento de moveis A MAIS para uma OS que ja existe.
# ---------------------------------------------------------------------------
"""
O cliente aprovou o projeto, a OS esta rodando, e ele pede mais um movel. Em
vez de desfazer a aprovacao (o que exige a OS parada) ou abrir outra OS para a
mesma obra, a loja faz um ADITIVO:

- nasce da aba "Orcamento" da OS, ja com o cliente, o vendedor, o projeto, o
  endereco da obra, os parametros de preco e os arquitetos do orcamento que
  gerou a OS -- e SEM moveis;
- e editado, enviado (proposta) e aprovado como qualquer orcamento;
- ao aprovar, os moveis SOMAM na mesma OS (itens, material, etapas de
  producao, entregas), em vez de criar outra (ver `aprovar_aditivo`);
- o desfazer devolve a OS ao que era antes dele, se nada dele comecou.

O aditivo tem codigo proprio (ORC-...) e o campo `aditivo_os_id` aponta a OS.
"""

from datetime import datetime, time
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enum import OrdemServicoItemAprovacao, OrdemServicoItemTipo
from app.core.regras_preco import reais
from app.db.crud import ordem_servico as os_crud
from app.db.crud.marcenaria import orcamento as crud
from app.db.models.marcenaria.orcamento import MarcenariaOrcamento, MarcenariaOrcamentoRT, StatusOrcamento
from app.db.models.ordem_servico_item import OrdemServicoItem
from app.services.marcenaria import erros
from app.services.marcenaria.orcamento_comum import (
    exigir_orcamento_tecnico,
    os_aberta,
    registrar_evento,
)

# Frases e codigos de erro do aditivo.
MSG_OS_SEM_ORCAMENTO = "Esta OS não veio de um orçamento aprovado: não há o que aditar."
MSG_OS_FECHADA = "A OS está finalizada ou cancelada: não recebe aditivo."
OS_FECHADA = "OS_FECHADA"


def _os_com_orcamento(db: Session, numero_os: str):
    """(OS, orcamento PRINCIPAL aprovado) ou 404; 409 se a OS ja fechou."""
    os_ = os_crud.get_ordem_servico_by_numero_os(db, numero_os)
    principal = crud.get_orcamento_por_os(db, os_.id) if os_ is not None and os_.ativo else None
    if principal is None or principal.status != StatusOrcamento.APROVADO:
        erros.nao_encontrado(MSG_OS_SEM_ORCAMENTO)
    if not os_aberta(os_):
        erros.conflito(OS_FECHADA, MSG_OS_FECHADA)
    return os_, principal


def criar_aditivo(db: Session, numero_os: str, usuario_token: dict) -> int:
    """POST /marcenaria/orcamentos/os/{numero_os}/aditivos: o aditivo em RASCUNHO.

    Copia do orcamento que gerou a OS: cliente, vendedor, projeto (o objeto da
    OS), endereco da obra, parametros de preco, validade, prazo e arquitetos.
    Moveis, instalacao, desconto e sinal comecam vazios: e o que a mais.
    Devolve o id do aditivo.
    """
    # Import aqui: `orcamento` importa este modulo indiretamente pelo detalhe.
    from app.services.marcenaria.orcamento import proximo_codigo

    exigir_orcamento_tecnico(db)
    os_, principal = _os_com_orcamento(db, numero_os)

    for tentativa in (1, 2):
        try:
            aditivo = MarcenariaOrcamento(
                codigo=proximo_codigo(db),
                versao=1,
                status=StatusOrcamento.RASCUNHO,
                revisao=1,
                aditivo_os_id=os_.id,                               # de qual OS ele e
                cliente_id=principal.cliente_id,
                funcionario_id=principal.funcionario_id,
                objeto_id=os_.objeto_id or principal.objeto_id,     # o projeto da OS (PRJ-...)
                projeto_nome=principal.projeto_nome,
                endereco_obra=principal.endereco_obra,
                # --- parametros do orcamento da OS (nao os da configuracao de hoje) ---
                markup_bp=principal.markup_bp,
                perda_bp=principal.perda_bp,
                custo_hora_centavos=principal.custo_hora_centavos,
                rt_padrao_bp=principal.rt_padrao_bp,
                rt_modo=principal.rt_modo,
                validade_dias=principal.validade_dias,
                prazo_entrega_dias=principal.prazo_entrega_dias,
            )
            # Os mesmos arquitetos, com o mesmo %: o RT do aditivo e do mesmo indicador.
            aditivo.rts = [MarcenariaOrcamentoRT(fornecedor_id=rt.fornecedor_id, rt_bp=rt.rt_bp) for rt in principal.rts]
            db.add(aditivo)
            db.flush()                                              # aqui o unico (codigo, versao) pode bater
            dados = {"os_numero": os_.numero_os, "aditivo": aditivo.codigo, "orcamento": principal.codigo}
            registrar_evento(db, aditivo, "ADITIVO_CRIADO",
                             f"Aditivo da {os_.numero_os} (orçamento {principal.codigo}).", usuario_token, dados,
                             os_id=os_.id)
            registrar_evento(db, principal, "ADITIVO_CRIADO",
                             f"Aditivo {aditivo.codigo} criado para a {os_.numero_os}.", usuario_token, dados,
                             os_id=os_.id)
            db.commit()
            return aditivo.id
        except IntegrityError:
            db.rollback()                                           # outro computador pegou o numero
            if tentativa == 2:
                raise
    raise RuntimeError("inalcancavel")


# ===========================================================================
# APROVAR: os moveis do aditivo SOMAM na OS que ja existe
# ===========================================================================

def _os_do_aditivo(db: Session, orc: MarcenariaOrcamento):
    """A OS do aditivo, aberta, com o orcamento principal ainda aprovado nela."""
    from app.db.models.ordem_servico import OrdemServico

    os_ = db.get(OrdemServico, orc.aditivo_os_id)
    principal = crud.get_orcamento_por_os(db, os_.id) if os_ is not None and os_.ativo else None
    if principal is None or principal.status != StatusOrcamento.APROVADO:
        erros.conflito("OS_SEM_ORCAMENTO", "A aprovação do orçamento desta OS foi desfeita: o aditivo não tem onde somar.")
    if not os_aberta(os_):
        erros.conflito(OS_FECHADA, MSG_OS_FECHADA)
    return os_, principal


def _sugeridos(db: Session, vista) -> dict[int, "object"]:
    """{produto_id: InsumoDaOS} do material da vista (principal + aditivos que ela tiver)."""
    from app.db.models.produto import Produto
    from app.services.marcenaria.insumos_os import insumos_da_os

    ids = sorted({i.produto_id for a in vista.ambientes for m in a.moveis
                  if m.aprovado and m.tipo_producao == "INTERNA" for i in m.insumos if i.produto_id})
    produtos = crud.buscar_por_ids(db, Produto, ids)
    unidades = {pid: p.unidade_medida or "UN" for pid, p in produtos.items()}
    return {p.produto_id: p for p in insumos_da_os(vista, unidades)}


def _item_de_peca(os_, produto_id: int) -> Optional[OrdemServicoItem]:
    """A peca embutida da OS para este produto (uma por produto, como na aprovacao)."""
    from app.services.marcenaria.aprovacao import ORIGEM

    return next((i for i in os_.itens if i.origem == ORIGEM and i.tipo == OrdemServicoItemTipo.PRODUTO
                 and i.produto_id == produto_id), None)


def aprovar_aditivo(db: Session, orc: MarcenariaOrcamento, resultado, sinal, usuario_token: dict) -> None:
    """Soma o aditivo aprovado na OS (chamado por `aprovacao.aprovar`, sem commit).

    - Moveis e instalacao: itens de SERVICO novos, travados (`origem`), como os
      da aprovacao normal.
    - Material: a peca embutida de cada produto cresce o que o SUGERIDO da OS
      cresceu (o sugerido e arredondado por produto: 3,2 + 0,5 chapa = 3,7 -> 4,
      o mesmo das 4 que ja havia; nada a somar). Produto novo vira peca nova.
    - Desconto do aditivo soma ao da OS; o sinal RECEBIDO soma a entrada.
    - Etapas de producao e entregas para os moveis e ambientes do aditivo.
    O que mudou fica no evento ADITIVO_APROVADO: e com ele que o desfazer volta.
    """
    from app.core.tempo import agora_utc
    from app.db.models.cliente import Cliente
    from app.services import ordem_servico as os_service
    from app.services.marcenaria.aprovacao import ORIGEM, _erro_interno, _itens_da_os, _previsao, _todos_os_moveis
    from app.services.marcenaria.entrega import criar_entregas_da_aprovacao
    from app.services.marcenaria.orcamento_comum import OrcamentosDaOS
    from app.services.marcenaria.producao import criar_etapas_da_aprovacao

    os_, principal = _os_do_aditivo(db, orc)
    aprovados_antes = crud.listar_aditivos_da_os(db, os_.id, so_aprovados=True)

    # --- 1. Material: quanto o sugerido de cada produto cresce com este aditivo ---
    antes = _sugeridos(db, OrcamentosDaOS(principal, aprovados_antes))
    depois = _sugeridos(db, OrcamentosDaOS(principal, [*aprovados_antes, orc]))
    pecas: dict[str, int] = {}                                   # {produto_id: milesimos a mais}
    for pid, insumo in depois.items():
        delta = insumo.sugerido_milesimos - (antes[pid].sugerido_milesimos if pid in antes else 0)
        if delta <= 0:
            continue                                             # o arredondamento ja cobria
        pecas[str(pid)] = delta
        item = _item_de_peca(os_, pid)
        if item is None:                                         # produto novo na OS
            nome = insumo.nome if len(insumo.nome) >= 3 else f"{insumo.nome} (insumo)"
            item = OrdemServicoItem(
                ordem_servico_id=os_.id, tipo=OrdemServicoItemTipo.PRODUTO, produto_id=pid,
                nome=nome[:255], unidade_medida=_unidade(insumo.unidade), quantidade=delta / 1000,
                valor_unitario=0, valor_total=0, custo_unitario=insumo.custo_unitario_centavos,
                status_aprovacao=OrdemServicoItemAprovacao.APROVADO, visivel_cliente=False, origem=ORIGEM,
            )
            os_crud.create_os_item(db, item_to_add=item)
        elif item.status_aprovacao == OrdemServicoItemAprovacao.REPROVADO:
            # Estava "nao usado" nesta OS: o aditivo volta a usar (so o que ele pede).
            item.status_aprovacao = OrdemServicoItemAprovacao.APROVADO
            item.quantidade = round(max(delta / 1000, item.quantidade_separada or 0), 3)
        else:
            item.quantidade = round((item.quantidade or 0) + delta / 1000, 3)

    # --- 2. Moveis e instalacao: itens novos, travados como os da aprovacao ---
    bruto_antes = os_.valor_bruto or 0
    itens, fontes = _itens_da_os(orc, resultado, [])             # sem pecas: elas foram acima
    itens_novos = []
    for dados_item, (tipo, fonte) in zip(itens, fontes):
        novo = OrdemServicoItem(
            **dados_item.model_dump(exclude={"item_id"}, exclude_unset=True),
            ordem_servico_id=os_.id,
            valor_total=round(dados_item.quantidade * dados_item.valor_unitario),
            origem=ORIGEM,
        )
        os_crud.create_os_item(db, item_to_add=novo)            # flush: o item ganha id
        itens_novos.append(novo.id)
        if tipo == "movel":
            fonte.os_item_id = novo.id

    # --- 3. Desconto, totais e conferencia ---
    os_.desconto = (os_.desconto or 0) + resultado.desconto_centavos
    db.flush()
    db.refresh(os_)                                              # a lista de itens com os novos
    os_service.recalcular_totais(os_)
    if (os_.valor_bruto or 0) - bruto_antes != resultado.bruto_centavos:
        _erro_interno("A OS não confere com o aditivo. Nada foi gravado.")

    # --- 4. Sinal recebido: soma a entrada da OS (uma forma de pagamento so) ---
    if sinal.valor_entrada > 0:
        ja = os_.valor_entrada or 0
        if ja > 0 and os_.forma_pagamento_entrada_id != sinal.forma_pagamento_id:
            erros.invalido("A OS já tem um sinal em outra forma de pagamento. Aprove o aditivo sem o sinal "
                           "e registre o pagamento do aditivo na OS.")
        if sinal.usar_credito:
            cliente = db.get(Cliente, os_.cliente_id)
            if cliente is None or (cliente.saldo_credito or 0) < sinal.valor_entrada:
                erros.invalido("O cliente não tem crédito suficiente para o sinal do aditivo.")
            cliente.saldo_credito = (cliente.saldo_credito or 0) - sinal.valor_entrada
        os_.valor_entrada = ja + sinal.valor_entrada
        os_.forma_pagamento_entrada_id = sinal.forma_pagamento_id

    # A previsao de entrega da OS so anda para a frente (o aditivo pode pedir mais prazo).
    previsao = datetime.combine(_previsao(orc), time(0, 0))
    if os_.data_previsao is None or os_.data_previsao < previsao:
        os_.data_previsao = previsao

    # --- 5. O aditivo fica aprovado nesta OS ---
    orc.status = StatusOrcamento.APROVADO
    orc.data_aprovacao = agora_utc()
    orc.os_id = os_.id
    orc.objeto_id = os_.objeto_id
    orc.resumo_aprovado_total_centavos = resultado.total_centavos
    orc.resumo_aprovado_sinal_centavos = resultado.sinal_centavos
    orc.sinal_recebido_centavos = sinal.valor_entrada
    criar_etapas_da_aprovacao(db, orc)                           # 12A: etapas dos moveis internos
    criar_entregas_da_aprovacao(db, orc, os_.id)                 # 13A: uma entrega por ambiente

    aprovados = [m.id for _a, m in _todos_os_moveis(orc) if m.aprovado]
    dados = {
        "os_numero": os_.numero_os, "aditivo": orc.codigo, "orcamento": principal.codigo,
        "moveis_aprovados": aprovados, "instalacao": orc.instalacao_aprovada,
        "total_centavos": resultado.total_centavos, "desconto_centavos": resultado.desconto_centavos,
        "sinal_recebido_centavos": sinal.valor_entrada,
        # Para o desfazer voltar a OS exatamente ao que era:
        "itens_novos": itens_novos, "pecas": pecas,
    }
    frase = (f"Aditivo aprovado: {len(aprovados)} móvel(is) somados na {os_.numero_os}, "
             f"total de {reais(resultado.total_centavos)}.")
    registrar_evento(db, orc, "ADITIVO_APROVADO", frase, usuario_token, dados, os_id=os_.id)
    registrar_evento(db, principal, "ADITIVO_APROVADO", f"{orc.codigo}: {frase}", usuario_token, dados, os_id=os_.id)


def _unidade(unidade: str):
    """A unidade do item da OS (enum) a partir da do produto (texto livre)."""
    from app.services.marcenaria.aprovacao import _unidade_do_item

    return _unidade_do_item(unidade)


# ===========================================================================
# DESFAZER: a OS volta ao que era antes do aditivo
# ===========================================================================

def _evento_da_aprovacao(db: Session, orc: MarcenariaOrcamento) -> dict:
    """Os `dados` do ADITIVO_APROVADO desta versao: o que a aprovacao mudou na OS."""
    from app.db.crud.marcenaria import evento as crud_evento

    evento = next((e for e in crud_evento.listar_eventos_do_codigo(db, orc.codigo)
                   if e.tipo == "ADITIVO_APROVADO" and e.orcamento_id == orc.id), None)
    return dict(evento.dados or {}) if evento is not None else {}


def motivos_do_aditivo(db: Session, orc: MarcenariaOrcamento) -> list[str]:
    """O que impede desfazer o ADITIVO (todos os motivos, para a tela explicar de uma vez).

    Diferente do orcamento principal, a OS NAO precisa estar parada: ela segue
    com o resto da obra. So nao pode ter comecado nada DO ADITIVO.
    """
    from app.db.models.marcenaria.entrega import MarcenariaEntrega, SituacaoEntrega
    from app.db.models.produto import Produto
    from app.services.marcenaria.aprovacao_bloqueios import _bloqueio_pedido_a_central, _bloqueio_producao

    if orc.status != StatusOrcamento.APROVADO or orc.os is None:
        return ["O orçamento não está aprovado."]
    os_ = orc.os
    if not os_aberta(os_):
        return ["A OS está finalizada ou cancelada."]
    motivos = []
    if os_.pagamentos:
        motivos.append("A OS já tem pagamento registrado.")
    # Material: tirar o que o aditivo somou nao pode deixar a OS com menos do que ja saiu.
    pecas = _evento_da_aprovacao(db, orc).get("pecas", {})
    retirados = []
    for pid, delta in pecas.items():
        item = _item_de_peca(os_, int(pid))
        if item is not None and round((item.quantidade or 0) - delta / 1000, 3) < (item.quantidade_separada or 0):
            produto = db.get(Produto, int(pid))
            retirados.append(produto.nome if produto else item.nome)
    if retirados:
        motivos.append(f"Já há material deste aditivo retirado do estoque ({', '.join(retirados)}). "
                       "Devolva o material ao estoque antes de desfazer.")
    motivos += _bloqueio_pedido_a_central(db, orc)          # pedido a central dos moveis DELE
    motivos += _bloqueio_producao(db, orc)                  # etapas dos moveis DELE
    ambientes = {a.id for a in orc.ambientes}
    entregues = [e for e in db.query(MarcenariaEntrega).filter(MarcenariaEntrega.os_id == os_.id).all()
                 if e.ambiente_id in ambientes and e.situacao != SituacaoEntrega.PENDENTE]
    if entregues:
        motivos.append(f"Já há entrega registrada ({', '.join(e.ambiente.nome for e in entregues)}).")
    return motivos


def desfazer_aditivo(db: Session, orc: MarcenariaOrcamento, dados, usuario_token: dict) -> None:
    """Tira da OS o que o aditivo somou e volta o aditivo a ENVIADO (sem commit).

    A OS NAO e cancelada: ela continua com o orcamento principal (e os outros
    aditivos). O sinal recebido do aditivo sai da entrada da OS e vira credito
    do cliente, ou foi devolvido (`destino_sinal`).
    """
    from fastapi import HTTPException, status as http
    from app.db.models.cliente import Cliente
    from app.db.models.marcenaria.entrega import MarcenariaEntrega
    from app.services import ordem_servico as os_service
    from app.services.marcenaria.aprovacao import _todos_os_moveis
    from app.services.marcenaria.producao import apagar_etapas_do_desfazer

    motivos = motivos_do_aditivo(db, orc)
    if motivos:
        raise HTTPException(status_code=http.HTTP_409_CONFLICT, detail={
            "codigo": "DESFAZER_BLOQUEADO", "mensagem": "Não é possível desfazer a aprovação.", "motivos": motivos,
        })
    os_ = orc.os
    aprovacao = _evento_da_aprovacao(db, orc)

    # Itens de servico que o aditivo criou (moveis e instalacao): saem.
    for item in [i for i in os_.itens if i.id in set(aprovacao.get("itens_novos", []))]:
        os_crud.delete_os_item(db, item_to_delete=item)
    # Material: cada peca volta ao que era (a que nasceu com o aditivo, some).
    for pid, delta in aprovacao.get("pecas", {}).items():
        item = _item_de_peca(os_, int(pid))
        if item is None:
            continue
        restante = round((item.quantidade or 0) - delta / 1000, 3)
        if restante > 0:
            item.quantidade = restante
        elif not item.quantidade_separada:
            os_crud.delete_os_item(db, item_to_delete=item)
    # Desconto e sinal do aditivo saem da OS.
    os_.desconto = max(0, (os_.desconto or 0) - int(aprovacao.get("desconto_centavos", 0)))
    sinal = orc.sinal_recebido_centavos or 0
    if sinal:
        os_.valor_entrada = max(0, (os_.valor_entrada or 0) - sinal)
        if not os_.valor_entrada:
            os_.forma_pagamento_entrada_id = None
        if dados.destino_sinal == "CREDITO":
            cliente = db.get(Cliente, os_.cliente_id)
            if cliente is not None:
                cliente.saldo_credito = (cliente.saldo_credito or 0) + sinal
    db.flush()
    db.refresh(os_)
    os_service.recalcular_totais(os_)

    # Entregas (todas pendentes) e etapas (todas pendentes) do aditivo saem.
    ambientes = {a.id for a in orc.ambientes}
    for entrega in db.query(MarcenariaEntrega).filter(MarcenariaEntrega.os_id == os_.id).all():
        if entrega.ambiente_id in ambientes:
            db.delete(entrega)
    apagar_etapas_do_desfazer(orc)
    for _a, movel in _todos_os_moveis(orc):
        movel.aprovado, movel.os_item_id = None, None

    numero_os, os_id = os_.numero_os, os_.id
    orc.os_id = None
    orc.data_aprovacao = None
    orc.instalacao_aprovada = None
    orc.resumo_aprovado_total_centavos = None
    orc.resumo_aprovado_sinal_centavos = None
    orc.sinal_recebido_centavos = None
    orc.status = StatusOrcamento.ENVIADO
    destino = {"CREDITO": "virou crédito do cliente", "DEVOLVIDO": "foi devolvido ao cliente"}[dados.destino_sinal]
    frase = f"Aprovação do aditivo desfeita (saiu da {numero_os}): {dados.motivo}"
    info = {"motivo": dados.motivo, "os_numero": numero_os, "aditivo": orc.codigo,
            "sinal_centavos": sinal, "destino_sinal": dados.destino_sinal if sinal else None,
            "destino_texto": destino if sinal else None}
    registrar_evento(db, orc, "APROVACAO_DESFEITA", frase, usuario_token, info, os_id=os_id)
    principal = crud.get_orcamento_por_os(db, os_id)
    if principal is not None:
        registrar_evento(db, principal, "ADITIVO_DESFEITO", f"{orc.codigo}: {frase}", usuario_token, info, os_id=os_id)
