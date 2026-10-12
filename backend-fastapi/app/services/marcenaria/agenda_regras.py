# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/agenda_regras.py
# DESCRICAO: As regras da agenda de instalacao que a ENTREGA e a AGENDA usam
#            (Spec 13A D10, D12, D20).
#
# Separado de agenda.py porque a entrega tambem precisa delas (agendamento
# atrasado, data de instalacao da OS) e a agenda responde com a tela da
# entrega: assim nenhum dos dois servicos importa o outro (sem ciclo).
# ---------------------------------------------------------------------------

from datetime import date
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.db.crud.marcenaria import entrega as crud
from app.db.models.funcionario import Funcionario
from app.db.models.marcenaria.entrega import MarcenariaAgendamento, MarcenariaEntrega, SituacaoEntrega
from app.services.marcenaria import erros

MSG_FUNCIONARIO = "Funcionário não encontrado ou inativo."


def ambientes_pendentes(entregas: Iterable[MarcenariaEntrega]) -> set[int]:
    """Os ambientes cuja entrega ainda nao foi registrada."""
    return {e.ambiente_id for e in entregas if e.situacao == SituacaoEntrega.PENDENTE}


def ambientes_registrados(entregas: Iterable[MarcenariaEntrega]) -> set[int]:
    """Os ambientes com entrega registrada (Conforme ou Com ressalvas)."""
    return {e.ambiente_id for e in entregas if e.situacao != SituacaoEntrega.PENDENTE}


def atrasado(agendamento: MarcenariaAgendamento, pendentes: set[int], hoje: date) -> bool:
    """D12: a data ja passou e algum ambiente do agendamento segue PENDENTE."""
    return agendamento.data < hoje and any(aid in pendentes for aid in agendamento.ambiente_ids)


def travado(agendamento: MarcenariaAgendamento, registrados: set[int]) -> bool:
    """D10: com a entrega de algum ambiente registrada, o agendamento vira historico."""
    return any(aid in registrados for aid in agendamento.ambiente_ids)


def sincronizar_data_instalacao(db: Session, os_) -> None:
    """D20 (I5b): a OS guarda a MENOR data entre os agendamentos que ainda tem
    ambiente pendente (ou nada). O Compras le essa data para dar prioridade a
    chapa de quem instala primeiro; a Lista de OS nao le (T8a).

    Sem commit: vai junto com a acao que chamou.
    """
    db.flush()                                            # o que acabou de mudar entra na conta
    pendentes = ambientes_pendentes(crud.entregas_da_os(db, os_.id))
    datas = [a.data for a in crud.agendamentos_da_os(db, os_.id) if any(aid in pendentes for aid in a.ambiente_ids)]
    os_.data_instalacao = min(datas) if datas else None


def montadores(db: Session, ids: list[int], so_ativos: bool) -> list[dict]:
    """[{"funcionario_id": 4, "nome": "Carlos"}] na ordem dada, com o nome COPIADO (I4).

    `so_ativos`: agendar exige funcionario ativo; registrar aceita quem ja saiu
    (ele montou de verdade, e a correcao do registro nao pode travar por isso).
    """
    lista = []
    for funcionario_id in ids:
        funcionario: Optional[Funcionario] = db.get(Funcionario, funcionario_id)
        if funcionario is None or (so_ativos and not funcionario.ativo):
            erros.invalido(MSG_FUNCIONARIO)
        lista.append({"funcionario_id": funcionario.id, "nome": funcionario.nome})
    return lista


def nomes(montadores_json: Optional[list]) -> str:
    """"Carlos, Davi" (para as frases do historico)."""
    return ", ".join(m.get("nome", "") for m in (montadores_json or []))
