# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/producao.py
# DESCRICAO: Producao da OS da marcenaria: etapas por movel, progresso,
#            sugestao de status e o quadro da fabrica (Spec 12A).
# ---------------------------------------------------------------------------
"""
- Na APROVACAO, cada movel INTERNO recebe uma copia das etapas padrao da
  configuracao (D1). O movel TERCEIRIZADO nao tem etapas: esta pronto quando
  CONFERIDO (11A).
- A ordem das etapas NAO e imposta (D10): da para concluir Montagem antes de
  Borda. A resposta so indica a proxima etapa de cada movel.
- Concluir e IDEMPOTENTE (D12): concluir de novo nao muda nada, sem 409.
- O backend NUNCA muda o status da OS (P2): ele so SUGERE ("Em Producao" na
  primeira etapa; "Aguardando Entrega" quando tudo fica pronto) e a tela
  pergunta ao usuario.
- Nenhum preco em nenhuma resposta (P4): e a tela do marceneiro.
"""

from collections import Counter
from datetime import date
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.enum import OrdemServicoStatus
from app.core.tempo import agora_utc, hoje_local
from app.db.crud import empresa as empresa_crud
from app.db.crud.configuracao_marcenaria import get_configuracao_marcenaria
from app.db.crud.marcenaria import orcamento as crud
from app.db.models.configuracao_marcenaria import ETAPAS_PADRAO
from app.db.models.funcionario import Funcionario
from app.db.models.marcenaria.ambiente import MarcenariaAmbiente, MarcenariaMovel
from app.db.models.marcenaria.etapa import MarcenariaEtapa, StatusEtapa
from app.db.models.marcenaria.orcamento import MarcenariaOrcamento, StatusOrcamento
from app.db.models.ordem_servico import OrdemServico
from app.db.models.pedido_compra import PedidoCompra
from app.schemas.configuracao_marcenaria import _lista_de_nomes
from app.schemas.marcenaria.producao import EtapasDoMovelEntrada, LoteEntrada
from app.services.marcenaria import erros
from app.services.marcenaria import terceirizado_situacao as terceirizado
from app.services.marcenaria.aprovacao_bloqueios import rotulo_status_os
from app.services.marcenaria.orcamento_comum import (
    exigir_orcamento_tecnico,
    os_aberta,
    os_e_orcamento_aprovado,
    registrar_evento,
    usuario_nome,
)
from app.services.marcenaria.orcamento_detalhe import nome_do_cliente

# --- Frases e codigos (secao 6.2) -------------------------------------------------
MSG_SEM_ORCAMENTO = "Esta OS não veio de um orçamento."
MSG_OS_FECHADA = "A OS está finalizada ou cancelada; a produção não pode mais ser alterada."
MSG_ETAPA_FORA = "Etapa não encontrada nesta OS."
MSG_MOVEL_FORA = "Este móvel não faz parte desta OS."
MSG_LOTE_VAZIO = "Escolha pelo menos uma etapa."
MSG_TERCEIRIZADO = "Móvel terceirizado não tem etapas de produção: ele fica pronto quando é conferido."
OS_FECHADA = "OS_FECHADA"
ETAPA_CONCLUIDA = "ETAPA_CONCLUIDA"

LIMITE_ETAPAS = 20                       # D4: as mesmas regras da configuracao (04A)
LIMITE_NOME = 60

# O "andamento" da producao da OS, para decidir a sugestao (D16, D17).
NAO_INICIADA, EM_ANDAMENTO, CONCLUIDA = "NAO_INICIADA", "EM_ANDAMENTO", "CONCLUIDA"

# ===========================================================================
# AJUDANTES
# ===========================================================================

def _valor(status) -> str:
    return getattr(status, "value", status)


def _aprovados(orc: MarcenariaOrcamento) -> list[tuple[MarcenariaAmbiente, MarcenariaMovel]]:
    """Os moveis APROVADOS, na ordem da tela (ambiente, movel)."""
    return [
        (ambiente, movel)
        for ambiente in sorted(orc.ambientes, key=lambda a: (a.ordem, a.id))
        for movel in sorted(ambiente.moveis, key=lambda m: (m.ordem, m.id))
        if movel.aprovado
    ]


def _interno(movel: MarcenariaMovel) -> bool:
    return movel.tipo_producao != terceirizado.TERCEIRIZADA


