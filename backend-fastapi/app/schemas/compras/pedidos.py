# ---------------------------------------------------------------------------
# ARQUIVO: schemas/compras/pedidos.py
# DESCRICAO: Schemas de compras - pedido (escrita, leitura, listagem, parcelas,
#            mensagem ao fornecedor) e a leitura do recebimento.
# ---------------------------------------------------------------------------

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Fase 2 — pedido de compra e necessidades
# ---------------------------------------------------------------------------
#
# Custos (custo_unitario, valores, parcelas) saem NULOS para quem não pode ver
# preço (D14) — o corte é no service, não na tela.

MAX_ITENS_POR_PEDIDO = 300


MAX_PARCELAS_POR_PEDIDO = 24


class PedidoItemEscrita(BaseModel):
    produto_id: int = Field(..., ge=1)
    embalagem_id: Optional[int] = Field(None, ge=1)
    fator: int = Field(1, ge=1, le=100_000)
    quantidade: int = Field(..., ge=1, le=1_000_000, description="Na unidade de compra")
    custo_unitario: int = Field(0, ge=0, le=100_000_000, description="Centavos por unidade de compra")


class PedidoParcelaEscrita(BaseModel):
    dias: int = Field(..., ge=0, le=365)
    valor: int = Field(..., ge=0)


class PedidoEscrita(BaseModel):
    """Criar ou substituir um RASCUNHO inteiro."""

    fornecedor_id: int = Field(..., ge=1)
    previsao_entrega: Optional[date] = None
    condicao_pagamento: Optional[str] = Field(None, max_length=60)
    frete: int = Field(0, ge=0, le=100_000_000)
    desconto: int = Field(0, ge=0, le=100_000_000)
    observacao: Optional[str] = Field(None, max_length=2000)
    itens: list[PedidoItemEscrita] = Field(default_factory=list, max_length=MAX_ITENS_POR_PEDIDO)
    # None = gerar pela condição de pagamento; lista = as parcelas como vieram.
    parcelas: Optional[list[PedidoParcelaEscrita]] = Field(None, max_length=MAX_PARCELAS_POR_PEDIDO)

    @model_validator(mode="after")
    def _sem_produto_repetido(self) -> "PedidoEscrita":
        ids = [i.produto_id for i in self.itens]
        if len(ids) != len(set(ids)):
            raise ValueError("O mesmo produto aparece duas vezes no pedido. Some as quantidades numa linha só.")
        return self


class PedidoDadosEscrita(BaseModel):
    """O que ainda dá para mudar num pedido ENVIADO: data e observação."""

    previsao_entrega: Optional[date] = None
    observacao: Optional[str] = Field(None, max_length=2000)


class MotivoEscrita(BaseModel):
    motivo: str = Field(..., min_length=3, max_length=255)

    @field_validator("motivo")
    @classmethod
    def _limpo(cls, valor: str) -> str:
        valor = valor.strip()
        if len(valor) < 3:
            raise ValueError("Diga o motivo (ao menos 3 letras).")
        return valor


class PedidoItemRead(BaseModel):
    id: int
    produto_id: Optional[int] = None
    descricao: str
    codigo_fornecedor: Optional[str] = None
    embalagem_id: Optional[int] = None
    unidade_compra: str
    fator: int
    quantidade: int
    quantidade_recebida: int
    quantidade_cancelada: int
    custo_unitario: Optional[int] = None
    subtotal: Optional[int] = None
    pendente: int = Field(0, description="Unidades de compra que ainda não chegaram nem foram encerradas")
    codigos_barras: list[str] = Field(
        default_factory=list, description="O que o leitor pode bipar para este item (embalagem e produto)"
    )


class PedidoParcelaRead(BaseModel):
    numero: int
    dias: int
    valor: Optional[int] = None


class CompraLogRead(BaseModel):
    acao: str
    situacao_anterior: Optional[str] = None
    situacao_nova: Optional[str] = None
    motivo: Optional[str] = None
    usuario_nome: Optional[str] = None
    ocorrido_em: datetime


class RecebimentoItemRead(BaseModel):
    descricao: str
    unidade_compra: str
    fator: int
    quantidade: int
    unidades: float
    custo_unitario: Optional[int] = None


class RecebimentoRead(BaseModel):
    id: int
    recebido_em: datetime
    recebido_por_nome: Optional[str] = None
    numero_nota: Optional[str] = None
    observacao: Optional[str] = None
    valor_itens: Optional[int] = None
    valor_ajuste: Optional[int] = None
    valor_total: Optional[int] = None
    contas_pagar_lancadas: int = 0
    itens: list[RecebimentoItemRead]


class PedidoResumo(BaseModel):
    id: int
    numero: int
    codigo: str
    situacao: str
    fornecedor_id: Optional[int] = None
    fornecedor_nome: str
    previsao_entrega: Optional[date] = None
    atrasado: bool = Field(False, description="Enviado e com a previsão já passada")
    quantidade_itens: int
    valor_total: Optional[int] = None
    criado_em: datetime
    enviado_em: Optional[datetime] = None


class PedidoRead(PedidoResumo):
    tipo: str
    condicao_pagamento: Optional[str] = None
    frete: Optional[int] = None
    desconto: Optional[int] = None
    valor_itens: Optional[int] = None
    observacao: Optional[str] = None
    motivo_cancelamento: Optional[str] = None
    criado_por_nome: Optional[str] = None
    fornecedor_telefone: Optional[str] = None
    itens: list[PedidoItemRead]
    parcelas: list[PedidoParcelaRead]
    historico: list[CompraLogRead]
    recebimentos: list[RecebimentoRead] = Field(default_factory=list)


class PedidoListagem(BaseModel):
    itens: list[PedidoResumo]
    total_itens: int


class MensagemFornecedor(BaseModel):
    """Texto pronto para mandar o pedido por WhatsApp."""

    texto: str
    telefone: Optional[str] = Field(None, description="Com DDI 55, só dígitos; nulo se o fornecedor não tem")


class SimularParcelas(BaseModel):
    total: int = Field(..., ge=0)
    condicao: Optional[str] = Field(None, max_length=60)


class ParcelaSimulada(BaseModel):
    numero: int
    dias: int
    valor: int
