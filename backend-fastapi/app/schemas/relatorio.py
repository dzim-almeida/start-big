# ---------------------------------------------------------------------------
# ARQUIVO: schemas/relatorio.py
# DESCRICAO: Schemas de resposta do modulo de Relatorios.
#            Todos os valores monetarios sao INTEIROS EM CENTAVOS.
# ---------------------------------------------------------------------------

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class FaturamentoDiaItem(BaseModel):
    """Faturamento consolidado de um dia (vendas + OS)."""
    dia: date
    total_vendas: int = Field(..., description="Faturamento de vendas no dia (centavos)")
    total_os: int = Field(..., description="Faturamento de OS no dia (centavos)")
    total_geral: int = Field(..., description="Soma vendas + OS no dia (centavos)")


class FormaPagamentoResumo(BaseModel):
    """Total recebido por forma de pagamento no periodo."""
    nome: str
    valor_total: int = Field(..., description="Total recebido nesta forma (centavos)")


class RelatorioFaturamento(BaseModel):
    """Resposta do relatorio de faturamento por periodo."""
    inicio: date
    fim: date
    faturamento_total: int = Field(..., description="Bruto: vendas + OS finalizadas no periodo (centavos)")
    faturamento_vendas: int = Field(..., description="Somente vendas (centavos)")
    faturamento_os: int = Field(..., description="Somente OS (centavos)")
    juros_repassado: int = Field(
        0,
        description="Juros cobrado do cliente. Já está dentro do faturamento_total, "
                    "mas fica com a operadora — por isso sai do líquido (centavos)",
    )
    juros_absorvido: int = Field(
        0,
        description="Juros que a loja bancou. NÃO está no faturamento_total (o cliente "
                    "não foi cobrado), e mesmo assim reduz o líquido (centavos)",
    )
    faturamento_liquido: int = Field(
        0,
        description="faturamento_total − juros_repassado − juros_absorvido. É o que "
                    "efetivamente sobra para a loja (centavos)",
    )
    cmv: int = Field(
        0,
        description="Custo da mercadoria vendida: Σ do custo congelado das pecas que "
                    "sairam por venda e OS no periodo, menos os estornos (centavos)",
    )
    lucro_bruto: int = Field(
        0,
        description="faturamento_liquido − cmv. E o que sobra depois do custo das pecas "
                    "e do juros de cartao. Nao desconta despesa fixa (centavos)",
    )
    margem_percentual: float = Field(
        0.0,
        description="lucro_bruto ÷ faturamento_total × 100. Zero quando nao houve faturamento",
    )
    saidas_sem_custo: int = Field(
        0,
        description="Movimentacoes do periodo sem custo apurado (anteriores ao registro de "
                    "custo). Enquanto for > 0 o lucro esta SUBESTIMADO e a tela avisa",
    )
    ticket_medio: int = Field(..., description="Faturamento / nº de transacoes finalizadas (centavos)")
    qtd_vendas: int = Field(..., description="Quantidade de vendas finalizadas")
    qtd_os: int = Field(..., description="Quantidade de OS finalizadas")
    por_dia: list[FaturamentoDiaItem] = Field(default_factory=list)
    formas_pagamento: list[FormaPagamentoResumo] = Field(default_factory=list)


class RankingFuncionarioItem(BaseModel):
    """Faturamento de um funcionario no periodo (base da comissao)."""
    funcionario_id: int
    nome: str
    faturamento_vendas: int = Field(..., description="Vendas finalizadas do funcionario (centavos)")
    faturamento_os: int = Field(..., description="OS finalizadas do funcionario (centavos)")
    faturamento_total: int = Field(..., description="Vendas + OS (centavos)")
    qtd_vendas: int
    qtd_os: int


class RelatorioRanking(BaseModel):
    """Ranking de funcionarios por faturamento no periodo."""
    inicio: date
    fim: date
    itens: list[RankingFuncionarioItem] = Field(default_factory=list)


