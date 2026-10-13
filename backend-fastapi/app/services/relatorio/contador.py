# ---------------------------------------------------------------------------
# ARQUIVO: services/relatorio/contador.py
# DESCRICAO: Relatorios - receita segregada para o contador (PGDAS-D) (so o Master).
# ---------------------------------------------------------------------------

from datetime import date
from sqlalchemy.orm import Session
from app.core.tempo import intervalo_utc
from app.core import segregacao_receita
from app.core.enum import OrdemServicoItemTipo
from app.db.models.empresa import Empresa
from app.db.crud import relatorio as relatorio_crud
from app.schemas.relatorio import (
    RelatorioContador,
    ReceitaGrupoItem,
    ProdutoSemClassificacaoItem,
)


# ---------------------------------------------------------------------------
# RECEITA PARA O CONTADOR (segregação do PGDAS-D)
# ---------------------------------------------------------------------------

# Todo grupo aparece, mesmo zerado: o contador confere a declaração linha a
# linha, e um grupo que some parece esquecido.
_GRUPOS = [
    segregacao_receita.Grupo(icms_st=False, monofasico=False),
    segregacao_receita.Grupo(icms_st=True, monofasico=False),
    segregacao_receita.Grupo(icms_st=False, monofasico=True),
    segregacao_receita.Grupo(icms_st=True, monofasico=True),
]


def get_contador(db: Session, inicio: date, fim: date, empresa_id: int) -> RelatorioContador:
    """
    A receita do período como o contador declara no PGDAS-D: mercadoria em
    quatro grupos (ICMS normal/ST × PIS-COFINS normal/monofásico), serviços, e
    frete e juros à parte.

    Bate com o faturamento bruto do relatório de faturamento (mesmas datas e
    filtros): `receita_total == faturamento_vendas + faturamento_os`.

    - Classifica pelo cadastro fiscal ATUAL do produto: a linha da venda não
      congela o CST. Corrigir o cadastro corrige o relatório do mês passado.
    - O desconto da OS é da OS, não do item: é rateado pelos itens na
      proporção do valor. Na venda o desconto já está na linha.
    - Avulso e produto sem CSOSN/CST não são chutados como "normal": vão para
      "sem classificação", com a lista do que corrigir.
    """
    dt_inicio, dt_fim = intervalo_utc(inicio, fim)
    empresa = db.get(Empresa, empresa_id)
    crt = empresa.crt if empresa else None
    motivo_sem_codigo = (
        "Sem CSOSN no cadastro fiscal" if crt in segregacao_receita.CRT_QUE_USAM_CSOSN
        else "Sem CST de ICMS no cadastro fiscal"
    )

    grupos: dict[segregacao_receita.Grupo, int] = {g: 0 for g in _GRUPOS}
    sem_classificacao: dict[tuple, dict] = {}
    servicos = 0
    frete_e_juros = 0

    def mercadoria(linha, valor: int, motivo_avulso: str) -> None:
        if linha.produto_id is None:
            grupo, motivo = None, motivo_avulso
        else:
            grupo = segregacao_receita.classificar(
                crt, linha.csosn, linha.cst_icms, linha.cst_pis, linha.cst_cofins
            )
            motivo = motivo_sem_codigo
        if grupo is not None:
            grupos[grupo] += valor
            return
        # Avulso não tem id: agrupa pelo nome digitado.
        chave = (linha.produto_id, linha.nome if linha.produto_id is None else None)
        item = sem_classificacao.setdefault(
            chave, {"produto_id": linha.produto_id, "nome": linha.nome or "—", "valor": 0, "motivo": motivo}
        )
        item["valor"] += valor

    # Vendas: a linha já é líquida (desconto do operador e da regra).
    for linha in relatorio_crud.get_linhas_venda_fiscal(db, dt_inicio, dt_fim, empresa_id):
        mercadoria(linha, linha.valor or 0, "Item avulso (sem cadastro)")
    extras = relatorio_crud.get_extras_vendas(db, dt_inicio, dt_fim, empresa_id)
    frete_e_juros += (extras.entrega or 0) + (extras.acrescimo or 0)
    faturamento_vendas = extras.total or 0

    # OS: agrupa os itens por OS para ratear o desconto dela.
    por_os: dict[int, list] = {}
    for linha in relatorio_crud.get_itens_os_fiscal(db, dt_inicio, dt_fim, empresa_id):
        por_os.setdefault(linha.os_id, []).append(linha)

    faturamento_os = 0
    for itens in por_os.values():
        os_total = itens[0].os_total or 0
        faturamento_os += os_total
        pesos = [i.valor or 0 for i in itens]
        liquido = max(0, sum(pesos) - (itens[0].os_desconto or 0))
        # O que sobra do total é taxa de entrega e juros.
        frete_e_juros += os_total - liquido
        for item, valor in zip(itens, segregacao_receita.ratear(liquido, pesos)):
            if item.tipo == OrdemServicoItemTipo.SERVICO:
                servicos += valor
            else:
                mercadoria(item, valor, "Peça avulsa na OS (sem cadastro)")

    # OS sem item que conte (só taxa, ou tudo reprovado): o total é extra.
    sem_itens = relatorio_crud.get_os_finalizadas_sem_itens_total(db, dt_inicio, dt_fim, empresa_id)
    faturamento_os += sem_itens
    frete_e_juros += sem_itens

    lista_sem = sorted(
        (ProdutoSemClassificacaoItem(**i) for i in sem_classificacao.values() if i["valor"]),
        key=lambda i: i.valor,
        reverse=True,
    )
    total_sem = sum(i["valor"] for i in sem_classificacao.values())

    return RelatorioContador(
        inicio=inicio,
        fim=fim,
        crt=crt,
        receita_total=sum(grupos.values()) + total_sem + servicos + frete_e_juros,
        mercadoria=[
            ReceitaGrupoItem(icms_st=g.icms_st, monofasico=g.monofasico, valor=v) for g, v in grupos.items()
        ],
        mercadoria_sem_classificacao=total_sem,
        servicos=servicos,
        frete_e_juros=frete_e_juros,
        faturamento_vendas=faturamento_vendas,
        faturamento_os=faturamento_os,
        produtos_sem_classificacao=lista_sem,
    )
