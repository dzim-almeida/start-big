# ---------------------------------------------------------------------------
# ARQUIVO: services/ordem_servico/status.py
# DESCRICAO: Ordem de servico - finalizar, cancelar e reabrir.
# ---------------------------------------------------------------------------

from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.ordem_servico import (
    OrdemServicoFinalizar,
    OrdemServicoCancelar,
)
from app.db.models.ordem_servico import OrdemServico as OSModel
from app.db.models.ordem_servico_pagamento import OrdemServicoPagamento as OSPagamentoModel
from app.db.crud import ordem_servico as os_crud
from app.db.crud import forma_pagamento as fp_crud
from app.db.crud.configuracao import seguranca as config_seg_crud
from app.services.fabrica import trilho as trilho_fabrica
from app.services.ordem_servico import ganchos as ganchos_os   # Spec 09A: quem reage ao ciclo da OS
from app.core.enum import (
    OrdemServicoStatus,
    SituacaoEquipamento,
)
from app.core.security import verify_password
from app.services.ordem_servico.estoque import _movimentar_estoque_os
from app.services.ordem_servico.excecoes import forma_pagamento_not_found_exce, os_nao_pode_reabrir_exce, pagamento_valor_invalido_exce
from app.services.ordem_servico.regras import _assert_os_editavel, _assert_sem_itens_pendentes, _get_os_or_raise, _recalcular_valor_total_os


# ===========================================================================
# AÇÕES DE STATUS
# ===========================================================================

