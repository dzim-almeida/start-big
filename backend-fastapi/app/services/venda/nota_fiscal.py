# ---------------------------------------------------------------------------
# ARQUIVO: services/venda/nota_fiscal.py (era services/venda_nota_fiscal.py ate 13/10/2026)
# DESCRIÇÃO: Lógica de negócio para nota fiscal por venda.
# ---------------------------------------------------------------------------

from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.crud import venda as venda_crud
from app.db.crud.venda import nota_fiscal as crud
from app.db.models.venda_nota_fiscal import VendaNotaFiscal
from app.schemas.vendas import VendaNotaFiscalUpdate


def _validar_venda(db: Session, venda_id: int) -> None:
    if venda_crud.get_sale_by_id(db, venda_id) is None:
        raise HTTPException(status_code=404, detail="Venda não encontrada")


def get_dados_fiscais(db: Session, venda_id: int) -> Optional[VendaNotaFiscal]:
    _validar_venda(db, venda_id)
    return crud.get_by_venda_id(db, venda_id)


def upsert_dados_fiscais(
    db: Session, venda_id: int, dados: VendaNotaFiscalUpdate
) -> VendaNotaFiscal:
    _validar_venda(db, venda_id)
    return crud.upsert(db, venda_id, dados)
