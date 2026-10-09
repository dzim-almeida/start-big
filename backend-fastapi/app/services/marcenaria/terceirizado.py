# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/terceirizado.py
# DESCRICAO: Moveis TERCEIRIZADOS da OS da marcenaria (Spec 11A): a marcenaria
#            compra pronto de uma central parceira e so instala.
# ---------------------------------------------------------------------------
"""
Dois modos, conforme a loja tem o modulo COMPRAS:

- COM o Compras: "Pedir a central" cria UM pedido de SERVICO no Compras (um
  item por movel) e a situacao do movel ACOMPANHA o pedido (D2). Enviar,
  receber, cancelar e lancar a conta sao do Compras, como ele e (FB2).
- SEM o Compras: a fabrica anota o pedido e a chegada a mao (D3); a conta da
  central e lancada em Contas a Pagar.

"Conferido" e "registrar problema" sao da marcenaria nos dois modos: o
Compras sabe se chegou; a fabrica sabe se o movel esta bom para instalar.

Uma regra para a situacao (terceirizado_situacao.situacao_do_movel), usada
aqui, no bloqueio do "desfazer aprovacao" e na producao (12A).
"""

from datetime import date
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enum import OrdemServicoStatus
from app.core.tempo import hoje_local
from app.db.crud.marcenaria import orcamento as crud
from app.db.models.marcenaria.ambiente import MarcenariaAmbiente, MarcenariaMovel
from app.db.models.marcenaria.orcamento import MarcenariaOrcamento, StatusOrcamento
from app.db.models.ordem_servico import OrdemServico
from app.db.models.pedido_compra import PedidoCompra, PedidoCompraItem, SituacaoPedido, TipoPedido
from app.db.models.recebimento_compra import RecebimentoCompra
from app.schemas.marcenaria.terceirizado import (
    EnviarManualEntrada,
    MoveisEntrada,
    PedidoCentralEntrada,
    ProblemaEntrada,
    ReceberManualEntrada,
)
from app.services import licenca as licenca_service
from app.services.compras import pedidos as pedidos_service
from app.services.compras.permissoes import pode_ver_custos as pode_ver_custos_compras
from app.services.marcenaria import erros, producao
from app.services.marcenaria import terceirizado_situacao as sit
from app.services.marcenaria.orcamento_comum import (
    exigir_orcamento_tecnico,
    os_aberta,
    os_e_orcamento_aprovado,
    registrar_evento,
)
from app.services.marcenaria.orcamento_detalhe import nome_do_cliente
from app.services.marcenaria.permissoes import pode_ver_custos_marcenaria

# --- Frases e codigos (secao 6.2) -------------------------------------------------
MSG_SEM_ORCAMENTO = "Esta OS não veio de um orçamento."
MSG_OS_FECHADA = "A OS está finalizada ou cancelada; os terceirizados não podem mais ser alterados."
MSG_FORA_DA_OS = "Este móvel não faz parte desta OS."
MSG_NAO_TERCEIRIZADO = "Este móvel não é terceirizado."
MSG_CENTRAIS = "Os móveis do mesmo pedido precisam ser da mesma central."
MSG_PEDIDO_NO_COMPRAS = "Este móvel tem pedido no Compras: envie e receba por lá."
OS_FECHADA = "OS_FECHADA"
JA_PEDIDO = "JA_PEDIDO"
PEDIDO_NO_COMPRAS = "PEDIDO_NO_COMPRAS"

UNIDADE_SERVICO = "SV"                  # a unidade do item de servico no pedido (como a fabrica F5)

# A situacao com letra maiuscula, para o historico.
ROTULO = {sit.A_PEDIR: "A pedir", sit.ENVIADO: "Pedido enviado", sit.RECEBIDO: "Recebido", sit.CONFERIDO: "Conferido"}


# ===========================================================================
# AJUDANTES
# ===========================================================================

