# ---------------------------------------------------------------------------
# ARQUIVO: services/financeiro/fluxo_caixa.py
# DESCRICAO: Financeiro - fluxo de caixa dos proximos dias.
# ---------------------------------------------------------------------------

from datetime import date, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.core.enum import (
    MovimentacaoFinanceiraTipo,
)
from app.core.tempo import hoje_local
from app.db.crud import financeiro as financeiro_crud
from app.schemas.financeiro import (
    FluxoCaixa,
    FluxoDia,
    FluxoLancamento,
)
from app.services.financeiro.saldo import saldo_atual_das_contas


# ===========================================================================
# FLUXO DE CAIXA (Onda 3)
# ===========================================================================

def get_fluxo_caixa(db: Session, empresa_id: int, dias: int = 30) -> FluxoCaixa:
    """A projeção dos próximos `dias`, a partir do saldo declarado pelo dono.

    Três decisões que sustentam a tela, e o motivo de cada uma:

    O SALDO DE PARTIDA É O DE HOJE, DERIVADO. É a âncora que o dono declarou
    mais tudo que o livro registrou depois dela (ver `saldo_atual_das_contas`).
    Era o `saldo_informado` puro até 02/09/2026, e essa foto parada é o defeito
    que fez o dono relatar "não sobe conforme vou vendendo". Enquanto ninguém
    declarar a âncora, `saldo_declarado` sai False e a tela pede o número em vez
    de desenhar uma linha que parte de zero.

    O ATRASADO NÃO ENTRA NA RÉGUA. Conta vencida não tem dia futuro para
    ocupar. Empurrá-la para hoje inventaria um aperto que talvez não aconteça
    (o fiado atrasado pode nunca chegar; o boleto vencido pode já ter sido
    pago no banco sem alguém dar baixa aqui). Vai num balde à parte, como
    aviso, e o dono decide.

    SÓ DIAS COM MOVIMENTO. Sessenta linhas de zero escondem as cinco que
    importam. A régua contínua é trabalho da tela, que sabe o tamanho dela.
    """
    hoje = hoje_local()
    # `dias` conta a partir de HOJE inclusive: "próximos 30 dias" para o dono da
    # loja começa hoje de manhã, não amanhã.
    fim = hoje + timedelta(days=dias - 1)

    atual = saldo_atual_das_contas(db, empresa_id)
    saldo_inicial = atual.saldo

    pagar, receber = financeiro_crud.pendentes_por_vencimento(
        db, empresa_id, inicio=hoje, fim=fim
    )

    por_dia: Dict[date, Dict[str, Any]] = {}

    def _bucket(dia: date) -> Dict[str, Any]:
        return por_dia.setdefault(
            dia, {"entradas": 0, "saidas": 0, "lancamentos": []}
        )

    for conta in receber:
        b = _bucket(conta.vencimento)
        b["entradas"] += int(conta.valor or 0)
        b["lancamentos"].append(
            FluxoLancamento(
                conta_id=conta.id, tipo=MovimentacaoFinanceiraTipo.ENTRADA.value,
                descricao=conta.descricao, valor=int(conta.valor or 0),
            )
        )

    for conta in pagar:
        b = _bucket(conta.vencimento)
        b["saidas"] += int(conta.valor or 0)
        b["lancamentos"].append(
            FluxoLancamento(
                conta_id=conta.id, tipo=MovimentacaoFinanceiraTipo.SAIDA.value,
                descricao=conta.descricao, valor=int(conta.valor or 0),
                # A tela marca as que se repetem. Sem isso, pagar a internet de
                # setembro fazia a de outubro aparecer na régua e o dono ler que
                # o pagamento não tinha sido registrado -- foi o primeiro
                # estranhamento relatado depois que o saldo passou a andar.
                recorrente=bool(conta.recorrente),
            )
        )

    # Módulo Compras (docs/compras-plano.md, D8d): pedido enviado ainda não é
    # conta a pagar — a conta nasce no recebimento —, mas já é dinheiro
    # comprometido. Entra na régua MARCADO como previsão. Sem o módulo Compras
    # a lista vem vazia e a projeção fica exatamente como era.
    from app.services.compras.previsoes import previsoes_de_pagamento

    previsto_compras = 0
    for previsao in previsoes_de_pagamento(db, empresa_id, hoje, fim):
        b = _bucket(previsao.data)
        b["saidas"] += previsao.valor
        previsto_compras += previsao.valor
        b["lancamentos"].append(
            FluxoLancamento(
                conta_id=0, tipo=MovimentacaoFinanceiraTipo.SAIDA.value,
                descricao=previsao.descricao, valor=previsao.valor,
                previsao_compra=True, pedido_compra_id=previsao.pedido_id,
            )
        )

    saldo = saldo_inicial
    # O fundo do poço começa no próprio saldo de hoje: numa loja sem nada
    # agendado, o menor saldo do período é o que ela já tem.
    menor_saldo, menor_saldo_em = saldo_inicial, None
    primeiro_negativo: Optional[date] = None
    total_entradas = total_saidas = 0
    linha: List[FluxoDia] = []

    for data_dia in sorted(por_dia):
        dados = por_dia[data_dia]
        saldo += dados["entradas"] - dados["saidas"]
        total_entradas += dados["entradas"]
        total_saidas += dados["saidas"]

        if saldo < menor_saldo:
            menor_saldo, menor_saldo_em = saldo, data_dia
        # O PRIMEIRO dia negativo, e não o último: é a data em que o dono
        # precisa ter feito alguma coisa, e depois dela o resto é consequência.
        if saldo < 0 and primeiro_negativo is None:
            primeiro_negativo = data_dia

        linha.append(
            FluxoDia(
                data=data_dia,
                entradas=dados["entradas"],
                saidas=dados["saidas"],
                saldo=saldo,
                # Entrada antes de saída no mesmo dia: é a ordem em que o dono
                # lê ("entrou tanto, saiu tanto"), e o saldo do dia não depende
                # da ordem dentro dele.
                lancamentos=sorted(
                    dados["lancamentos"],
                    key=lambda item: (item.tipo != MovimentacaoFinanceiraTipo.ENTRADA.value,
                                      -item.valor),
                ),
            )
        )

    _p, _pg, atrasado_a_pagar = financeiro_crud.totais_contas_pagar(
        db, empresa_id, hoje=hoje
    )
    _r, _rc, atrasado_a_receber = financeiro_crud.totais_contas_receber(
        db, empresa_id, hoje=hoje
    )

    return FluxoCaixa(
        inicio=hoje,
        fim=fim,
        dias=dias,
        saldo_inicial=saldo_inicial,
        saldo_declarado=atual.declarado,
        # As duas metades do saldo, para a tela poder mostrar a conta em vez de
        # pedir fé num total: "declarou X no dia tal, e desde então moveu Y".
        saldo_ancora=atual.ancora,
        saldo_movimentado=atual.movimentado,
        saldo_entrou=atual.entrou,
        saldo_saiu=atual.saiu,
        saldo_informado_em=atual.informado_em,
        total_entradas=total_entradas,
        total_saidas=total_saidas,
        saldo_final=saldo,
        primeiro_dia_negativo=primeiro_negativo,
        menor_saldo=menor_saldo,
        menor_saldo_em=menor_saldo_em,
        atrasado_a_receber=atrasado_a_receber,
        atrasado_a_pagar=atrasado_a_pagar,
        previsto_compras=previsto_compras,
        linha=linha,
    )
