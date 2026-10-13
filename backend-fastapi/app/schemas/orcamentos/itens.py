# ---------------------------------------------------------------------------
# ARQUIVO: schemas/orcamentos/itens.py
# DESCRICAO: Schemas do orcamento - itens.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Optional
from app.core.enum import TipoProdutoVenda
from app.schemas.quantidade import Quantidade, QuantidadeLida


# --- Schemas para criacao de orcamento e produtos ---

class OrcamentoProdutoCreate(BaseModel):
    tipo_produto: TipoProdutoVenda = Field(..., description="Tipo do produto, obrigatorio")
    produto_id: Optional[int] = Field(None, description="ID do produto, obrigatorio se nao for avulso")
    quantidade: Quantidade = Field(0, description="Quantidade (3 casas; quebrada so em KG, G, L, ML, M, M2, M3)")
    descricao_avulsa: Optional[str] = Field(None, max_length=100, description="Descricao do produto avulso")
    valor_unitario: Optional[int] = Field(None, ge=0, description="Valor unitario do produto")
    desconto: int = Field(0, ge=0, description="Desconto do produto")
    embalagem_id: Optional[int] = Field(
        None,
        description=(
            "Vende a EMBALAGEM (fardo/caixa): a quantidade é de embalagens e o preço é o dela; "
            "o estoque baixa quantidade × fator. Só com `usar_embalagens` ligado."
        ),
    )

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


# --- Schemas para atualizacao ---

class OrcamentoProdutoUpdate(BaseModel):
    quantidade: Optional[Quantidade] = Field(None, description="Quantidade (3 casas; quebrada so em KG, G, L, ML, M, M2, M3)")
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


# --- Schemas para leitura ---

class OrcamentoProdutoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID do produto no orcamento")
    tipo_produto: TipoProdutoVenda = Field(..., description="Tipo do produto")
    produto_id: Optional[int] = Field(None, description="ID do produto")
    sku: Optional[str] = Field(None, description="SKU do produto")
    nome: str = Field(..., description="Nome do produto")
    quantidade: QuantidadeLida = Field(0, description="Quantidade do produto (inteira volta inteira)")
    valor_unitario: int = Field(0, ge=0, description="Valor unitario do produto")
    desconto: int = Field(0, ge=0, description="Desconto do produto")
    subtotal: int = Field(0, ge=0, description="Subtotal do produto")
    total: int = Field(0, ge=0, description="Total do produto (subtotal - desconto)")
    imagem_url: Optional[str] = Field(None, description="URL da imagem do produto")
    unidade_medida: Optional[str] = Field(None, description="Unidade do produto (KG aceita 3,5; UN só inteiro)")
    embalagem_id: Optional[int] = Field(None, description="Embalagem vendida (nulo = unidade)")
    fator_embalagem: int = Field(1, ge=1, description="Unidades por embalagem, congelado na linha")
    sigla_embalagem: Optional[str] = Field(None, description="Sigla congelada (FD, CX...)")
