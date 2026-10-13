# ---------------------------------------------------------------------------
# ARQUIVO: schemas/vendas/cadastro.py
# DESCRICAO: Schemas da venda - criar, editar e ler a venda.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field, ConfigDict
from app.core.enum import VendaStatus
from datetime import datetime
from typing import Optional, Sequence
from app.schemas.cliente import ClienteSimpleRead
from app.schemas.funcionario import CargoBase
from app.schemas.vendas.itens import ProdutoVendaRead
from app.schemas.vendas.pagamento import PagamentoVendaRead


class VendaCreate(BaseModel):
    cliente_id: Optional[int] = Field(None, description="ID do cliente")
    funcionario_id: int = Field(..., description="ID do funcionário")


class VendaUpdate(BaseModel):
    cliente_id: Optional[int] = Field(None, description="ID do cliente")
    funcionario_id: Optional[int] = Field(None, description="ID do funcionário")
    entrega: Optional[int] = Field(None, ge=0, description="Valor da entrega")
    desconto: Optional[int] = Field(None, ge=0, description="Desconto da venda")
    observacao: Optional[str] = Field(None, max_length=500, description="Observação da venda")
    observacao_interna: Optional[str] = Field(None, max_length=500, description="Observação interna (não impressa no comprovante)")
    codigo_gerente: Optional[str] = Field(None, description="PIN do gerente para aprovar desconto acima do limite")
    modo_atacado: Optional[bool] = Field(None, description="Liga/desliga o preço de atacado na venda inteira")


class FuncionarioVendaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID do funcionário")
    nome: str = Field(..., description="Nome do funcionário")
    cargo: Optional[CargoBase] = Field(None, description="Cargo do funcionário")


class VendaSimpleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID da venda")
    numero_venda: Optional[int] = Field(None, description="Número sequencial oficial (atribuído ao finalizar)")

    sessao_caixa_id: Optional[int] = Field(None, description="ID da sessão de caixa associada à venda")
    cliente_id: Optional[int] = Field(None, description="ID do cliente associado à venda")
    funcionario_id: int = Field(..., description="ID do funcionário associado à venda")

    total: int = Field(0, ge=0, description="Total da venda")

    status: VendaStatus = Field("ATIVA", description="Status da venda")
    criado_em: datetime = Field(..., description="Data de criação da venda no formato ISO 8601")
    atualizado_em: datetime = Field(..., description="Data da última atualização da venda no formato ISO 8601")
    # Mora na SimpleRead, e não na VendaRead: quem precisa saber quem está na
    # fila é a LISTA, que carrega o schema enxuto.
    enviada_ao_caixa_em: Optional[datetime] = Field(
        None,
        description="Quando o atendente entregou a venda ao caixa. Nulo = ainda em montagem",
    )

    cliente: Optional[ClienteSimpleRead] = Field(None, description="Dados do cliente associado à venda, preenchido automaticamente com base no cliente_id")
    funcionario: Optional[FuncionarioVendaRead] = Field(None, description="Dados do funcionário responsável pela venda")


class VendaRead(VendaSimpleRead):
    entrega: int = Field(0, ge=0, description="Valor da entrega")
    subtotal: int = Field(0, ge=0, description="Subtotal da venda")
    descontos: int = Field(0, ge=0, description="Desconto da venda (só o do operador)")
    descontos_regra: int = Field(0, ge=0, description="Soma dos descontos das regras de preço (R1/R3)")
    modo_atacado: bool = Field(False, description="Venda no preço de atacado")
    acrescimo: int = Field(0, ge=0, description="Acréscimo de juros/cartão aplicado no checkout")
    troco: int = Field(0, ge=0, description="Valor do troco a ser devolvido ao cliente")
    observacao: Optional[str] = Field(None, max_length=500, description="Observação da venda")
    observacao_interna: Optional[str] = Field(None, max_length=500, description="Observação interna (não impressa no comprovante)")
    motivo_cancelamento: Optional[str] = Field(None, max_length=500, description="Motivo do cancelamento")
    produtos: Optional[Sequence[ProdutoVendaRead]] = Field(default_factory=list, validation_alias="itens", description="Lista de produtos relacionados à venda")
    pagamentos: Optional[Sequence[PagamentoVendaRead]] = Field(default_factory=list, description="Lista de pagamentos relacionados à venda")
