# ---------------------------------------------------------------------------
# ARQUIVO: schemas/vendas/itens.py
# DESCRICAO: Schemas da venda - itens.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Optional
from app.core.enum import TipoProdutoVenda
from app.schemas.quantidade import Quantidade, QuantidadeLida


# Schemas para criação de venda, produtos e pagamentos relacionados a uma venda

class ProdutoVendaCreate(BaseModel):
    tipo_produto: TipoProdutoVenda = Field(..., description="Tipo do produto, obrigatório")
    produto_id: Optional[int] = Field(None, description="ID do produto, obrigatório se não for uma descrição avulsa")
    quantidade: Quantidade = Field(0, description="Quantidade (3 casas; quebrada só em KG, G, L, ML, M, M2, M3)")
    descricao_avulsa: Optional[str] = Field(None, max_length=100, description="Descrição do produto avulso, obrigatório se não for um produto cadastrado")
    valor_unitario: Optional[int] = Field(None, ge=0, description="Valor unitário do produto, obrigatório")
    custo_unitario: Optional[int] = Field(
        None,
        ge=0,
        description=(
            "Quanto a loja PAGOU por unidade, em centavos. Só para item AVULSO — o "
            "cadastrado tem o custo no livro de estoque, e contar os dois dobraria "
            "o CMV. Campo interno: nunca sai em via impressa."
        )
    )
    desconto: int = Field(0, ge=0, description="Desconto do produto, obrigatório")
    embalagem_id: Optional[int] = Field(
        None,
        description=(
            "Vende a EMBALAGEM (fardo/caixa): a quantidade é de embalagens e o preço é o dela; "
            "o estoque baixa quantidade × fator. Só com `usar_embalagens` ligado."
        ),
    )

    @model_validator(mode='after')
    def check_produto_references(self) -> 'ProdutoVendaCreate':
        if self.tipo_produto == TipoProdutoVenda.AVULSO:
            if self.produto_id is not None:
                raise ValueError("O campo 'produto_id' não deve ser fornecido quando o tipo de produto é 'AVULSO'.")
            if self.descricao_avulsa is None:
                raise ValueError("O campo 'descricao_avulsa' é obrigatório quando o tipo de produto é 'AVULSO'.")
            if self.valor_unitario is None:
                raise ValueError("O campo 'valor_unitario' é obrigatório quando o tipo de produto é 'AVULSO'.")
            subtotal = (self.quantidade or 0) * (self.valor_unitario or 0) - (self.desconto or 0)
            if subtotal < 0:
                raise ValueError("O desconto não pode ser maior que o valor total do produto.", )
            return self

        if self.produto_id is None:
            raise ValueError("O campo 'produto_id' é obrigatório quando o tipo de produto é 'CADASTRADO'.")
        if self.descricao_avulsa is not None:
            raise ValueError("O campo 'descricao_avulsa' deve ser nulo quando o tipo de produto é 'CADASTRADO'.")
        if self.valor_unitario is not None:
            raise ValueError("O campo 'valor_unitario' deve ser nulo quando o tipo de produto é 'CADASTRADO'.")
        if self.custo_unitario is not None:
            raise ValueError("O campo 'custo_unitario' deve ser nulo quando o tipo de produto é 'CADASTRADO': o custo vem do livro de estoque.")
        return self


# Schemas para atualização de venda, produtos e pagamentos relacionados a uma venda

class ProdutoVendaUpdate(BaseModel):
    quantidade: Optional[Quantidade] = Field(None, description="Quantidade (3 casas; quebrada só em KG, G, L, ML, M, M2, M3)")
    descricao_avulsa: Optional[str] = Field(None, max_length=100, description="Descrição do produto avulso")
    valor_unitario: Optional[int] = Field(None, ge=0, description="Valor unitário do produto")
    custo_unitario: Optional[int] = Field(None, ge=0, description="Custo interno por unidade (item avulso). Nunca impresso.")
    desconto: Optional[int] = Field(None, ge=0, description="Desconto do produto")
    codigo_gerente: Optional[str] = Field(None, description="PIN do gerente para aprovar alteração de preço")

    @model_validator(mode='after')
    def check_produto_references(self) -> 'ProdutoVendaUpdate':
        if self.valor_unitario and self.quantidade:
            subtotal = (self.quantidade or 0) * (self.valor_unitario or 0) - (self.desconto or 0)
            if subtotal < 0:
                raise ValueError("O desconto não pode ser maior que o valor total do produto.")
        return self


# Schemas para leitura de venda, produtos e pagamentos relacionados a uma venda

class ProdutoVendaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID do produto na venda")
    tipo_produto: TipoProdutoVenda = Field(..., description="Tipo do produto, obrigatório")
    produto_id: Optional[int] = Field(None, description="ID do produto, obrigatório se não for uma descrição avulsa")
    sku: Optional[str] = Field(None, description="SKU do produto, preenchido automaticamente com base no tipo do produto e suas referências")
    nome: str = Field(..., description="Nome do produto, preenchido automaticamente com base no tipo do produto e suas referências")
    quantidade: QuantidadeLida = Field(0, description="Quantidade do produto (inteira volta inteira: 3, não 3.0)")
    valor_unitario: int = Field(0, ge=0, description="Valor unitário do produto, obrigatório")
    custo_unitario: Optional[int] = Field(
        None,
        description="Custo interno por unidade (só item avulso). Nunca impresso na via do cliente."
    )
    desconto: int = Field(0, ge=0, description="Desconto do produto, obrigatório")
    subtotal: int = Field(0, ge=0, description="Subtotal do produto (quantidade * valor_unitario - desconto)")
    total: int = Field(0, ge=0, description="Total do produto (subtotal - desconto)")
    imagem_url: Optional[str] = Field(None, description="URL da imagem do produto, preenchido automaticamente com base no tipo do produto e suas referências")
    unidade_medida: Optional[str] = Field(None, description="Unidade de medida do produto (ex: UN, KG, CX)")
    # float: o estoque é fracionado desde f97d3c1 (kg quebrado). Como int, um
    # produto com 1,5 kg derrubava esta resposta com erro 500.
    estoque_disponivel: Optional[float] = Field(None, description="Estoque atual do produto no momento da consulta")
    embalagem_id: Optional[int] = Field(None, description="Embalagem vendida (nulo = unidade)")
    fator_embalagem: int = Field(1, ge=1, description="Unidades por embalagem, congelado na linha")
    sigla_embalagem: Optional[str] = Field(None, description="Sigla congelada (FD, CX...)")
    # Regra de preço por quantidade aplicada (§6.1). `desconto` continua sendo
    # só o do operador; `total` já desconta os dois.
    desconto_regra: int = Field(0, ge=0, description="Desconto da regra de preço R1/R3 (centavos)")
    regra_preco: Optional[str] = Field(None, description="R1, R2, R3, ATACADO ou MANUAL (preço trocado pelo gerente)")
    regra_descricao: Optional[str] = Field(None, description="O que a linha mostra ('Leve 3, pague 2: 1 grátis')")
    valor_unitario_tabela: Optional[int] = Field(None, description="R2/ATACADO: preço cheio da unidade, mostrado riscado")
