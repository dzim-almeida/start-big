# ---------------------------------------------------------------------------
# ARQUIVO: services/relatorio/faturamento.py
# DESCRICAO: Relatorios - faturamento da loja (Master) e o pessoal do funcionario.
# ---------------------------------------------------------------------------

from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.core.tempo import intervalo_utc
from app.db.crud import dashboard as dashboard_crud
from app.db.crud import relatorio as relatorio_crud
from app.services.precificacao import custo_mercadoria as custo_mercadoria
from app.schemas.relatorio import (
    RelatorioFaturamento,
    FaturamentoDiaItem,
    FormaPagamentoResumo,
)


def _serie_por_dia(
    inicio: date,
    fim: date,
    vendas_dia: dict[str, int],
    os_dia: dict[str, int],
) -> list[FaturamentoDiaItem]:
    """Serie diaria continua: dia sem movimento entra como zero, senao o grafico pula buracos."""
    por_dia: list[FaturamentoDiaItem] = []
    dia = inicio
    while dia <= fim:
        chave = dia.isoformat()
        tv = vendas_dia.get(chave, 0)
        to = os_dia.get(chave, 0)
        por_dia.append(
            FaturamentoDiaItem(dia=dia, total_vendas=tv, total_os=to, total_geral=tv + to)
        )
        dia += timedelta(days=1)
    return por_dia


def get_faturamento_pessoal(
    db: Session, inicio: date, fim: date, funcionario_id: int
) -> RelatorioFaturamento:
    """
    O relatorio de faturamento restrito ao que ESTE funcionario fez.

    Mesmo schema do relatorio da loja, de proposito: a tela e a impressao sao as
    mesmas, muda so o recorte. Reusa as agregacoes pessoais do dashboard
    (get_meu_resumo_stats, get_minhas_*_por_dia), entao o numero daqui bate com o
    "Meu resumo" da Home — dois lugares que discordassem seriam pior que um so.

    O QUE FICA DE FORA, E POR QUE. Juros de cartao, CMV, lucro bruto, margem e
    formas de pagamento ficam no DEFAULT (zero/vazio). Nao e omissao por
    preguica: sao contas da LOJA, nao do funcionario.

      - juros e CMV sao custo do dono. Repassar um pedaco deles ao funcionario
        que fez a venda daria um "lucro" que nao e o lucro de ninguem: o juros
        de uma venda dele foi bancado pelo caixa da loja, e o custo da peca saiu
        do estoque da loja.
      - formas de pagamento respondem "como o dinheiro entrou na loja", que e
        pergunta de conciliacao — do dono.

    A tela ja esconde esses blocos quando os valores sao zero, mas quem garante
    que o dado nao sai daqui e ESTE recorte, nao o `v-if`.
    """
    dt_inicio, dt_fim = intervalo_utc(inicio, fim)

    stats = dashboard_crud.get_meu_resumo_stats(db, dt_inicio, dt_fim, funcionario_id)
    faturamento_vendas = stats.minhas_vendas_valor
    faturamento_os = stats.minhas_os_valor
    faturamento_total = faturamento_vendas + faturamento_os
    qtd_transacoes = stats.minhas_vendas_count + stats.minhas_os_concluidas
    ticket_medio = int(faturamento_total / qtd_transacoes) if qtd_transacoes else 0

    vendas_dia = {
        str(r.dia): (r.total or 0)
        for r in dashboard_crud.get_minhas_vendas_por_dia(db, dt_inicio, dt_fim, funcionario_id)
    }
    os_dia = {
        str(r.dia): (r.total or 0)
        for r in dashboard_crud.get_minhas_os_por_dia(db, dt_inicio, dt_fim, funcionario_id)
    }

    return RelatorioFaturamento(
        inicio=inicio,
        fim=fim,
        faturamento_total=faturamento_total,
        faturamento_vendas=faturamento_vendas,
        faturamento_os=faturamento_os,
        # Sem juros a descontar, o liquido E o total. Preencher explicitamente
        # evita que a tela caia no fallback e mostre "R$ 0,00" de faturamento.
        faturamento_liquido=faturamento_total,
        ticket_medio=ticket_medio,
        qtd_vendas=stats.minhas_vendas_count,
        qtd_os=stats.minhas_os_concluidas,
        por_dia=_serie_por_dia(inicio, fim, vendas_dia, os_dia),
    )