def _etapas(movel: MarcenariaMovel) -> list[MarcenariaEtapa]:
    return sorted(movel.etapas, key=lambda e: (e.ordem, e.id))


def _plural(n: int) -> str:
    return f"{n} móvel" if n == 1 else f"{n} móveis"


def etapas_da_configuracao(db: Session) -> list[str]:
    """As etapas padrao da configuracao de AGORA (sem configuracao: as da 04A).

    Lista vazia vale como esta: a aprovacao deixa o movel "sem etapas" (D6).
    """
    config = get_configuracao_marcenaria(db, empresa_crud.get_empresa_atual(db).id)
    return list(config.etapas_producao or []) if config is not None else list(ETAPAS_PADRAO)


def _novas_etapas(nomes: list[str]) -> list[MarcenariaEtapa]:
    return [MarcenariaEtapa(nome=nome, ordem=ordem, status=StatusEtapa.PENDENTE) for ordem, nome in enumerate(nomes, 1)]


# ===========================================================================
# APROVACAO E DESFAZER (chamadas pela 08A)
# ===========================================================================

def criar_etapas_da_aprovacao(db: Session, orc: MarcenariaOrcamento) -> None:
    """D1: dentro da transacao da aprovacao, uma COPIA das etapas padrao em cada
    movel interno aprovado. Mudar a configuracao depois nao mexe nesta OS."""
    nomes = etapas_da_configuracao(db)
    for _a, movel in _aprovados(orc):
        if _interno(movel) and not movel.etapas:
            movel.etapas = _novas_etapas(nomes)


def apagar_etapas_do_desfazer(orc: MarcenariaOrcamento) -> None:
    """08A §7.5: o desfazer apaga as etapas (todas pendentes: o D20 garante)."""
    for ambiente in orc.ambientes:
        for movel in ambiente.moveis:
            movel.etapas.clear()


# ===========================================================================
# LEITURA (secao 6.1)
# ===========================================================================

def _etapa(etapa: MarcenariaEtapa) -> dict[str, Any]:
    return {
        "id": etapa.id,
        "nome": etapa.nome,
        "ordem": etapa.ordem,
        "status": etapa.status,
        "responsavel": etapa.responsavel_nome,
        "responsavel_funcionario_id": etapa.responsavel_funcionario_id,
        "iniciada_em": etapa.iniciada_em,
        "concluida_em": etapa.concluida_em,
        "concluida_por": etapa.concluida_por_nome,
    }


def _medidas(movel: MarcenariaMovel) -> dict[str, Optional[int]]:
    return {"largura_mm": movel.largura_mm, "altura_mm": movel.altura_mm, "profundidade_mm": movel.profundidade_mm}


def _montar(os_: OrdemServico, orc: MarcenariaOrcamento, pedidos: dict[int, PedidoCompra], hoje: date) -> dict[str, Any]:
    """A producao da OS: cada movel, o progresso e se tudo esta pronto (D15)."""
    moveis = []
    etapas_total = etapas_concluidas = prontos = 0
    for ambiente, movel in _aprovados(orc):
        linha = {
            "movel_id": movel.id, "nome": movel.nome, "ambiente": ambiente.nome, "quantidade": movel.quantidade,
            "medidas": _medidas(movel), "tipo_producao": movel.tipo_producao,
        }
        if _interno(movel):
            etapas = _etapas(movel)
            pronto = bool(etapas) and all(e.status == StatusEtapa.CONCLUIDA for e in etapas)
            linha.update(
                pronto=pronto,
                sem_etapas=not etapas,                  # D6: sem caminho para ficar pronto
                # D10: a primeira etapa ainda nao concluida, na ordem do movel.
                proxima_etapa=next((e.nome for e in etapas if e.status != StatusEtapa.CONCLUIDA), None),
                etapas=[_etapa(e) for e in etapas],
            )
            etapas_total += len(etapas)
            etapas_concluidas += sum(1 for e in etapas if e.status == StatusEtapa.CONCLUIDA)
        else:
            # D5: o terceirizado fica pronto quando CONFERIDO (11A, nos dois modos).
            pedido = pedidos.get(movel.pedido_compra_id) if movel.pedido_compra_id else None
            situacao = terceirizado.situacao_do_movel(movel, pedido)
            pronto = situacao.situacao == terceirizado.CONFERIDO
            linha.update(pronto=pronto, terceirizado={
                "situacao": situacao.situacao, "previsao": situacao.previsao,
                "atrasado": terceirizado.atrasado(situacao, hoje),
            })
        prontos += pronto
        moveis.append(linha)
    return {
        "os": {
            "numero_os": os_.numero_os, "status": _valor(os_.status), "editavel": os_aberta(os_),
            "previsao": os_.data_previsao.date() if os_.data_previsao else None,
        },
        "progresso": {"etapas_concluidas": etapas_concluidas, "etapas_total": etapas_total,
                      "moveis_prontos": prontos, "moveis_total": len(moveis)},
        "producao_concluida": bool(moveis) and prontos == len(moveis),
        "moveis": moveis,
        "sugestao_status": None,
    }


