# ---------------------------------------------------------------------------
# ARQUIVO: app/services/produto_fiscal.py
# MÓDULO: Service Layer — Dados Fiscais de Produto
# DESCRIÇÃO: Regras de negócio para leitura e atualização de dados fiscais
#            de produtos. Camada 2 de validação (completude condicional).
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.db.crud import perfil_tributario as perfil_crud
from app.db.crud import produto_fiscal as crud
from app.db.crud import produto as produto_crud
from app.db.models.produto_fiscal import ProdutoFiscal
from app.schemas.produto_fiscal import ProdutoFiscalRead, ProdutoFiscalUpdate


def get_dados_fiscais(db: Session, produto_id: int, empresa_id: int) -> Optional[ProdutoFiscal]:
    """
    Retorna os dados fiscais de um produto.

    Raises:
        HTTPException 404: Se o produto não existir.
    """
    _validar_produto_existe(db, produto_id)
    return crud.get_by_produto_id(db, produto_id)


def upsert_dados_fiscais(
    db: Session,
    produto_id: int,
    empresa_id: int,
    dados: ProdutoFiscalUpdate,
) -> ProdutoFiscal:
    """
    Cria ou atualiza os dados fiscais de um produto.

    Raises:
        HTTPException 404: Se o produto não existir.
    """
    _validar_produto_existe(db, produto_id)
    _validar_perfil_da_empresa(db, empresa_id, dados)
    return crud.upsert(db, produto_id, dados)


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _validar_perfil_da_empresa(db: Session, empresa_id: int, dados: ProdutoFiscalUpdate) -> None:
    """
    O perfil vinculado tem que ser desta empresa: por id daria para apontar
    para o perfil de outra loja. `None` (desvincular) e campo omitido passam.

    Raises:
        HTTPException 422: perfil inexistente ou de outra empresa.
    """
    perfil_id = dados.perfil_tributario_id
    if perfil_id is None:
        return
    if perfil_crud.get_perfil(db, empresa_id, perfil_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "codigo": "PERFIL_TRIBUTARIO_INVALIDO",
                "mensagem": f"Perfil tributário {perfil_id} não existe nesta empresa.",
            },
        )


def _validar_produto_existe(db: Session, produto_id: int) -> None:
    """
    Garante que o produto existe.

    Raises:
        HTTPException 404: Se o produto não existir.
    """
    if produto_crud.get_produto_by_id(db, produto_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Produto {produto_id} não encontrado.",
        )