class ComissaoFuncionarioItem(BaseModel):
    """Comissao apurada de um funcionario no periodo."""
    funcionario_id: int
    nome: str
    faturamento_vendas: int = Field(..., description="Base de vendas (centavos)")
    faturamento_os: int = Field(..., description="Base de OS (centavos)")
    faturamento_total: int
    percentual_venda: Optional[int] = Field(None, description="Taxa aplicada em vendas (basis points); None = sem taxa")
    percentual_servico: Optional[int] = Field(None, description="Taxa aplicada em serviços (basis points)")
    comissao_vendas: int = Field(..., description="Comissao de vendas (centavos)")
    comissao_servico: int = Field(..., description="Comissao de serviços (centavos)")
    comissao_total: int = Field(..., description="Comissao total a pagar (centavos)")
    meta_mensal: Optional[int] = Field(None, description="Meta do funcionario/cargo (centavos)")
    meta_atingida_percentual: Optional[float] = Field(None, description="% da meta atingido no período")
    comissao_modo: str = Field("direto", description="Modo aplicado: 'direto' | 'meta' (gatilho por meta)")
    comissao_liberada: bool = Field(True, description="False quando o modo 'meta' travou a comissao por nao bater a meta")


class RelatorioComissao(BaseModel):
    """Relatorio de comissao por funcionario no periodo."""
    inicio: date
    fim: date
    total_comissao: int = Field(..., description="Soma das comissões — total a pagar (centavos)")
    itens: list[ComissaoFuncionarioItem] = Field(default_factory=list)


# ===========================================================================
# RELATORIO DE ESTOQUE / CURVA ABC (Fase 4a)
# ===========================================================================

class EstoqueAbcItem(BaseModel):
    """Produto na Curva ABC (classificado por faturamento no período)."""
    produto_id: int
    nome: str
    sku: Optional[str] = Field(None, description="Codigo do produto (SKU)")
    categoria: Optional[str] = None
    faturamento: int = Field(..., description="Receita líquida gerada no período (centavos)")
    quantidade: int = Field(..., description="Unidades vendidas no período")
    participacao_pct: float = Field(..., description="% do faturamento total do período")
    acumulado_pct: float = Field(..., description="% acumulado (base da classificação ABC)")
    classe: str = Field(..., description="Classe ABC: 'A' | 'B' | 'C'")


class EstoqueReposicaoItem(BaseModel):
    """Produto abaixo do mínimo — alerta de reposição."""
    produto_id: int
    nome: str
    sku: Optional[str] = None
    quantidade: int = Field(..., description="Quantidade atual em estoque")
    quantidade_minima: Optional[int] = Field(None, description="Mínimo configurado")
    quantidade_ideal: Optional[int] = Field(None, description="Quantidade ideal configurada")


class EstoqueParadoItem(BaseModel):
    """Produto ativo com estoque e SEM vendas no período (encalhado)."""
    produto_id: int
    nome: str
    sku: Optional[str] = None
    quantidade: int = Field(..., description="Quantidade parada em estoque")
    valor_custo: int = Field(..., description="Capital imobilizado a custo (quantidade × custo, centavos)")


class RelatorioEstoque(BaseModel):
    """Relatorio de estoque: KPIs + Curva ABC + reposição + parados."""
    inicio: date
    fim: date
    # KPIs de valor imobilizado (posição atual — não depende do período)
    valor_custo_total: int = Field(..., description="Σ quantidade × custo de todos os produtos ativos (centavos)")
    valor_venda_total: int = Field(..., description="Σ quantidade × preço de varejo (centavos)")
    skus_ativos: int = Field(..., description="Produtos ativos cadastrados")
    itens_abaixo_minimo: int = Field(..., description="Quantos produtos estão abaixo do mínimo")
    itens_parados: int = Field(..., description="Quantos produtos ativos não venderam no período")
    curva_abc: list[EstoqueAbcItem] = Field(default_factory=list)
    abaixo_minimo: list[EstoqueReposicaoItem] = Field(default_factory=list)
    parados: list[EstoqueParadoItem] = Field(default_factory=list)



# ===========================================================================
# VENDAS POR REGRA DE PREÇO (plano de embalagens, fase 6)
# ===========================================================================

