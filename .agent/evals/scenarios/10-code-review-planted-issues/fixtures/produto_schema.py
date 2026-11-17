# ---------------------------------------------------------------------------
# FIXTURE do cenário 10 (revisão de código). NÃO faz parte da aplicação.
# ARQUIVO: produto_schema.py
# DESCRIÇÃO: contratos Pydantic (o que entra e o que sai da API) de produto.
# ---------------------------------------------------------------------------

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field  # ferramentas de validação do Pydantic


class ProdutoCreate(BaseModel):
    """Dados que o frontend envia para cadastrar um produto."""

    empresa_id: int  # a qual empresa o produto pertence
    nome: str = Field(..., min_length=2, max_length=120)  # obrigatório, de 2 a 120 letras
    preco_venda: Decimal = Field(..., ge=0)  # preço, não pode ser negativo
    estoque_minimo: Optional[int] = Field(None, ge=0)  # opcional; se vier, não pode ser negativo


class ProdutoRead(BaseModel):
    """Dados que a API devolve ao frontend."""

    model_config = ConfigDict(from_attributes=True)  # permite montar a partir do objeto do banco

    id: int
    nome: str
    preco_venda: Decimal
    estoque_minimo: Optional[int] = None