def modo_compras(db: Session) -> bool:
    """O modulo COMPRAS esta contratado? (secao 3)

    A MESMA regra do `requer_modulo` para o Compras: lista vazia ou sem
    resposta da licenca = NAO contratado (o Compras esta entre os modulos
    negados sem resposta, ao contrario do Financeiro).
    """
    modulos = licenca_service.modulos_da_licenca(db)
    return bool(modulos) and "COMPRAS" in modulos


def _aprovados(orc: MarcenariaOrcamento) -> list[tuple[MarcenariaAmbiente, MarcenariaMovel]]:
    """Os moveis APROVADOS do orcamento, na ordem da tela (ambiente, movel)."""
    return [
        (ambiente, movel)
        for ambiente in sorted(orc.ambientes, key=lambda a: (a.ordem, a.id))
        for movel in sorted(ambiente.moveis, key=lambda m: (m.ordem, m.id))
        if movel.aprovado
    ]


def _terceirizados(orc: MarcenariaOrcamento) -> list[tuple[MarcenariaAmbiente, MarcenariaMovel]]:
    """D1: so os aprovados de producao TERCEIRIZADA."""
    return [(a, m) for a, m in _aprovados(orc) if m.tipo_producao == sit.TERCEIRIZADA]


def _pedidos(db: Session, moveis: list[MarcenariaMovel]) -> dict[int, PedidoCompra]:
    """{pedido_id: PedidoCompra} dos moveis, numa consulta so."""
    return crud.buscar_por_ids(db, PedidoCompra, sorted({m.pedido_compra_id for m in moveis if m.pedido_compra_id}))


def _recebidos_em(db: Session, pedido_ids: list[int]) -> dict[int, date]:
    """{pedido_id: data da ultima chegada} (o Compras guarda data e hora)."""
    if not pedido_ids:
        return {}
    linhas = db.execute(
        select(RecebimentoCompra.pedido_id, func.max(RecebimentoCompra.recebido_em))
        .where(RecebimentoCompra.pedido_id.in_(pedido_ids))
        .group_by(RecebimentoCompra.pedido_id)
    )
    return {pedido_id: (quando.date() if hasattr(quando, "date") else quando) for pedido_id, quando in linhas if quando}


def _central(movel: MarcenariaMovel) -> Optional[dict]:
    """A central do movel com o telefone para ligar (o mesmo nome que o Compras usa)."""
    central = movel.central
    if central is None:
        return None
    return {
        "id": central.id,
        "nome": central.nome_fantasia or central.nome,
        "telefone": central.celular or central.telefone,
    }


def _nome_da_central(movel: MarcenariaMovel) -> str:
    central = movel.central
    return (central.nome_fantasia or central.nome) if central is not None else "parceira"


def _situacao(movel: MarcenariaMovel, pedidos: dict[int, PedidoCompra]) -> sit.SituacaoTerceirizado:
    return sit.situacao_do_movel(movel, pedidos.get(movel.pedido_compra_id) if movel.pedido_compra_id else None)