class RegraPrecoResumo(BaseModel):
    """Total de uma regra (R1, R2 ou R3) no período."""
    regra: str = Field(..., description="R1, R2 ou R3")
    qtd_vendas: int = Field(..., description="Vendas finalizadas com esta regra em alguma linha")
    unidades: int = Field(..., description="Unidades vendidas com a regra (na unidade base)")
    faturamento: int = Field(..., description="O que entrou nessas linhas (centavos)")
    abatimento: int = Field(..., description="O que a regra deixou de cobrar (centavos)")


class RegraPrecoProdutoItem(BaseModel):
    """Um produto vendido com uma regra no período."""
    regra: str
    produto_id: int
    nome: str
    sku: Optional[str] = None
    qtd_vendas: int
    unidades: int
    faturamento: int = Field(..., description="Centavos")
    abatimento: int = Field(..., description="Centavos")


class RelatorioRegrasPreco(BaseModel):
    """Vendas com regra de preço por quantidade: quanto venderam e quanto abateram."""
    inicio: date
    fim: date
    qtd_vendas: int = Field(0, description="Vendas com ao menos uma linha com regra (sem contar duas vezes)")
    faturamento: int = Field(0, description="Σ faturamento das linhas com regra (centavos)")
    abatimento: int = Field(0, description="Σ do que as regras deixaram de cobrar (centavos)")
    por_regra: list[RegraPrecoResumo] = Field(default_factory=list)
    por_produto: list[RegraPrecoProdutoItem] = Field(default_factory=list)


# ===========================================================================
# RECEITA PARA O CONTADOR (segregação do PGDAS-D)
# ===========================================================================

class ReceitaGrupoItem(BaseModel):
    """Receita de mercadoria de um grupo do PGDAS-D."""
    icms_st: bool = Field(..., description="ICMS já pago por substituição tributária (CSOSN 500 / CST 60)")
    monofasico: bool = Field(..., description="PIS/COFINS monofásico (CST 04)")
    valor: int = Field(..., description="Centavos")


class ProdutoSemClassificacaoItem(BaseModel):
    """Produto vendido no período cujo cadastro não diz se o ICMS é ST."""
    produto_id: Optional[int] = None
    nome: str
    valor: int = Field(..., description="Receita do período (centavos)")
    motivo: str


class RelatorioContador(BaseModel):
    """Receita do período separada como o contador declara no PGDAS-D."""
    inicio: date
    fim: date
    crt: Optional[int] = Field(None, description="Regime da empresa: 1 Simples, 2 excesso de sublimite, 3 normal, 4 MEI")
    receita_total: int = Field(0, description="Bate com o faturamento bruto (vendas + OS)")
    mercadoria: list[ReceitaGrupoItem] = Field(default_factory=list)
    mercadoria_sem_classificacao: int = 0
    servicos: int = Field(0, description="Itens de serviço das OS")
    frete_e_juros: int = Field(0, description="Frete/taxa de entrega e juros de cartão cobrados do cliente")
    faturamento_vendas: int = 0
    faturamento_os: int = 0
    produtos_sem_classificacao: list[ProdutoSemClassificacaoItem] = Field(default_factory=list)

# ===========================================================================
# RELATORIO DE OS-PERFORMANCE (Fase 4b)
# ===========================================================================

class OSReparoResumo(BaseModel):
    """Desfecho das OS finalizadas no período (situacao_equipamento)."""
    reparado: int = 0
    sem_reparo: int = 0
    condenado: int = 0
    nao_informado: int = Field(0, description="Finalizadas sem situação registrada")
    taxa_reparo_pct: float = Field(0.0, description="% REPARADO sobre as finalizadas")


class OSStatusItem(BaseModel):
    """Quantidade de OS ativas por status atual (snapshot do backlog)."""
    status: str
    quantidade: int


class OSTecnicoItem(BaseModel):
    """Desempenho de um técnico (funcionário) nas OS finalizadas do período."""
    funcionario_id: int
    nome: str
    finalizadas: int
    tempo_medio_horas: Optional[float] = Field(None, description="Média de (finalização - criação) em horas")
    faturamento: int = Field(..., description="Σ valor_total das OS finalizadas (centavos)")


