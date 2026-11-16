# ---------------------------------------------------------------------------
# ARQUIVO: schemas/financeiro/resumo.py
# DESCRICAO: Financeiro - schemas da Visao Geral (resumo, despesas, alertas).
# ---------------------------------------------------------------------------

from datetime import date
from typing import List
from pydantic import BaseModel, Field
from app.schemas.financeiro.conta_pagar import ContaPagarRead


class DespesaPorCategoria(BaseModel):
    """Quanto saiu em cada categoria, no período."""

    plano_conta_id: int | None = Field(None, description="NULL agrupa as contas sem categoria")
    nome: str = Field(..., description="Nome da categoria, ou 'Sem categoria'")
    total: int = Field(..., description="Soma do que foi PAGO na categoria (centavos)")


class AlertaFinanceiro(BaseModel):
    """Um ponto que precisa de atenção — SEM TEXTO, de propósito.

    O backend diz o QUE aconteceu (código + números); quem escreve a frase é a
    tela. Mandar texto pronto daqui congelaria o idioma, o rótulo por segmento
    ("cliente" vs "paciente") e a redação numa camada que não vê a tela.

    A regra para entrar nesta lista: precisa ter AÇÃO POSSÍVEL e um lugar para
    onde ir. Alerta que só informa vira ruído, e um painel que grita todo dia
    deixa de ser lido -- e aí some junto o alerta que importava.
    """

    codigo: str = Field(
        ...,
        description=(
            "CAIXA_NEGATIVO, CONTAS_VENCIDAS, FIADO_ATRASADO, MES_NO_VERMELHO, "
            "SALDO_NUNCA_INFORMADO, SALDO_DESATUALIZADO, DESPESA_SEM_CATEGORIA"
        ),
    )
    severidade: str = Field(..., description="CRITICO ou ATENCAO")
    valor: int | None = Field(None, description="Quanto (centavos), quando faz sentido")
    data: date | None = Field(None, description="Quando, quando faz sentido")
    quantidade: int | None = Field(None, description="Contagem (dias, itens)")
    rotulo: str | None = Field(
        None,
        description=(
            "Nome de uma origem, quando o alerta fala de uma. É DADO, não frase: "
            "a tela escreve 'X% veio de {rotulo}' — o backend continua sem "
            "mandar texto pronto"
        ),
    )