def finalizar_ordem_servico(
    db: Session,
    numero_os: str,
    data: OrdemServicoFinalizar,
    usuario_token: dict | None = None,
) -> OSModel:
    """
    Finaliza uma OS registrando a solução e os pagamentos.

    Regras de negócio:
    1. OS não pode estar FINALIZADA ou CANCELADA.
    2. Se desconto for informado, recalcula valor_total antes da validação.
    3. A soma dos pagamentos deve ser exatamente igual ao valor_total.
    4. Cada forma_pagamento_id deve existir e estar ativa no catálogo.
    5. Status → FINALIZADA, data_finalizacao → now().
    6. Nenhum item pode estar PENDENTE (aguardando resposta do cliente).
    """
    os_in_db = _get_os_or_raise(db, numero_os)
    _assert_os_editavel(os_in_db)
    _assert_sem_itens_pendentes(os_in_db)
    # Marcenaria-fábrica com etapas travadas: só entrega depois da vistoria.
    trilho_fabrica.assert_pode_finalizar(db, os_in_db)

    # Aplica campos financeiros se informados
    if data.desconto is not None:
        # Acumula desconto de todas as finalizações (não sobrescreve) — mesmo padrão do acrescimo
        os_in_db.desconto = (os_in_db.desconto or 0) + data.desconto
    if data.valor_entrada is not None:
        os_in_db.valor_entrada = data.valor_entrada
        # Adiantamento zerado nao pode manter forma de pagamento pendurada:
        # sobraria "pago em PIX" sem valor algum por tras.
        if data.valor_entrada == 0:
            os_in_db.forma_pagamento_entrada_id = None
    if data.taxa_entrega is not None:
        os_in_db.taxa_entrega = data.taxa_entrega
    if data.acrescimo is not None:
        # Acumula juros de todas as finalizações (não sobrescreve) para preservar histórico
        os_in_db.acrescimo = (os_in_db.acrescimo or 0) + data.acrescimo

    # Recalcula valor_total com todos os campos financeiros atualizados
    _recalcular_valor_total_os(os_in_db)

    # Valida valor total: tudo que já entrou + o que entra agora >= valor_total.
    #
    # O recebido é uma SOMA EXATA de três lugares que não se sobrepõem:
    #   pagamentos               -- todos, de todas as sessões (nunca se apagam
    #                               numa reabertura "pagou")
    #   adiantamentos_anteriores -- os `valor_entrada` das sessões anteriores,
    #                               dobrados ali a cada reabertura
    #   valor_entrada            -- o adiantamento desta sessão
    #
    # A conta antiga tentava DERIVAR os pagamentos novos como
    # `pagamentos - credito_anterior`, com `max(0, ...)`. Como o crédito
    # continha o adiantamento antigo, a subtração engolia o pagamento novo
    # quando ele era menor que aquele adiantamento -- e a OS exigia pagar de
    # novo. `credito_anterior` fica só para a tela.
    recebido_antes = (
        sum(p.valor for p in os_in_db.pagamentos)
        + (os_in_db.adiantamentos_anteriores or 0)
    )
    total_novos = sum(p.valor for p in data.pagamentos)
    valor_entrada = os_in_db.valor_entrada or 0
    situacao_sem_cobranca = data.situacao_equipamento in (
        SituacaoEquipamento.SEM_REPARO, SituacaoEquipamento.CONDENADO
    )
    if not situacao_sem_cobranca:
        if (recebido_antes + valor_entrada + total_novos) < os_in_db.valor_total:
            raise pagamento_valor_invalido_exce

    # Valida e cria cada pagamento
    pagamentos_criados = []
    for pagamento_data in data.pagamentos:
        forma_pagamento = fp_crud.get_forma_pagamento_by_id(db, fp_id=pagamento_data.forma_pagamento_id)
        if not forma_pagamento or not forma_pagamento.ativo:
            raise forma_pagamento_not_found_exce

        pagamento = OSPagamentoModel(
            ordem_servico_id=os_in_db.id,
            forma_pagamento_id=pagamento_data.forma_pagamento_id,
            valor=pagamento_data.valor,
            juros_valor=pagamento_data.juros_valor,
            juros_responsavel=pagamento_data.juros_responsavel.value,
            parcelas=pagamento_data.parcelas,
            bandeira_cartao=pagamento_data.bandeira_cartao,
            vencimento=pagamento_data.vencimento,
            detalhes=pagamento_data.detalhes,
        )
        os_crud.create_os_pagamento(db, pagamento_to_add=pagamento)
        # Guarda só os desta finalização: `os_in_db.pagamentos` traz também os
        # de finalizações anteriores, e relançá-los duplicaria dinheiro no livro.
        pagamentos_criados.append(pagamento)

    # Para SEM_REPARO / CONDENADO: trata o excedente do adiantamento (entrada - total cobrado)
    if situacao_sem_cobranca and (os_in_db.valor_entrada or 0) > 0:
        excedente = max(0, (os_in_db.valor_entrada or 0) - (os_in_db.valor_total or 0))
        if excedente > 0 and not data.zerar_adiantamento:
            cliente = os_in_db.equipamento.cliente if os_in_db.equipamento else None
            if cliente:
                cliente.saldo_credito = (cliente.saldo_credito or 0) + excedente

    # Baixa das peças aplicadas. Vai aqui, junto da mudança de status, para que
    # a OS só consuma estoque quando de fato fecha — e para que reabrir devolva.
    _movimentar_estoque_os(db, os_in_db, saida=True, usuario_token=usuario_token)

    # O dinheiro entra no livro junto com a peça saindo do estoque, e pelo mesmo
    # motivo: é neste instante que a OS fecha. Sem isto o fechamento de caixa
    # somava a origem ORDEM_SERVICO que ninguém escrevia, e a gaveta de uma loja
    # com caixa ligado fechava com sobra todo dia.
    # ANTES de lancar: o vencimento que a FORMA declarou. Cartao com prazo nao
    # entra na gaveta hoje -- so em D+n, quando a operadora deposita.
    from app.services.financeiro import promessas as financeiro_receber_service
    financeiro_receber_service.aplicar_prazo_de_recebimento(db, pagamentos_criados)

    from app.services import sessao_caixa as caixa_service
    caixa_service.registrar_pagamentos_de_os(
        db,
        os_in_db,
        pagamentos_criados,
        operador_funcionario_id=(usuario_token or {}).get("funcionario_id"),
    )

    # E o que NÃO entrou na gaveta por ser promessa vira conta a receber. Roda
    # com o caixa ligado ou desligado — fiado é fiado em qualquer loja.
    financeiro_receber_service.registrar_promessas_de_os(db, os_in_db, pagamentos_criados)

    # Aplica finalização
    os_in_db.situacao_equipamento = data.situacao_equipamento
    os_in_db.garantia = data.garantia
    os_in_db.solucao = data.solucao
    os_in_db.status = OrdemServicoStatus.FINALIZADA
    # UTC, não hora local. Todo o resto do sistema grava em UTC (func.now()) e os
    # filtros de período do dashboard/relatórios comparam em UTC. Com hora local
    # (UTC-3), uma OS finalizada depois das 21h caía no dia seguinte pela régua
    # do relatório — e desde que o faturamento passou a ancorar em
    # data_finalizacao, isso virou dinheiro no dia errado.
    os_in_db.data_finalizacao = datetime.utcnow()
    trilho_fabrica.ao_finalizar(db, os_in_db, (usuario_token or {}).get("nome") or "Sistema")
    # Quem reage a finalizacao (ex.: conta do RT do arquiteto, Spec 09A da
    # marcenaria). Lista vazia = nada muda. Falha aqui desfaz a finalizacao.
    ganchos_os.disparar(ganchos_os.ao_finalizar, db, os_in_db, usuario_token)

    if data.observacoes:
        os_in_db.observacoes = data.observacoes

    return os_crud.update_ordem_servico(db, os_to_update=os_in_db)