def montar_producao(db: Session, os_: OrdemServico, orc: MarcenariaOrcamento) -> dict[str, Any]:
    """A producao de uma OS (le os pedidos do Compras dos terceirizados numa consulta)."""
    ids = sorted({m.pedido_compra_id for _a, m in _aprovados(orc) if m.pedido_compra_id})
    return _montar(os_, orc, crud.buscar_por_ids(db, PedidoCompra, ids), hoje_local())


def andamento(producao: dict[str, Any]) -> str:
    """NAO_INICIADA, EM_ANDAMENTO ou CONCLUIDA (a sugestao so aparece na MUDANCA, D17)."""
    if producao["producao_concluida"]:
        return CONCLUIDA
    comecou = any(
        etapa["status"] != StatusEtapa.PENDENTE
        for movel in producao["moveis"] for etapa in movel.get("etapas", [])
    )
    return EM_ANDAMENTO if comecou else NAO_INICIADA


def sugestao(db: Session, os_: OrdemServico, antes: str, producao: dict[str, Any]) -> Optional[dict[str, str]]:
    """D16/D17: o proximo status da OS, so quando o andamento MUDA. Nada e gravado.

    - a producao acabou (e a OS ainda nao chegou la) -> AGUARDANDO_RETIRADA ("Aguardando Entrega");
    - a primeira etapa saiu de "pendente" numa OS ABERTA -> EM_ANDAMENTO ("Em Producao").
    """
    depois = andamento(producao)
    status_os = _valor(os_.status)
    para = None
    if depois == CONCLUIDA and antes != CONCLUIDA and status_os in ("ABERTA", "EM_ANDAMENTO", "AGUARDANDO_PECAS"):
        para = OrdemServicoStatus.AGUARDANDO_RETIRADA.value
    elif antes == NAO_INICIADA and depois != NAO_INICIADA and status_os == "ABERTA":
        para = OrdemServicoStatus.EM_ANDAMENTO.value
    if para is None:
        return None
    return {"de": status_os, "para": para, "rotulo": rotulo_status_os(db, para)}


def ler(db: Session, numero_os: str) -> dict[str, Any]:
    """GET /os/{numero_os}/producao."""
    os_, orc = os_e_orcamento_aprovado(db, numero_os, MSG_SEM_ORCAMENTO)
    return montar_producao(db, os_, orc)


# ===========================================================================
# ESCRITAS
# ===========================================================================

def _preparar(db: Session, numero_os: str) -> tuple:
    """OS aberta (D13) e o andamento ANTES da acao (para a sugestao)."""
    os_, orc = os_e_orcamento_aprovado(db, numero_os, MSG_SEM_ORCAMENTO)
    if not os_aberta(os_):
        erros.conflito(OS_FECHADA, MSG_OS_FECHADA)
    return os_, orc, andamento(montar_producao(db, os_, orc))


def _responder(db: Session, os_: OrdemServico, orc: MarcenariaOrcamento, antes: str) -> dict[str, Any]:
    """Grava e devolve a producao atualizada com a sugestao de status (secao 6)."""
    db.commit()
    producao = montar_producao(db, os_, orc)
    producao["sugestao_status"] = sugestao(db, os_, antes, producao)
    return producao


