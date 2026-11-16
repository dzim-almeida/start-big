# ---------------------------------------------------------------------------
# ARQUIVO: services/venda/cadastro.py
# DESCRICAO: Venda - criar, editar e apagar rascunho.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.db.models.venda import Venda
from app.schemas.vendas import VendaCreate, VendaUpdate, VendaRead
from app.services.cliente import cliente_exists
from app.services.funcionario import funcionario_exists
from app.services.venda import atacado as venda_atacado
from app.db.crud import venda as venda_crud
from app.db.crud.configuracao import vendas as config_vendas_crud
from app.db.crud.configuracao import seguranca as config_seg_crud
from app.core.enum import VendaStatus
from app.core.security import verify_password
from app.helpers.exceptions import BadRequestException
from app.services.venda.calculo import _aplly_discount, _linhas_sem_desconto, _recalc_total_sale
from app.services.venda.consultas import get_sale_by_id
from app.services.venda.guarda_fiscal import _assert_sem_documento_fiscal_ativo


def create_sale(db: Session, sale: VendaCreate) -> VendaRead:
    # Valida existência de cliente (se informado) e funcionário.
    # `funcionario_exists` existe pelo efeito -- levanta se nao achar.
    if sale.cliente_id is not None:
        cliente_exists(db, sale.cliente_id)
    funcionario_exists(db, sale.funcionario_id)

    # AQUI NAO HA TRAVA DE CAIXA -- e a ausencia e deliberada.
    #
    # Ate 21/08/2026 esta funcao chamava `exigir_caixa_aberto_para_vender`, e o
    # comentario de entao ja admitia que aquilo era CORTESIA: "a trava existe
    # tambem na finalizacao, e la e a garantia de verdade -- e o momento do
    # dinheiro". Montar carrinho nao move dinheiro nenhum; so `finish_sale` move.
    #
    # Tirar a cortesia e o que permite o atendente montar a venda e o CAIXA
    # receber, sem que os dois precisem de turno aberto no proprio nome. O
    # dinheiro continua caindo no turno de quem recebe -- isso e `finish_sale` e
    # `registrar_pagamentos_de_venda`, e nenhum dos dois mudou.
    #
    # E de graca fecha o beco da maquina RETAGUARDA, que escondia a barra do
    # caixa mas continuava sendo cobrada por `exigir_caixa_aberto`: ficava sem o
    # botao de abrir E sem poder vender.
    #
    # O QUE VEIO NO LUGAR, no frontend: a barra do caixa avisa que a venda pode
    # ser montada mas nao finalizada. Sem esse aviso, quem trabalha sozinho na
    # loja montaria o carrinho inteiro para descobrir no checkout -- que era
    # exatamente o atrito que a linha removida evitava.

    sale_data = Venda(
        **sale.model_dump(exclude_unset=True),
        status=VendaStatus.ATIVA
    )

    return venda_crud.create_sale(db, sale_data=sale_data)


def update_sale(db: Session, sale_id: int, update_data: VendaUpdate) -> Venda:
    sale_in_db = get_sale_by_id(db, sale_id=sale_id)
    if sale_in_db.status != VendaStatus.ATIVA:
        raise BadRequestException(detail="Venda não pode ser editada")

    _assert_sem_documento_fiscal_ativo(db, sale_in_db, "editar a venda")

    update_fields = update_data.model_dump(exclude_unset=True)

    if 'cliente_id' in update_fields:
        if update_data.cliente_id is not None:
            customer_in_db = cliente_exists(db, update_data.cliente_id)
            sale_in_db.cliente_id = customer_in_db.id
        else:
            sale_in_db.cliente_id = None

    if update_data.funcionario_id:
        funcionario_in_db = funcionario_exists(db, update_data.funcionario_id)
        sale_in_db.funcionario_id = funcionario_in_db.id

    if update_data.entrega is not None:
        sale_in_db.entrega = update_data.entrega

    if update_data.modo_atacado is not None and update_data.modo_atacado != sale_in_db.modo_atacado:
        # Ligar exige a chave da loja; desligar vale sempre (é a saída).
        if update_data.modo_atacado:
            venda_atacado.exigir_habilitado(
                config_vendas_crud.get_configuracao_vendas(db, empresa_id=sale_in_db.funcionario.empresa_id)
            )
        sale_in_db.modo_atacado = update_data.modo_atacado

    if update_data.desconto is not None:
        empresa_id = sale_in_db.funcionario.empresa_id
        config_vendas = config_vendas_crud.get_configuracao_vendas(db, empresa_id=empresa_id)
        config_seg = config_seg_crud.get_configuracao_seguranca(db, empresa_id=empresa_id)
        fora = _linhas_sem_desconto(sale_in_db, config_vendas)
        # O desconto do operador vale sobre o que sobra depois da regra de
        # preço. Sem regra, `base` é o `subtotal` de sempre (que inclui a
        # entrega — é assim desde antes, e o limite não pode mudar para ninguém).
        base = (sale_in_db.subtotal or 0) - sale_in_db.descontos_regra - sum(
            item.subtotal - (item.desconto_regra or 0)
            for item in sale_in_db.itens if item.id in fora
        )
        if update_data.desconto > base:
            if fora and update_data.desconto <= sale_in_db.subtotal:
                raise BadRequestException(
                    detail="Itens com regra de preço não aceitam desconto manual (Configurações › Regras de Vendas)"
                )
            raise BadRequestException(detail="O desconto não pode ser maior que o total da venda")
        if config_vendas and config_vendas.permitir_desconto and base > 0 and update_data.desconto > 0:
            percentual = (update_data.desconto * 100) // base
            if percentual > config_vendas.desconto_maximo_percent:
                if config_seg and config_seg.requer_pin_desconto_venda and config_seg.pin_gerente:
                    codigo = update_data.codigo_gerente
                    if not codigo:
                        raise BadRequestException(detail="REQUER_APROVACAO_GERENTE")
                    if not verify_password(codigo, config_seg.pin_gerente):
                        raise BadRequestException(detail="PIN_GERENTE_INVALIDO")
                else:
                    raise BadRequestException(
                        detail=f"Desconto máximo permitido é de {config_vendas.desconto_maximo_percent}%"
                    )
        sale_in_db = _aplly_discount(sale_in_db=sale_in_db, discount=update_data.desconto, fora=fora)

    if update_data.observacao is not None:
        sale_in_db.observacao = update_data.observacao

    return _recalc_total_sale(db, sale_in_db=sale_in_db)


def delete_draft_sale(db: Session, sale_id: int) -> None:
    sale_in_db = get_sale_by_id(db, sale_id=sale_id)
    if sale_in_db.status != VendaStatus.ATIVA:
        raise BadRequestException(detail="Apenas vendas ativas podem ser descartadas")

    _assert_sem_documento_fiscal_ativo(db, sale_in_db, "descartar a venda")
    db.delete(sale_in_db)
    db.commit()
