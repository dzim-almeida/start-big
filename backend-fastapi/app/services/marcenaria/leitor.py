# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/leitor.py
# DESCRICAO: Leitor de codigo de barras da separacao (Spec 10A, D20, E4).
#            Acha, entre os itens da separacao de UMA OS, o que foi lido.
#            So procura: nao mexe em estoque nem no item.
# ---------------------------------------------------------------------------
"""
O leitor (a "pistola" de codigo de barras) digita o codigo e manda Enter. Aqui
o codigo vira o item da separacao, procurando SO entre os itens desta OS, em
tres passos, nesta ordem:

1. o codigo de barras do produto (`produtos.codigo_barras`);
2. o codigo do produto (`produtos.codigo_produto`, o SKU digitado a mao);
3. o codigo de barras de uma EMBALAGEM ativa do produto (`ProdutoEmbalagem`):
   a caixa de 10 corredicas devolve o fator 10 (uma leitura = 10 unidades).

E a mesma busca que a separacao da fabrica fazia (fabrica/separacao._achar),
copiada para ca: a da fabrica sai na limpeza depois do piloto (FB1).
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.ordem_servico_item import OrdemServicoItem
from app.db.models.produto import Produto
from app.db.models.produto_embalagem import ProdutoEmbalagem


def achar(db: Session, itens: list[OrdemServicoItem], codigo: str) -> Optional[tuple[OrdemServicoItem, int]]:
    """(item, fator) do codigo lido, ou None se nao for de nenhum item desta OS.

    `itens` sao as linhas da separacao desta OS (pecas embutidas com produto),
    concluidas ou nao: ler um item ja concluido tambem acha (a tela avisa).
    """
    codigo = (codigo or "").strip()
    if not codigo or not itens:
        return None
    por_produto = {i.produto_id: i for i in itens}           # um item por produto (D1)
    produtos = list(db.scalars(select(Produto).where(Produto.id.in_(list(por_produto)))))

    # Passos 1 e 2: o produto inteiro (fator 1). Primeiro TODOS os codigos de
    # barras e so depois os codigos internos, para um SKU que por acaso seja
    # igual ao codigo de barras de outro produto nao ganhar a vez.
    for campo in ("codigo_barras", "codigo_produto"):
        for produto in produtos:
            if getattr(produto, campo) == codigo:
                return por_produto[produto.id], 1

    # Passo 3: a embalagem (caixa, fardo) ATIVA de um dos produtos desta OS.
    embalagem = db.scalars(
        select(ProdutoEmbalagem).where(
            ProdutoEmbalagem.codigo_barras == codigo,
            ProdutoEmbalagem.ativo.is_(True),
            ProdutoEmbalagem.produto_id.in_(list(por_produto)),
        )
    ).first()
    if embalagem is not None:
        return por_produto[embalagem.produto_id], int(embalagem.fator or 1)
    return None