def _montar(ambiente: MarcenariaAmbiente, movel: MarcenariaMovel, situacao: sit.SituacaoTerceirizado,
            recebidos: dict[int, date], hoje: date, ver_custos: bool) -> dict[str, Any]:
    """Um movel terceirizado (secao 6.1)."""
    pedido = situacao.pedido
    if pedido is not None:                                   # modo Compras: o pedido manda
        dados_pedido = {"origem": "COMPRAS", "id": pedido.id, "codigo": pedido.codigo, "situacao": pedido.situacao}
        enviado_em = pedido.enviado_em.date() if pedido.enviado_em else None
        recebido_em = recebidos.get(pedido.id) if situacao.situacao in (sit.RECEBIDO, sit.CONFERIDO) else None
    elif situacao.situacao != sit.A_PEDIR:                   # modo manual, ja anotado
        dados_pedido = {"origem": "MANUAL", "numero": movel.terc_pedido}
        enviado_em, recebido_em = movel.terc_enviado_em, movel.terc_recebido_em
    else:
        dados_pedido, enviado_em, recebido_em = None, None, None

    linha = {
        "movel_id": movel.id,
        "nome": movel.nome,
        "ambiente": ambiente.nome,
        "quantidade": movel.quantidade,
        "medidas": {"largura_mm": movel.largura_mm, "altura_mm": movel.altura_mm,
                    "profundidade_mm": movel.profundidade_mm},
        "central": _central(movel),
        "situacao": situacao.situacao,
        "atrasado": sit.atrasado(situacao, hoje),
        "previsao": situacao.previsao,
        "pedido": dados_pedido,
        "enviado_em": enviado_em,
        "recebido_em": recebido_em,
        "conferido_em": movel.terc_conferido_em if situacao.situacao == sit.CONFERIDO else None,
        "problema": movel.terc_problema,
    }
    if ver_custos:                                           # D13: o orcado e custo (P4)
        linha["valor_orcado_centavos"] = movel.terceirizado_centavos * movel.quantidade
    return linha


def _leitura(db: Session, os_: OrdemServico, orc: MarcenariaOrcamento, usuario: dict) -> dict[str, Any]:
    """GET /os/{n}/terceirizados (e a resposta de toda escrita)."""
    pares = _terceirizados(orc)
    pedidos = _pedidos(db, [m for _a, m in pares])
    recebidos = _recebidos_em(db, list(pedidos))
    hoje = hoje_local()
    ver_custos = pode_ver_custos_marcenaria(usuario)
    return {
        "os": {"numero_os": os_.numero_os, "status": getattr(os_.status, "value", os_.status),
               "editavel": os_aberta(os_)},
        "modo_compras": modo_compras(db),
        "moveis": [_montar(a, m, _situacao(m, pedidos), recebidos, hoje, ver_custos) for a, m in pares],
    }


def ler(db: Session, numero_os: str, usuario: dict) -> dict[str, Any]:
    os_, orc = os_e_orcamento_aprovado(db, numero_os, MSG_SEM_ORCAMENTO)
    return _leitura(db, os_, orc, usuario)


def _com_sugestao(db: Session, os_: OrdemServico, orc: MarcenariaOrcamento, antes: str, usuario: dict) -> dict:
    """Spec 12A §7: conferir/voltar o terceirizado tambem muda a prontidao. Se ele
    for o ultimo movel a ficar pronto, a pergunta de status vem nesta resposta."""
    resposta = _leitura(db, os_, orc, usuario)
    resposta["sugestao_status"] = producao.sugestao(db, os_, antes, producao.montar_producao(db, os_, orc))
    return resposta


# ===========================================================================
# ESCRITAS
# ===========================================================================

def _preparar(db: Session, numero_os: str, movel_ids: list[int]) -> tuple:
    """OS aberta (D7) e os moveis pedidos: todos desta OS e terceirizados."""
    os_, orc = os_e_orcamento_aprovado(db, numero_os, MSG_SEM_ORCAMENTO)
    if not os_aberta(os_):
        erros.conflito(OS_FECHADA, MSG_OS_FECHADA)
    da_os = {m.id: (a, m) for a, m in _aprovados(orc)}
    escolhidos = []
    for movel_id in movel_ids:
        par = da_os.get(movel_id)
        if par is None:
            erros.nao_encontrado(MSG_FORA_DA_OS)
        if par[1].tipo_producao != sit.TERCEIRIZADA:
            erros.invalido(MSG_NAO_TERCEIRIZADO)
        escolhidos.append(par)
    return os_, orc, escolhidos


