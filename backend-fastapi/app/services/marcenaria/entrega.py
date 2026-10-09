# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/entrega.py
# DESCRICAO: A entrega da obra da marcenaria: uma por ambiente, com checklist,
#            resultado, pendencias e fotos (Spec 13A).
# ---------------------------------------------------------------------------
"""
- Na APROVACAO, cada ambiente com movel aprovado recebe uma entrega PENDENTE
  com a COPIA do checklist de vistoria da configuracao (D1). Mudar a
  configuracao depois nao mexe nesta OS (D2: o checklist da entrega e editavel).
- O montador leva o TERMO no papel (P3); quando ele volta assinado, alguem
  passa o resultado a limpo: CONFORME ou COM_RESSALVAS (com pendencia, D4).
  Corrigir depois e permitido com a OS aberta, com evento (D5).
- Pendencias podem nascer e ser resolvidas ate com a OS finalizada (D6): a
  assistencia pos-entrega acontece depois da finalizacao.
- As fotos sao FOTOS DA OS (mesmo pipeline e galeria); a entrega so guarda o
  vinculo e o tipo (TERMO ou MONTAGEM, D7).
- Nenhum preco em nenhuma resposta (P4). O backend nunca finaliza a OS: ele
  so diz `todos_entregues` e a tela oferece a finalizacao de sempre (D16).
"""

from typing import Any, Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.tempo import agora_utc, hoje_local
from app.db.crud import empresa as empresa_crud
from app.db.crud.configuracao_marcenaria import get_configuracao_marcenaria
from app.db.crud.marcenaria import entrega as crud
from app.db.models.configuracao_marcenaria import CHECKLIST_PADRAO
from app.db.models.marcenaria.entrega import (
    MarcenariaEntrega,
    MarcenariaEntregaFoto,
    MarcenariaPendencia,
    SituacaoEntrega,
    SituacaoPendencia,
    TipoFotoEntrega,
)
from app.db.models.marcenaria.orcamento import MarcenariaOrcamento
from app.db.models.ordem_servico import OrdemServico
from app.schemas.configuracao_marcenaria import _lista_de_nomes
from app.schemas.marcenaria.entrega import ChecklistEntrada, PendenciaEntrada, RegistroEntrada, ResolverEntrada
from app.services import ordem_servico_foto as os_foto_service
from app.services.marcenaria import agenda_regras as regras
from app.services.marcenaria import erros
from app.services.marcenaria.orcamento_comum import os_aberta, os_e_orcamento_aprovado, registrar_evento, usuario_nome
from app.services.marcenaria.orcamento_detalhe import nome_do_cliente

# --- Frases e codigos (secao 6.3) -------------------------------------------------
MSG_SEM_ORCAMENTO = "Esta OS não veio de um orçamento."
MSG_OS_FECHADA = "A OS está finalizada ou cancelada; a entrega não pode mais ser alterada."
MSG_ENTREGA_FORA = "Entrega não encontrada nesta OS."
MSG_PENDENCIA_FORA = "Pendência não encontrada nesta entrega."
MSG_FOTO_FORA = "Foto não encontrada nesta entrega."
MSG_RESSALVAS = "Com ressalvas, informe pelo menos uma pendência."
MSG_DATA_FUTURA = "A data da entrega não pode ser no futuro."
MSG_MARCACOES = "As marcações não conferem com o checklist do ambiente."
MSG_CHECKLIST_REGISTRADO = "O checklist só muda enquanto a entrega está pendente."
MSG_PENDENCIA_SEM_REGISTRO = "Registre a entrega do ambiente antes de anotar pendências."
OS_FECHADA = "OS_FECHADA"

LIMITE_ITENS = 30                        # D2: as mesmas regras do checklist da configuracao (04A)
LIMITE_TEXTO = 120

