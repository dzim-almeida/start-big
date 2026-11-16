# ---------------------------------------------------------------------------
# ARQUIVO: schemas/financeiro/fluxo_caixa.py
# DESCRICAO: Financeiro - schemas do fluxo de caixa.
# ---------------------------------------------------------------------------

from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


# ===========================================================================
# FLUXO DE CAIXA (Onda 3)
# ===========================================================================

class FluxoLancamento(BaseModel):
    """Um documento previsto para um dia. Não é movimento: nada disso andou."""

    conta_id: int
    tipo: str = Field(..., description="ENTRADA (a receber) ou SAIDA (a pagar)")
    descricao: str
    valor: int = Field(..., description="Sempre positivo (centavos); o sinal é o `tipo`")
    recorrente: bool = Field(
        False,
        description=(
            "A conta se repete todo mês. A tela marca porque a próxima "
            "ocorrência nasce da BAIXA da anterior: quem paga a internet de "
            "setembro vê a de outubro aparecer aqui na mesma hora, e sem a "
            "marca isso se lê como 'o pagamento não foi registrado'"
        ),
    )
    # Módulo Compras: parcela PREVISTA de um pedido enviado (ainda não é conta;
    # vira conta no recebimento). `conta_id` vem 0 nestas linhas.
    previsao_compra: bool = False
    pedido_compra_id: Optional[int] = None


class FluxoDia(BaseModel):
    """Um dia com movimento previsto.

    Dias vazios NÃO entram na lista: sessenta linhas de zero escondem as cinco
    que importam. Quem desenha a régua do tempo é a tela.
    """

    data: date
    entradas: int
    saidas: int
    saldo: int = Field(..., description="Saldo previsto ao FIM do dia (centavos)")
    lancamentos: List[FluxoLancamento] = Field(default_factory=list)


class FluxoCaixa(BaseModel):
    """A projeção dos próximos N dias, a partir do saldo DECLARADO pelo dono.

    NÃO é o extrato do que aconteceu — é o que está agendado para acontecer.
    Cada linha nasce de um documento em aberto (conta a pagar ou a receber) na
    data do vencimento, e a régua acumula o saldo dia a dia.

    O saldo de partida é o de HOJE: a âncora que o dono declarou mais tudo que o
    livro registrou depois dela (ver `financeiro_visao.saldo_atual_das_contas`).
    Enquanto ninguém declarar a âncora, a projeção sai com
    `saldo_declarado=False` e a tela pede o número antes de desenhar — uma linha
    que parte de zero fingindo ser saldo é pior que nenhuma linha.

    O ATRASADO fica FORA da régua, num balde só dele. Conta vencida não tem
    data futura para ocupar, e empurrá-la para hoje inventaria um dia de aperto
    que talvez nunca aconteça (o fiado atrasado pode nunca chegar). Ela aparece
    como aviso, para o dono decidir o que fazer com ela.
    """

    inicio: date
    fim: date
    dias: int

    saldo_inicial: int = Field(
        ...,
        description=(
            "O saldo de HOJE nas contas ativas (centavos): a âncora declarada "
            "mais tudo que o livro moveu depois dela. Era a âncora pura até "
            "02/09/2026, e por isso não andava com as vendas"
        ),
    )
    saldo_ancora: int = Field(
        0, description="A parte DECLARADA do saldo (centavos)"
    )
    saldo_movimentado: int = Field(
        0,
        description=(
            "O que o livro moveu desde a declaração (centavos, com sinal). "
            "Mostrado ao lado da âncora para o dono poder conferir a conta em "
            "vez de acreditar num total"
        ),
    )
    saldo_entrou: int = Field(
        0,
        description=(
            "As entradas do livro desde a declaração (centavos, positivo). "
            "Separado do líquido porque zero líquido pode ser 'nada aconteceu' "
            "ou 'entraram 500 e saíram 500'"
        ),
    )
    saldo_saiu: int = Field(
        0, description="As saídas do livro desde a declaração (centavos, positivo)"
    )
    saldo_declarado: bool = Field(
        ..., description="Se alguma conta já teve saldo informado alguma vez"
    )
    saldo_informado_em: date | None = Field(
        None,
        description=(
            "A data MAIS ANTIGA entre as contas com saldo declarado — é a que "
            "envelhece o número, e por isso é ela que a tela mostra"
        ),
    )

    total_entradas: int
    total_saidas: int
    saldo_final: int = Field(..., description="Saldo previsto no último dia do período")

    primeiro_dia_negativo: date | None = Field(
        None, description="O dia em que o dinheiro acaba, se acabar no período"
    )
    menor_saldo: int = Field(..., description="O fundo do poço previsto (centavos)")
    menor_saldo_em: date | None = None

    atrasado_a_receber: int = Field(
        ..., description="Vencido e não recebido, fora da régua (centavos)"
    )
    atrasado_a_pagar: int = Field(
        ..., description="Vencido e não pago, fora da régua (centavos)"
    )
    previsto_compras: int = Field(
        0, description="Parcelas PREVISTAS de pedidos de compra em aberto, já dentro da régua (módulo Compras)"
    )

    linha: List[FluxoDia] = Field(
        default_factory=list, description="Só os dias com movimento previsto"
    )
