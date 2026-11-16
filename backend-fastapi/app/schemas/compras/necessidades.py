# ---------------------------------------------------------------------------
# ARQUIVO: schemas/compras/necessidades.py
# DESCRICAO: Schemas de compras - necessidades, alternativas e gerar pedidos.
# ---------------------------------------------------------------------------

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.compras.pedidos import MAX_ITENS_POR_PEDIDO


class AlternativaMaisBarata(BaseModel):
    """D18: outro fornecedor do produto vende mais barato por unidade."""

    fornecedor_id: int
    fornecedor_nome: str
    preco_unidade: float = Field(..., description="Centavos por unidade do produto")
    economia_bp: int = Field(..., description="Quanto é mais barato, em pontos-base (1000 = 10%)")


class OpcaoFornecedor(BaseModel):
    fornecedor_id: int
    fornecedor_nome: str
    embalagem_id: Optional[int] = None
    unidade_compra: str
    fator: int
    ultimo_preco: Optional[int] = None
    prazo_dias: Optional[int] = None


class DemandaOSRead(BaseModel):
    """Uma OS aberta que usa o produto (fase 6)."""

    os_id: int
    numero_os: str
    quantidade: float = Field(..., description="Unidades do produto que a OS precisa")
    data_previsao: Optional[date] = None
    data_instalacao: Optional[date] = None
    aguardando_sinal: bool = Field(False, description="Fábrica sem sinal: reserva, mas não entra na compra")


class NecessidadeItem(BaseModel):
    produto_id: int
    produto_nome: str
    codigo_produto: Optional[str] = None
    unidade_medida: str
    saldo: float
    minimo: Optional[float] = Field(None, description="Nulo quando o produto entra só pela venda (base VENDAS)")
    ideal: Optional[float] = None
    em_pedido: float = Field(..., description="A caminho (pedidos enviados), na unidade do produto")
    em_rascunho: float = Field(0, description="Em rascunhos ainda não enviados — NÃO desconta da sugestão")
    rascunhos: list[str] = Field(default_factory=list, description="Códigos dos rascunhos que já têm o produto")
    fornecedor_id: Optional[int] = None
    fornecedor_nome: Optional[str] = None
    embalagem_id: Optional[int] = None
    unidade_compra: str
    fator: int
    sugestao: int = Field(..., description="Unidades de compra")
    ultimo_preco: Optional[int] = None
    alternativa: Optional[AlternativaMaisBarata] = None
    opcoes: list[OpcaoFornecedor] = Field(default_factory=list, description="Outros fornecedores do produto")
    # Fase 5: de onde veio a sugestão, e o giro do produto quando a base é VENDAS.
    origem: str = Field("MINIMO", description="MINIMO, VENDAS ou OS (peça de OS aberta que falta)")
    media_diaria: Optional[float] = Field(None, description="Vendido por dia na janela (unidade do produto)")
    dura_dias: Optional[float] = Field(None, description="Para quantos dias o estoque de hoje dá, nesse ritmo")
    # Fase 6: o que as OS abertas já comprometeram (reserva CALCULADA).
    reservado_os: float = Field(0, description="Unidades comprometidas com OS abertas; o saldo livre é saldo − isto")
    ordens: list[DemandaOSRead] = Field(default_factory=list, description="As OS que usam o produto, a mais antiga 1º")


class NecessidadeGrupo(BaseModel):
    fornecedor_id: Optional[int] = None
    fornecedor_nome: str
    itens: list[NecessidadeItem]


class GerarPedidoItem(BaseModel):
    produto_id: int = Field(..., ge=1)
    fornecedor_id: int = Field(..., ge=1)
    quantidade: int = Field(..., ge=1, le=1_000_000, description="Unidades de compra")


class GerarPedidos(BaseModel):
    itens: list[GerarPedidoItem] = Field(..., min_length=1, max_length=MAX_ITENS_POR_PEDIDO)