def _etapas_por_id(orc: MarcenariaOrcamento, etapa_ids: list[int]) -> list[tuple[MarcenariaMovel, MarcenariaEtapa]]:
    """As etapas pedidas, todas desta OS. Uma de fora = 404 e NADA muda (caso 18)."""
    if not etapa_ids:
        erros.invalido(MSG_LOTE_VAZIO)
    da_os = {e.id: (m, e) for _a, m in _aprovados(orc) for e in m.etapas}
    if any(etapa_id not in da_os for etapa_id in etapa_ids):
        erros.nao_encontrado(MSG_ETAPA_FORA)
    return [da_os[etapa_id] for etapa_id in dict.fromkeys(etapa_ids)]


def _responsavel(db: Session, funcionario_id: Optional[int], usuario: dict) -> tuple[Optional[int], str]:
    """D7: quem faz. Padrao: o funcionario do usuario logado; pode ser outro, ativo."""
    escolhido = funcionario_id if funcionario_id is not None else usuario.get("funcionario_id")
    if escolhido is not None:
        funcionario = db.get(Funcionario, escolhido)
        if funcionario is None or not funcionario.ativo:
            if funcionario_id is not None:                    # escolhido na tela: avisa
                erros.invalido("Funcionário não encontrado ou inativo.")
        else:
            return funcionario.id, funcionario.nome
    return None, usuario_nome(usuario)                        # usuario sem funcionario (ex.: o dono)


def _frase_lote(verbo: str, pares: list, usuario: dict) -> str:
    """D14: UM evento para o lote. "Etapa Corte concluída em 6 móveis por João."."""
    por_nome = Counter(etapa.nome for _m, etapa in pares)
    quem = usuario_nome(usuario)
    if len(por_nome) == 1:
        (nome, n), = por_nome.items()
        return f"Etapa {nome} {verbo} em {_plural(n)} por {quem}."
    partes = ", ".join(f"{nome} ({_plural(n)})" for nome, n in por_nome.most_common())
    return f"Etapas {verbo}s por {quem}: {partes}."


def iniciar(db: Session, numero_os: str, dados: LoteEntrada, usuario: dict) -> dict[str, Any]:
    """D7, D11: PENDENTE -> EM_EXECUCAO com o responsavel. As outras ficam como estao."""
    os_, orc, antes = _preparar(db, numero_os)
    pares = _etapas_por_id(orc, dados.etapa_ids)
    responsavel_id, responsavel_nome = _responsavel(db, dados.responsavel_funcionario_id, usuario)
    mudaram = [(m, e) for m, e in pares if e.status == StatusEtapa.PENDENTE]
    for _m, etapa in mudaram:
        etapa.status = StatusEtapa.EM_EXECUCAO
        etapa.iniciada_em = agora_utc()
        etapa.responsavel_funcionario_id, etapa.responsavel_nome = responsavel_id, responsavel_nome
    if mudaram:
        registrar_evento(db, orc, "ETAPAS_INICIADAS", _frase_lote("iniciada", mudaram, usuario), usuario,
                         {"etapa_ids": [e.id for _m, e in mudaram]}, os_id=os_.id)
    return _responder(db, os_, orc, antes)


def _concluir(db: Session, os_, orc, pares: list, funcionario_id: Optional[int], usuario: dict) -> None:
    """D8, D12: conclui as que nao estavam concluidas (as concluidas ficam intactas)."""
    responsavel_id, responsavel_nome = _responsavel(db, funcionario_id, usuario)
    mudaram = [(m, e) for m, e in pares if e.status != StatusEtapa.CONCLUIDA]
    for _m, etapa in mudaram:
        etapa.status = StatusEtapa.CONCLUIDA
        etapa.concluida_em = agora_utc()
        etapa.concluida_por_nome = usuario_nome(usuario)
        if etapa.responsavel_funcionario_id is None and not etapa.responsavel_nome:
            # D8: marcada direto do "pendente" (o comum no fim do dia): quem fez = o padrao.
            etapa.responsavel_funcionario_id, etapa.responsavel_nome = responsavel_id, responsavel_nome
    if mudaram:
        registrar_evento(db, orc, "ETAPAS_CONCLUIDAS", _frase_lote("concluída", mudaram, usuario), usuario,
                         {"etapa_ids": [e.id for _m, e in mudaram]}, os_id=os_.id)