def cancelar_ordem_servico(
    db: Session,
    numero_os: str,
    data: OrdemServicoCancelar,
    usuario_token: dict | None = None,
) -> OSModel:
    """
    Cancela uma OS.

    O motivo, se informado, é acrescentado ao campo observações.
    Restrição: OS já CANCELADA não pode ser cancelada novamente.
    """
    os_in_db = _get_os_or_raise(db, numero_os)

    if os_in_db.status == OrdemServicoStatus.CANCELADA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta OS já está cancelada"
        )

    if os_in_db.funcionario:
        empresa_id = os_in_db.funcionario.empresa_id
        config_seg = config_seg_crud.get_configuracao_seguranca(db, empresa_id=empresa_id)
        if config_seg and config_seg.requer_pin_cancelar_os and config_seg.pin_gerente:
            if not data.codigo_gerente:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="REQUER_APROVACAO_GERENTE")
            if not verify_password(data.codigo_gerente, config_seg.pin_gerente):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PIN_GERENTE_INVALIDO")

    # Só devolve peça ao estoque se ela chegou a sair — ou seja, se a OS estava
    # FINALIZADA. Cancelar uma OS que nunca foi finalizada não movimenta nada;
    # estornar aqui inventaria estoque que nunca saiu.
    if os_in_db.status == OrdemServicoStatus.FINALIZADA:
        _movimentar_estoque_os(db, os_in_db, saida=False, usuario_token=usuario_token)

    from app.services.financeiro import promessas as financeiro_receber_service

    # A COBRANÇA MORRE COM A OS. Cancelar mexia no estoque e no livro do
    # dinheiro, mas deixava a conta a receber PENDENTE para sempre -- a loja
    # seguia esperando um dinheiro de um serviço que não vai acontecer, e a
    # Conciliação prometia o depósito no dia. Só as em aberto: cobrança já
    # recebida virou dinheiro no livro e se desfaz por estorno, não por aqui.
    financeiro_receber_service.cancelar_promessas_do_documento(
        db,
        empresa_id=getattr(os_in_db.funcionario, "empresa_id", None),
        ordem_servico_pagamentos=list(os_in_db.pagamentos or []),
    )

    status_anterior = os_in_db.status.value if hasattr(os_in_db.status, "value") else os_in_db.status
    os_in_db.status = OrdemServicoStatus.CANCELADA
    # Fábrica APOSENTADA (SPEC-00 da marcenaria, Revisão 15, FB1; Spec 03A, D15):
    # só a OS que ainda está no trilho antigo devolve sozinha a separação ao
    # cancelar. A OS da marcenaria nova também separa (Spec 10A), mas a regra
    # dela é a contrária: chapa cortada não volta à prateleira por um clique
    # (E2a). Nos outros segmentos nada muda: nenhum item deles tem
    # `quantidade_separada`.
    if os_in_db.fase_fabrica is not None:
        from app.services.fabrica import separacao as separacao_fabrica
        separacao_fabrica.devolver_tudo(db, os_in_db, usuario_token or {})
    trilho_fabrica.ao_cancelar(db, os_in_db, (usuario_token or {}).get("nome") or "Sistema", data.motivo)
    # Quem reage ao cancelamento (Spec 09A). O status anterior importa: so a OS
    # que estava FINALIZADA tem, por exemplo, conta de RT a tratar.
    ganchos_os.disparar(ganchos_os.ao_cancelar, db, os_in_db, usuario_token, {"status_anterior": status_anterior})

    if data.motivo:
        obs_atual = os_in_db.observacoes or ""
        os_in_db.observacoes = f"{obs_atual}\n[CANCELAMENTO] {data.motivo}".strip()

    if data.zerar_adiantamento:
        os_in_db.valor_entrada = 0
        os_in_db.forma_pagamento_entrada_id = None
    elif os_in_db.valor_entrada > 0:
        cliente = os_in_db.equipamento.cliente if os_in_db.equipamento else None
        if cliente:
            cliente.saldo_credito = (cliente.saldo_credito or 0) + os_in_db.valor_entrada

    return os_crud.update_ordem_servico(db, os_to_update=os_in_db)


