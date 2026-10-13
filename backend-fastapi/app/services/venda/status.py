# ---------------------------------------------------------------------------
# ARQUIVO: services/venda/status.py
# DESCRICAO: Venda - cancelar e reabrir.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.db.models.venda import Venda
from app.services import produto as produto_service
from app.db.crud import venda as venda_crud
from app.db.crud.configuracao import seguranca as config_seg_crud
from app.core.enum import VendaStatus, TipoProdutoVenda
from app.core.security import verify_password
from app.helpers.exceptions import BadRequestException
from app.services.venda.consultas import get_sale_by_id
from app.services.venda.guarda_fiscal import _assert_sem_documento_fiscal_ativo


def cancel_sale(db: Session, sale_id: int, motivo: str, codigo_gerente: str | None = None) -> Venda:
    sale_in_db = get_sale_by_id(db, sale_id=sale_id)

    if sale_in_db.status != VendaStatus.FINALIZADA:
        raise BadRequestException("Apenas vendas finalizadas podem ser canceladas")

    _assert_sem_documento_fiscal_ativo(db, sale_in_db, "cancelar a venda")

    empresa_id = sale_in_db.funcionario.empresa_id
    config_seg = config_seg_crud.get_configuracao_seguranca(db, empresa_id=empresa_id)
    if config_seg and config_seg.requer_pin_cancelar_venda and config_seg.pin_gerente:
        if not codigo_gerente:
            raise BadRequestException(detail="REQUER_APROVACAO_GERENTE")
        if not verify_password(codigo_gerente, config_seg.pin_gerente):
            raise BadRequestException(detail="PIN_GERENTE_INVALIDO")

    for product in sale_in_db.itens:
        if product.tipo_produto == TipoProdutoVenda.CADASTRADO:
            produto_service.restore_product_to_stock(
                db,
                produto_id=product.produto_id,
                quantidade=product.quantidade_base,  # o fator congelado na linha
                funcionario_id=sale_in_db.funcionario_id,
                venda_id=sale_in_db.id,
            )

    # Mesmo buraco da OS, mesmo conserto: sem isto a venda fiado cancelada
    # continuava cobrando o cliente no contas a receber.
    from app.services.financeiro import promessas as financeiro_receber_service
    financeiro_receber_service.cancelar_promessas_do_documento(
        db,
        empresa_id=empresa_id,
        venda_pagamentos=list(sale_in_db.pagamentos or []),
    )

    sale_in_db.status = VendaStatus.CANCELADA
    sale_in_db.motivo_cancelamento = motivo
    return venda_crud.update_sale(db, sale_in_db)


def reopen_sale(db: Session, sale_id: int, codigo_gerente: str | None = None) -> Venda:
    sale_in_db = get_sale_by_id(db, sale_id=sale_id)

    if sale_in_db.status != VendaStatus.CANCELADA:
        raise BadRequestException(detail="Venda não pode ser reaberta")

    _assert_sem_documento_fiscal_ativo(db, sale_in_db, "reabrir a venda")

    empresa_id = sale_in_db.funcionario.empresa_id
    config_seg = config_seg_crud.get_configuracao_seguranca(db, empresa_id=empresa_id)
    if config_seg and config_seg.requer_pin_reabrir_venda and config_seg.pin_gerente:
        if not codigo_gerente:
            raise BadRequestException(detail="REQUER_APROVACAO_GERENTE")
        if not verify_password(codigo_gerente, config_seg.pin_gerente):
            raise BadRequestException(detail="PIN_GERENTE_INVALIDO")

    sale_in_db.status = VendaStatus.ATIVA
    return venda_crud.update_sale(db, sale_in_db)
