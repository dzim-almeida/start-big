from pydantic import BaseModel, Field, model_validator, ConfigDict
from app.core.enum import VendaStatus
from datetime import datetime
from typing import Optional, Sequence

from app.core.enum import TipoProdutoVenda

# Schemas para criação de venda, produtos e pagamentos relacionados a uma venda

class ProdutoVendaCreate(BaseModel):
    tipo_produto: TipoProdutoVenda = Field(..., description="Tipo do produto, obrigatório")
    produto_id: Optional[int] = Field(None, description="ID do produto, obrigatório se não for uma descrição avulsa")
    quantidade: int = Field(0, gt=0, description="Quantidade do produto, obrigatório")
    descricao_avulsa: Optional[str] = Field(None, max_length=100, description="Descrição do produto avulso, obrigatório se não for um produto cadastrado")
    valor_unitario: int = Field(0, ge=0, description="Valor unitário do produto, obrigatório")
    desconto: int = Field(0, ge=0, description="Desconto do produto, obrigatório")

    @model_validator(mode='after')
    def check_produto_references(self) -> 'ProdutoVendaCreate':
        subtotal = (self.quantidade or 0) * (self.valor_unitario or 0) - (self.desconto or 0)
        if subtotal < 0:
            raise ValueError("O desconto não pode ser maior que o valor total do produto.")
        if self.tipo_produto == TipoProdutoVenda.CADASTRADO and self.produto_id is None:
            raise ValueError("O campo 'produto_id' é obrigatório quando o tipo de produto é 'CADASTRADO'.")
        if self.tipo_produto == TipoProdutoVenda.AVULSO and self.descricao_avulsa is None:
            raise ValueError("O campo 'descricao_avulsa' é obrigatório quando o tipo de produto é 'AVULSO'.")
        if self.tipo_produto == TipoProdutoVenda.AVULSO and self.produto_id is not None:
            raise ValueError("O campo 'produto_id' não deve ser fornecido quando o tipo de produto é 'AVULSO'.")
        return self
        

class PagamentoVendaCreate(BaseModel):
    forma_pagamento_id: int = Field(..., description="ID da forma de pagamento, obrigatório")
    parcelado: Optional[bool] = Field(False, description="Indica se o pagamento é parcelado")
    qtd_parcelas: Optional[int] = Field(1, gt=0, description="Quantidade de parcelas")
    valor: int = Field(..., ge=0, description="Valor do pagamento, obrigatório")

    @model_validator(mode='after')
    def check_pagamento_fields(self) -> 'PagamentoVendaCreate':
        if self.parcelado:
            if self.qtd_parcelas is None:
                raise ValueError("O campo 'qtd_parcelas' é obrigatório quando o pagamento é parcelado.")
        return self

class VendaCreate(BaseModel):
    cliente_id: Optional[int] = Field(None, description="ID do cliente")
    funcionario_id: int = Field(..., description="ID do funcionário")

# Schemas para atualização de venda, produtos e pagamentos relacionados a uma venda

class ProdutoVendaUpdate(BaseModel):
    quantidade: Optional[int] = Field(None, gt=0, description="Quantidade do produto")
    descricao_avulsa: Optional[str] = Field(None, max_length=100, description="Descrição do produto avulso")
    valor_unitario: Optional[int] = Field(None, ge=0, description="Valor unitário do produto")
    desconto: Optional[int] = Field(None, ge=0, description="Desconto do produto")

    @model_validator(mode='after')
    def check_produto_references(self) -> 'ProdutoVendaUpdate':
        if self.descricao_avulsa is not None and self.valor_unitario is None:
            raise ValueError("O campo 'valor_unitario' é obrigatório quando 'descricao_avulsa' é fornecida.")
        subtotal = (self.quantidade or 0) * (self.valor_unitario or 0) - (self.desconto or 0)
        if subtotal < 0:
            raise ValueError("O desconto não pode ser maior que o valor total do produto.")
        return self

class VendaUpdate(BaseModel):
    cliente_id: Optional[int] = Field(None, description="ID do cliente")
    funcionario_id: Optional[int] = Field(None, description="ID do funcionário")
    entrega: Optional[int] = Field(None, ge=0, description="Valor da entrega")
    adiantamento: Optional[int] = Field(None, ge=0, description="Valor do adiantamento")
    desconto: Optional[int] = Field(None, ge=0, description="Desconto da venda")
    observacao: Optional[str] = Field(None, max_length=500, description="Observação da venda")
    
# Schemas para leitura de venda, produtos e pagamentos relacionados a uma venda

class ProdutoVendaRead(ProdutoVendaCreate):
    id: int = Field(..., description="ID do produto na venda")
    subtotal: int = Field(0, ge=0, description="Subtotal do produto (quantidade * valor_unitario - desconto)")

class PagamentoVendaRead(PagamentoVendaCreate):
    id: int = Field(..., description="ID do pagamento na venda")
    data_pagamento: datetime = Field(..., description="Data do pagamento no formato ISO 8601")

class VendaRead(VendaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID da venda")

    sessao_caixa_id: Optional[int] = Field(None, description="ID da sessão de caixa associada à venda")

    entrega: int = Field(0, ge=0, description="Valor da entrega")
    subtotal: int = Field(0, ge=0, description="Subtotal da venda")
    desconto: int = Field(0, ge=0, description="Desconto da venda")
    adiantamento: int = Field(0, ge=0, description="Valor do adiantamento")
    total: int = Field(0, ge=0, description="Total da venda")

    status: VendaStatus = Field(..., description="Status da venda")
    observacao: Optional[str] = Field(None, max_length=500, description="Observação da venda")
    criado_em: datetime = Field(..., description="Data de criação da venda no formato ISO 8601")
    atualizado_em: datetime = Field(..., description="Data da última atualização da venda no formato ISO 8601")

    produtos: Sequence[ProdutoVendaRead] = Field(default_factory=list, description="Lista de produtos relacionados à venda")
    pagamentos: Sequence[PagamentoVendaRead] = Field(default_factory=list, description="Lista de pagamentos relacionados à venda")

# Resumos financeiros para modal

class VendaResumoFinanceiro(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    subtotal: int = Field(0, ge=0, description="Subtotal da venda")
    entrega: int = Field(0, ge=0, description="Valor da entrega")
    desconto: int = Field(0, ge=0, description="Desconto da venda")
    adiantamento: int = Field(0, ge=0, description="Valor do adiantamento")
    total: int = Field(0, ge=0, description="Total da venda")

class AddProdutoVendaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    produto_adicionado: ProdutoVendaRead
    resumo_financeiro: VendaResumoFinanceiro

class FinalizarVendaPayload(BaseModel):
    pagamentos: list[PagamentoVendaCreate] = Field(..., min_length=1, description="Lista de pagamentos para finalizar a venda")