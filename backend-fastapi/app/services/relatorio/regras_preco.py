# ---------------------------------------------------------------------------
# ARQUIVO: services/relatorio/regras_preco.py
# DESCRICAO: Relatorios - vendas por regra de preco por quantidade (so o Master).
# ---------------------------------------------------------------------------

from datetime import date
from sqlalchemy.orm import Session
from app.core.tempo import intervalo_utc
from app.db.crud import relatorio as relatorio_crud
from app.schemas.relatorio import (
    RelatorioRegrasPreco,
    RegraPrecoResumo,
    RegraPrecoProdutoItem,
)


# ---------------------------------------------------------------------------
# VENDAS POR REGRA DE PREÇO (plano de embalagens, fase 6)
# ---------------------------------------------------------------------------

def get_regras_preco(db: Session, inicio: date, fim: date, empresa_id: int) -> RelatorioRegrasPreco:
    """
    O que as regras de preço por quantidade (R1, R2, R3) venderam e abateram.

    Responde a pergunta do dono que ligou a regra: "quanto eu deixei de cobrar
    com o preço de fardo, e quanto vendi por causa dele?". Lê o que ficou
    congelado na linha (`regra_preco`, `desconto_regra`, `valor_unitario_tabela`),
    então mudar a regra hoje não reescreve o relatório do mês passado.

    `qtd_vendas` do topo vem de uma contagem própria: a mesma venda pode ter
    linhas de duas regras, e somar os grupos a contaria duas vezes. Pelo mesmo
    motivo o `qtd_vendas` de cada regra não soma o do topo.
    """
    dt_inicio, dt_fim = intervalo_utc(inicio, fim)

    linhas = relatorio_crud.get_vendas_por_regra_preco(db, dt_inicio, dt_fim, empresa_id)

    por_produto = [
        RegraPrecoProdutoItem(
            regra=r.regra,
            produto_id=r.produto_id,
            nome=r.nome,
            sku=r.sku,
            qtd_vendas=r.qtd_vendas or 0,
            unidades=r.unidades or 0,
            faturamento=r.faturamento or 0,
            abatimento=r.abatimento or 0,
        )
        for r in linhas
    ]

    # Por regra: a contagem de vendas sai do crud por produto, então aqui ela
    # é por (regra, venda). Monta a partir dos ids, não somando os grupos.
    acumulado: dict[str, dict[str, int]] = {}
    for item in por_produto:
        a = acumulado.setdefault(item.regra, {"unidades": 0, "faturamento": 0, "abatimento": 0})
        a["unidades"] += item.unidades
        a["faturamento"] += item.faturamento
        a["abatimento"] += item.abatimento
    vendas_por_regra = relatorio_crud.get_vendas_com_regra_por_regra(db, dt_inicio, dt_fim, empresa_id)

    por_regra = [
        RegraPrecoResumo(regra=regra, qtd_vendas=vendas_por_regra.get(regra, 0), **valores)
        for regra, valores in sorted(acumulado.items())
    ]

    return RelatorioRegrasPreco(
        inicio=inicio,
        fim=fim,
        qtd_vendas=relatorio_crud.get_vendas_com_regra_count(db, dt_inicio, dt_fim, empresa_id),
        faturamento=sum(i.faturamento for i in por_produto),
        abatimento=sum(i.abatimento for i in por_produto),
        por_regra=por_regra,
        por_produto=por_produto,
    )