# Como cada situacao entra nas frases do historico.
ROTULO = {
    SituacaoEntrega.PENDENTE: "Pendente",
    SituacaoEntrega.CONFORME: "Conforme",
    SituacaoEntrega.COM_RESSALVAS: "Com ressalvas",
}
AVISO_SEM_FOTO_TERMO = {
    "codigo": "SEM_FOTO_TERMO",
    "mensagem": "A entrega foi registrada sem a foto do termo assinado.",
}


# ===========================================================================
# APROVACAO E DESFAZER (chamadas pela 08A)
# ===========================================================================

def checklist_da_configuracao(db: Session) -> list[str]:
    """O checklist de vistoria da configuracao de AGORA (sem configuracao: o da 04A)."""
    config = get_configuracao_marcenaria(db, empresa_crud.get_empresa_atual(db).id)
    return list(config.checklist_vistoria or []) if config is not None else list(CHECKLIST_PADRAO)


def _checklist_vazio(textos: list[str]) -> list[dict]:
    """Os itens com a marcacao em branco (o papel e marcado a caneta na obra)."""
    return [{"texto": texto, "marcacao": None} for texto in textos]


def criar_entregas_da_aprovacao(db: Session, orc: MarcenariaOrcamento, os_id: int) -> None:
    """D1: dentro da transacao da aprovacao, uma entrega PENDENTE por ambiente
    com pelo menos um movel aprovado, com a COPIA do checklist. A instalacao
    nao tem entrega propria (D3): ela acontece dentro dos ambientes."""
    textos = checklist_da_configuracao(db)
    for ambiente in sorted(orc.ambientes, key=lambda a: (a.ordem, a.id)):
        if any(m.aprovado for m in ambiente.moveis):
            db.add(MarcenariaEntrega(os_id=os_id, ambiente_id=ambiente.id, checklist=_checklist_vazio(textos),
                                     situacao=SituacaoEntrega.PENDENTE))


def apagar_do_desfazer(db: Session, os_) -> None:
    """08A §7.6: o desfazer apaga as entregas (todas pendentes: o D17 garante) e
    os agendamentos. As fotos ja enviadas continuam na galeria da OS cancelada."""
    for entrega in crud.entregas_da_os(db, os_.id):
        db.delete(entrega)                               # leva pendencias e vinculos de foto
    for agendamento in crud.agendamentos_da_os(db, os_.id):
        db.delete(agendamento)
    os_.data_instalacao = None                           # D20: nada mais a instalar


# ===========================================================================
# LEITURA (secao 6.1)
# ===========================================================================

def _medidas(movel) -> dict[str, Optional[int]]:
    return {"largura_mm": movel.largura_mm, "altura_mm": movel.altura_mm, "profundidade_mm": movel.profundidade_mm}


def _pendencia(p: MarcenariaPendencia) -> dict[str, Any]:
    return {
        "id": p.id, "descricao": p.descricao, "situacao": p.situacao,
        "criada_em": p.criada_em, "criada_por": p.criada_por_nome,
        "resolucao": p.resolucao, "resolvida_em": p.resolvida_em, "resolvida_por": p.resolvida_por_nome,
    }


def _foto(vinculo: MarcenariaEntregaFoto) -> Optional[dict[str, Any]]:
    foto = vinculo.foto
    if foto is None:                                     # apagada pela galeria no meio do caminho
        return None
    return {"id": vinculo.id, "os_foto_id": foto.id, "tipo": vinculo.tipo, "url": foto.url,
            "nome_arquivo": foto.nome_arquivo}


def _agendamento_resumido(agendamento) -> Optional[dict[str, Any]]:
    if agendamento is None:
        return None
    return {"id": agendamento.id, "data": agendamento.data, "hora_inicio": agendamento.hora_inicio,
            "montadores": list(agendamento.montadores or [])}