def _exigir_mesma_central(pares: list) -> int:
    """D9/D3: um pedido = uma central. Devolve o id dela."""
    centrais = {m.central_fornecedor_id for _a, m in pares}
    if len(centrais) != 1:
        erros.invalido(MSG_CENTRAIS)
    (central_id,) = centrais
    if central_id is None:
        erros.invalido(f"O móvel {pares[0][1].nome} não tem central parceira no orçamento.")
    return central_id


def _exigir_situacao(movel: MarcenariaMovel, situacao: sit.SituacaoTerceirizado, *esperadas: str) -> None:
    """Transicao fora de ordem: 409 com a situacao de agora na frase."""
    if situacao.situacao not in esperadas:
        erros.conflito(erros.TRANSICAO_INVALIDA,
                       f"Ação não permitida: o móvel {movel.nome} está {sit.NA_FRASE[situacao.situacao]}.")


def _exigir_manual(situacao: sit.SituacaoTerceirizado) -> None:
    """Acao manual num movel com pedido do Compras: o pedido e quem manda (D2)."""
    if situacao.pedido is not None:
        erros.conflito(PEDIDO_NO_COMPRAS, MSG_PEDIDO_NO_COMPRAS)


def _nomes(pares: list) -> str:
    return ", ".join(m.nome for _a, m in pares)


def _descricao_servico(ambiente: MarcenariaAmbiente, movel: MarcenariaMovel, os_: OrdemServico) -> str:
    """"Servico: Cozinha Gourmet — Torre Quente (700 × 2200 × 600 mm) · OS-2026-000512" (D9)."""
    descricao = f"Serviço: {ambiente.nome} — {movel.nome}"
    medidas = [m for m in (movel.largura_mm, movel.altura_mm, movel.profundidade_mm) if m]
    if medidas:
        descricao += f" ({' × '.join(str(m) for m in medidas)} mm)"
    return f"{descricao} · {os_.numero_os}"[:255]


def _data(valor: Optional[date]) -> str:
    return valor.strftime("%d/%m/%Y") if valor else ""


def pedir(db: Session, numero_os: str, dados: PedidoCentralEntrada, usuario: dict) -> dict[str, Any]:
    """D9-D11: UM pedido de SERVICO no Compras, em rascunho, com um item por movel.

    O mesmo uso do servico do Compras que a fabrica F5 fazia (enviar, receber,
    cancelar e lancar a conta continuam no Compras). A rota ja exigiu o modulo
    COMPRAS e a permissao de gerenciar compras.
    """
    os_, orc, pares = _preparar(db, numero_os, dados.movel_ids)
    central_id = _exigir_mesma_central(pares)
    pedidos = _pedidos(db, [m for _a, m in pares])
    for _a, movel in pares:
        ativo = sit.pedido_ativo(pedidos.get(movel.pedido_compra_id) if movel.pedido_compra_id else None)
        if ativo is not None:                                # D11: nao pede duas vezes
            erros.conflito(JA_PEDIDO, f"O móvel {movel.nome} já está no pedido {ativo.codigo}.")
        _exigir_situacao(movel, _situacao(movel, pedidos), sit.A_PEDIR)   # anotado a mao: volte antes

    central = pedidos_service.validar_fornecedor(db, central_id)
    pedido = pedidos_service.novo_rascunho(db, usuario, central)          # o Compras numera (PC-000123)
    pedido.tipo = TipoPedido.SERVICO                                       # servico nao entra no estoque
    pedido.previsao_entrega = dados.previsao_entrega
    pedido.observacao = (dados.observacao or "").strip() or None
    for ambiente, movel in pares:
        pedido.itens.append(PedidoCompraItem(
            produto_id=None,                                               # servico: sem produto
            descricao=_descricao_servico(ambiente, movel, os_),
            unidade_compra=UNIDADE_SERVICO,
            fator=1,
            quantidade=movel.quantidade,
            custo_unitario=movel.terceirizado_centavos,                    # o orcado, copiado (06A)
        ))
    pedidos_service._recalcular(pedido)                                    # totais, como o Compras faz
    pedidos_service._definir_parcelas(pedido, None)                        # parcelas padrao do Compras
    db.flush()
    pedidos_service.registrar_log(db, usuario, pedido, "CRIADO", None, SituacaoPedido.RASCUNHO,
                                  f"Central parceira da OS {os_.numero_os}")
    for _a, movel in pares:
        movel.pedido_compra_id = pedido.id                                 # D11
        movel.terc_conferido_em = None                                     # recomeca limpo
        movel.terc_problema = None
    registrar_evento(db, orc, "TERCEIRIZADO_PEDIDO",
                     f"Pedido {pedido.codigo} à central {pedido.fornecedor_nome}: {_nomes(pares)}.",
                     usuario, {"pedido_id": pedido.id, "movel_ids": dados.movel_ids}, os_id=os_.id)
    db.commit()

    resumo_pedido = {"id": pedido.id, "codigo": pedido.codigo, "situacao": pedido.situacao,
                     "fornecedor_nome": pedido.fornecedor_nome}
    if pode_ver_custos_compras(usuario):                                   # D13: a regra de custo do Compras
        resumo_pedido["valor_total_centavos"] = pedido.valor_total
    return {"pedido": resumo_pedido, "terceirizados": _leitura(db, os_, orc, usuario)}


