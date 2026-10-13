# ---------------------------------------------------------------------------
# ARQUIVO: services/ordem_servico/estoque.py
# DESCRICAO: Ordem de servico - baixa e estorno de estoque das pecas.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.db.models.ordem_servico import OrdemServico as OSModel
from app.db.models.ordem_servico_item import OrdemServicoItem as OSItemModel
from app.db.crud import produto as produto_crud
from app.services.produto import movimentacao as mov_service
from app.core.enum import (
    OrdemServicoItemTipo,
    OrdemServicoItemAprovacao,
    MovimentacaoTipo,
    MovimentacaoOrigem,
)


# ===========================================================================
# ESTOQUE
#
# Peça aplicada numa OS sai do estoque igual peça vendida no balcão — o que
# mudava era só que ninguém dava a baixa. A baixa acontece na FINALIZAÇÃO (é
# quando a OS vira fato consumado, mesmo padrão da venda) e é desfeita se a OS
# for cancelada ou reaberta, senão reabrir e refinalizar tirava a peça duas
# vezes do estoque.
# ===========================================================================

def _itens_de_produto(os_in_db: OSModel) -> list[OSItemModel]:
    """Itens que consomem estoque: produto do catálogo e APROVADO.

    Item PENDENTE ou REPROVADO não entra no valor_total da OS, então também não
    pode sair do estoque — o cliente recusou a peça e ela continua na prateleira.
    Item avulso (sem produto_id) não tem estoque para movimentar.
    """
    return [
        item for item in os_in_db.itens
        if item.tipo == OrdemServicoItemTipo.PRODUTO
        and item.produto_id is not None
        and item.status_aprovacao == OrdemServicoItemAprovacao.APROVADO
        and (item.quantidade or 0) > 0
    ]


def _quantidade_a_movimentar(item: OSItemModel) -> float:
    """O que a finalização baixa (e o estorno devolve): o que a SEPARAÇÃO não levou.

    Só a OS da fábrica separa (services/fabrica/separacao.py); em toda outra
    `quantidade_separada` é nula e isto é `quantidade`, como sempre foi.
    Separou tudo e finalizou = uma baixa só.
    """
    return max((item.quantidade or 0) - (item.quantidade_separada or 0), 0)


def _movimentar_estoque_os(
    db: Session,
    os_in_db: OSModel,
    saida: bool,
    usuario_token: dict | None = None,
) -> None:
    """Aplica (saida=True) ou estorna (saida=False) o estoque dos itens da OS.

    Delega ao registro central em services/movimentacao_estoque, que é quem
    altera a quantidade e grava o histórico na mesma operação. `permitir_negativo`
    é a regra específica da OS (ver o helper).
    """
    usuario_token = usuario_token or {}
    sub = usuario_token.get("sub")

    for item in _itens_de_produto(os_in_db):
        quantidade = _quantidade_a_movimentar(item)
        if quantidade <= 0:
            continue
        produto = produto_crud.get_produto_by_id(db, produto_id=item.produto_id)
        mov_service.registrar_movimentacao(
            db,
            produto=produto,
            tipo=MovimentacaoTipo.SAIDA if saida else MovimentacaoTipo.ENTRADA,
            quantidade=quantidade,
            origem=MovimentacaoOrigem.ORDEM_SERVICO,
            usuario_id=int(sub) if sub else None,
            usuario_nome=usuario_token.get("nome", "Sistema"),
            ordem_servico_id=os_in_db.id,
            observacao=f"{'Baixa' if saida else 'Estorno'} pela OS {os_in_db.numero_os}",
            permitir_negativo=True,
        )
