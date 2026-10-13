# ---------------------------------------------------------------------------
# ARQUIVO: schemas/compras/fornecedores.py
# DESCRICAO: Schemas de compras - fornecedores do produto e produto para pedido.
# ---------------------------------------------------------------------------

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


MAX_FORNECEDORES_POR_PRODUTO = 30


class FornecedorResumo(BaseModel):
    """Para o seletor da tela — só o que ela mostra."""

    id: int
    nome: str
    nome_fantasia: Optional[str] = None


class FornecedorDoProdutoRead(BaseModel):
    """Uma linha da aba Fornecedores do produto.

    `id` nulo = o fornecedor principal do cadastro do produto, que ainda não
    tem linha aqui (aparece para o lojista completar código, embalagem e preço).
    """

    id: Optional[int] = None
    fornecedor_id: int
    fornecedor_nome: str
    codigo_fornecedor: Optional[str] = None
    embalagem_id: Optional[int] = None
    embalagem_sigla: Optional[str] = None
    fator: int = 1
    ultimo_preco: Optional[int] = Field(None, description="Centavos por unidade de compra; nulo sem permissão de custo")
    preco_unidade: Optional[float] = Field(None, description="Centavos por unidade do produto (só para exibir)")
    ultima_compra_em: Optional[date] = None
    prazo_dias: Optional[int] = None
    padrao: bool = Field(False, description="É o fornecedor principal do produto")
    mais_barato: bool = Field(False, description="Menor preço por unidade entre os fornecedores com preço (D18)")
    acima_do_menor_bp: int = Field(0, description="Quanto está acima do mais barato, em pontos-base (1000 = 10%)")


class FornecedorDoProdutoEscrita(BaseModel):
    fornecedor_id: int = Field(..., ge=1)
    codigo_fornecedor: Optional[str] = Field(None, max_length=60)
    embalagem_id: Optional[int] = Field(None, ge=1)
    fator: int = Field(1, ge=1, le=100_000)
    ultimo_preco: Optional[int] = Field(None, ge=0, le=100_000_000)
    prazo_dias: Optional[int] = Field(None, ge=0, le=365)
    padrao: bool = False

    @field_validator("codigo_fornecedor")
    @classmethod
    def _codigo_limpo(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return None
        valor = valor.strip()
        return valor or None


class FornecedoresDoProdutoSalvar(BaseModel):
    fornecedores: list[FornecedorDoProdutoEscrita] = Field(default_factory=list, max_length=MAX_FORNECEDORES_POR_PRODUTO)

    @model_validator(mode="after")
    def _sem_repeticao(self) -> "FornecedoresDoProdutoSalvar":
        ids = [f.fornecedor_id for f in self.fornecedores]
        if len(ids) != len(set(ids)):
            raise ValueError("O mesmo fornecedor aparece duas vezes na lista.")
        if sum(1 for f in self.fornecedores if f.padrao) > 1:
            raise ValueError("Só um fornecedor pode ser o principal.")
        return self


class EmbalagemResumo(BaseModel):
    id: int
    sigla: str
    fator: int


class ProdutoParaPedido(BaseModel):
    """O mínimo para pôr um produto no pedido, sem depender da permissão de Produtos."""

    id: int
    nome: str
    codigo_produto: Optional[str] = None
    codigo_barras: Optional[str] = None
    unidade_medida: str
    saldo: float
    embalagens: list[EmbalagemResumo] = Field(default_factory=list)
