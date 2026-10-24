# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/faturamento/estoque_acabado.py
# DESCRICAO: O movel pronto entra no estoque como PRODUTO ACABADO
#            (docs/marcenaria-faturamento-plano.md, F2).
# ---------------------------------------------------------------------------
"""
Quando um movel aprovado fica PRONTO (interno: todas as etapas concluidas;
terceirizado: conferido -- a mesma regra da aba Producao), ele entra no
estoque do produto acabado. Quando deixa de estar pronto (etapa desmarcada,
terceirizado voltou um passo, OS cancelada), a entrada e estornada.

Regras que nao podem regredir:
- Origem `PRODUCAO` nas duas pontas: o CMV so le VENDA e ORDEM_SERVICO, entao
  o material NAO e contado duas vezes (R3). Ele ja entrou pela separacao.
- `sincronizar` e idempotente: pode ser chamado depois de qualquer escrita da
  producao; so movimenta o que mudou.
- Movel FATURADO nunca e estornado por aqui: a nota saiu. Quem quer desfazer
  cancela a nota antes (o cancelamento da OS e barrado, ver `ao_cancelar_os`).
- Desligado (`faturamento_modo = DESLIGADO`), nada acontece (R1).
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enum import MovimentacaoOrigem, MovimentacaoTipo
from app.db.models.configuracao_marcenaria import ConfiguracaoMarcenaria
from app.db.models.marcenaria.ambiente import MarcenariaMovel
from app.db.models.marcenaria.faturamento import MarcenariaMovelFaturamento, SituacaoFaturamento
from app.db.models.produto import Produto
from app.services.marcenaria.faturamento import configuracao_ligada, empresa_atual_id
from app.services.produto.movimentacao import registrar_movimentacao

TERCEIRIZADA = "TERCEIRIZADA"
MSG_FATURADO = (
    "Há móveis desta OS que já saíram em nota fiscal ({nomes}). "
    "Cancele a nota antes de cancelar a OS ou desfazer a aprovação."
)


def produto_do_movel(config: ConfiguracaoMarcenaria, movel: MarcenariaMovel) -> Optional[int]:
    """O produto acabado do movel (D3/D4): o escolhido nele, senao o padrao.

    Terceirizado usa o de revenda; sem ele configurado, cai no de producao
    propria (o NCM e o mesmo movel; o CFOP de revenda e decidido na nota pelo
    `tipo_producao`, nao pelo produto).
    """
    if movel.produto_acabado_id:
        return movel.produto_acabado_id
    if movel.tipo_producao == TERCEIRIZADA and config.produto_acabado_revenda_id:
        return config.produto_acabado_revenda_id
    return config.produto_acabado_padrao_id


def _custos_de_material(orcamentos) -> dict[int, int]:
    """{movel_id: custo de material por unidade, em centavos} (D9).

    Interno: material + perda do motor do orcamento. Terceirizado: o valor da
    central. Mao de obra e RT ficam de fora: entram no resultado pelos seus
    registros (F2a). Um orcamento que o motor recusa nao derruba a producao:
    o custo fica 0 (so a avaliacao do estoque perde precisao).
    """
    from app.services.marcenaria.orcamento_calculo import calcular_orcamento_do_banco

    custos: dict[int, int] = {}
    for orc in orcamentos:
        try:
            resultado = calcular_orcamento_do_banco(orc)
        except HTTPException:
            continue
        for ambiente in resultado.ambientes:
            for linha in ambiente.moveis:
                material = Decimal(linha.material_centavos) + Decimal(linha.perda_centavos)
                interno = int(material.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
                custos[int(linha.id)] = interno + int(linha.terceirizado_centavos or 0)
    return custos


def linhas_da_os(db: Session, os_id: int) -> dict[int, MarcenariaMovelFaturamento]:
    linhas = db.query(MarcenariaMovelFaturamento).filter(MarcenariaMovelFaturamento.os_id == os_id).all()
    return {linha.movel_id: linha for linha in linhas}


def _movimentar(db: Session, produto: Produto, tipo: MovimentacaoTipo, quantidade: float, os_id: int,
                observacao: str, usuario: Optional[dict], custo: Optional[int] = None):
    return registrar_movimentacao(
        db,
        produto=produto,
        tipo=tipo,
        quantidade=quantidade,
        origem=MovimentacaoOrigem.PRODUCAO,
        ordem_servico_id=os_id,
        usuario_id=int(usuario["sub"]) if usuario and str(usuario.get("sub", "")).isdigit() else None,
        usuario_nome=(usuario or {}).get("nome", "Sistema"),
        observacao=observacao,
        permitir_negativo=True,        # o estorno de um acabado que alguem ajustou a mao nao pode travar a OS
        custo_unitario=custo,
    )


def _dar_entrada(db, os_, movel, linha, produto_id, custo, usuario) -> MarcenariaMovelFaturamento:
    produto = db.get(Produto, produto_id)
    mov = _movimentar(db, produto, MovimentacaoTipo.ENTRADA, float(movel.quantidade), os_.id,
                      f"Móvel pronto: {movel.nome} ({os_.numero_os})", usuario, custo=custo)
    if linha is None:
        linha = MarcenariaMovelFaturamento(os_id=os_.id, movel_id=movel.id)
        db.add(linha)
    linha.produto_id = produto_id
    linha.quantidade = float(movel.quantidade)
    linha.custo_unitario_centavos = custo
    linha.mov_entrada_id = mov.id if mov is not None else None
    linha.mov_saida_id = None
    linha.situacao = SituacaoFaturamento.NO_ESTOQUE
    return linha


def _estornar(db, os_, movel_nome: str, linha: MarcenariaMovelFaturamento, usuario, motivo: str) -> None:
    produto = db.get(Produto, linha.produto_id)
    _movimentar(db, produto, MovimentacaoTipo.SAIDA, linha.quantidade, os_.id,
                f"Estorno ({motivo}): {movel_nome} ({os_.numero_os})", usuario)
    linha.situacao = SituacaoFaturamento.ESTORNADO


def sincronizar(db: Session, os_, orc, usuario: Optional[dict]) -> None:
    """Leva o estoque de acabados ao que a producao diz agora. Sem commit.

    `orc` e a vista da OS (principal + aditivos). Chamado depois de toda escrita
    que muda a prontidao de um movel (etapas, terceirizado).
    """
    config = configuracao_ligada(db, empresa_atual_id(db))
    if config is None:
        return
    from app.services.marcenaria import producao

    db.flush()                                            # a prontidao le o que acabou de mudar
    prontos = {linha["movel_id"]: linha["pronto"] for linha in producao.montar_producao(db, os_, orc)["moveis"]}
    moveis = {m.id: m for a in orc.ambientes for m in a.moveis if m.aprovado}
    linhas = linhas_da_os(db, os_.id)
    custos: Optional[dict[int, int]] = None
    for movel_id, pronto in prontos.items():
        movel = moveis[movel_id]
        linha = linhas.get(movel_id)
        situacao = linha.situacao if linha is not None else None
        if pronto and situacao in (None, SituacaoFaturamento.ESTORNADO):
            produto_id = produto_do_movel(config, movel)
            if produto_id is None:
                continue                                  # sem produto: a nota e que vai cobrar
            if custos is None:
                custos = _custos_de_material(getattr(orc, "orcamentos", [orc]))
            _dar_entrada(db, os_, movel, linha, produto_id, custos.get(movel_id, 0), usuario)
        elif not pronto and situacao == SituacaoFaturamento.NO_ESTOQUE:
            _estornar(db, os_, movel.nome, linha, usuario, "deixou de estar pronto")
    db.flush()


def situacao_dos_moveis(db: Session, os_id: int) -> dict[int, str]:
    """{movel_id: NO_ESTOQUE | FATURADO | ESTORNADO} para os selos da tela."""
    return {movel_id: linha.situacao for movel_id, linha in linhas_da_os(db, os_id).items()}


def _assert_sem_simples_faturamento_vivo(db: Session, os_) -> None:
    """Entrega futura (F4): a OS nao cai com a 5922 dela valendo."""
    from app.db.models.documento_fiscal import DocumentoFiscal

    vivo = (db.query(DocumentoFiscal)
            .filter(DocumentoFiscal.origem_tipo == "OS", DocumentoFiscal.origem_id == os_.id,
                    DocumentoFiscal.papel == "SIMPLES_FATURAMENTO",
                    DocumentoFiscal.status.in_(("AUTORIZADA", "PROCESSANDO", "INDETERMINADA")))
            .first())
    if vivo is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(f"Esta OS tem nota de simples faturamento (NF-e {vivo.numero_documento}). "
                    f"Cancele a nota antes de cancelar a OS ou desfazer a aprovação."),
        )


def ao_cancelar_os(db: Session, os_, usuario: Optional[dict], contexto: Optional[dict] = None) -> None:
    """Gancho do cancelamento da OS (e do desfazer aprovacao, que cancela a OS).

    Movel FATURADO barra o cancelamento (a nota existe); os NO_ESTOQUE sao
    estornados. Roda dentro da transacao do cancelamento: a HTTPException
    desfaz tudo.
    """
    _assert_sem_simples_faturamento_vivo(db, os_)
    linhas = [l for l in linhas_da_os(db, os_.id).values() if l.situacao != SituacaoFaturamento.ESTORNADO]
    if not linhas:
        return
    nomes = {m.id: m.nome for m in db.query(MarcenariaMovel).filter(
        MarcenariaMovel.id.in_([l.movel_id for l in linhas])).all()}
    faturados = [nomes.get(l.movel_id, "?") for l in linhas if l.situacao == SituacaoFaturamento.FATURADO]
    if faturados:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=MSG_FATURADO.format(nomes=", ".join(faturados)))
    for linha in linhas:
        _estornar(db, os_, nomes.get(linha.movel_id, "?"), linha, usuario, "OS cancelada")


def sincronizar_todas(db: Session, usuario: Optional[dict]) -> dict:
    """Da entrada dos moveis JA prontos de todas as OS abertas (ao ligar o
    faturamento com obras em andamento). Idempotente; OS fechada fica de fora:
    o movel dela ja foi entregue e nunca vai sair numa nota por aqui.
    """
    from app.db.models.marcenaria.orcamento import MarcenariaOrcamento
    from app.services.marcenaria.orcamento_comum import orcamentos_da_os, os_aberta

    if configuracao_ligada(db, empresa_atual_id(db)) is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Ligue o faturamento dos móveis antes de dar entrada nos móveis prontos.")
    antes = db.query(MarcenariaMovelFaturamento).filter(
        MarcenariaMovelFaturamento.situacao == SituacaoFaturamento.NO_ESTOQUE).count()
    principais = (db.query(MarcenariaOrcamento)
                  .filter(MarcenariaOrcamento.status == "APROVADO",
                          MarcenariaOrcamento.os_id.isnot(None),
                          MarcenariaOrcamento.aditivo_os_id.is_(None))
                  .all())
    oss = 0
    for principal in principais:
        os_ = principal.os
        if os_ is None or not os_.ativo or not os_aberta(os_):
            continue
        sincronizar(db, os_, orcamentos_da_os(db, os_), usuario)
        oss += 1
    depois = db.query(MarcenariaMovelFaturamento).filter(
        MarcenariaMovelFaturamento.situacao == SituacaoFaturamento.NO_ESTOQUE).count()
    return {"os_conferidas": oss, "moveis_no_estoque": depois, "entraram_agora": max(0, depois - antes)}


# ===========================================================================
# A NOTA (F3/F4): o movel sai do estoque com a nota e volta se ela cair
# ===========================================================================

# A nota nao vale (ou deixou de valer): o movel volta ao estoque de acabados.
STATUS_QUE_DEVOLVEM = ("REJEITADA", "NAO_TRANSMITIDA", "DENEGADA", "CANCELADA")


def faturar(db: Session, os_, linhas: list[MarcenariaMovelFaturamento], doc, usuario: Optional[dict]) -> None:
    """Os moveis da nota saem do estoque e ficam presos a ela. Sem commit.

    Chamado ANTES de transmitir: se a resposta da SEFAZ se perder, o movel ja
    esta preso e nao vai para uma segunda nota (a consulta resolve depois).
    """
    nomes = {m.id: m.nome for m in db.query(MarcenariaMovel).filter(
        MarcenariaMovel.id.in_([l.movel_id for l in linhas])).all()}
    for linha in linhas:
        produto = db.get(Produto, linha.produto_id)
        mov = _movimentar(db, produto, MovimentacaoTipo.SAIDA, linha.quantidade, os_.id,
                          f"NF-e {doc.numero_documento}: {nomes.get(linha.movel_id, '?')} ({os_.numero_os})", usuario)
        linha.mov_saida_id = mov.id if mov is not None else None
        linha.documento_fiscal_id = doc.id
        linha.situacao = SituacaoFaturamento.FATURADO
    db.flush()


def ao_mudar_documento(db: Session, doc, usuario: Optional[dict] = None) -> None:
    """Depois de toda mudanca de status de uma nota: se ela caiu, os moveis voltam.

    Chamado na emissao, na consulta e no cancelamento (`consulta_cancelamento`).
    Nota que nao e de movel nenhum (venda, OS comum) sai na primeira linha.
    """
    if doc is None or doc.status not in STATUS_QUE_DEVOLVEM:
        return
    if getattr(doc, "papel", None) == "SIMPLES_FATURAMENTO":
        # Entrega futura (F4): o simples faturamento caiu; os moveis voltam a
        # precisar de um (nenhum estoque mexe: a 5922 nao movimenta).
        for movel in db.query(MarcenariaMovel).filter(MarcenariaMovel.simples_faturamento_id == doc.id).all():
            movel.simples_faturamento_id = None
        db.flush()
        return
    linhas = (db.query(MarcenariaMovelFaturamento)
              .filter(MarcenariaMovelFaturamento.documento_fiscal_id == doc.id,
                      MarcenariaMovelFaturamento.situacao == SituacaoFaturamento.FATURADO)
              .all())
    if not linhas:
        return
    from app.db.models.ordem_servico import OrdemServico

    os_ = db.get(OrdemServico, linhas[0].os_id)
    nomes = {m.id: m.nome for m in db.query(MarcenariaMovel).filter(
        MarcenariaMovel.id.in_([l.movel_id for l in linhas])).all()}
    motivo = "nota cancelada" if doc.status == "CANCELADA" else "nota não autorizada"
    for linha in linhas:
        produto = db.get(Produto, linha.produto_id)
        _movimentar(db, produto, MovimentacaoTipo.ENTRADA, linha.quantidade, os_.id,
                    f"Volta ao estoque ({motivo}, NF-e {doc.numero_documento}): "
                    f"{nomes.get(linha.movel_id, '?')} ({os_.numero_os})", usuario)
        linha.situacao = SituacaoFaturamento.NO_ESTOQUE
        linha.documento_fiscal_id = None
        linha.mov_saida_id = None
    db.flush()


def assert_pode_cancelar(db: Session, doc) -> None:
    """Entrega futura (F4): o simples faturamento nao cai com remessa viva.

    A remessa aponta para ele pela chave; cancelar a 5922 deixaria a mercadoria
    entregue sem a venda. Cancele as remessas antes. Outra nota: passa.
    """
    if getattr(doc, "papel", None) != "SIMPLES_FATURAMENTO":
        return
    vivas = (db.query(MarcenariaMovelFaturamento)
             .filter(MarcenariaMovelFaturamento.documento_simples_faturamento_id == doc.id,
                     MarcenariaMovelFaturamento.situacao == SituacaoFaturamento.FATURADO)
             .count())
    if vivas:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(f"Há {vivas} móvel(is) já entregue(s) com nota de remessa deste simples faturamento. "
                    f"Cancele as remessas antes."),
        )
