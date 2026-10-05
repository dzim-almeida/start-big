# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fabrica/orcamentos.py
# DESCRIÇÃO: Orçamento por móvel que gera a OS (docs/marcenaria-fabrica-plano.md, F2).
# ---------------------------------------------------------------------------
"""
O ciclo de uma versão: RASCUNHO (edita) → ENVIADO (o cliente está olhando)
→ APROVADO ou RECUSADO. VENCIDO não é gravado: é ENVIADO com a validade
passada, e não se aprova (copie numa versão nova com a validade certa).

APROVAR é o momento em que o orçamento vira OS (§2 do plano):
- um item por MÓVEL: SERVIÇO avulso, visível, valor = preço do móvel. É o que
  o cliente comprou e o que soma no total da OS;
- um item por INSUMO, somado em todos os móveis: PRODUTO, invisível, valor
  zero, quantidade em unidades de compra inteiras (calculo.py). É o que
  reserva, vai para as Necessidades de Compras e baixa do estoque.

Os itens gerados levam `fabrica_orcamento_id`: aprovar outra versão troca
exatamente esses (D12), e a OS não deixa editá-los à mão.

CUSTO, sem contar duas vezes: o insumo é produto do catálogo, então o custo
dele no lucro do mês vem do livro de estoque na baixa — o `custo_unitario`
gravado no item é só a referência congelada (RC11). O item do móvel leva
custo apenas quando é terceirizado (o custo do terceiro não passa pelo
estoque); senão, contaria o material de novo.
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enum import (
    OrdemServicoItemAprovacao,
    OrdemServicoItemTipo,
    OrdemServicoStatus,
    UnidadeMedida,
)
from app.core.tempo import agora_utc, hoje_local
from app.db.models.fabrica_orcamento import (
    FabricaAmbiente,
    FabricaMaterial,
    FabricaMovel,
    FabricaOrcamento,
    SituacaoOrcamento,
)
from app.db.models.ordem_servico import OrdemServico
from app.db.models.ordem_servico_item import OrdemServicoItem
from app.db.models.produto import Produto
from app.schemas.fabrica import (
    AmbienteRead,
    InsumoDaAprovacao,
    MaterialRead,
    MovelRead,
    OrcamentoEscrita,
    OrcamentoRead,
    OrcamentoResumo,
)
from app.services.fabrica import calculo
from app.services.fabrica import trilho
from app.services.fabrica.modo import Fase
from app.db.models.fabrica_orcamento import EventoFase
from app.services.movimentacao_estoque import custo_atual
from app.services.ordem_servico import _recalcular_valor_total_os

VENCIDO = "VENCIDO"


def _erro(codigo: int, detalhe: str) -> HTTPException:
    return HTTPException(status_code=codigo, detail=detalhe)


# --- Busca e travas -------------------------------------------------------------

def _os_da_fabrica(db: Session, numero_os: str) -> OrdemServico:
    os_ = db.scalar(select(OrdemServico).where(OrdemServico.numero_os == numero_os))
    if os_ is None:
        raise _erro(status.HTTP_404_NOT_FOUND, "Ordem de Serviço não encontrada")
    if os_.fase_fabrica is None:
        raise _erro(
            status.HTTP_409_CONFLICT,
            "Esta OS não está no trilho da fábrica. Só OS de Planejados abertas com o modo fábrica ligado têm orçamento por móvel.",
        )
    return os_


def _assert_os_aberta(os_: OrdemServico) -> None:
    if os_.status in (OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA):
        raise _erro(status.HTTP_409_CONFLICT, "A OS está finalizada ou cancelada: o orçamento não muda mais.")


def _orcamento(db: Session, orcamento_id: int) -> FabricaOrcamento:
    orc = db.get(FabricaOrcamento, orcamento_id)
    if orc is None:
        raise _erro(status.HTTP_404_NOT_FOUND, "Orçamento não encontrado.")
    os_ = db.get(OrdemServico, orc.os_id)
    if os_ is None or os_.fase_fabrica is None:
        raise _erro(status.HTTP_404_NOT_FOUND, "Orçamento não encontrado.")
    return orc


def _situacao(orc: FabricaOrcamento) -> str:
    return VENCIDO if orc.vencido(hoje_local()) else orc.situacao


def _exigir(orc: FabricaOrcamento, *situacoes: str, acao: str) -> None:
    atual = _situacao(orc)
    if atual not in situacoes:
        raise _erro(
            status.HTTP_409_CONFLICT,
            f"Não dá para {acao} a versão {orc.versao}: ela está {atual.lower()}.",
        )


# --- Cálculo e leitura --------------------------------------------------------------

def _eh_insumo(produto: Optional[Produto]) -> bool:
    return bool(produto and produto.unidade_consumo and produto.consumo_por_unidade)


def _custo_material(mat: FabricaMaterial, perda_bp: int) -> int:
    produto = mat.produto
    if not _eh_insumo(produto):
        return 0
    return calculo.custo_do_material(
        mat.consumo, perda_bp, bool(produto.sofre_perda), produto.consumo_por_unidade, mat.custo_unitario
    )


def _custo_movel(movel: FabricaMovel, perda_bp: int) -> int:
    materiais = sum(_custo_material(m, perda_bp) for m in movel.materiais)
    terceiro = (movel.custo_terceiro or 0) if movel.terceirizado else 0
    return materiais + terceiro


def _moveis(orc: FabricaOrcamento) -> list[tuple[FabricaAmbiente, FabricaMovel]]:
    return [(amb, mov) for amb in orc.ambientes for mov in amb.moveis]


def _insumos(orc: FabricaOrcamento) -> list[InsumoDaAprovacao]:
    """O que a aprovação escreve na OS: cada insumo somado em TODOS os móveis."""
    linhas: list[calculo.LinhaDeMaterial] = []
    por_produto: dict[int, FabricaMaterial] = {}
    for _amb, mov in _moveis(orc):
        for mat in mov.materiais:
            if not _eh_insumo(mat.produto):
                continue
            linhas.append(calculo.LinhaDeMaterial(
                produto_id=mat.produto_id,
                consumo=mat.consumo,
                sofre_perda=bool(mat.produto.sofre_perda),
                consumo_por_unidade=mat.produto.consumo_por_unidade,
            ))
            por_produto.setdefault(mat.produto_id, mat)
    quantidades = calculo.quantidades_por_insumo(linhas, orc.perda_bp)
    consumo_total: dict[int, int] = {}
    for linha in linhas:
        consumo_total[linha.produto_id] = consumo_total.get(linha.produto_id, 0) + calculo.consumo_com_perda(
            linha.consumo, orc.perda_bp, linha.sofre_perda
        )
    return [
        InsumoDaAprovacao(
            produto_id=pid,
            descricao=por_produto[pid].produto.nome,
            unidade_medida=por_produto[pid].produto.unidade_medida,
            consumo_total=consumo_total[pid],
            quantidade=quantidades[pid],
            custo_unitario=por_produto[pid].custo_unitario,
        )
        for pid in quantidades
    ]


def _recalcular_totais(orc: FabricaOrcamento) -> None:
    moveis = [mov for _amb, mov in _moveis(orc)]
    orc.total = sum(m.preco_venda for m in moveis)
    orc.custo_total = sum(_custo_movel(m, orc.perda_bp) for m in moveis)


def _sinal(orc: FabricaOrcamento) -> int:
    return -(-orc.total * orc.sinal_bp // 10000)


def _resumo(orc: FabricaOrcamento) -> OrcamentoResumo:
    return OrcamentoResumo(
        id=orc.id, versao=orc.versao, situacao=_situacao(orc), total=orc.total,
        criado_em=orc.criado_em, enviado_em=orc.enviado_em, aprovado_em=orc.aprovado_em,
    )


def _ler(db: Session, orc: FabricaOrcamento, ver_custos: bool = True) -> OrcamentoRead:
    os_ = db.get(OrdemServico, orc.os_id)
    ambientes = [
        AmbienteRead(
            id=amb.id,
            nome=amb.nome,
            moveis=[
                MovelRead(
                    id=mov.id, nome=mov.nome,
                    largura_mm=mov.largura_mm, altura_mm=mov.altura_mm, profundidade_mm=mov.profundidade_mm,
                    medidas=mov.medidas, preco_venda=mov.preco_venda,
                    terceirizado=mov.terceirizado, custo_terceiro=mov.custo_terceiro,
                    custo=_custo_movel(mov, orc.perda_bp),
                    materiais=[
                        MaterialRead(
                            id=mat.id, produto_id=mat.produto_id, descricao=mat.descricao, consumo=mat.consumo,
                            unidade_consumo=mat.produto.unidade_consumo if mat.produto else None,
                            consumo_por_unidade=mat.produto.consumo_por_unidade if mat.produto else None,
                            sofre_perda=bool(mat.produto.sofre_perda) if mat.produto else False,
                            unidade_medida=mat.produto.unidade_medida if mat.produto else None,
                            custo_unitario=mat.custo_unitario,
                            custo=_custo_material(mat, orc.perda_bp),
                        )
                        for mat in mov.materiais
                    ],
                )
                for mov in amb.moveis
            ],
        )
        for amb in orc.ambientes
    ]
    base = _resumo(orc).model_dump()
    lido = OrcamentoRead(
        **base,
        os_id=orc.os_id, numero_os=os_.numero_os,
        perda_bp=orc.perda_bp, sinal_bp=orc.sinal_bp, sinal_valor=_sinal(orc),
        validade=orc.validade, custo_total=orc.custo_total, observacao=orc.observacao,
        aprovado_por=orc.aprovado_por, recusado_motivo=orc.recusado_motivo,
        editavel=orc.situacao == SituacaoOrcamento.RASCUNHO,
        ambientes=ambientes,
        insumos=_insumos(orc),
    )
    return lido if ver_custos else _sem_custos(lido)


def _sem_custos(lido: OrcamentoRead) -> OrcamentoRead:
    """O marceneiro e o montador veem o orçamento, nunca o custo (DC5/D14)."""
    lido.custo_total = None
    for amb in lido.ambientes:
        for mov in amb.moveis:
            mov.custo = None
            mov.custo_terceiro = None
            for mat in mov.materiais:
                mat.custo_unitario = None
                mat.custo = None
    for ins in lido.insumos:
        ins.custo_unitario = None
    return lido


# --- Leitura ----------------------------------------------------------------------------

def listar(db: Session, numero_os: str) -> list[OrcamentoResumo]:
    os_ = _os_da_fabrica(db, numero_os)
    versoes = db.scalars(
        select(FabricaOrcamento).where(FabricaOrcamento.os_id == os_.id).order_by(FabricaOrcamento.versao.desc())
    ).all()
    return [_resumo(v) for v in versoes]


def obter(db: Session, orcamento_id: int, ver_custos: bool = True) -> OrcamentoRead:
    return _ler(db, _orcamento(db, orcamento_id), ver_custos)


# --- Escrita --------------------------------------------------------------------------------

def criar(db: Session, numero_os: str, copiar_de: Optional[int], usuario: str = "Sistema") -> OrcamentoRead:
    """Nova versão: vazia, ou cópia de outra DESTA OS (a árvore e os custos copiados)."""
    os_ = _os_da_fabrica(db, numero_os)
    _assert_os_aberta(os_)
    ultima = db.scalar(select(func.max(FabricaOrcamento.versao)).where(FabricaOrcamento.os_id == os_.id)) or 0
    novo = FabricaOrcamento(os_id=os_.id, versao=ultima + 1, situacao=SituacaoOrcamento.RASCUNHO)

    if copiar_de is not None:
        origem = _orcamento(db, copiar_de)
        if origem.os_id != os_.id:
            raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, "Só dá para copiar uma versão desta mesma OS.")
        novo.perda_bp, novo.sinal_bp = origem.perda_bp, origem.sinal_bp
        novo.validade, novo.observacao = origem.validade, origem.observacao
        for amb in origem.ambientes:
            novo.ambientes.append(FabricaAmbiente(
                nome=amb.nome, ordem=amb.ordem,
                moveis=[
                    FabricaMovel(
                        nome=mov.nome, largura_mm=mov.largura_mm, altura_mm=mov.altura_mm,
                        profundidade_mm=mov.profundidade_mm, preco_venda=mov.preco_venda,
                        terceirizado=mov.terceirizado, custo_terceiro=mov.custo_terceiro, ordem=mov.ordem,
                        materiais=[
                            FabricaMaterial(
                                produto_id=mat.produto_id, descricao=mat.descricao,
                                consumo=mat.consumo, custo_unitario=mat.custo_unitario,
                            )
                            for mat in mov.materiais
                        ],
                    )
                    for mov in amb.moveis
                ],
            ))
    db.add(novo)
    db.flush()
    _recalcular_totais(novo)

    # Orçar é o que se faz depois de medir. Com a medição completa (ou as
    # etapas em modo aviso), a OS passa a "Em elaboração"; com a trava ligada e
    # sem foto, o orçamento nasce mas a OS espera a medição.
    if os_.fase_fabrica == Fase.MEDICAO:
        medicao_ok = all(t.ok for t in trilho.travas(db, os_))
        if medicao_ok or not trilho.travar_etapas(db):
            trilho.mudar_fase(db, os_, Fase.ELABORACAO, EventoFase.AVANCO, usuario, f"Versão {novo.versao} criada")
    db.flush()
    db.refresh(novo)
    return _ler(db, novo)


def _produtos(db: Session, ids: set[int]) -> dict[int, Produto]:
    if not ids:
        return {}
    return {p.id: p for p in db.scalars(select(Produto).where(Produto.id.in_(ids))).all()}


def salvar(db: Session, orcamento_id: int, dados: OrcamentoEscrita) -> OrcamentoRead:
    """Substitui a árvore inteira de um RASCUNHO e recalcula tudo no servidor."""
    orc = _orcamento(db, orcamento_id)
    _exigir(orc, SituacaoOrcamento.RASCUNHO, acao="editar")
    _assert_os_aberta(db.get(OrdemServico, orc.os_id))

    ids = {mat.produto_id for amb in dados.ambientes for mov in amb.moveis for mat in mov.materiais}
    produtos = _produtos(db, ids)
    faltando = sorted(ids - produtos.keys())
    if faltando:
        raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Produto não encontrado: {', '.join(map(str, faltando))}.")
    nao_insumo = sorted(p.nome for p in produtos.values() if not _eh_insumo(p))
    if nao_insumo:
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Estes produtos ainda não são insumo da fábrica (falta dizer quanto rendem, no cadastro do produto): "
            + ", ".join(nao_insumo) + ".",
        )

    # O custo é copiado do cadastro AO INCLUIR a linha: a linha que já existia
    # (mesmo id, mesmo produto) guarda o custo de quando entrou.
    custos_antigos = {
        mat.id: (mat.produto_id, mat.custo_unitario)
        for _amb, mov in _moveis(orc) for mat in mov.materiais
    }

    def custo_da_linha(linha) -> int:
        antigo = custos_antigos.get(linha.id) if linha.id else None
        if antigo and antigo[0] == linha.produto_id:
            return antigo[1]
        return custo_atual(produtos[linha.produto_id].estoque) or 0

    novos = [
        FabricaAmbiente(
            nome=amb.nome.strip(), ordem=i,
            moveis=[
                FabricaMovel(
                    nome=mov.nome.strip(), largura_mm=mov.largura_mm, altura_mm=mov.altura_mm,
                    profundidade_mm=mov.profundidade_mm, preco_venda=mov.preco_venda,
                    terceirizado=mov.terceirizado,
                    custo_terceiro=mov.custo_terceiro if mov.terceirizado else None,
                    ordem=j,
                    materiais=[
                        FabricaMaterial(
                            produto_id=mat.produto_id, descricao=produtos[mat.produto_id].nome,
                            consumo=mat.consumo, custo_unitario=custo_da_linha(mat),
                        )
                        for mat in mov.materiais
                    ],
                )
                for j, mov in enumerate(amb.moveis)
            ],
        )
        for i, amb in enumerate(dados.ambientes)
    ]

    orc.ambientes.clear()
    db.flush()
    orc.ambientes.extend(novos)
    orc.perda_bp, orc.sinal_bp = dados.perda_bp, dados.sinal_bp
    orc.validade, orc.observacao = dados.validade, dados.observacao
    db.flush()
    db.refresh(orc)
    _recalcular_totais(orc)
    db.flush()
    return _ler(db, orc)


def enviar(db: Session, orcamento_id: int, usuario: str = "Sistema") -> OrcamentoRead:
    """RASCUNHO → ENVIADO: a proposta foi para o cliente e não muda mais."""
    orc = _orcamento(db, orcamento_id)
    _exigir(orc, SituacaoOrcamento.RASCUNHO, acao="enviar")
    os_ = db.get(OrdemServico, orc.os_id)
    _assert_os_aberta(os_)

    moveis = _moveis(orc)
    if not moveis:
        raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, "O orçamento não tem nenhum móvel.")
    sem_preco = [f"{amb.nome} — {mov.nome}" for amb, mov in moveis if mov.preco_venda <= 0]
    if sem_preco:
        raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, "Móveis sem preço: " + "; ".join(sem_preco) + ".")
    _exigir_insumos_validos(orc)

    if os_.fase_fabrica == Fase.MEDICAO and trilho.travar_etapas(db):
        pendentes = [t.texto for t in trilho.travas(db, os_) if not t.ok]
        if pendentes:
            raise _erro(status.HTTP_409_CONFLICT, "Conclua a medição antes de enviar: " + "; ".join(pendentes) + ".")

    _recalcular_totais(orc)
    orc.situacao = SituacaoOrcamento.ENVIADO
    orc.enviado_em = agora_utc()
    if os_.fase_fabrica in (Fase.MEDICAO, Fase.ELABORACAO):
        trilho.mudar_fase(db, os_, Fase.AGUARDANDO_APROVACAO, EventoFase.AVANCO, usuario,
                          f"Proposta v{orc.versao} enviada")
    db.flush()
    return _ler(db, orc)


def _exigir_insumos_validos(orc: FabricaOrcamento) -> None:
    """O produto pode ter deixado de ser insumo (ou sumido) depois de entrar na lista."""
    ruins = sorted({
        mat.descricao for _amb, mov in _moveis(orc) for mat in mov.materiais if not _eh_insumo(mat.produto)
    })
    if ruins:
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Estes materiais não são mais insumo da fábrica (ou o produto foi apagado): " + ", ".join(ruins) + ".",
        )


def _unidade_do_item(produto: Produto) -> UnidadeMedida:
    """O item da OS exige o enum; a unidade do produto é texto livre ("CH", "RL")."""
    try:
        return UnidadeMedida((produto.unidade_medida or "UN").upper())
    except ValueError:
        return UnidadeMedida.OUTROS


def _itens_da_aprovacao(db: Session, orc: FabricaOrcamento) -> list[OrdemServicoItem]:
    itens: list[OrdemServicoItem] = []
    for amb, mov in _moveis(orc):
        nome = f"{amb.nome} — {mov.nome}" + (f" ({mov.medidas})" if mov.medidas else "")
        itens.append(OrdemServicoItem(
            tipo=OrdemServicoItemTipo.SERVICO,
            nome=nome[:255],
            unidade_medida=UnidadeMedida.UNIDADE,
            quantidade=1,
            valor_unitario=mov.preco_venda,
            valor_total=mov.preco_venda,
            status_aprovacao=OrdemServicoItemAprovacao.APROVADO,
            visivel_cliente=True,
            # Só o terceiro: o material entra no custo pela baixa do estoque.
            custo_unitario=mov.custo_terceiro if mov.terceirizado else None,
            fabrica_orcamento_id=orc.id,
            fabrica_movel_id=mov.id,
        ))
    for insumo in _insumos(orc):
        produto = db.get(Produto, insumo.produto_id)
        itens.append(OrdemServicoItem(
            tipo=OrdemServicoItemTipo.PRODUTO,
            produto_id=insumo.produto_id,
            nome=insumo.descricao[:255],
            unidade_medida=_unidade_do_item(produto),
            quantidade=insumo.quantidade,
            valor_unitario=0,
            valor_total=0,
            status_aprovacao=OrdemServicoItemAprovacao.APROVADO,
            visivel_cliente=False,
            custo_unitario=insumo.custo_unitario,
            fabrica_orcamento_id=orc.id,
        ))
    return itens


def aprovar(db: Session, orcamento_id: int, usuario_nome: str) -> OrcamentoRead:
    """ENVIADO → APROVADO: escreve os itens na OS, congelados (§2, D12)."""
    orc = _orcamento(db, orcamento_id)
    _exigir(orc, SituacaoOrcamento.ENVIADO, acao="aprovar")
    os_ = db.get(OrdemServico, orc.os_id)
    _assert_os_aberta(os_)
    _exigir_insumos_validos(orc)

    outras = db.scalars(
        select(FabricaOrcamento).where(FabricaOrcamento.os_id == os_.id, FabricaOrcamento.id != orc.id)
    ).all()
    for outra in outras:
        if outra.situacao == SituacaoOrcamento.APROVADO:
            outra.situacao = SituacaoOrcamento.RECUSADO
            outra.recusado_motivo = f"Substituída pela versão {orc.versao}."
        elif outra.situacao == SituacaoOrcamento.ENVIADO:
            outra.situacao = SituacaoOrcamento.RECUSADO
            outra.recusado_motivo = f"O cliente aprovou a versão {orc.versao}."

    # Troca SÓ os itens que a fábrica gerou; o que foi lançado à mão fica.
    os_.itens = [i for i in os_.itens if i.fabrica_orcamento_id is None]
    db.flush()
    os_.itens.extend(_itens_da_aprovacao(db, orc))
    db.flush()
    _recalcular_valor_total_os(os_)

    _recalcular_totais(orc)
    orc.situacao = SituacaoOrcamento.APROVADO
    orc.aprovado_em = agora_utc()
    orc.aprovado_por = usuario_nome
    orc.recusado_motivo = None
    if os_.fase_fabrica in Fase.ANTES_DA_APROVACAO:
        trilho.mudar_fase(db, os_, Fase.AGUARDANDO_SINAL, EventoFase.APROVACAO, usuario_nome,
                          f"Versão {orc.versao} aprovada")
    else:
        # Nova versão aprovada com a OS já andando: a fase fica, o log conta.
        trilho.registrar(db, os_, EventoFase.APROVACAO, usuario_nome, f"Versão {orc.versao} aprovada")
    db.flush()
    return _ler(db, orc)


def recusar(db: Session, orcamento_id: int, motivo: str, usuario: str = "Sistema") -> OrcamentoRead:
    """ENVIADO (ou vencido) → RECUSADO. Sem outra versão na mesa, a OS volta a orçar."""
    orc = _orcamento(db, orcamento_id)
    _exigir(orc, SituacaoOrcamento.ENVIADO, VENCIDO, acao="recusar")
    os_ = db.get(OrdemServico, orc.os_id)
    _assert_os_aberta(os_)

    orc.situacao = SituacaoOrcamento.RECUSADO
    orc.recusado_motivo = motivo.strip()
    db.flush()

    ainda_na_mesa = db.scalar(
        select(func.count()).select_from(FabricaOrcamento).where(
            FabricaOrcamento.os_id == os_.id,
            FabricaOrcamento.situacao.in_((SituacaoOrcamento.ENVIADO, SituacaoOrcamento.APROVADO)),
        )
    )
    if not ainda_na_mesa and os_.fase_fabrica == Fase.AGUARDANDO_APROVACAO:
        trilho.mudar_fase(db, os_, Fase.ELABORACAO, EventoFase.RETROCESSO, usuario,
                          f"Versão {orc.versao} recusada: {motivo.strip()}")
    db.flush()
    return _ler(db, orc)