class ResumoFinanceiro(BaseModel):
    """O mês em dois blocos: o LUCRO e o CAIXA. Não é DRE.

    O nome importa: DRE é peça contábil de regime de competência, e um contador
    que comparasse os dois números acharia diferença legítima e abriria chamado.
    Mas as duas perguntas do dono são diferentes e as duas precisam de resposta,
    e por isso são dois blocos e não um número só:

      LUCRO   faturamento - custo das mercadorias - despesas pagas.
              Responde "eu ganhei dinheiro este mês?".
      CAIXA   entrou_caixa - saiu_caixa.
              Responde "sobrou dinheiro na gaveta este mês?".

    Eles divergem por motivo legítimo -- a venda fiado de hoje está no lucro e
    não no caixa; o boleto de estoque pago hoje está no caixa e não no lucro --
    e é exatamente por isso que mostrar só um deles não serve.

    O CUSTO PASSOU A ENTRAR EM 02/09/2026. Antes, `resultado` era faturamento
    menos despesa paga, e um serviço de R$ 160 com peça de R$ 60 comprada na
    hora aparecia como R$ 160 de lucro. A objeção de então era a dupla contagem
    (a compra do fornecedor já estaria em `despesas_pagas`), e ela foi resolvida
    na origem: compra de mercadoria é categoria de tipo CUSTO no plano de contas
    e sai do lucro -- ver PlanoContaTipo.
    """

    periodo_inicio: date
    periodo_fim: date

    faturamento: int = Field(
        ...,
        description=(
            "Vendas + OS finalizadas no período (centavos), JÁ SEM o juros de "
            "parcelamento repassado ao cliente: esse pedaço é retido pela "
            "operadora do cartão e nunca chega na loja. Difere do "
            "`faturamento_total` do Relatório de faturamento, que é o BRUTO "
            "(o que o cliente desembolsou) e traz o juros em linha própria; "
            "aqui a pergunta é só uma -- quanto virou dinheiro da loja"
        ),
    )
    entrou_caixa: int = Field(
        ...,
        description=(
            "O que de fato PASSOU PELO CAIXA no período (centavos): venda, OS e "
            "recebimento pelo livro do dinheiro, já descontados os estornos. "
            "Leitura diferente de `faturamento`, não um pedaço dele -- aqui "
            "entra o fiado do mês passado que foi quitado agora, e não entra a "
            "venda fechada que ainda não foi paga. O livro só passou a receber "
            "venda e OS sem caixa aberto em 29/08/2026; antes disso ele é "
            "incompleto, e por isso este número NÃO substitui o faturamento"
        ),
    )
    saiu_caixa: int = Field(
        0,
        description=(
            "O que de fato SAIU do caixa no período (centavos), pelo livro, já "
            "descontados os estornos. Inclui a compra de mercadoria, que é "
            "dinheiro saindo mesmo não sendo despesa"
        ),
    )
    sobrou_caixa: int = Field(
        0,
        description=(
            "entrou_caixa - saiu_caixa (centavos). A pergunta da gaveta, não a "
            "do lucro: pode ser negativo num mês de boa venda fiado"
        ),
    )

    despesas_pagas: int = Field(
        ...,
        description=(
            "Contas pagas no período que SÃO despesa (centavos) — tudo menos "
            "compra de mercadoria. Conta sem categoria entra aqui, que é o lado "
            "seguro do erro"
        ),
    )
    compras_estoque: int = Field(
        0,
        description=(
            "Contas pagas no período em categoria de tipo CUSTO (centavos): "
            "dinheiro que virou estoque. Sai do caixa, não sai do lucro"
        ),
    )
    custo_mercadorias: int = Field(
        0,
        description=(
            "CMV do período (centavos): o que custou à loja aquilo que ela "
            "vendeu. Custo congelado no livro de estoque, mais o custo declarado "
            "à mão na OS e no item avulso da venda"
        ),
    )
    custo_sem_registro: int = Field(
        0,
        description=(
            "Quantas saídas de estoque não tinham custo conhecido. Não é "
            "dinheiro: é a medida da confiança do CMV, e a tela avisa quando "
            "não é zero — um custo subestimado em silêncio vira lucro inventado"
        ),
    )
    lucro_bruto: int = Field(
        0, description="faturamento - custo_mercadorias (centavos)"
    )
    resultado: int = Field(
        ...,
        description=(
            "O LUCRO: faturamento - custo_mercadorias - despesas_pagas "
            "(centavos). Pode ser negativo"
        ),
    )

    a_pagar_pendente: int = Field(
        ...,
        description=(
            "Em aberto com vencimento ATÉ o fim do período (centavos). Inclui o "
            "atrasado de meses anteriores, que continua devido; exclui o que só "
            "vence depois — senão o card somaria outubro na visão de agosto."
        ),
    )
    a_pagar_vencido: int = Field(
        ..., description="Parte do pendente que já passou do vencimento (centavos)"
    )

    a_receber_pendente: int = Field(
        ...,
        description=(
            "TODA cobrança em aberto, de qualquer vencimento (centavos) — a única "
            "coisa nesta tela que não respeita o mês visto, e de propósito. O teto "
            "do a pagar existe por causa da recorrência, que não existe aqui; e "
            "fiado quase sempre vence no mês seguinte, então com teto o card "
            "mostraria zero justamente quando importa (a Visão Geral nem deixa "
            "avançar de mês). É dinheiro já contado em `faturamento` que ainda não "
            "passou pelo caixa — por isso não entra no resultado."
        ),
    )
    a_receber_vencido: int = Field(
        ..., description="Parte do a receber que já passou do vencimento (centavos)"
    )

    despesas_por_categoria: List[DespesaPorCategoria] = Field(
        default_factory=list, description="Onde o dinheiro foi, no período"
    )
    proximas_a_vencer: List[ContaPagarRead] = Field(
        default_factory=list,
        description="Contas pendentes vencendo nos próximos dias, das mais urgentes",
    )
    alertas: List[AlertaFinanceiro] = Field(
        default_factory=list,
        description="O que precisa de atenção, mais grave primeiro. Vazio é bom sinal",
    )
