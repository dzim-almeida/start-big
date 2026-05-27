import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enum import VendaStatus
from app.db.models.venda import Venda

logger = logging.getLogger(__name__)

DIAS_EXPIRACAO_ORCAMENTO = 3


def limpar_orcamentos_antigos(db: Session) -> int:
    """
    Remove orcamentos que nao foram atualizados nos ultimos
    DIAS_EXPIRACAO_ORCAMENTO dias. Retorna a quantidade removida.
    """
    limite = datetime.now() - timedelta(days=DIAS_EXPIRACAO_ORCAMENTO)

    stmt = select(Venda).where(
        Venda.status == VendaStatus.ORCAMENTO,
        Venda.atualizado_em < limite,
    )
    orcamentos_antigos = db.scalars(stmt).all()
    quantidade = len(orcamentos_antigos)

    for orcamento in orcamentos_antigos:
        db.delete(orcamento)

    if quantidade > 0:
        db.commit()
        logger.info(
            "Limpeza automatica: %d orcamento(s) removido(s) (anterior a %s)",
            quantidade,
            limite.isoformat(),
        )
    else:
        logger.debug("Limpeza automatica: nenhum orcamento antigo encontrado.")

    return quantidade