def enviar_manual(db: Session, numero_os: str, dados: EnviarManualEntrada, usuario: dict) -> dict[str, Any]:
    """D3: sem o Compras, anota que o pedido saiu (numero e previsao opcionais)."""
    os_, orc, pares = _preparar(db, numero_os, dados.movel_ids)
    _exigir_mesma_central(pares)
    pedidos = _pedidos(db, [m for _a, m in pares])
    for _a, movel in pares:
        situacao = _situacao(movel, pedidos)
        _exigir_manual(situacao)
        _exigir_situacao(movel, situacao, sit.A_PEDIR)
    numero = (dados.pedido or "").strip() or None
    for _a, movel in pares:
        movel.terc_situacao = sit.ENVIADO
        movel.terc_pedido = numero
        movel.terc_enviado_em = hoje_local()
        movel.terc_previsao = dados.previsao
        movel.terc_recebido_em = None
        movel.terc_conferido_em = None
    detalhes = ", ".join(p for p in (f"nº {numero}" if numero else "",
                                     f"previsão {_data(dados.previsao)}" if dados.previsao else "") if p)
    registrar_evento(db, orc, "TERCEIRIZADO_ENVIADO",
                     f"Pedido à central {_nome_da_central(pares[0][1])} anotado"
                     f"{f' ({detalhes})' if detalhes else ''}: {_nomes(pares)}.",
                     usuario, {"movel_ids": dados.movel_ids, "pedido": numero}, os_id=os_.id)
    db.commit()
    return _leitura(db, os_, orc, usuario)


def receber_manual(db: Session, numero_os: str, dados: ReceberManualEntrada, usuario: dict) -> dict[str, Any]:
    """D3: sem o Compras, anota que o movel chegou (padrao: hoje)."""
    os_, orc, pares = _preparar(db, numero_os, dados.movel_ids)
    pedidos = _pedidos(db, [m for _a, m in pares])
    for _a, movel in pares:
        situacao = _situacao(movel, pedidos)
        _exigir_manual(situacao)
        _exigir_situacao(movel, situacao, sit.ENVIADO)
    quando = dados.data or hoje_local()
    for _a, movel in pares:
        movel.terc_situacao = sit.RECEBIDO
        movel.terc_recebido_em = quando
    registrar_evento(db, orc, "TERCEIRIZADO_RECEBIDO", f"Recebido da central em {_data(quando)}: {_nomes(pares)}.",
                     usuario, {"movel_ids": dados.movel_ids}, os_id=os_.id)
    db.commit()
    return _leitura(db, os_, orc, usuario)