def get_faturamento(db: Session, inicio: date, fim: date, empresa_id: int) -> RelatorioFaturamento:
    """
    Faturamento (vendas + OS finalizadas) no intervalo [inicio, fim]:
    KPIs, serie por dia e formas de pagamento.

    Os KPIs reusam get_stats_agregados (mesma base do dashboard), entao a soma da
    serie por dia bate com o faturamento_total.
    """
    dt_inicio, dt_fim = intervalo_utc(inicio, fim)

    stats = dashboard_crud.get_stats_agregados(db, dt_inicio, dt_fim, empresa_id)
    faturamento_vendas = stats.vendas_total
    faturamento_os = stats.os_soma
    faturamento_total = faturamento_vendas + faturamento_os
    qtd_transacoes = stats.vendas_count + stats.os_finalizadas_count
    ticket_medio = int(faturamento_total / qtd_transacoes) if qtd_transacoes else 0

    # Juros de cartao: sempre fica com a operadora — o que muda e quem pagou.
    # Repassado, ja inflou o faturamento_total (esta dentro do total da venda/OS).
    # Absorvido, nunca entrou no total, mas saiu do caixa da loja.
    # Os dois saem do liquido; so o segundo pode deixar o liquido menor que o bruto
    # sem que nenhuma linha de venda tenha mudado.
    juros = {"CLIENTE": 0, "LOJA": 0}
    for linha in relatorio_crud.get_juros_vendas_por_responsavel(db, dt_inicio, dt_fim, empresa_id):
        juros[linha.responsavel or "CLIENTE"] = juros.get(linha.responsavel or "CLIENTE", 0) + (linha.total or 0)
    for linha in relatorio_crud.get_juros_os_por_responsavel(db, dt_inicio, dt_fim, empresa_id):
        juros[linha.responsavel or "CLIENTE"] = juros.get(linha.responsavel or "CLIENTE", 0) + (linha.total or 0)

    juros_repassado = juros.get("CLIENTE", 0)
    juros_absorvido = juros.get("LOJA", 0)
    faturamento_liquido = faturamento_total - juros_repassado - juros_absorvido

    # CMV: o custo das pecas que sairam, congelado no livro de estoque no dia em
    # que sairam. A conta inteira mora em services/custo_mercadoria.py desde que
    # o Financeiro passou a descontar o custo do lucro dele — duas copias da
    # mesma soma e as duas telas mostrariam lucros diferentes para o mesmo mes.
    cmv, saidas_sem_custo = custo_mercadoria.calcular_cmv(
        db, dt_inicio, dt_fim, empresa_id
    )

    lucro_bruto = faturamento_liquido - cmv
    margem_percentual = (lucro_bruto / faturamento_total * 100) if faturamento_total else 0.0

    # Serie por dia — preenche dias sem movimento com zero para o grafico ficar continuo.
    vendas_dia = {
        str(r.dia): (r.total or 0)
        for r in relatorio_crud.get_faturamento_vendas_por_dia(db, dt_inicio, dt_fim, empresa_id)
    }
    os_dia = {
        str(r.dia): (r.total or 0)
        for r in relatorio_crud.get_faturamento_os_por_dia(db, dt_inicio, dt_fim, empresa_id)
    }

    por_dia = _serie_por_dia(inicio, fim, vendas_dia, os_dia)

    # Formas de pagamento — reusa o crud do dashboard e mescla vendas + OS.
    totais: dict[str, int] = {}
    for r in dashboard_crud.get_formas_pagamento_vendas(db, dt_inicio, dt_fim, empresa_id):
        totais[r.nome] = totais.get(r.nome, 0) + (r.total or 0)
    for r in dashboard_crud.get_formas_pagamento_os(db, dt_inicio, dt_fim, empresa_id):
        totais[r.nome] = totais.get(r.nome, 0) + (r.total or 0)
    formas = [
        FormaPagamentoResumo(nome=nome, valor_total=valor)
        for nome, valor in sorted(totais.items(), key=lambda x: x[1], reverse=True)
    ]

    return RelatorioFaturamento(
        inicio=inicio,
        fim=fim,
        faturamento_total=faturamento_total,
        faturamento_vendas=faturamento_vendas,
        faturamento_os=faturamento_os,
        juros_repassado=juros_repassado,
        juros_absorvido=juros_absorvido,
        faturamento_liquido=faturamento_liquido,
        cmv=cmv,
        lucro_bruto=lucro_bruto,
        margem_percentual=round(margem_percentual, 2),
        saidas_sem_custo=saidas_sem_custo,
        ticket_medio=ticket_medio,
        qtd_vendas=stats.vendas_count,
        qtd_os=stats.os_finalizadas_count,
        por_dia=por_dia,
        formas_pagamento=formas,
    )
