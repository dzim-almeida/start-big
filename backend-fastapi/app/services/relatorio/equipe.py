# ---------------------------------------------------------------------------
# ARQUIVO: services/relatorio/equipe.py
# DESCRICAO: Relatorios - ranking, comissao e extrato do funcionario (so o Master).
# ---------------------------------------------------------------------------

from datetime import date, datetime, timezone
from sqlalchemy.orm import Session
from app.core.tempo import fuso_local, intervalo_utc
from app.core.segregacao_receita import ratear
from app.helpers.exceptions import NotFoundException
from app.db.crud import relatorio as relatorio_crud
from app.db.crud import funcionario as funcionario_crud
from app.schemas.relatorio import (
    RelatorioRanking,
    RankingFuncionarioItem,
    RelatorioComissao,
    ComissaoFuncionarioItem,
    RelatorioExtratoFuncionario,
    ExtratoServicoItem,
    ExtratoVendaItem,
)


def get_ranking(db: Session, inicio: date, fim: date, empresa_id: int) -> RelatorioRanking:
    """Ranking de funcionarios por faturamento (vendas + OS finalizadas) no periodo.

    Só entram funcionarios que faturaram algo (total > 0), ja ordenados desc pelo crud.
    """
    dt_inicio, dt_fim = intervalo_utc(inicio, fim)

    rows = relatorio_crud.get_ranking_faturamento(db, dt_inicio, dt_fim, empresa_id)
    itens: list[RankingFuncionarioItem] = []
    for r in rows:
        vendas = r.vendas_valor or 0
        os = r.os_valor or 0
        total = vendas + os
        if total <= 0:
            continue
        itens.append(
            RankingFuncionarioItem(
                funcionario_id=r.id,
                nome=r.nome,
                faturamento_vendas=vendas,
                faturamento_os=os,
                faturamento_total=total,
                qtd_vendas=r.vendas_qtd or 0,
                qtd_os=r.os_qtd or 0,
            )
        )

    return RelatorioRanking(inicio=inicio, fim=fim, itens=itens)


def get_comissao(db: Session, inicio: date, fim: date, empresa_id: int) -> RelatorioComissao:
    """
    Comissao apurada por funcionario no periodo.

    Base LIQUIDA (Venda.total e OS.valor_total ja sao pos-desconto), só FINALIZADO.
    Taxa e modo resolvidos por cascata funcionario -> cargo (no crud).

    Modo (F3c):
      - 'direto' (padrao; tambem quando o modo vem NULL): comissao = base * taxa.
      - 'meta'  : gatilho — só paga se o faturamento_total atingir a meta; abaixo
                  da meta a comissao é ZERO. Sem meta definida nao ha como travar,
                  entao cai em 'direto' (nao zera ninguem em silencio).
    Taxa em basis points (500 = 5,00% -> divide por 10000).
    """
    dt_inicio, dt_fim = intervalo_utc(inicio, fim)

    rows = relatorio_crud.get_comissao_base(db, dt_inicio, dt_fim, empresa_id)
    itens: list[ComissaoFuncionarioItem] = []
    total_comissao = 0
    for r in rows:
        vendas = r.vendas_valor or 0
        os = r.os_valor or 0
        fat_total = vendas + os
        if fat_total <= 0:
            continue  # só quem faturou entra na apuração

        rate_v = r.rate_venda  # basis points ou None
        rate_s = r.rate_servico
        meta = r.meta
        modo = r.modo or "direto"

        # Gatilho por meta: modo 'meta' COM meta definida trava a comissao ate bater.
        # Sem meta, o gatilho nao tem referencia -> comporta como 'direto'.
        bloqueada_por_meta = modo == "meta" and bool(meta) and fat_total < meta
        comissao_liberada = not bloqueada_por_meta

        if comissao_liberada:
            comissao_vendas = round(vendas * (rate_v or 0) / 10000)
            comissao_servico = round(os * (rate_s or 0) / 10000)
        else:
            comissao_vendas = 0
            comissao_servico = 0
        comissao_total = comissao_vendas + comissao_servico
        total_comissao += comissao_total

        meta_pct = round(fat_total / meta * 100, 1) if meta else None

        itens.append(
            ComissaoFuncionarioItem(
                funcionario_id=r.id,
                nome=r.nome,
                faturamento_vendas=vendas,
                faturamento_os=os,
                faturamento_total=fat_total,
                percentual_venda=rate_v,
                percentual_servico=rate_s,
                comissao_vendas=comissao_vendas,
                comissao_servico=comissao_servico,
                comissao_total=comissao_total,
                meta_mensal=meta,
                meta_atingida_percentual=meta_pct,
                comissao_modo=modo,
                comissao_liberada=comissao_liberada,
            )
        )

    return RelatorioComissao(inicio=inicio, fim=fim, total_comissao=total_comissao, itens=itens)


