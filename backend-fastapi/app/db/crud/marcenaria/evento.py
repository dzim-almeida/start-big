# ---------------------------------------------------------------------------
# ARQUIVO: app/db/crud/marcenaria/evento.py
# DESCRICAO: Gravacao e leitura do historico da marcenaria (Spec 06A, D25).
#            So SQL; quem decide QUANDO registrar e o servico.
# ---------------------------------------------------------------------------

from typing import Any, Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.tempo import agora_utc
from app.db.models.marcenaria.evento import MarcenariaEvento
from app.db.models.marcenaria.orcamento import MarcenariaOrcamento


def inserir_evento(
    db: Session,
    *,
    tipo: str,
    descricao: str,
    usuario_nome: str,
    orcamento_id: Optional[int] = None,
    os_id: Optional[int] = None,
    dados: Optional[dict[str, Any]] = None,
    usuario_id: Optional[int] = None,
) -> MarcenariaEvento:
    """Inclui um evento (sem commit: entra na mesma transacao da acao)."""
    evento = MarcenariaEvento(
        orcamento_id=orcamento_id,
        os_id=os_id,
        tipo=tipo,
        descricao=descricao[:500],               # a coluna tem 500; a frase nunca passa disso
        dados=dados,
        usuario_id=usuario_id,
        usuario_nome=(usuario_nome or "Sistema")[:150],
        ocorrido_em=agora_utc(),
    )
    db.add(evento)
    return evento


def listar_eventos_do_codigo(db: Session, codigo: str) -> list[MarcenariaEvento]:
    """Eventos de TODAS as versoes de um codigo, do mais novo ao mais antigo."""
    stmt = (
        select(MarcenariaEvento)
        .join(MarcenariaOrcamento, MarcenariaOrcamento.id == MarcenariaEvento.orcamento_id)
        .where(MarcenariaOrcamento.codigo == codigo)
        # `id` desempata dois eventos no mesmo instante (ex.: os dois da nova versao).
        .order_by(MarcenariaEvento.ocorrido_em.desc(), MarcenariaEvento.id.desc())
    )
    return list(db.scalars(stmt))


def desligar_eventos_do_orcamento(db: Session, orcamento_id: int) -> None:
    """Solta os eventos de um orcamento que vai ser excluido (D18).

    O banco da loja tem `PRAGMA foreign_keys=ON`: sem isto, apagar o orcamento
    quebraria a chave estrangeira dos eventos. Os eventos ficam (o historico
    nao some), so sem o orcamento.
    """
    db.execute(
        update(MarcenariaEvento)
        .where(MarcenariaEvento.orcamento_id == orcamento_id)
        .values(orcamento_id=None)
    )
