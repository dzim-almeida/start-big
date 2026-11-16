# ---------------------------------------------------------------------------
# ARQUIVO: schemas/compras/relatorios.py
# DESCRICAO: Schemas de compras - relatorio de fornecedores e variacao de preco.
# ---------------------------------------------------------------------------

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Fase 5 — relatórios
# ---------------------------------------------------------------------------


class RelatorioFornecedor(BaseModel):
    fornecedor_id: Optional[int] = None
    fornecedor_nome: str
    pedidos_enviados: int
    recebimentos: int
    valor_recebido: int = Field(..., description="Centavos")
    prazo_medio_dias: Optional[float] = Field(None, description="Do envio do pedido à primeira chegada")
    entregas_com_previsao: int = 0
    entregas_no_prazo: int = 0


class VariacaoPreco(BaseModel):
    produto_id: int
    descricao: str
    fornecedor_nome: str = Field(..., description="Da última compra")
    compras: int
    primeiro_custo_unidade: float = Field(..., description="Centavos por unidade, na 1ª chegada do período")
    ultimo_custo_unidade: float
    variacao_bp: int = Field(..., description="Pontos-base (1000 = 10%); positivo = subiu")


class RelatorioCompras(BaseModel):
    inicio: date
    fim: date
    pedidos_enviados: int
    valor_recebido: int
    por_fornecedor: list[RelatorioFornecedor]
    variacao_precos: list[VariacaoPreco]