def reabrir_ordem_servico(
    db: Session,
    numero_os: str,
    codigo_gerente: str | None = None,
    cliente_pagou: bool = True,
    usuario_token: dict | None = None,
) -> OSModel:
    """
    Reabre uma OS FINALIZADA ou CANCELADA.

    Limpa: status → EM_ANDAMENTO, data_finalizacao → None.

    cliente_pagou:
      - True (padrão): o valor já pago é preservado como crédito da OS
        (credito_anterior) e será abatido do novo total ao refinalizar.
      - False: o pagamento não era real (ex.: OS reaberta na hora, antes de o
        cliente pagar). Apaga os pagamentos e zera o crédito, então a OS recobra
        o valor cheio. Só use quando tiver certeza de que o dinheiro NÃO entrou —
        senão o registro do pagamento do cliente é perdido. O desconto e o
        acréscimo (juros) daquele fechamento também são zerados: ver abaixo.
    """
    os_in_db = _get_os_or_raise(db, numero_os)

    if os_in_db.status not in (OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA):
        raise os_nao_pode_reabrir_exce

    if os_in_db.funcionario:
        empresa_id = os_in_db.funcionario.empresa_id
        config_seg = config_seg_crud.get_configuracao_seguranca(db, empresa_id=empresa_id)
        if config_seg and config_seg.requer_pin_reabrir_os and config_seg.pin_gerente:
            if not codigo_gerente:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="REQUER_APROVACAO_GERENTE")
            if not verify_password(codigo_gerente, config_seg.pin_gerente):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PIN_GERENTE_INVALIDO")

    # Devolve as peças ao estoque, mas SÓ se elas tinham saído. Vindo de
    # FINALIZADA, saíram na finalização. Vindo de CANCELADA, o cancelamento já
    # estornou — estornar de novo aqui criaria estoque do nada, e o erro só
    # apareceria muito depois, na contagem física.
    if os_in_db.status == OrdemServicoStatus.FINALIZADA:
        _movimentar_estoque_os(db, os_in_db, saida=False, usuario_token=usuario_token)

    if cliente_pagou:
        # Preserva o que foi pago como crédito abatido do novo total.
        #
        # O adiantamento desta sessão vai para `adiantamentos_anteriores` ANTES
        # de `valor_entrada` ser zerado logo abaixo -- é o único dinheiro
        # recebido que não fica em `pagamentos`. A conta antiga recomputava o
        # crédito como `pagamentos + valor_entrada`, e na SEGUNDA reabertura o
        # adiantamento da primeira sessão (já zerado) sumia: o cliente era
        # cobrado de novo por ele. Esta conta acumula; a antiga sobrescrevia.
        #
        # Sem o `min(..., valor_total)` que havia aqui: o crédito passa a ser
        # exatamente o recebido, e quem abate do total é o `finalizar`. O teto
        # escondia sobra de pagamento e quebrava a derivação "pagamentos novos
        # = pagamentos - crédito" que a tela usa para separar as vias.
        adiantamentos = (os_in_db.adiantamentos_anteriores or 0) + (os_in_db.valor_entrada or 0)
        os_in_db.adiantamentos_anteriores = adiantamentos or None
        recebido = sum(p.valor for p in os_in_db.pagamentos) + adiantamentos
        os_in_db.credito_anterior = recebido or None
    else:
        # Pagamento não era real: apaga os pagamentos (cascade delete-orphan) e
        # zera o crédito, para a OS recobrar o valor cheio.
        #
        # Antes de apagar, devolve ao livro o que chegou a entrar. A FK do
        # movimento é SET NULL, então as linhas ficariam para trás contando
        # dinheiro que nunca existiu, e o turno passaria a fechar com FALTA.
        # O estorno lança o contrário na data de hoje; nada é apagado do livro.
        from app.services import sessao_caixa as caixa_service
        caixa_service.estornar_pagamentos_de_os(
            db,
            os_in_db,
            list(os_in_db.pagamentos),
            operador_funcionario_id=(usuario_token or {}).get("funcionario_id"),
        )
        from app.services.financeiro import promessas as financeiro_receber_service

        # ANTES DO CLEAR, obrigatoriamente: a FK da conta a receber é
        # `ondelete=SET NULL`, então depois de apagar os pagamentos a cobrança
        # perde o vínculo e vira órfã -- PENDENTE para sempre e exibida como
        # "lançada à mão", sem forma de rastrear de onde veio. Foi o defeito que
        # o dono achou na loja em 05/09/2026, numa OS cancelada e refeita.
        financeiro_receber_service.cancelar_promessas_do_documento(
            db,
            empresa_id=getattr(os_in_db.funcionario, "empresa_id", None),
            ordem_servico_pagamentos=list(os_in_db.pagamentos or []),
        )
        os_in_db.pagamentos.clear()
        os_in_db.credito_anterior = None
        # O dinheiro não era real -- nem o adiantado.
        os_in_db.adiantamentos_anteriores = None

        # Desconto e acréscimo vão junto com o fechamento que não aconteceu.
        # Os dois só nascem na finalização (a tela não edita nenhum fora dela)
        # e ACUMULAM a cada uma: mantidos, o desconto antigo ficava travado na
        # tela como "Desc. anterior" e somava com o novo, e o acréscimo -- que é
        # o juros do cartão daqueles pagamentos, agora apagados -- cobrava o
        # juros de um cartão que nunca passou. Na reabertura "pagou" os dois
        # ficam: o pagamento foi real e o crédito foi calculado sobre eles.
        os_in_db.desconto = 0
        os_in_db.acrescimo = 0
        _recalcular_valor_total_os(os_in_db)

    os_in_db.valor_entrada = 0
    os_in_db.forma_pagamento_entrada_id = None
    os_in_db.status = OrdemServicoStatus.EM_ANDAMENTO
    os_in_db.data_finalizacao = None
    # Fábrica: volta para a etapa (e o status dela). No-op nas outras OS.
    trilho_fabrica.ao_reabrir(db, os_in_db, (usuario_token or {}).get("nome") or "Sistema")
    # Quem reage a reabertura (Spec 09A). Lista vazia = nada muda.
    ganchos_os.disparar(ganchos_os.ao_reabrir, db, os_in_db, usuario_token)

    return os_crud.update_ordem_servico(db, os_to_update=os_in_db)
