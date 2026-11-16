# ---------------------------------------------------------------------------
# ARQUIVO: services/produto/estoque.py
# DESCRICAO: Produtos - baixa e devolucao de estoque (venda, OS, cancelamentos).
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.db.crud import produto as produto_crud
from app.db.crud import funcionario as funcionario_crud
from app.core.enum import MovimentacaoTipo, MovimentacaoOrigem
from app.services.produto.cadastro import _bad_request_exce, not_found_exce
from app.services.produto.movimentacao import registrar_movimentacao


def _usuario_do_funcionario(db: Session, funcionario_id: int | None) -> tuple[int | None, str]:
    """Resolve o usuário responsável a partir do funcionário da venda.

    A movimentação de estoque registra USUÁRIO (quem operou o sistema); a venda
    guarda FUNCIONÁRIO. São entidades diferentes ligadas por FK.
    """
    if not funcionario_id:
        return None, "Sistema"
    funcionario = funcionario_crud.get_funcionario_by_id(db, funcionario_id=funcionario_id)
    if not funcionario:
        return None, "Sistema"
    return funcionario.usuario_id, funcionario.nome or "Sistema"


def decrease_product_in_stock(db: Session, produto_id: int, quantidade: int, venda_id: int, funcionario_id: int):
    """Baixa de estoque por venda.

    NÃO permite estoque negativo: diferente da OS, aqui a peça ainda está na
    prateleira e dá para simplesmente não vender.
    """
    product_in_db = produto_crud.get_produto_by_id(db, produto_id=produto_id)
    if not product_in_db:
        raise not_found_exce

    if quantidade > (product_in_db.estoque.quantidade or 0):
        raise _bad_request_exce

    usuario_id, usuario_nome = _usuario_do_funcionario(db, funcionario_id)
    registrar_movimentacao(
        db,
        produto=product_in_db,
        tipo=MovimentacaoTipo.SAIDA,
        quantidade=quantidade,
        origem=MovimentacaoOrigem.VENDA,
        usuario_id=usuario_id,
        usuario_nome=usuario_nome,
        venda_id=venda_id,
        observacao="Baixa por venda",
    )

    return produto_crud.update_produto(db, product_in_db)


def restore_product_to_stock(db: Session, produto_id: int, quantidade: int, venda_id: int, funcionario_id: int):
    """Estorno de estoque por cancelamento de venda."""
    product_in_db = produto_crud.get_produto_by_id(db, produto_id=produto_id)
    if not product_in_db:
        raise not_found_exce

    usuario_id, usuario_nome = _usuario_do_funcionario(db, funcionario_id)
    registrar_movimentacao(
        db,
        produto=product_in_db,
        tipo=MovimentacaoTipo.ENTRADA,
        quantidade=quantidade,
        origem=MovimentacaoOrigem.VENDA,
        usuario_id=usuario_id,
        usuario_nome=usuario_nome,
        venda_id=venda_id,
        observacao="Estorno por cancelamento de venda",
    )

    return produto_crud.update_produto(db, product_in_db)