def conferir(db: Session, numero_os: str, dados: MoveisEntrada, usuario: dict) -> dict[str, Any]:
    """D1/D4: o movel chegou bom. Vale nos dois modos e limpa o problema."""
    os_, orc, pares = _preparar(db, numero_os, dados.movel_ids)
    antes = producao.andamento(producao.montar_producao(db, os_, orc))      # 12A: para a sugestao
    pedidos = _pedidos(db, [m for _a, m in pares])
    for _a, movel in pares:
        _exigir_situacao(movel, _situacao(movel, pedidos), sit.RECEBIDO)
    for _a, movel in pares:
        movel.terc_conferido_em = hoje_local()
        movel.terc_problema = None
        if _situacao(movel, pedidos).modo == "MANUAL":
            movel.terc_situacao = sit.CONFERIDO
    registrar_evento(db, orc, "TERCEIRIZADO_CONFERIDO", f"Conferido: {_nomes(pares)}.",
                     usuario, {"movel_ids": dados.movel_ids}, os_id=os_.id)
    db.commit()
    return _com_sugestao(db, os_, orc, antes, usuario)


def registrar_problema(db: Session, numero_os: str, movel_id: int, dados: ProblemaEntrada,
                       usuario: dict) -> dict[str, Any]:
    """D4: chegou com defeito. O movel fica RECEBIDO (nao pronto) com o texto."""
    os_, orc, pares = _preparar(db, numero_os, [movel_id])
    (_a, movel), = pares
    pedidos = _pedidos(db, [movel])
    situacao = _situacao(movel, pedidos)
    _exigir_situacao(movel, situacao, sit.RECEBIDO, sit.CONFERIDO)
    movel.terc_problema = dados.texto
    movel.terc_conferido_em = None
    if situacao.modo == "MANUAL":
        movel.terc_situacao = sit.RECEBIDO
    registrar_evento(db, orc, "TERCEIRIZADO_PROBLEMA", f"Problema no móvel {movel.nome}: {dados.texto}",
                     usuario, {"movel_id": movel.id}, os_id=os_.id)
    db.commit()
    return _leitura(db, os_, orc, usuario)


def voltar(db: Session, numero_os: str, movel_id: int, usuario: dict) -> dict[str, Any]:
    """D5: desfaz o ultimo passo (erro de clique).

    - Conferido -> Recebido, nos dois modos;
    - modo manual: Recebido -> Enviado -> A pedir (voltar a "A pedir" limpa o
      pedido anotado e a previsao);
    - modo Compras: os outros passos voltam pelo Compras (cancelar o pedido
      devolve o movel a "A pedir"), nunca por baixo dele.
    """
    os_, orc, pares = _preparar(db, numero_os, [movel_id])
    antes = producao.andamento(producao.montar_producao(db, os_, orc))      # 12A: para a sugestao
    (_a, movel), = pares
    situacao = _situacao(movel, _pedidos(db, [movel]))
    if situacao.situacao == sit.CONFERIDO:
        movel.terc_conferido_em = None
        if situacao.modo == "MANUAL":
            movel.terc_situacao = sit.RECEBIDO
        para = sit.RECEBIDO
    else:
        _exigir_manual(situacao)
        if situacao.situacao == sit.RECEBIDO:
            movel.terc_situacao, movel.terc_recebido_em, movel.terc_problema = sit.ENVIADO, None, None
            para = sit.ENVIADO
        elif situacao.situacao == sit.ENVIADO:
            movel.terc_situacao = None                       # nulo = A pedir
            movel.terc_pedido = movel.terc_enviado_em = movel.terc_previsao = None
            para = sit.A_PEDIR
        else:
            _exigir_situacao(movel, situacao, sit.ENVIADO, sit.RECEBIDO, sit.CONFERIDO)   # A pedir: nao ha volta
    registrar_evento(db, orc, "TERCEIRIZADO_VOLTOU",
                     f"{movel.nome} voltou de {ROTULO[situacao.situacao]} para {ROTULO[para]}.",
                     usuario, {"movel_id": movel.id}, os_id=os_.id)
    db.commit()
    return _com_sugestao(db, os_, orc, antes, usuario)


