from pydantic import BaseModel, Field, model_validator, ConfigDict
from datetime import datetime
from typing import Optional, Sequence

from app.core.enum import TipoProdutoVenda
from app.schemas.cargo import CargoBase


# --- Schemas para criacao de orcamento e produtos ---

class OrcamentoProdutoCreate(BaseModel):
    tipo_produto: TipoProdutoVenda = Field(..., description="Tipo do produto, obrigatorio")
    produto_id: Optional[int] = Field(None, description="ID do produto, obrigatorio se nao for avulso")
    quantidade: int = Field(0, gt=0, description="Quantidade do produto, obrigatorio")
    descricao_avulsa: Optional[str] = Field(None, max_length=100, description="Descricao do produto avulso")
    valor_unitario: Optional[int] = Field(None, ge=0, description="Valor unitario do produto")
    desconto: int = Field(0, ge=0, description="Desconto do produto")

    @model_validator(mode='after')
    def check_produto_references(self) -> 'OrcamentoProdutoCreate':
        if self.tipo_produto == TipoProdutoVenda.AVULSO:
            if self.produto_id is not None:
                raise ValueError("O campo 'produto_id' nao deve ser fornecido quando o tipo de produto e 'AVULSO'.")
            if self.descricao_avulsa is None:
                raise ValueError("O campo 'descricao_avulsa' e obrigatorio quando o tipo de produto e 'AVULSO'.")
            if self.valor_unitario is None:
                raise ValueError("O campo 'valor_unitario' e obrigatorio quando o tipo de produto e 'AVULSO'.")
            subtotal = (self.quantidade or 0) * (self.valor_unitario or 0) - (self.desconto or 0)
            if subtotal < 0:
                raise ValueError("O desconto nao pode ser maior que o valor total do produto.")
            return self

        if self.produto_id is None:
            raise ValueError("O campo 'produto_id' e obrigatorio quando o tipo de produto e 'CADASTRADO'.")
        if self.descricao_avulsa is not None:
            raise ValueError("O campo 'descricao_avulsa' deve ser nulo quando o tipo de produto e 'CADASTRADO'.")
        if self.valor_unitario is not None:
            raise ValueError("O campo 'valor_unitario' deve ser nulo quando o tipo de produto e 'CADASTRADO'.")
        return self


class OrcamentoCreate(BaseModel):
    funcionario_id: int = Field(..., description="ID do funcionario")


# --- Schemas para atualizacao ---

class OrcamentoProdutoUpdate(BaseModel):
    quantidade: Optional[int] = Field(None, gt=0, description="Quantidade do produto")
    descricao_avulsa: Optional[str] = Field(None, max_length=100, description="Descricao do produto avulso")
    valor_unitario: Optional[int] = Field(None, ge=0, description="Valor unitario do produto")
    desconto: Optional[int] = Field(None, ge=0, description="Desconto do produto")

    @model_validator(mode='after')
    def check_produto_references(self) -> 'OrcamentoProdutoUpdate':
        if self.valor_unitario and self.quantidade:
            subtotal = (self.quantidade or 0) * (self.valor_unitario or 0) - (self.desconto or 0)
            if subtotal < 0:
                raise ValueError("O desconto nao pode ser maior que o valor total do produto.")
        return self


class OrcamentoUpdate(BaseModel):
    funcionario_id: Optional[int] = Field(None, description="ID do funcionario")
    entrega: Optional[int] = Field(None, ge=0, description="Valor da entrega")
    desconto: Optional[int] = Field(None, ge=0, description="Desconto do orcamento")
    observacao: Optional[str] = Field(None, max_length=500, description="Observacao do orcamento")


# --- Schemas para leitura ---

class OrcamentoProdutoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID do produto no orcamento")
    tipo_produto: TipoProdutoVenda = Field(..., description="Tipo do produto")
    produto_id: Optional[int] = Field(None, description="ID do produto")
    sku: Optional[str] = Field(None, description="SKU do produto")
    nome: str = Field(..., description="Nome do produto")
    quantidade: int = Field(0, gt=0, description="Quantidade do produto")
    valor_unitario: int = Field(0, ge=0, description="Valor unitario do produto")
    desconto: int = Field(0, ge=0, description="Desconto do produto")
    subtotal: int = Field(0, ge=0, description="Subtotal do produto")
    total: int = Field(0, ge=0, description="Total do produto (subtotal - desconto)")
    imagem_url: Optional[str] = Field(None, description="URL da imagem do produto")


class FuncionarioOrcamentoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID do funcionario")
    nome: str = Field(..., description="Nome do funcionario")
    cargo: Optional[CargoBase] = Field(None, description="Cargo do funcionario")


class OrcamentoSimpleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID do orcamento (numero do orcamento)")
    funcionario_id: int = Field(..., description="ID do funcionario responsavel")
    total: int = Field(0, ge=0, description="Total do orcamento")
    convertido: bool = Field(False, description="Se foi convertido em venda")
    venda_id: Optional[int] = Field(None, description="ID da venda criada a partir deste orcamento")
    criado_em: datetime = Field(..., description="Data de criacao do orcamento")
    atualizado_em: datetime = Field(..., description="Data da ultima atualizacao do orcamento")
    funcionario: Optional[FuncionarioOrcamentoRead] = Field(None, description="Dados do funcionario responsavel")


class OrcamentoRead(OrcamentoSimpleRead):
    entrega: int = Field(0, ge=0, description="Valor da entrega")
    subtotal: int = Field(0, ge=0, description="Subtotal do orcamento")
    descontos: int = Field(0, ge=0, description="Total de descontos do orcamento")
    observacao: Optional[str] = Field(None, max_length=500, description="Observacao do orcamento")
    produtos: Optional[Sequence[OrcamentoProdutoRead]] = Field(default_factory=list, validation_alias="itens", description="Lista de produtos do orcamento")


class OrcamentoFinanceSummary(BaseModel):
    subtotal: int = Field(0, ge=0, description="Subtotal atualizado do orcamento")
    descontos: int = Field(0, ge=0, description="Descontos atualizados do orcamento")
    entrega: int = Field(0, ge=0, description="Valor da entrega atualizado")
    total: int = Field(0, ge=0, description="Total atualizado do orcamento")


class OrcamentoProdutosAlterSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    produto_adicionado: OrcamentoProdutoRead
    financeiro_atualizado: OrcamentoFinanceSummary


class OrcamentoStatusSummary(BaseModel):
    orcamentos_ativos: int = Field(0, ge=0, description="Quantidade de orcamentos ativos")
    orcamentos_convertidos: int = Field(0, ge=0, description="Quantidade de orcamentos convertidos")


class ConverterOrcamentoPayload(BaseModel):
    cliente_id: int = Field(..., description="ID do cliente para a venda")


class OrcamentoSearchFilters(BaseModel):
    search: Optional[str] = Field(None, max_length=255, description="Termo de busca")
    convertido: Optional[bool] = Field(None, description="Filtrar por status de conversao")
    funcionario_id: Optional[int] = Field(None, description="Filtrar por funcionario")


class OrcamentoListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    filters: OrcamentoSearchFilters = Field(..., description="Filtros aplicados")
    orcamentos: Sequence[OrcamentoSimpleRead] = Field(default_factory=list, description="Lista de orcamentos")
    total: int = Field(0, ge=0, description="Total de orcamentos encontrados")
    page: int = Field(1, ge=1, description="Pagina atual")
    limit: int = Field(20, ge=1, le=100, description="Limite por pagina")
    total_pages: int = Field(1, ge=1, description="Total de paginas")
    links: dict = Field(..., description="Links de navegacao")
