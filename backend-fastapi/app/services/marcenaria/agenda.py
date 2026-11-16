# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/agenda.py
# DESCRICAO: A agenda de instalacao da marcenaria: agendar a visita dos
#            montadores e a lista "quem instala onde" (Spec 13A D9-D14, D20).
# ---------------------------------------------------------------------------
"""
- Uma OS pode ter VARIOS agendamentos (a cozinha numa semana, o closet na
  outra, I6). Cada um tem a data, a hora (opcional), os ambientes ainda nao
  entregues e os montadores (funcionarios ativos, I4).
- Montador em dois agendamentos no mesmo dia: permitido, com AVISO (D11).
- Depois que a entrega de um ambiente do agendamento e registrada, ele vira
  historico: nao se edita nem se exclui (D10).
- A lista de instalacoes vive na marcenaria (D13, D14): a Lista de OS
  compartilhada nao muda.
"""

from datetime import date
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.tempo import agora_utc, hoje_local
from app.db.crud.marcenaria import entrega as crud
from app.db.models.marcenaria.entrega import MarcenariaAgendamento
from app.db.models.ordem_servico import OrdemServico
from app.schemas.marcenaria.entrega import AgendamentoEntrada
from app.services.marcenaria import agenda_regras as regras
from app.services.marcenaria import erros
from app.services.marcenaria.entrega import montar_entrega, os_editavel
from app.services.marcenaria.orcamento_comum import exigir_orcamento_tecnico, registrar_evento, usuario_nome
from app.services.marcenaria.orcamento_detalhe import nome_do_cliente

MSG_VAZIO = "Escolha pelo menos um ambiente e um montador."
MSG_AMBIENTE_FORA = "Ambiente não encontrado nesta OS."
MSG_AGENDAMENTO_FORA = "Agendamento não encontrado nesta OS."
MSG_TRAVADO = "Este agendamento já tem entrega registrada e não pode mais ser alterado."
AGENDAMENTO_REGISTRADO = "AGENDAMENTO_REGISTRADO"

# Status de OS que ja nao instala: fora do aviso de montador e da lista (D11, D13).
_FORA_DA_AGENDA = ("CANCELADA",)


def _dia(valor: date) -> str:
    """"03/11" (as frases do historico e dos avisos)."""
    return valor.strftime("%d/%m")


def _valor(status) -> str:
    return getattr(status, "value", status)


def _validar(db: Session, os_, dados: AgendamentoEntrada) -> tuple:
    """Os ambientes (da OS e ainda pendentes) e os montadores (ativos), ou 422/404 (D9)."""
    if not dados.ambiente_ids or not dados.montadores:
        erros.invalido(MSG_VAZIO)
    entregas = {e.ambiente_id: e for e in crud.entregas_da_os(db, os_.id)}
    for ambiente_id in dados.ambiente_ids:
        entrega = entregas.get(ambiente_id)
        if entrega is None:
            erros.nao_encontrado(MSG_AMBIENTE_FORA)
        if entrega.situacao != "PENDENTE":
            erros.invalido(f"O ambiente {entrega.ambiente.nome} já foi entregue.")
    nomes_ambientes = [entregas[aid].ambiente.nome for aid in dados.ambiente_ids]
    return nomes_ambientes, regras.montadores(db, dados.montadores, so_ativos=True)


def _avisos_de_montador(db: Session, data: date, montadores: list[dict], agendamento_id: Optional[int]) -> list[dict]:
    """D11: o mesmo montador em outro agendamento no mesmo dia (quem e onde). Nao trava."""
    ids = {m["funcionario_id"] for m in montadores}
    outros = [a for a in crud.agendamentos_no_periodo(db, data, data) if a.id != agendamento_id]
    if not outros:
        return []
    os_por_id = {o.id: o for o in db.scalars(select(OrdemServico).where(OrdemServico.id.in_({a.os_id for a in outros})))}
    orcamentos = crud.orcamentos_aprovados_das_os(db, list(os_por_id))
    avisos = []
    for outro in outros:
        os_ = os_por_id.get(outro.os_id)
        if os_ is None or not os_.ativo or _valor(os_.status) in _FORA_DA_AGENDA:
            continue
        cliente = nome_do_cliente(orcamentos[os_.id].cliente) if os_.id in orcamentos else ""
        onde = f"{os_.numero_os} ({cliente})" if cliente else os_.numero_os
        hora = f" às {outro.hora_inicio}" if outro.hora_inicio else ""
        for montador in outro.montadores or []:
            if montador.get("funcionario_id") in ids:
                avisos.append({
                    "codigo": "MONTADOR_OCUPADO",
                    "mensagem": f"{montador.get('nome')} já tem instalação em {_dia(data)}{hora} na {onde}.",
                    "funcionario_id": montador.get("funcionario_id"),
                    "numero_os": os_.numero_os,
                })
    return avisos