def concluir(db: Session, numero_os: str, dados: LoteEntrada, usuario: dict) -> dict[str, Any]:
    os_, orc, antes = _preparar(db, numero_os)
    _concluir(db, os_, orc, _etapas_por_id(orc, dados.etapa_ids), dados.responsavel_funcionario_id, usuario)
    return _responder(db, os_, orc, antes)


def concluir_em_todos(db: Session, numero_os: str, nome: str, usuario: dict) -> dict[str, Any]:
    """D11: "concluir o Corte em todos os moveis da OS" (o nome sem diferenciar maiusculas)."""
    os_, orc, antes = _preparar(db, numero_os)
    alvo = nome.strip().casefold()
    pares = [(m, e) for _a, m in _aprovados(orc) for e in m.etapas if e.nome.casefold() == alvo]
    if not pares:
        erros.invalido(f"Nenhum móvel desta OS tem a etapa {nome.strip()}.")
    _concluir(db, os_, orc, pares, None, usuario)
    return _responder(db, os_, orc, antes)


def reabrir(db: Session, numero_os: str, etapa_id: int, usuario: dict) -> dict[str, Any]:
    """D9: volta a PENDENTE, limpando datas, conclusao e responsavel (o evento guarda a historia)."""
    os_, orc, antes = _preparar(db, numero_os)
    ((movel, etapa),) = _etapas_por_id(orc, [etapa_id])
    if etapa.status != StatusEtapa.PENDENTE:
        de = "concluída" if etapa.status == StatusEtapa.CONCLUIDA else "em execução"
        etapa.status = StatusEtapa.PENDENTE
        etapa.iniciada_em = etapa.concluida_em = None
        etapa.concluida_por_nome = None
        etapa.responsavel_funcionario_id = etapa.responsavel_nome = None
        registrar_evento(db, orc, "ETAPA_REABERTA",
                         f"Etapa {etapa.nome} do móvel {movel.nome} reaberta (estava {de}) por {usuario_nome(usuario)}.",
                         usuario, {"etapa_id": etapa.id}, os_id=os_.id)
    return _responder(db, os_, orc, antes)


def _movel_interno(orc: MarcenariaOrcamento, movel_id: int) -> MarcenariaMovel:
    movel = next((m for _a, m in _aprovados(orc) if m.id == movel_id), None)
    if movel is None:
        erros.nao_encontrado(MSG_MOVEL_FORA)
    if not _interno(movel):
        erros.invalido(MSG_TERCEIRIZADO)
    return movel


def editar_etapas(db: Session, numero_os: str, movel_id: int, dados: EtapasDoMovelEntrada, usuario: dict) -> dict[str, Any]:
    """D3/D4: a lista nova do movel, na ordem nova (`id` = etapa que ja existia).

    Etapa CONCLUIDA nao pode ser removida nem renomeada: o que foi feito nao
    some do historico (reabra antes). As regras de nome sao as da configuracao.
    """
    os_, orc, antes = _preparar(db, numero_os)
    movel = _movel_interno(orc, movel_id)
    try:
        nomes = _lista_de_nomes([e.nome for e in dados.etapas], LIMITE_ETAPAS, LIMITE_NOME, "Etapas")
    except ValueError as erro:
        erros.invalido(str(erro))
    atuais = {e.id: e for e in movel.etapas}
    if any(e.id is not None and e.id not in atuais for e in dados.etapas):
        erros.nao_encontrado(MSG_ETAPA_FORA)
    mantidas = {e.id for e in dados.etapas if e.id is not None}
    for etapa in atuais.values():
        if etapa.status != StatusEtapa.CONCLUIDA:
            continue
        novo_nome = next((n for e, n in zip(dados.etapas, nomes) if e.id == etapa.id), None)
        if etapa.id not in mantidas or novo_nome != etapa.nome:
            erros.conflito(ETAPA_CONCLUIDA,
                           f"A etapa {etapa.nome} está concluída: reabra antes de remover ou renomear.")

    # 1) Remove as que sairam; 2) nomes provisorios unicos nas que ficam (trocar
    # "Borda" por "Corte" e vice-versa nao bate na unicidade no meio do caminho);
    # 3) os nomes e a ordem finais, e as novas no lugar delas.
    for etapa_id, etapa in atuais.items():
        if etapa_id not in mantidas:
            movel.etapas.remove(etapa)
    for etapa_id in mantidas:
        atuais[etapa_id].nome = f"~{etapa_id}"
    db.flush()
    for ordem, (entrada, nome) in enumerate(zip(dados.etapas, nomes), start=1):
        if entrada.id is not None:
            atuais[entrada.id].nome, atuais[entrada.id].ordem = nome, ordem
        else:
            movel.etapas.append(MarcenariaEtapa(nome=nome, ordem=ordem, status=StatusEtapa.PENDENTE))
    registrar_evento(db, orc, "ETAPAS_EDITADAS", f"Etapas do móvel {movel.nome}: {', '.join(nomes)}.",
                     usuario, {"movel_id": movel.id, "etapas": nomes}, os_id=os_.id)
    return _responder(db, os_, orc, antes)


