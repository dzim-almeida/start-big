# ---------------------------------------------------------------------------
# ARQUIVO: services/venda/calculo.py
# DESCRICAO: Venda - recalculo do total, desconto e conferencia dos pagamentos.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from typing import Sequence
from app.db.models.venda import Venda
from app.db.models.venda_pagamento import PagamentoVenda
from app.schemas.vendas import PagamentoVendaCreate
from app.services.precificacao import regras as regras_preco_service
from app.services.venda import atacado as venda_atacado
from app.db.crud import venda as venda_crud
from app.db.crud.forma_pagamento import formas as forma_pagamento_crud
from app.helpers.exceptions import BadRequestException


def _recalc_total_sale(
    db: Session, sale_in_db: Venda, *, sai_da_fila: bool = True, aplicar_regras: bool = True
) -> Venda:

    # Regras de preço por quantidade (§6.1): recalculadas a cada mudança no
    # carrinho, porque "17 latas" só vira "1 fardo + 2" olhando o carrinho
    # inteiro. `finish_sale` passa False: o caixa cobra o que viu na tela.
    # Com as chaves desligadas não toca em nada (B8). Os ids das OUTRAS linhas
    # que mudaram vão para a resposta, para a tela trocá-las também.
    if aplicar_regras:
        # Atacado (services/venda_atacado.py) e regras por quantidade não se
        # somam. A ordem importa: ao LIGAR, as regras saem primeiro (devolvem o
        # varejo) e o atacado entra por cima; ao DESLIGAR, o atacado devolve o
        # varejo primeiro e as regras voltam a valer sobre ele.
        if sale_in_db.modo_atacado:
            alteradas = regras_preco_service.aplicar_na_venda(db, sale_in_db)
            alteradas |= venda_atacado.aplicar(sale_in_db)
        else:
            alteradas = venda_atacado.aplicar(sale_in_db)
            alteradas |= regras_preco_service.aplicar_na_venda(db, sale_in_db)
        sale_in_db.itens_alterados_pela_regra = alteradas

    descontos = sale_in_db.descontos + sale_in_db.descontos_regra
    if sale_in_db.total_bruto < descontos:
        raise BadRequestException(detail="O desconto não pode ser maior que o total da venda")

    total_sale = sale_in_db.total_bruto - descontos + (sale_in_db.acrescimo or 0)

    sale_in_db.subtotal = sale_in_db.total_bruto
    sale_in_db.total = total_sale

    # MUDOU O VALOR DO CARRINHO, A VENDA SAI DA FILA DO CAIXA.
    #
    # Se o atendente acrescentar um item depois de entregar, o caixa fica
    # olhando um total que mudou embaixo dele. Custa um reenvio ao atendente e
    # evita cobrar valor errado.
    #
    # A regra mora AQUI porque este e o ponto de estrangulamento: acrescentar,
    # alterar e remover item, e aplicar desconto, todos passam por esta funcao.
    # Repeti-la nos quatro chamadores seria quatro chances de esquecer uma.
    #
    # `finish_sale` passa `sai_da_fila=False`, e e a unica excecao: la quem esta
    # mexendo e o proprio caixa, a venda esta saindo da fila pela porta certa, e
    # apagar o carimbo perderia o registro de que ela chegou a esperar.
    if sai_da_fila:
        sale_in_db.enviada_ao_caixa_em = None

    return venda_crud.update_sale(db, sale_in_db)


def _aplly_discount(sale_in_db: Venda, discount: int, *, fora: frozenset[int] = frozenset()) -> Venda:
    # Rateia sobre o que SOBRA depois da regra de preço (§6.1): a linha com
    # "leve 3 pague 2" já tem um terço em `desconto_regra`, e o desconto do
    # operador vem depois dela. Sem regra, `desconto_regra` é 0 e a conta é a
    # de sempre. `fora`: linhas que não recebem desconto (trava da regra).
    for item in sale_in_db.itens:
        if item.id in fora:
            item.desconto = 0
    itens = [item for item in sale_in_db.itens if item.id not in fora]
    base = [item.subtotal - (item.desconto_regra or 0) for item in itens]
    items_subtotal = sum(base)
    discount_remaining = discount
    for index, item in enumerate(itens):
        if index == len(itens) - 1:
            item.desconto = discount_remaining
        else:
            item_discount = (base[index] * discount) // (items_subtotal or 1)
            item.desconto = item_discount
            discount_remaining -= item_discount
    return sale_in_db


def _linhas_sem_desconto(sale_in_db: Venda, config_vendas) -> frozenset[int]:
    """Com `bloquear_desconto_com_regra`, a linha com regra de preço não
    recebe desconto manual (a trava do TOTVS, §6.1)."""
    if not (config_vendas and config_vendas.bloquear_desconto_com_regra):
        return frozenset()
    return frozenset(
        item.id for item in sale_in_db.itens
        if item.regra_preco in regras_preco_service.calc.REGRAS
    )


def _payments_valid(db: Session, payments: Sequence[PagamentoVendaCreate]) -> Sequence[PagamentoVenda]:
    sale_payments: Sequence[PagamentoVenda] = []
    for payment in payments:
        payment_type = forma_pagamento_crud.get_forma_pagamento_by_id(db, payment.forma_pagamento_id)
        if not payment_type:
            raise BadRequestException(detail="Pagamentos devem ser uma forma válida")
        if payment.parcelado and payment.qtd_parcelas is None:
            raise BadRequestException(detail="Pagamentos parcelados devem ter no mínimo 1 parcela")
        if not payment.parcelado and payment.qtd_parcelas is not None:
            raise BadRequestException(detail="Pagamentos a vista não deve ter parcelas")
        dados = payment.model_dump()
        # O enum é str-subclass, mas gravamos o `.value` explicitamente para que a
        # coluna String nunca dependa da representação do Enum.
        dados["juros_responsavel"] = payment.juros_responsavel.value
        sale_payments.append(PagamentoVenda(**dados))
    return sale_payments
