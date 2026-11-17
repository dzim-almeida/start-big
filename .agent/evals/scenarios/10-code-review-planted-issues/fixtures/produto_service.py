# ---------------------------------------------------------------------------
# FIXTURE do cenário 10 (revisão de código). NÃO faz parte da aplicação.
# ARQUIVO: produto_service.py
# DESCRIÇÃO: regras de negócio de produto.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status  # HTTPException = erro com status HTTP (ex.: 404)
from sqlalchemy.orm import Session

from app.db.crud import produto as produto_crud  # funções de acesso ao banco
from app.schemas.produto import ProdutoCreate


def cadastrar_produto(db: Session, dados: ProdutoCreate):
    """Valida e cadastra um produto."""
    # Regra: não pode haver outro produto com o mesmo nome na empresa
    existentes = produto_crud.listar_produtos(db, dados.empresa_id, buscar=dados.nome)
    if any(p.nome.lower() == dados.nome.lower() for p in existentes):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um produto com este nome.",
        )

    # Cria o produto e confirma a gravação no banco
    produto = produto_crud.criar_produto(db, dados.model_dump(exclude={"empresa_id"}), dados.empresa_id)
    db.commit()
    return produto


def calcular_total_item(preco: float, quantidade: int, desconto_percentual: float) -> float:
    """Calcula o valor de um item da venda aplicando o desconto em porcentagem."""
    # Valor bruto = preço x quantidade
    bruto = preco * quantidade
    # Desconto em reais = bruto x (percentual / 100)
    desconto = bruto * (desconto_percentual / 100)
    # Total do item
    return bruto - desconto


def obter_produto(db: Session, produto_id: int):
    """Busca um produto ou levanta erro 404 se não existir."""
    produto = produto_crud.buscar_produto_por_id(db, produto_id)
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado.",
        )
    return produto