class ExtratoServicoItem(BaseModel):
    """Um servico executado, na OS em que foi executado."""
    numero_os: str
    data_finalizacao: date
    objeto: Optional[str] = Field(None, description="Marca modelo · identificador, como a OS mostra")
    cliente: Optional[str] = Field(None, description="Nome do cliente, ou nulo se a OS nao tiver")
    servico: str
    quantidade: float
    valor_total: int = Field(..., description="Valor do item (centavos)")
    custo: int = Field(
        0,
        description=(
            "Custo da peça embutida no preço deste serviço (centavos). Interno "
            "— nunca sai na via do cliente, só no extrato de quem executou"
        ),
    )
    mao_de_obra: int = Field(
        0,
        description=(
            "valor_total − custo (centavos). É a base da comissão de serviço; "
            "o extrato mostra este número para o técnico conferir o próprio "
            "pagamento"
        ),
    )
    comissao: int = Field(0, description="Parte da comissão de serviço que cabe a esta linha (centavos)")


class ExtratoVendaItem(BaseModel):
    """Uma venda finalizada do funcionário, com a base da comissão dela."""
    venda_id: int
    numero: str
    data: date
    cliente: Optional[str] = None
    valor_total: int = Field(..., description="Total da venda (centavos)")
    base: int = Field(
        ...,
        description=(
            "Margem da venda: total − juros da operadora − custo das mercadorias "
            "(centavos). Pode ser negativa (venda abaixo do custo)"
        ),
    )
    comissao: int = Field(0, description="Parte da comissão de venda que cabe a esta venda (centavos)")


class RelatorioExtratoFuncionario(BaseModel):
    """O que uma pessoa executou no periodo -- o papel que ela leva para conferir."""
    inicio: date
    fim: date
    funcionario_id: int
    funcionario_nome: str
    qtd_os: int = Field(..., description="OS DISTINTAS, nao linhas: tres servicos numa OS contam 1")
    qtd_servicos: int
    valor_total: int = Field(..., description="Soma dos servicos (centavos)")
    total_mao_de_obra: int = Field(
        0,
        description=(
            "Soma da mão de obra — `valor_total` menos o custo das peças "
            "embutidas (centavos). É a BASE DA COMISSÃO de serviço. Quando não "
            "há peça embutida ele é igual ao `valor_total`"
        ),
    )
    itens: list[ExtratoServicoItem] = Field(default_factory=list)

    # --- Vendas e comissão (extrato de comissão, 01/10/2026) ---------------
    # A comissão é a MESMA da folha (`get_comissao`): o total vem de lá e é
    # repartido pelas linhas, para a soma do papel bater com a folha.
    qtd_vendas: int = 0
    total_vendas: int = Field(0, description="Σ total das vendas (centavos)")
    vendas: list[ExtratoVendaItem] = Field(default_factory=list)
    base_vendas: int = Field(0, description="Margem das vendas usada na folha (piso em zero)")
    base_servicos: int = Field(0, description="Mão de obra usada na folha (piso em zero)")
    percentual_venda: Optional[int] = Field(None, description="Basis points (500 = 5,00%)")
    percentual_servico: Optional[int] = Field(None, description="Basis points")
    comissao_vendas: int = 0
    comissao_servico: int = 0
    comissao_total: int = 0
    comissao_modo: str = "direto"
    meta_mensal: Optional[int] = None
    meta_atingida_percentual: Optional[float] = None
    comissao_liberada: bool = True


class RelatorioOSPerformance(BaseModel):
    """Desempenho de OS no período: throughput, tempo, reparo e por técnico."""
    inicio: date
    fim: date
    abertas: int = Field(..., description="OS criadas no período")
    finalizadas: int = Field(..., description="OS finalizadas no período")
    tempo_medio_horas: Optional[float] = Field(None, description="Tempo médio de conclusão (horas); None se não há finalizadas")
    faturamento_total: int = Field(..., description="Σ valor_total das OS finalizadas no período (centavos)")
    reparo: OSReparoResumo
    por_status: list[OSStatusItem] = Field(default_factory=list)
    por_tecnico: list[OSTecnicoItem] = Field(default_factory=list)
