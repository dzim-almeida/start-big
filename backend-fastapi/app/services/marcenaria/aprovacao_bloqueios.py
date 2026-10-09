# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/aprovacao_bloqueios.py
# DESCRICAO: O que impede DESFAZER a aprovacao do orcamento (Spec 08A, D20,
#            secao 7.6) e se a OS da aprovacao foi cancelada (D21).
#
# Separado de aprovacao.py porque o DETALHE do orcamento tambem precisa: ele
# so liga `acoes.desfazer_aprovacao` quando nada impede (a tela nao oferece o
# que vai falhar). Assim nenhum dos dois importa o outro.
# ---------------------------------------------------------------------------

from collections import Counter
from typing import Callable

from sqlalchemy.orm import Session

from app.core import segmentos as reg
from app.core.enum import OrdemServicoStatus
from app.db.models.marcenaria.etapa import StatusEtapa
from app.db.models.marcenaria.orcamento import MarcenariaOrcamento, StatusOrcamento
from app.db.models.pedido_compra import PedidoCompra
from app.services.marcenaria import terceirizado_situacao as terceirizado
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


def rotulo_status_os(db: Session, status_os: str) -> str:
    """'Em Produção' na marcenaria; o texto de sempre nos outros (Spec 01A).

    Publica: a producao (12A) usa o mesmo texto na sugestao e no quadro.
    """
    return reg.rotulo_status(get_segmento_atual(db), status_os) or _STATUS_OS.get(status_os, status_os)


def _bloqueio_status_da_os(db: Session, orc: MarcenariaOrcamento) -> list[str]:
    """So desfaz com a OS ainda ABERTA (nada comecou)."""
    valor = _valor(orc.os.status)
    if valor != OrdemServicoStatus.ABERTA.value:
        return [f"A OS já não está aberta (status: {rotulo_status_os(db, valor)})."]
    return []


def _bloqueio_pagamentos_da_os(db: Session, orc: MarcenariaOrcamento) -> list[str]:
    """Pagamento registrado e dinheiro: o caminho e o cancelamento pela OS."""
    return ["A OS já tem pagamento registrado."] if orc.os.pagamentos else []


def _bloqueio_material_retirado(db: Session, orc: MarcenariaOrcamento) -> list[str]:
    """Spec 10A D23: com chapa ja cortada, desfazer deixaria estoque e custo sem dono."""
    if any((item.quantidade_separada or 0) > 0 for item in orc.os.itens):
        return ["Já há material retirado do estoque para esta OS. "
                "Devolva o material ao estoque antes de desfazer a aprovação."]
    return []


def _bloqueio_pedido_a_central(db: Session, orc: MarcenariaOrcamento) -> list[str]:
    """Spec 11A D15: desfazer com pedido feito deixaria a central produzindo sem OS."""
    motivos = []
    for ambiente in sorted(orc.ambientes, key=lambda a: (a.ordem, a.id)):
        for movel in sorted(ambiente.moveis, key=lambda m: (m.ordem, m.id)):
            if not movel.aprovado or movel.tipo_producao != terceirizado.TERCEIRIZADA:
                continue
            pedido = db.get(PedidoCompra, movel.pedido_compra_id) if movel.pedido_compra_id else None
            situacao = terceirizado.situacao_do_movel(movel, pedido)
            central = (movel.central.nome_fantasia or movel.central.nome) if movel.central else "parceira"
            if situacao.pedido is not None:          # pedido do Compras (ate em rascunho)
                motivos.append(f"Já há pedido à central {central} ({situacao.pedido.codigo}). Cancele o pedido "
                               "no Compras e volte o móvel para 'A pedir' antes de desfazer.")
            elif situacao.situacao != terceirizado.A_PEDIR:   # anotado a mao
                motivos.append(f"Já há pedido à central {central} para o móvel {movel.nome}. "
                               "Volte o móvel para 'A pedir' antes de desfazer.")
    return list(dict.fromkeys(motivos))              # um pedido com 2 moveis: uma frase so


def _plural(n: int) -> str:
    return f"{n} móvel" if n == 1 else f"{n} móveis"


def _bloqueio_producao(db: Session, orc: MarcenariaOrcamento) -> list[str]:
    """Spec 12A D20: com etapa iniciada ou concluida, a producao ja comecou."""
    concluidas, em_execucao = Counter(), Counter()
    for ambiente in orc.ambientes:
        for movel in ambiente.moveis:
            for etapa in movel.etapas:
                if etapa.status == StatusEtapa.CONCLUIDA:
                    concluidas[etapa.nome] += 1
                elif etapa.status == StatusEtapa.EM_EXECUCAO:
                    em_execucao[etapa.nome] += 1
    if not concluidas and not em_execucao:
        return []
    partes = [f"{nome} concluída em {_plural(n)}" for nome, n in concluidas.most_common()]
    partes += [f"{nome} em execução em {_plural(n)}" for nome, n in em_execucao.most_common()]
    return [f"A produção já começou ({'; '.join(partes)})."]


# Ponto de extensao: cada spec seguinte acrescenta a regra que ELA conhece
# (10A: material retirado; 11A: pedido a central; 12A: producao; 13A: entrega).
BLOQUEIOS_DESFAZER: list[Callable[[Session, MarcenariaOrcamento], list[str]]] = [
    _bloqueio_status_da_os,
    _bloqueio_pagamentos_da_os,
    _bloqueio_material_retirado,          # 10A
    _bloqueio_pedido_a_central,           # 11A
    _bloqueio_producao,                   # 12A
]


def motivos_que_impedem_desfazer(db: Session, orc: MarcenariaOrcamento) -> list[str]:
    """TODOS os motivos, para a tela explicar de uma vez (nao o primeiro que falhar)."""
    if orc.status != StatusOrcamento.APROVADO or orc.os is None:
        return ["O orçamento não está aprovado."]
    return [motivo for regra in BLOQUEIOS_DESFAZER for motivo in regra(db, orc)]


def os_cancelada(orc: MarcenariaOrcamento) -> bool:
    """D21: aprovado, mas a OS foi cancelada pela tela de OS (o caminho e nova versao)."""
    return orc.os is not None and _valor(orc.os.status) == OrdemServicoStatus.CANCELADA.value