def get_extrato_funcionario(
    db: Session, inicio: date, fim: date, empresa_id: int, funcionario_id: int
) -> RelatorioExtratoFuncionario:
    """O extrato de servicos de uma pessoa -- o papel que ela leva para conferir.

    A CONTAGEM DE OS E POR OS DISTINTA, e isso nao e detalhe. O crud devolve uma
    linha por ITEM, entao somar linhas diria "3 OS" onde ha uma OS com tres
    servicos. O ranking, que e o primeiro lugar onde alguem confere este extrato,
    conta OS -- e dois relatorios que discordam do mesmo numero destroem a
    confianca nos dois.

    Pela mesma razao o `valor_total` soma os ITENS de servico, e nao o
    `valor_total` da OS: a OS carrega peca junto, e o extrato e sobre o trabalho.
    O numero daqui e menor que o `faturamento_os` do ranking sempre que houver
    peca -- e isso e correto, nao divergencia.
    """
    dt_inicio, dt_fim = intervalo_utc(inicio, fim)

    funcionario = funcionario_crud.get_funcionario_by_id(db, funcionario_id)
    if not funcionario or funcionario.empresa_id != empresa_id:
        raise NotFoundException(detail="Funcionário não encontrado")

    linhas = relatorio_crud.get_servicos_do_funcionario(
        db, dt_inicio, dt_fim, empresa_id, funcionario_id
    )

    itens: list[ExtratoServicoItem] = []
    os_distintas: set[int] = set()
    total = 0
    total_mao_de_obra = 0

    for linha in linhas:
        os_distintas.add(linha.os_id)
        total += linha.valor_total or 0

        # "Fiat Uno · ABC-1234" -- o mesmo par que a OS mostra na tela. Cada
        # pedaco pode faltar (objeto sem serie, OS sem objeto), entao monta com o
        # que houver em vez de assumir os tres.
        partes = [p for p in (linha.marca, linha.modelo) if p]
        descricao = " ".join(partes) if partes else None
        if descricao and linha.numero_serie:
            descricao = f"{descricao} · {linha.numero_serie}"
        elif not descricao and linha.numero_serie:
            descricao = linha.numero_serie

        # O custo e por UNIDADE; a mao de obra multiplica pela quantidade,
        # senao dois servicos iguais na mesma linha descontariam so uma peca.
        custo_linha = round((linha.quantidade or 0) * (linha.custo_unitario or 0))
        itens.append(
            ExtratoServicoItem(
                numero_os=linha.numero_os,
                data_finalizacao=linha.data_finalizacao.date(),
                objeto=descricao,
                cliente=linha.cliente_nome,
                servico=linha.servico,
                quantidade=linha.quantidade,
                valor_total=linha.valor_total or 0,
                custo=custo_linha,
                mao_de_obra=max(0, (linha.valor_total or 0) - custo_linha),
            )
        )
        total_mao_de_obra += max(0, (linha.valor_total or 0) - custo_linha)

    # --- Vendas: uma por linha, com a margem que é a base da comissão -------
    vendas: list[ExtratoVendaItem] = []
    for v in relatorio_crud.get_vendas_do_funcionario(db, dt_inicio, dt_fim, funcionario_id):
        total_venda = v.total or 0
        vendas.append(ExtratoVendaItem(
            venda_id=v.venda_id,
            numero=str(v.numero_venda) if v.numero_venda is not None else f"#{v.venda_id}",
            data=_data_local(v.criado_em),
            cliente=v.cliente_nome,
            valor_total=total_venda,
            base=round(total_venda - (v.acrescimo or 0) - (v.custo or 0)),
        ))

    # --- Comissão: a MESMA da folha, repartida pelas linhas -----------------
    #
    # Recalcular aqui seria a segunda cópia da regra (taxa por cascata, meta,
    # piso em zero, base sobre margem) — e duas cópias divergem. O total vem
    # de `get_comissao` e é dividido na proporção da base de cada linha; linha
    # com base negativa (venda abaixo do custo) não recebe parte. Assim a soma
    # das linhas é exatamente o que a folha manda pagar.
    folha = next(
        (c for c in get_comissao(db, inicio, fim, empresa_id).itens if c.funcionario_id == funcionario_id),
        None,
    )
    if folha is not None:
        for venda, parte in zip(vendas, ratear(folha.comissao_vendas, [max(0, v.base) for v in vendas])):
            venda.comissao = parte
        for item, parte in zip(itens, ratear(folha.comissao_servico, [max(0, i.mao_de_obra) for i in itens])):
            item.comissao = parte

    return RelatorioExtratoFuncionario(
        inicio=inicio,
        fim=fim,
        funcionario_id=funcionario_id,
        funcionario_nome=funcionario.nome,
        qtd_os=len(os_distintas),
        qtd_servicos=len(itens),
        valor_total=total,
        total_mao_de_obra=total_mao_de_obra,
        itens=itens,
        qtd_vendas=len(vendas),
        total_vendas=sum(v.valor_total for v in vendas),
        vendas=vendas,
        base_vendas=folha.faturamento_vendas if folha else 0,
        base_servicos=folha.faturamento_os if folha else 0,
        percentual_venda=folha.percentual_venda if folha else None,
        percentual_servico=folha.percentual_servico if folha else None,
        comissao_vendas=folha.comissao_vendas if folha else 0,
        comissao_servico=folha.comissao_servico if folha else 0,
        comissao_total=folha.comissao_total if folha else 0,
        comissao_modo=folha.comissao_modo if folha else "direto",
        meta_mensal=folha.meta_mensal if folha else None,
        meta_atingida_percentual=folha.meta_atingida_percentual if folha else None,
        comissao_liberada=folha.comissao_liberada if folha else True,
    )


def _data_local(dt_utc: datetime) -> date:
    """A data da loja de um timestamp gravado em UTC (venda às 22h não vira o dia seguinte)."""
    return dt_utc.replace(tzinfo=timezone.utc).astimezone(fuso_local()).date()
