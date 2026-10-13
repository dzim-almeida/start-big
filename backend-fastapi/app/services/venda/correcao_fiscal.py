# ---------------------------------------------------------------------------
# ARQUIVO: services/venda/correcao_fiscal.py
# DESCRICAO: Venda - corrigir dados fiscais da venda.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.db.models.venda import Venda
from app.services.cliente import cliente_exists
from app.db.crud import venda as venda_crud
from app.schemas.vendas import VendaCorrecaoFiscalPayload
from app.schemas.vendas import VendaNotaFiscalUpdate
from app.services.venda import nota_fiscal as venda_nota_fiscal_service
from app.services.venda.consultas import get_sale_by_id
from app.services.venda.guarda_fiscal import _assert_sem_documento_fiscal_ativo


    

    
        
        
    
    

    


def corrigir_dados_venda_fiscal(
    db: Session, venda_id: int, payload: VendaCorrecaoFiscalPayload
) -> Venda:
    """
    Atualiza dados de cliente, observações e parâmetros fiscais de uma venda.
    Permite atualização mesmo se status for FINALIZADA ou ATIVA,
    garantindo a invariância de valores financeiros e movimentações de estoque.
    """
    sale_in_db = get_sale_by_id(db, sale_id=venda_id)

    # Bloqueio de segurança. Cobre também PROCESSANDO/PENDENTE/INDETERMINADA:
    # durante o polling o payload já viajou com os dados antigos, então trocar
    # cliente ou natureza da operação agora deixaria o registro local divergindo
    # da nota que está na SEFAZ.
    _assert_sem_documento_fiscal_ativo(db, sale_in_db, "alterar os dados fiscais")

    # 1. Validação e atualização de cliente
    if payload.cliente_id is not None:
        customer_in_db = cliente_exists(db, payload.cliente_id)
        sale_in_db.cliente_id = customer_in_db.id
    elif "cliente_id" in payload.model_fields_set and payload.cliente_id is None:
        sale_in_db.cliente_id = None

    # 2. Atualização de observações da venda
    if payload.observacao is not None:
        sale_in_db.observacao = payload.observacao
    if payload.observacao_interna is not None:
        sale_in_db.observacao_interna = payload.observacao_interna

    # 3. Atualização de dados fiscais (VendaNotaFiscal) caso informados
    campos_fiscais = ["natureza_operacao", "consumidor_final", "indicador_presenca", "finalidade_emissao"]
    fiscal_present = any(getattr(payload, f) is not None for f in campos_fiscais)
    if fiscal_present:
        venda_nota_fiscal_service.upsert_dados_fiscais(
            db,
            venda_id,
            VendaNotaFiscalUpdate(
                natureza_operacao=payload.natureza_operacao,
                consumidor_final=payload.consumidor_final,
                indicador_presenca=payload.indicador_presenca,
                finalidade_emissao=payload.finalidade_emissao,
            ),
        )

    return venda_crud.update_sale(db, sale_in_db)