def aplicar_padrao(db: Session, numero_os: str, movel_id: int, usuario: dict) -> dict[str, Any]:
    """D6: movel sem etapas ganha as etapas ATUAIS da configuracao."""
    os_, orc, antes = _preparar(db, numero_os)
    movel = _movel_interno(orc, movel_id)
    if movel.etapas:
        erros.conflito("JA_TEM_ETAPAS", f"O móvel {movel.nome} já tem etapas: edite a lista.")
    # Configuracao vazia: as etapas padrao do sistema (o movel precisa de um caminho).
    nomes = etapas_da_configuracao(db) or list(ETAPAS_PADRAO)
    movel.etapas = _novas_etapas(nomes)
    registrar_evento(db, orc, "ETAPAS_EDITADAS", f"Etapas padrão aplicadas ao móvel {movel.nome}: {', '.join(nomes)}.",
                     usuario, {"movel_id": movel.id, "etapas": nomes}, os_id=os_.id)
    return _responder(db, os_, orc, antes)


# ===========================================================================
# QUADRO DA FABRICA (D18)
# ===========================================================================

def quadro(db: Session) -> dict[str, Any]:
    """GET /producao: as OS abertas da marcenaria, com progresso e a proxima etapa.

    Poucas consultas no total (a arvore, as etapas e os pedidos vem de uma vez
    para todas as OS), nunca uma por OS num laco.
    """
    exigir_orcamento_tecnico(db)
    orcamentos = db.scalars(
        select(MarcenariaOrcamento)
        .join(OrdemServico, OrdemServico.id == MarcenariaOrcamento.os_id)
        .where(
            MarcenariaOrcamento.status == StatusOrcamento.APROVADO,
            OrdemServico.ativo.is_(True),
            OrdemServico.status.not_in([OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA]),
        )
        .options(
            selectinload(MarcenariaOrcamento.os),
            selectinload(MarcenariaOrcamento.cliente),
            selectinload(MarcenariaOrcamento.ambientes)
            .selectinload(MarcenariaAmbiente.moveis)
            .selectinload(MarcenariaMovel.etapas),
        )
    ).all()
    ids = sorted({m.pedido_compra_id for orc in orcamentos for _a, m in _aprovados(orc) if m.pedido_compra_id})
    pedidos = crud.buscar_por_ids(db, PedidoCompra, ids)
    hoje = hoje_local()

    itens = []
    for orc in orcamentos:
        producao = _montar(orc.os, orc, pedidos, hoje)
        previsao = producao["os"]["previsao"]
        proximas = Counter(m["proxima_etapa"] for m in producao["moveis"] if m.get("proxima_etapa"))
        mais_comum = proximas.most_common(1)
        itens.append({
            "numero_os": orc.os.numero_os,
            "cliente": nome_do_cliente(orc.cliente) or None,
            "projeto": orc.projeto_nome,
            "status": producao["os"]["status"],
            "rotulo_status": rotulo_status_os(db, producao["os"]["status"]),
            "previsao": previsao,
            "progresso": producao["progresso"],
            "producao_concluida": producao["producao_concluida"],
            # Moveis ainda nao prontos com a previsao de entrega da OS ja vencida.
            "moveis_atrasados": sum(1 for m in producao["moveis"] if not m["pronto"]) if previsao and previsao < hoje else 0,
            # "Montagem em 4 moveis": onde esta a maior parte da OS.
            "proxima_etapa": {"nome": mais_comum[0][0], "moveis": mais_comum[0][1]} if mais_comum else None,
        })
    itens.sort(key=lambda i: (i["previsao"] or date.max, i["numero_os"]))
    return {"itens": itens}