def _frase(nomes_ambientes: list[str], data: date, hora: Optional[str], montadores: list[dict]) -> str:
    """"Instalação de Cozinha, Sala em 03/11 às 08:00 com Carlos, Davi"."""
    hora_txt = f" às {hora}" if hora else ""
    return f"{', '.join(nomes_ambientes)} em {_dia(data)}{hora_txt} com {regras.nomes(montadores)}"


def _responder(db: Session, os_, orc, avisos: list) -> dict[str, Any]:
    """D20: a data de instalacao da OS acompanha; grava e devolve a aba Entrega."""
    regras.sincronizar_data_instalacao(db, os_)
    db.commit()
    resposta = montar_entrega(db, os_, orc)
    resposta["avisos"] = avisos
    return resposta


def criar(db: Session, numero_os: str, dados: AgendamentoEntrada, usuario: dict) -> dict[str, Any]:
    """POST /os/{n}/agendamentos (D9)."""
    os_, orc = os_editavel(db, numero_os)
    nomes_ambientes, montadores = _validar(db, os_, dados)
    agendamento = MarcenariaAgendamento(
        os_id=os_.id, data=dados.data, hora_inicio=dados.hora_inicio, ambiente_ids=list(dados.ambiente_ids),
        montadores=montadores, observacao=dados.observacao,
        criado_por_nome=usuario_nome(usuario), criado_em=agora_utc(),
    )
    db.add(agendamento)
    db.flush()                                           # o id entra no evento
    registrar_evento(db, orc, "AGENDAMENTO_CRIADO",
                     f"Instalação agendada: {_frase(nomes_ambientes, dados.data, dados.hora_inicio, montadores)}."[:500],
                     usuario, {"agendamento_id": agendamento.id}, os_id=os_.id)
    return _responder(db, os_, orc, _avisos_de_montador(db, dados.data, montadores, agendamento.id))


def _agendamento_editavel(db: Session, os_, agendamento_id: int) -> MarcenariaAgendamento:
    """O agendamento desta OS, ainda sem entrega registrada (D10)."""
    agendamento = next((a for a in crud.agendamentos_da_os(db, os_.id) if a.id == agendamento_id), None)
    if agendamento is None:
        erros.nao_encontrado(MSG_AGENDAMENTO_FORA)
    if regras.travado(agendamento, regras.ambientes_registrados(crud.entregas_da_os(db, os_.id))):
        erros.conflito(AGENDAMENTO_REGISTRADO, MSG_TRAVADO)
    return agendamento


def editar(db: Session, numero_os: str, agendamento_id: int, dados: AgendamentoEntrada,
           usuario: dict) -> dict[str, Any]:
    """PUT /os/{n}/agendamentos/{id}: o agendamento muda com a chuva (D10)."""
    os_, orc = os_editavel(db, numero_os)
    agendamento = _agendamento_editavel(db, os_, agendamento_id)
    nomes_ambientes, montadores = _validar(db, os_, dados)
    antes = _dia(agendamento.data)
    agendamento.data, agendamento.hora_inicio = dados.data, dados.hora_inicio
    agendamento.ambiente_ids, agendamento.montadores = list(dados.ambiente_ids), montadores   # listas NOVAS
    agendamento.observacao = dados.observacao
    registrar_evento(db, orc, "AGENDAMENTO_ALTERADO",
                     f"Instalação de {antes} remarcada: "
                     f"{_frase(nomes_ambientes, dados.data, dados.hora_inicio, montadores)}."[:500],
                     usuario, {"agendamento_id": agendamento.id}, os_id=os_.id)
    return _responder(db, os_, orc, _avisos_de_montador(db, dados.data, montadores, agendamento.id))


