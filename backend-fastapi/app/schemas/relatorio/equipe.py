# ---------------------------------------------------------------------------
# ARQUIVO: schemas/relatorio/equipe.py
# DESCRICAO: Schemas de relatorio - ranking, comissao e extrato do funcionario.
# ---------------------------------------------------------------------------

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


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