def _entrega(e: MarcenariaEntrega, agendamentos: list) -> dict[str, Any]:
    """Uma entrega para a tela (e para o termo, na 13B). Sem preco."""
    # O agendamento "da entrega" e o mais recente que inclui o ambiente (secao 6.1).
    do_ambiente = [a for a in agendamentos if e.ambiente_id in a.ambiente_ids]
    ultimo = max(do_ambiente, key=lambda a: (a.data, a.id), default=None)
    fotos = [f for f in (_foto(v) for v in e.fotos) if f is not None]
    return {
        "id": e.id,
        "ambiente_id": e.ambiente_id,
        "ambiente": e.ambiente.nome,
        "situacao": e.situacao,
        "moveis": [
            {"nome": m.nome, "quantidade": m.quantidade, "medidas": _medidas(m)}
            for m in e.ambiente.moveis if m.aprovado
        ],
        "checklist": [{"texto": i.get("texto", ""), "marcacao": i.get("marcacao")} for i in (e.checklist or [])],
        "data_entrega": e.data_entrega,
        "montadores": list(e.montadores or []),
        "recebido_por": e.recebido_por,
        "observacoes": e.observacoes,
        "registrado_por": e.registrado_por_nome,
        "registrado_em": e.registrado_em,
        "pendencias": [_pendencia(p) for p in e.pendencias],
        "fotos": fotos,
        "agendamento": _agendamento_resumido(ultimo),
    }


def resumo_das_entregas(entregas: list[MarcenariaEntrega]) -> dict[str, Any]:
    """D15/D16: quantos ambientes foram entregues, quais faltam e as pendencias abertas."""
    entregues = [e for e in entregas if e.situacao != SituacaoEntrega.PENDENTE]
    abertas = [
        {"id": p.id, "entrega_id": e.id, "ambiente": e.ambiente.nome, "descricao": p.descricao}
        for e in entregas for p in e.pendencias if p.situacao == SituacaoPendencia.ABERTA
    ]
    return {
        "entregues": len(entregues),
        "total": len(entregas),
        "todos_entregues": bool(entregas) and len(entregues) == len(entregas),
        "ambientes_pendentes": [e.ambiente.nome for e in entregas if e.situacao == SituacaoEntrega.PENDENTE],
        "pendencias_abertas": abertas,
    }


def montar_entrega(db: Session, os_: OrdemServico, orc: MarcenariaOrcamento) -> dict[str, Any]:
    """A aba Entrega da OS: projeto, cliente, entregas, agendamentos e resumo (secao 6.1)."""
    entregas = crud.entregas_da_os(db, os_.id)
    agendamentos = crud.agendamentos_da_os(db, os_.id)
    pendentes = regras.ambientes_pendentes(entregas)
    registrados = regras.ambientes_registrados(entregas)
    nome_do_ambiente = {e.ambiente_id: e.ambiente.nome for e in entregas}
    editavel = os_aberta(os_)
    hoje = hoje_local()
    cliente = orc.cliente
    return {
        "os": {"numero_os": os_.numero_os, "status": getattr(os_.status, "value", os_.status), "editavel": editavel},
        "projeto": {
            "codigo": orc.objeto.numero_serie if orc.objeto is not None else None,     # PRJ-... (08A D6)
            "nome": orc.projeto_nome,
            "endereco_obra": orc.endereco_obra,
        },
        "cliente": {
            "nome": nome_do_cliente(cliente) or None,
            "telefone": (cliente.celular or cliente.telefone) if cliente is not None else None,
        },
        "entregas": [_entrega(e, agendamentos) for e in entregas],
        "agendamentos": [
            {
                "id": a.id, "data": a.data, "hora_inicio": a.hora_inicio,
                "ambiente_ids": list(a.ambiente_ids),
                "ambientes": [nome_do_ambiente.get(aid, "Ambiente removido") for aid in a.ambiente_ids],
                "montadores": list(a.montadores or []),
                "observacao": a.observacao,
                "criado_por": a.criado_por_nome,
                "atrasado": regras.atrasado(a, pendentes, hoje),
                # D10: com entrega registrada vira historico; OS fechada nao muda.
                "editavel": editavel and not regras.travado(a, registrados),
            }
            for a in agendamentos
        ],
        "resumo": resumo_das_entregas(entregas),
        "avisos": [],
    }


