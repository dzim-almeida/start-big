# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/aprovacao_bloqueios.py
# DESCRICAO: O que impede DESFAZER a aprovacao do orcamento (Spec 08A, D20,
#            secao 7.6) e se a OS da aprovacao foi cancelada (D21).
#
# Separado de aprovacao.py porque o DETALHE do orcamento tambem precisa: ele
# so liga `acoes.desfazer_aprovacao` quando nada impede (a tela nao oferece o
# que vai falhar). Assim nenhum dos dois importa o outro.
# ---------------------------------------------------------------------------

from typing import Callable

from sqlalchemy.orm import Session

from app.core import segmentos as reg
from app.core.enum import OrdemServicoStatus
from app.db.models.marcenaria.orcamento import MarcenariaOrcamento, StatusOrcamento
from app.services.segmentos import get_segmento_atual

# Texto do status da OS quando o segmento nao declarou o seu (Spec 01A).
_STATUS_OS = {
    "ABERTA": "Aberta", "EM_ANDAMENTO": "Em Andamento", "AGUARDANDO_PECAS": "Aguardando Peças",
    "AGUARDANDO_APROVACAO": "Aguardando Aprovação", "AGUARDANDO_RETIRADA": "Aguardando Retirada",
    "FINALIZADA": "Finalizada", "CANCELADA": "Cancelada",
}


def _valor(status_os) -> str:
    """O texto do enum ("ABERTA"), venha o enum ou o texto."""
    return getattr(status_os, "value", status_os)


def _rotulo_status_os(db: Session, status_os: str) -> str:
    """'Em Produção' na marcenaria; o texto de sempre nos outros (Spec 01A)."""
    return reg.rotulo_status(get_segmento_atual(db), status_os) or _STATUS_OS.get(status_os, status_os)


def _bloqueio_status_da_os(db: Session, orc: MarcenariaOrcamento) -> list[str]:
    """So desfaz com a OS ainda ABERTA (nada comecou)."""
    valor = _valor(orc.os.status)
    if valor != OrdemServicoStatus.ABERTA.value:
        return [f"A OS já não está aberta (status: {_rotulo_status_os(db, valor)})."]
    return []


def _bloqueio_pagamentos_da_os(db: Session, orc: MarcenariaOrcamento) -> list[str]:
    """Pagamento registrado e dinheiro: o caminho e o cancelamento pela OS."""
    return ["A OS já tem pagamento registrado."] if orc.os.pagamentos else []


# Ponto de extensao: cada spec seguinte acrescenta a regra que ELA conhece
# (10A: material retirado; 11A: pedido a central; 12A: producao; 13A: entrega).
BLOQUEIOS_DESFAZER: list[Callable[[Session, MarcenariaOrcamento], list[str]]] = [
    _bloqueio_status_da_os,
    _bloqueio_pagamentos_da_os,
]


def motivos_que_impedem_desfazer(db: Session, orc: MarcenariaOrcamento) -> list[str]:
    """TODOS os motivos, para a tela explicar de uma vez (nao o primeiro que falhar)."""
    if orc.status != StatusOrcamento.APROVADO or orc.os is None:
        return ["O orçamento não está aprovado."]
    return [motivo for regra in BLOQUEIOS_DESFAZER for motivo in regra(db, orc)]


def os_cancelada(orc: MarcenariaOrcamento) -> bool:
    """D21: aprovado, mas a OS foi cancelada pela tela de OS (o caminho e nova versao)."""
    return orc.os is not None and _valor(orc.os.status) == OrdemServicoStatus.CANCELADA.value
