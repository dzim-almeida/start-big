# ---------------------------------------------------------------------------
# ARQUIVO: services/venda/finalizacao.py
# DESCRICAO: Venda - finalizar (pagamentos, estoque e caixa).
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from typing import Sequence
from app.db.models.contador_venda import ContadorVenda
from app.schemas.vendas import PagamentoVendaCreate
from app.services import produto as produto_service
from app.services import sessao_caixa as caixa_service
from app.services.venda import atacado as venda_atacado
from app.db.crud import venda as venda_crud
from app.db.crud.configuracao import vendas as config_vendas_crud
from app.core.enum import VendaStatus, TipoProdutoVenda
from app.helpers.exceptions import BadRequestException, InternalServerException
from app.services.venda.calculo import _aplly_discount, _payments_valid, _recalc_total_sale
from app.services.venda.consultas import get_sale_by_id


def finish_sale(
    db: Session,
    sale_id: int,
    payments: Sequence[PagamentoVendaCreate],
    acrescimo: int = 0,
    operador_funcionario_id: int | None = None,
):
    sale_in_db = get_sale_by_id(db, sale_id=sale_id)

    if sale_in_db.status != VendaStatus.ATIVA:
        raise BadRequestException(detail="Esta venda não pode ser finalizada")

    empresa_id = sale_in_db.funcionario.empresa_id
    config_vendas = config_vendas_crud.get_configuracao_vendas(db, empresa_id=empresa_id)
    if config_vendas and config_vendas.exigir_cliente_identificado and not sale_in_db.cliente_id:
        raise BadRequestException(detail="Esta venda exige um cliente identificado para ser finalizada")

    venda_atacado.exigir_pedido_minimo(sale_in_db, config_vendas)

    # Trava do caixa: so morde quando a loja ligou AS DUAS chaves
    # (`controlar_caixa` e `exigir_caixa_aberto`). Loja que nao ligou nada passa
    # reto -- e o que mantem as tres lojas em producao vendendo como sempre.
    caixa_service.exigir_caixa_aberto_para_vender(
        db, sale_in_db.funcionario, operador_funcionario_id
    )

    valid_payments_to_db = _payments_valid(db, payments)

    # Valida parcelamento
    if config_vendas:
        for p in valid_payments_to_db:
            if p.parcelado and not config_vendas.permitir_parcelamento:
                raise BadRequestException(detail="Parcelamento não é permitido nas configurações de vendas")
            if p.parcelado and p.qtd_parcelas and p.qtd_parcelas > config_vendas.parcelas_maximas:
                raise BadRequestException(detail=f"Máximo de {config_vendas.parcelas_maximas} parcelas permitido")

    # Aplica o acréscimo (juros de cartão informado no checkout) e recalcula o total.
    # O valor de cada pagamento já vem com o juros embutido; o acréscimo entra no
    # total para que o excedente não seja tratado como troco.
    sale_in_db.acrescimo = acrescimo or 0
    # `sai_da_fila=False`: quem esta mexendo aqui e o proprio caixa, e a venda
    # esta saindo da fila pela porta certa. Ver `_recalc_total_sale`.
    sale_in_db = _recalc_total_sale(db, sale_in_db, sai_da_fila=False, aplicar_regras=False)

    total_payments = sum(payment.valor for payment in valid_payments_to_db)
    total_sale = sale_in_db.total or 0

    if total_payments < total_sale:
        raise BadRequestException(detail="Os pagamentos não conferem ao total da venda")

    # Valida valor mínimo de venda
    if config_vendas and config_vendas.valor_minimo_venda > 0 and total_sale < config_vendas.valor_minimo_venda:
        raise BadRequestException(detail=f"Valor mínimo de venda não atingido")

    # Zera desconto se exceder o limite configurado no momento da finalização
    empresa_id = sale_in_db.funcionario.empresa_id
    config_vendas = config_vendas_crud.get_configuracao_vendas(db, empresa_id=empresa_id)
    # Só o desconto do OPERADOR: o da regra de preço (§6.1) não conta no
    # limite nem é zerado aqui — é a loja que o ligou. A base é o que sobra
    # depois da regra; sem regra, é o total bruto de sempre.
    base_desconto = sale_in_db.total_bruto - sale_in_db.descontos_regra
    if config_vendas and config_vendas.permitir_desconto and base_desconto > 0 and sale_in_db.descontos > 0:
        percentual = (sale_in_db.descontos * 100) // base_desconto
        if percentual > config_vendas.desconto_maximo_percent:
            sale_in_db = _aplly_discount(sale_in_db=sale_in_db, discount=0)
            sale_in_db = _recalc_total_sale(db, sale_in_db, sai_da_fila=False, aplicar_regras=False)

    # Atribui número sequencial oficial
    contador = db.query(ContadorVenda).filter(ContadorVenda.id == 1).with_for_update().first()
    if not contador:
        raise InternalServerException(detail="Contador de vendas não inicializado. Contate o suporte.")
    sale_in_db.numero_venda = contador.proximo_numero
    contador.proximo_numero += 1

    products_in_db = sale_in_db.itens

    for product in products_in_db:
        if product.tipo_produto == TipoProdutoVenda.CADASTRADO:
            # `quantidade_base`: a linha "2 FD" de 12 baixa 24 un (D6). Linha
            # sem embalagem tem fator 1 — baixa o mesmo de sempre.
            produto_service.decrease_product_in_stock(db, produto_id=product.produto_id, quantidade=product.quantidade_base, funcionario_id=sale_in_db.funcionario_id, venda_id=sale_in_db.id)

    sale_in_db.status = VendaStatus.FINALIZADA
    sale_in_db.pagamentos = valid_payments_to_db

    # Lanca os pagamentos no livro do dinheiro. Sai na primeira linha quando o
    # controle de caixa esta desligado, entao para quem nao usa esta chamada
    # custa uma consulta a configuracao e nada mais: nenhuma linha nova gravada.
    # Precisa vir DEPOIS do flush dos pagamentos, senao eles ainda nao teriam id
    # para o movimento apontar.
    db.flush()

    # ANTES de qualquer coisa lancar: carimba o vencimento que a FORMA declarou.
    # Cartao com prazo declarado nao entra na gaveta hoje -- a maquininha
    # deposita em D+n, e a partir daqui as duas funcoes abaixo ja sabem tratar
    # isso como promessa, sem saber que prazo existe.
    from app.services.financeiro import promessas as financeiro_receber_service
    financeiro_receber_service.aplicar_prazo_de_recebimento(db, sale_in_db.pagamentos)

    caixa_service.registrar_pagamentos_de_venda(db, sale_in_db, operador_funcionario_id)

    # O outro lado da mesma frase. `registrar_pagamentos_de_venda` PULA o
    # pagamento com vencimento futuro, porque "promessa: e conta a receber, nao
    # gaveta" -- e ate agora nada criava essa conta a receber. Roda com o caixa
    # ligado ou desligado: fiado e fiado em qualquer loja.
    financeiro_receber_service.registrar_promessas_de_venda(db, sale_in_db)

    return venda_crud.update_sale(db, sale_in_db)