def ler(db: Session, numero_os: str) -> dict[str, Any]:
    """GET /os/{numero_os}/entrega."""
    os_, orc = os_e_orcamento_aprovado(db, numero_os, MSG_SEM_ORCAMENTO)
    return montar_entrega(db, os_, orc)


def resumo(db: Session, numero_os: str) -> dict[str, Any]:
    """GET /os/{numero_os}/entrega/resumo: para o aviso da finalizacao (D15)."""
    os_, _orc = os_e_orcamento_aprovado(db, numero_os, MSG_SEM_ORCAMENTO)
    return resumo_das_entregas(crud.entregas_da_os(db, os_.id))


# ===========================================================================
# ESCRITAS
# ===========================================================================

def os_editavel(db: Session, numero_os: str) -> tuple:
    """(OS, orcamento) com a OS ABERTA; fechada = 409 OS_FECHADA. Publica: a agenda usa."""
    os_, orc = os_e_orcamento_aprovado(db, numero_os, MSG_SEM_ORCAMENTO)
    if not os_aberta(os_):
        erros.conflito(OS_FECHADA, MSG_OS_FECHADA)
    return os_, orc


def _entrega_da_os(db: Session, os_, entrega_id: int) -> MarcenariaEntrega:
    entrega = next((e for e in crud.entregas_da_os(db, os_.id) if e.id == entrega_id), None)
    if entrega is None:
        erros.nao_encontrado(MSG_ENTREGA_FORA)
    return entrega


def _responder(db: Session, os_, orc, avisos: Optional[list] = None) -> dict[str, Any]:
    """Grava e devolve a aba atualizada (com os avisos da acao)."""
    db.commit()
    resposta = montar_entrega(db, os_, orc)
    resposta["avisos"] = avisos or []
    return resposta


def editar_checklist(db: Session, numero_os: str, entrega_id: int, dados: ChecklistEntrada,
                     usuario: dict) -> dict[str, Any]:
    """D2: a lista do ambiente, enquanto a entrega esta pendente (regras da 04A)."""
    os_, orc = os_editavel(db, numero_os)
    entrega = _entrega_da_os(db, os_, entrega_id)
    if entrega.situacao != SituacaoEntrega.PENDENTE:
        erros.conflito(erros.TRANSICAO_INVALIDA, MSG_CHECKLIST_REGISTRADO)
    try:
        textos = _lista_de_nomes(dados.itens, LIMITE_ITENS, LIMITE_TEXTO, "Checklist")
    except ValueError as erro:
        erros.invalido(str(erro))
    entrega.checklist = _checklist_vazio(textos)          # lista NOVA: o JSON e regravado
    registrar_evento(db, orc, "ENTREGA_CHECKLIST_EDITADO",
                     f"Checklist da entrega de {entrega.ambiente.nome} alterado ({len(textos)} itens).",
                     usuario, {"entrega_id": entrega.id}, os_id=os_.id)
    return _responder(db, os_, orc)


def _aplicar_marcacoes(entrega: MarcenariaEntrega, marcacoes: Optional[list]) -> None:
    """D4: as marcacoes do papel, na ordem do checklist. Nulo = nao mexe."""
    if marcacoes is None:
        return
    itens = list(entrega.checklist or [])
    if len(marcacoes) != len(itens):
        erros.invalido(MSG_MARCACOES)
    entrega.checklist = [{"texto": i.get("texto", ""), "marcacao": m} for i, m in zip(itens, marcacoes)]


def _tem_foto_do_termo(entrega: MarcenariaEntrega) -> bool:
    return any(v.tipo == TipoFotoEntrega.TERMO and v.foto is not None for v in entrega.fotos)


def _nova_pendencia(descricao: str, usuario: dict) -> MarcenariaPendencia:
    return MarcenariaPendencia(descricao=descricao, situacao=SituacaoPendencia.ABERTA,
                               criada_em=agora_utc(), criada_por_nome=usuario_nome(usuario))


