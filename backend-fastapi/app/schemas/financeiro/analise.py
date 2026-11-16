# ---------------------------------------------------------------------------
# ARQUIVO: schemas/financeiro/analise.py
# DESCRICAO: Financeiro - schemas da Analise (serie mensal e projecao).
# ---------------------------------------------------------------------------

from datetime import date
from typing import List
from pydantic import BaseModel, Field


# ===========================================================================
# SÉRIE MENSAL (Análise — Fase 1)
# ===========================================================================

class SerieOrigem(BaseModel):
    """De onde veio o dinheiro num mês.

    ORIGEM É DADO, NÃO CÓDIGO NA TELA. A lista chega pronta, com rótulo, e o
    frontend desenha o que vier — ele não pode conhecer "venda" nem "OS". Uma
    tela que soubesse disso teria um `v-if` por segmento, e a serigrafia, a
    marcenaria e o que vier depois quebrariam uma a uma.

    Origem nova (locação, assinatura) é uma declaração no backend, sem tocar em
    Vue.
    """

    chave: str = Field(..., description="Identificador técnico (VENDA, ORDEM_SERVICO)")
    rotulo: str = Field(..., description="Nome que o lojista lê, já no vocabulário dele")
    total: int = Field(..., description="Receita da origem no mês (centavos)")


class SerieMes(BaseModel):
    """Um mês FECHADO. O mês corrente nunca entra.

    Comparar oito dias com um mês inteiro acusaria queda todo início de mês --
    e é o erro mais fácil de reintroduzir sem perceber.
    """

    mes: str = Field(..., description="AAAA-MM")
    inicio: date
    fim: date

    receita: int = Field(..., description="Soma das origens (centavos), por competência")
    origens: List[SerieOrigem] = Field(default_factory=list)

    despesas_pagas: int = Field(
        ..., description="Contas pagas que são despesa — sem a compra de mercadoria"
    )
    custo_mercadorias: int = Field(
        0, description="CMV do mês (centavos): o custo do que foi vendido"
    )
    resultado: int = Field(
        ...,
        description=(
            "receita - custo_mercadorias - despesas_pagas (pode ser negativo). "
            "MESMA fórmula do resultado da Visão Geral, de propósito: a Análise "
            "existe para comparar meses, e uma série que somasse diferente do "
            "card faria o dono ver queda onde não houve"
        ),
    )
    entrou_caixa: int = Field(
        ..., description="O que passou pelo caixa no mês, pelo livro do dinheiro"
    )
    prazo_medio_recebimento: int | None = Field(
        None,
        description=(
            "Dias que o cliente levou para pagar, em média, nas cobranças "
            "recebidas no mês. NULL quando não houve recebimento -- e nulo não "
            "é zero: zero diria que todo mundo pagou à vista"
        ),
    )


class Serie(BaseModel):
    """A série mensal que sustenta a tela de Análise.

    `meses_disponiveis` é o número que abre e fecha os PORTÕES da tela: cada
    métrica declara quantos meses fechados exige, e abaixo disso não aparece
    torta nem vazia -- aparece dizendo o que falta. Dois pontos fazem qualquer
    reta, e um sistema que projeta doze meses a partir de dois está inventando.
    """

    meses_disponiveis: int = Field(
        ...,
        description=(
            "Meses FECHADOS de histórico, do primeiro mês com movimento até o "
            "último mês fechado. Zero = a loja começou neste mês"
        ),
    )
    primeiro_mes: str | None = Field(None, description="AAAA-MM do primeiro mês com movimento")
    meses: List[SerieMes] = Field(default_factory=list)


# ===========================================================================
# PROJEÇÃO DE 12 MESES (Análise — Fase 4)
# ===========================================================================

class ProjecaoMes(BaseModel):
    """Um mês futuro estimado. Nada aqui existe no banco."""

    mes: str
    receita: int
    despesa: int
    resultado: int
    acumulado: int = Field(..., description="Soma dos resultados até este mês")


class Projecao(BaseModel):
    """Onde o ritmo atual leva a loja em doze meses.

    É a leitura mais arriscada do módulo, e por isso a mais cercada:

    RETA, E NÃO TENDÊNCIA. A projeção repete a média dos últimos meses; ela NÃO
    extrapola a inclinação. Com seis pontos, uma reta de regressão erra feio e a
    tela passaria a prometer uma data ("em março você quebra") que o dado não
    sustenta. Se a média já é negativa, isso é dito -- e é uma afirmação sobre o
    presente, não uma adivinhação.

    FAIXA, NUNCA NÚMERO SECO. `piso` e `teto` são os dois cenários explicáveis:
    vender `margem` a menos gastando `margem` a mais, e o contrário.

    A MARGEM SAI DO PRÓPRIO HISTÓRICO (coeficiente de variação da receita): loja
    estável ganha faixa estreita, loja instável ganha faixa larga. E alarga mais
    ainda quando o histórico é curto -- é a forma honesta de dizer "sei menos".
    """

    disponivel: bool = Field(..., description="False enquanto faltar histórico")
    meses_faltando: int = Field(0, description="Quantos meses até a projeção existir")
    base_meses: int = Field(0, description="Quantos meses entraram na média")

    receita_mensal: int = 0
    despesa_mensal: int = 0
    resultado_mensal: int = 0

    receita_12_meses: int = 0
    despesa_12_meses: int = 0
    resultado_12_meses: int = 0

    margem: float = Field(0, description="0.30 = os cenários abrem 30% para cada lado")
    piso_12_meses: int = Field(0, description="Cenário ruim: vende menos e gasta mais")
    teto_12_meses: int = Field(0, description="Cenário bom")

    meses: List[ProjecaoMes] = Field(default_factory=list)
