# ---------------------------------------------------------------------------
# FIXTURE do cenário 10 (revisão de código). NÃO faz parte da aplicação.
# ARQUIVO: produto_crud.py
# DESCRIÇÃO: acesso ao banco para a tabela de produtos.
# ---------------------------------------------------------------------------

from typing import Optional

from sqlalchemy.orm import Session  # sessão do banco (a "conversa" com o SQLite)

from app.db.models.produto import Produto  # classe que representa a tabela "produtos"


def buscar_produto_por_id(db: Session, produto_id: int) -> Optional[Produto]:
    """Procura um produto pelo número (id). Devolve None se não achar."""
    # .get() busca direto pela chave primária
    return db.get(Produto, produto_id)


def listar_produtos(db: Session, empresa_id: int, buscar: Optional[str] = None) -> list[Produto]:
    """Lista os produtos de uma empresa, com busca opcional pelo nome."""
    # Começa a consulta pedindo só os produtos da empresa informada
    consulta = db.query(Produto).filter(Produto.empresa_id == empresa_id)

    # Se o usuário digitou algo na busca, filtra os nomes que contêm o texto
    if buscar:
        consulta = consulta.filter(Produto.nome.ilike(f"%{buscar}%"))

    # Ordena pelo nome e devolve a lista
    return consulta.order_by(Produto.nome).all()


def criar_produto(db: Session, dados: dict, empresa_id: int) -> Produto:
    """Cria um produto novo da empresa e devolve o objeto já com o id gerado."""
    produto = Produto(**dados, empresa_id=empresa_id)  # monta o objeto com os dados recebidos
    db.add(produto)  # marca para ser gravado
    db.flush()  # grava de forma provisória para o id existir (o commit é feito por quem chamou)
    return produto