def registrar(db: Session, numero_os: str, entrega_id: int, dados: RegistroEntrada, usuario: dict) -> dict[str, Any]:
    """D4/D5: o resultado do termo (tambem corrige um registro anterior)."""
    os_, orc = os_editavel(db, numero_os)                 # D5: so com a OS aberta
    entrega = _entrega_da_os(db, os_, entrega_id)
    if dados.situacao == SituacaoEntrega.COM_RESSALVAS and not dados.pendencias and not entrega.pendencias:
        erros.invalido(MSG_RESSALVAS)                     # D4
    quando = dados.data_entrega or hoje_local()
    if quando > hoje_local():
        erros.invalido(MSG_DATA_FUTURA)
    montadores = regras.montadores(db, dados.montadores, so_ativos=False)
    _aplicar_marcacoes(entrega, dados.checklist)

    anterior = entrega.situacao
    entrega.situacao = dados.situacao
    entrega.data_entrega = quando
    entrega.montadores = montadores                      # copia dos nomes (I4)
    entrega.recebido_por, entrega.observacoes = dados.recebido_por, dados.observacoes
    for texto in dados.pendencias:
        entrega.pendencias.append(_nova_pendencia(texto, usuario))
    entrega.registrado_por_nome, entrega.registrado_em = usuario_nome(usuario), agora_utc()

    ambiente = entrega.ambiente.nome
    if anterior == SituacaoEntrega.PENDENTE:
        tipo, frase = "ENTREGA_REGISTRADA", f"Entrega de {ambiente} registrada: {ROTULO[entrega.situacao]}."
    else:                                                # D5: a correcao conta de onde para onde
        tipo = "ENTREGA_CORRIGIDA"
        frase = f"Entrega de {ambiente} corrigida: {ROTULO[anterior]} → {ROTULO[entrega.situacao]}."
    if dados.pendencias:
        frase += f" {len(dados.pendencias)} pendência(s) anotada(s)."
    registrar_evento(db, orc, tipo, frase[:500], usuario,
                     {"entrega_id": entrega.id, "situacao": entrega.situacao, "data_entrega": quando.isoformat(),
                      "montadores": [m["funcionario_id"] for m in montadores]}, os_id=os_.id)
    regras.sincronizar_data_instalacao(db, os_)          # D20: o ambiente saiu da fila
    # D8: sem a foto do termo, avisa (nao trava).
    return _responder(db, os_, orc, [] if _tem_foto_do_termo(entrega) else [dict(AVISO_SEM_FOTO_TERMO)])


# --- Pendencias (D6): valem ate com a OS finalizada -----------------------------------------

def _entrega_para_pendencia(db: Session, numero_os: str, entrega_id: int) -> tuple:
    os_, orc = os_e_orcamento_aprovado(db, numero_os, MSG_SEM_ORCAMENTO)   # sem exigir a OS aberta
    return os_, orc, _entrega_da_os(db, os_, entrega_id)


def _pendencia_da_entrega(entrega: MarcenariaEntrega, pendencia_id: int) -> MarcenariaPendencia:
    pendencia = next((p for p in entrega.pendencias if p.id == pendencia_id), None)
    if pendencia is None:
        erros.nao_encontrado(MSG_PENDENCIA_FORA)
    return pendencia


def criar_pendencia(db: Session, numero_os: str, entrega_id: int, dados: PendenciaEntrada,
                    usuario: dict) -> dict[str, Any]:
    """D6: o cliente ligou na semana seguinte. So depois do registro da entrega."""
    os_, orc, entrega = _entrega_para_pendencia(db, numero_os, entrega_id)
    if entrega.situacao == SituacaoEntrega.PENDENTE:
        erros.invalido(MSG_PENDENCIA_SEM_REGISTRO)
    entrega.pendencias.append(_nova_pendencia(dados.descricao, usuario))
    registrar_evento(db, orc, "PENDENCIA_CRIADA",
                     f"Pendência em {entrega.ambiente.nome}: {dados.descricao}"[:500],
                     usuario, {"entrega_id": entrega.id}, os_id=os_.id)
    return _responder(db, os_, orc)


