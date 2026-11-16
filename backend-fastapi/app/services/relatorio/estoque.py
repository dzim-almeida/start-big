# ---------------------------------------------------------------------------
# ARQUIVO: services/relatorio/estoque.py
# DESCRICAO: Relatorios - estoque e curva ABC (so o Master).
# ---------------------------------------------------------------------------

from datetime import date
from sqlalchemy.orm import Session
from app.core.tempo import intervalo_utc
from app.db.crud import relatorio as relatorio_crud
from app.schemas.relatorio import (
    RelatorioEstoque,
    EstoqueAbcItem,
    EstoqueReposicaoItem,
    EstoqueParadoItem,
)


# ---------------------------------------------------------------------------
# ESTOQUE / CURVA ABC (Fase 4a)
# ---------------------------------------------------------------------------

# Cortes clássicos da Curva ABC sobre o % ACUMULADO de faturamento.
_ABC_CORTE_A = 80.0   # até 80% acumulado -> classe A


_ABC_CORTE_B = 95.0   # de 80% a 95% -> classe B; acima -> classe C


def _classe_abc(acumulado_pct: float) -> str:
    if acumulado_pct <= _ABC_CORTE_A:
        return "A"
    if acumulado_pct <= _ABC_CORTE_B:
        return "B"
    return "C"


def get_estoque(db: Session, inicio: date, fim: date, empresa_id: int) -> RelatorioEstoque:
    """
    Relatório de estoque: Curva ABC (por faturamento no período) + KPIs de valor
    imobilizado (posição ATUAL) + reposição (abaixo do mínimo) + parados (sem venda).

    ABC classifica pelo % ACUMULADO de faturamento: A ≤ 80%, B ≤ 95%, C o resto.
    Só entram produtos que venderam. "Parados" são o complemento: ativos com estoque
    e sem nenhuma venda no período. Valor imobilizado é a foto de agora (independe do
    período) — custo usa o custo médio ponderado e cai para valor_entrada enquanto a
    média não existir; sem nenhum dos dois, conta como 0 (não estima).
    """
    dt_inicio, dt_fim = intervalo_utc(inicio, fim)

    vendas = relatorio_crud.get_vendas_por_produto(db, dt_inicio, dt_fim, empresa_id)
    faturamento_total = sum((r.faturamento or 0) for r in vendas)
    vendidos_ids: set[int] = set()

    curva: list[EstoqueAbcItem] = []
    acumulado = 0
    for r in vendas:
        fat = r.faturamento or 0
        if fat <= 0:
            continue  # sem receita não classifica (evita divisão por zero / ruído)
        vendidos_ids.add(r.produto_id)
        acumulado += fat
        participacao = round(fat / faturamento_total * 100, 2) if faturamento_total else 0.0
        acumulado_pct = round(acumulado / faturamento_total * 100, 2) if faturamento_total else 0.0
        curva.append(
            EstoqueAbcItem(
                produto_id=r.produto_id,
                nome=r.nome,
                sku=r.sku,
                categoria=r.categoria,
                faturamento=fat,
                quantidade=r.quantidade or 0,
                participacao_pct=participacao,
                acumulado_pct=acumulado_pct,
                classe=_classe_abc(acumulado_pct),
            )
        )

    # Posição de estoque (global) -> KPIs, abaixo do mínimo e parados.
    produtos = relatorio_crud.get_produtos_estoque(db)
    valor_custo_total = 0
    valor_venda_total = 0
    abaixo: list[EstoqueReposicaoItem] = []
    parados: list[EstoqueParadoItem] = []

    for p in produtos:
        qtd = p.quantidade or 0
        # Capital imobilizado vale pelo custo contábil, não pelo último preço
        # digitado no cadastro. A média só assume quando existe; até lá o
        # comportamento é o de antes.
        custo = p.custo_medio if p.custo_medio is not None else (p.valor_entrada or 0)
        # round: estoque fracionado (6,5 kg × R$ 10,01) dá centavo quebrado, e
        # a resposta é em centavo inteiro. Até 07/10/2026 isto derrubava o
        # relatório de estoque de qualquer loja com produto em KG.
        valor_custo_total += round(qtd * custo)
        valor_venda_total += round(qtd * (p.valor_varejo or 0))

        # Abaixo do mínimo: zerado, ou com mínimo definido e atingido.
        if qtd == 0 or (p.quantidade_minima is not None and qtd <= p.quantidade_minima):
            abaixo.append(
                EstoqueReposicaoItem(
                    produto_id=p.produto_id,
                    nome=p.nome,
                    sku=p.sku,
                    quantidade=qtd,
                    quantidade_minima=p.quantidade_minima,
                    quantidade_ideal=p.quantidade_ideal,
                )
            )

        # Parado: tem estoque e não vendeu nada no período.
        if qtd > 0 and p.produto_id not in vendidos_ids:
            parados.append(
                EstoqueParadoItem(
                    produto_id=p.produto_id,
                    nome=p.nome,
                    sku=p.sku,
                    quantidade=qtd,
                    valor_custo=round(qtd * custo),
                )
            )

    # Parados: maior capital imobilizado primeiro (prioriza a decisão do dono).
    parados.sort(key=lambda x: x.valor_custo, reverse=True)

    return RelatorioEstoque(
        inicio=inicio,
        fim=fim,
        valor_custo_total=valor_custo_total,
        valor_venda_total=valor_venda_total,
        skus_ativos=len(produtos),
        itens_abaixo_minimo=len(abaixo),
        itens_parados=len(parados),
        curva_abc=curva,
        abaixo_minimo=abaixo,
        parados=parados,
    )