def excluir(db: Session, numero_os: str, agendamento_id: int, usuario: dict) -> dict[str, Any]:
    """DELETE /os/{n}/agendamentos/{id} (D10)."""
    os_, orc = os_editavel(db, numero_os)
    agendamento = _agendamento_editavel(db, os_, agendamento_id)
    registrar_evento(db, orc, "AGENDAMENTO_EXCLUIDO",
                     f"Instalação de {_dia(agendamento.data)} desmarcada ({regras.nomes(agendamento.montadores)}).",
                     usuario, {"agendamento_id": agendamento.id}, os_id=os_.id)
    db.delete(agendamento)
    return _responder(db, os_, orc, [])


# ===========================================================================
# LISTA DE INSTALACOES (D13)
# ===========================================================================

def lista_instalacoes(db: Session, de: Optional[date] = None, ate: Optional[date] = None,
                      montador_id: Optional[int] = None, atrasadas: bool = False) -> dict[str, Any]:
    """GET /instalacoes: os agendamentos do periodo, por data e hora, com a obra.

    Poucas consultas (os agendamentos pelo indice em `data`, e as OS, os
    orcamentos e as entregas de todas de uma vez). O filtro por montador e
    feito aqui, sobre os agendamentos do periodo, que sao poucos (secao 5).
    """
    exigir_orcamento_tecnico(db)
    hoje = hoje_local()
    agendamentos = crud.agendamentos_no_periodo(db, de, ate)
    if montador_id is not None:
        agendamentos = [a for a in agendamentos
                        if any(m.get("funcionario_id") == montador_id for m in a.montadores or [])]
    os_ids = list({a.os_id for a in agendamentos})
    os_por_id = {o.id: o for o in db.scalars(select(OrdemServico).where(OrdemServico.id.in_(os_ids)))} if os_ids else {}
    orcamentos = crud.orcamentos_aprovados_das_os(db, os_ids)
    entregas_por_os: dict[int, dict[int, Any]] = {}
    for entrega in crud.entregas_das_os(db, os_ids):
        entregas_por_os.setdefault(entrega.os_id, {})[entrega.ambiente_id] = entrega

    itens = []
    for a in agendamentos:
        os_ = os_por_id.get(a.os_id)
        orc = orcamentos.get(a.os_id)
        if os_ is None or orc is None or not os_.ativo or _valor(os_.status) in _FORA_DA_AGENDA:
            continue
        entregas = entregas_por_os.get(a.os_id, {})
        pendentes = regras.ambientes_pendentes(entregas.values())
        e_atrasado = regras.atrasado(a, pendentes, hoje)
        if atrasadas and not e_atrasado:
            continue
        cliente = orc.cliente
        itens.append({
            "id": a.id,
            "data": a.data,
            "hora_inicio": a.hora_inicio,
            "numero_os": os_.numero_os,
            "status_os": _valor(os_.status),
            "cliente": nome_do_cliente(cliente) or None,
            "telefone": (cliente.celular or cliente.telefone) if cliente is not None else None,
            "projeto": orc.projeto_nome,
            "endereco_obra": orc.endereco_obra,
            "ambientes": [
                {"ambiente_id": aid,
                 "nome": entregas[aid].ambiente.nome if aid in entregas else "Ambiente removido",
                 "situacao": entregas[aid].situacao if aid in entregas else None}
                for aid in a.ambiente_ids
            ],
            "montadores": list(a.montadores or []),
            "observacao": a.observacao,
            "atrasado": e_atrasado,
        })
    # Por data e hora (sem hora no fim do dia) e pela OS.
    itens.sort(key=lambda i: (i["data"], i["hora_inicio"] or "99:99", i["numero_os"]))
    return {"itens": itens}