# ===========================================================================
# LISTA GERAL (D17) E GANCHO DO CANCELAMENTO (D16)
# ===========================================================================

def lista_geral(db: Session, usuario: dict, situacao: Optional[str] = None,
                central_id: Optional[int] = None, atrasados: bool = False) -> dict[str, Any]:
    """Os terceirizados das OS ABERTAS: para o dono ligar a central uma vez por dia."""
    exigir_orcamento_tecnico(db)
    orcamentos = db.scalars(
        select(MarcenariaOrcamento)
        .join(OrdemServico, OrdemServico.id == MarcenariaOrcamento.os_id)
        .where(
            MarcenariaOrcamento.status == StatusOrcamento.APROVADO,
            OrdemServico.ativo.is_(True),
            OrdemServico.status.not_in([OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA]),
        )
    ).all()
    por_orcamento = [(orc, _terceirizados(orc)) for orc in orcamentos]
    pedidos = _pedidos(db, [m for _orc, pares in por_orcamento for _a, m in pares])   # uma consulta so
    recebidos = _recebidos_em(db, list(pedidos))
    hoje = hoje_local()
    ver_custos = pode_ver_custos_marcenaria(usuario)

    itens = []
    for orc, pares in por_orcamento:
        for ambiente, movel in pares:
            linha = _montar(ambiente, movel, _situacao(movel, pedidos), recebidos, hoje, ver_custos)
            if situacao and linha["situacao"] != situacao:
                continue
            if central_id and (linha["central"] or {}).get("id") != central_id:
                continue
            if atrasados and not linha["atrasado"]:
                continue
            itens.append({"numero_os": orc.os.numero_os, "cliente": nome_do_cliente(orc.cliente) or None,
                          "orcamento_codigo": orc.codigo, **linha})
    # Atrasados primeiro; depois pela previsao (sem previsao no fim) e pela OS.
    itens.sort(key=lambda i: (not i["atrasado"], i["previsao"] or date.max, i["numero_os"], i["nome"]))
    return {"itens": itens}


def avisar_no_cancelamento(db: Session, os_, usuario: Optional[dict], contexto: Optional[dict] = None) -> None:
    """D16: cancelar a OS NAO cancela o pedido a central nem as contas: o movel
    existe e foi pedido. Fica escrito no historico, para a loja combinar.

    Roda dentro da transacao do cancelamento (sem commit). OS de outro
    segmento (ou sem orcamento) sai na hora.
    """
    orc = crud.get_orcamento_por_os(db, os_.id)
    if orc is None:
        return
    pares = _terceirizados(orc)
    pedidos = _pedidos(db, [m for _a, m in pares])
    pedidos_feitos = []
    for _a, movel in pares:
        situacao = _situacao(movel, pedidos)
        if situacao.pedido is not None:
            estado = "Rascunho" if situacao.situacao == sit.A_PEDIR else ROTULO[situacao.situacao]
            pedidos_feitos.append(f"{movel.nome} ({situacao.pedido.codigo}, {estado})")
        elif situacao.situacao != sit.A_PEDIR:
            numero = f"nº {movel.terc_pedido}, " if movel.terc_pedido else ""
            pedidos_feitos.append(f"{movel.nome} ({numero}{ROTULO[situacao.situacao]})")
    if not pedidos_feitos:
        return
    registrar_evento(
        db, orc, "TERCEIRIZADOS_EM_OS_CANCELADA",
        f"Há móveis pedidos à central para esta OS: {', '.join(pedidos_feitos)}. Combine com a central.",
        usuario, {"movel_ids": [m.id for _a, m in pares]}, os_id=os_.id,
    )
