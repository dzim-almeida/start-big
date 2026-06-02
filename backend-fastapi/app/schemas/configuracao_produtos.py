from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ConfiguracaoProdutosRead(BaseModel):
    id: int
    empresa_id: int

    exigir_codigo_barras: bool
    exigir_categoria: bool
    exigir_preco_custo: bool

    margem_lucro_padrao: float
    utilizar_preco_atacado: bool

    permitir_venda_estoque_zerado: bool
    quantidade_minima_padrao: int
    unidade_medida_padrao: str

    data_atualizacao: datetime

    model_config = {"from_attributes": True}


class ConfiguracaoProdutosUpdate(BaseModel):
    exigir_codigo_barras: Optional[bool] = None
    exigir_categoria: Optional[bool] = None
    exigir_preco_custo: Optional[bool] = None

    margem_lucro_padrao: Optional[float] = None
    utilizar_preco_atacado: Optional[bool] = None

    permitir_venda_estoque_zerado: Optional[bool] = None
    quantidade_minima_padrao: Optional[int] = None
    unidade_medida_padrao: Optional[str] = None