def resolver_pendencia(db: Session, numero_os: str, entrega_id: int, pendencia_id: int, dados: ResolverEntrada,
                       usuario: dict) -> dict[str, Any]:
    """D6: como foi resolvida, quando e por quem."""
    os_, orc, entrega = _entrega_para_pendencia(db, numero_os, entrega_id)
    pendencia = _pendencia_da_entrega(entrega, pendencia_id)
    if pendencia.situacao == SituacaoPendencia.RESOLVIDA:
        erros.conflito(erros.TRANSICAO_INVALIDA, "Esta pendência já está resolvida.")
    quando = dados.data or hoje_local()
    if quando > hoje_local():
        erros.invalido("A data da resolução não pode ser no futuro.")
    pendencia.situacao = SituacaoPendencia.RESOLVIDA
    pendencia.resolucao, pendencia.resolvida_em = dados.resolucao, quando
    pendencia.resolvida_por_nome = usuario_nome(usuario)
    registrar_evento(db, orc, "PENDENCIA_RESOLVIDA",
                     f"Pendência resolvida em {entrega.ambiente.nome} ({pendencia.descricao}): {dados.resolucao}"[:500],
                     usuario, {"entrega_id": entrega.id, "pendencia_id": pendencia.id}, os_id=os_.id)
    return _responder(db, os_, orc)


def reabrir_pendencia(db: Session, numero_os: str, entrega_id: int, pendencia_id: int,
                      usuario: dict) -> dict[str, Any]:
    """D6: o problema voltou. Limpa a resolucao (o historico guarda a anterior)."""
    os_, orc, entrega = _entrega_para_pendencia(db, numero_os, entrega_id)
    pendencia = _pendencia_da_entrega(entrega, pendencia_id)
    if pendencia.situacao == SituacaoPendencia.ABERTA:
        erros.conflito(erros.TRANSICAO_INVALIDA, "Esta pendência já está aberta.")
    pendencia.situacao = SituacaoPendencia.ABERTA
    pendencia.resolucao = pendencia.resolvida_em = pendencia.resolvida_por_nome = None
    registrar_evento(db, orc, "PENDENCIA_REABERTA",
                     f"Pendência reaberta em {entrega.ambiente.nome}: {pendencia.descricao}"[:500],
                     usuario, {"entrega_id": entrega.id, "pendencia_id": pendencia.id}, os_id=os_.id)
    return _responder(db, os_, orc)


# --- Fotos (D7): fotos da OS com o vinculo ao ambiente ----------------------------------

def enviar_foto(db: Session, numero_os: str, entrega_id: int, tipo: str, arquivo: UploadFile,
                usuario: dict) -> dict[str, Any]:
    """D7: a foto entra na galeria da OS (pipeline e limites de sempre) e fica ligada a entrega."""
    os_, orc = os_editavel(db, numero_os)
    entrega = _entrega_da_os(db, os_, entrega_id)          # tudo conferido ANTES de gravar o arquivo
    foto = os_foto_service.upload_foto_os(db, os_.numero_os, arquivo)
    entrega.fotos.append(MarcenariaEntregaFoto(os_foto_id=foto.id, tipo=tipo))
    return _responder(db, os_, orc)


def excluir_foto(db: Session, numero_os: str, entrega_id: int, vinculo_id: int, usuario: dict) -> dict[str, Any]:
    """D7: excluir pela entrega exclui a foto da OS (arquivo e galeria)."""
    os_, orc = os_editavel(db, numero_os)
    entrega = _entrega_da_os(db, os_, entrega_id)
    vinculo = next((v for v in entrega.fotos if v.id == vinculo_id), None)
    if vinculo is None:
        erros.nao_encontrado(MSG_FOTO_FORA)
    os_foto_id = vinculo.os_foto_id
    entrega.fotos.remove(vinculo)                        # primeiro o vinculo (a sessao fica coerente)
    db.flush()
    os_foto_service.delete_foto_os(db, os_.numero_os, os_foto_id)
    return _responder(db, os_, orc)
