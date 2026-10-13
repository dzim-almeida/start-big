# ---------------------------------------------------------------------------
# ARQUIVO: schemas/compras/demanda_os.py
# DESCRICAO: Schemas de compras - compras de uma OS.
# ---------------------------------------------------------------------------

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Fase 6 — compras de uma OS
# ---------------------------------------------------------------------------


class PedidoDaOS(BaseModel):
    pedido_id: int
    codigo: str
    situacao: str
    previsao_entrega: Optional[date] = None
    quantidade: float = Field(..., description="Unidades deste pedido que são desta OS")
    atrasa_os: bool = Field(False, description="A entrega prevista é depois da previsão da OS (RC08)")


class CompraDaOSItem(BaseModel):
    produto_id: int
    descricao: str
    unidade: str
    necessario: float
    no_estoque: float = Field(..., description="Quanto do estoque livre fica para esta OS (fila: a OS mais antiga 1º)")
    em_pedido: float = Field(..., description="Em pedidos ainda não recebidos, ligados a esta OS")
    falta: float = Field(..., description="O que ninguém cobre ainda: precisa comprar")
    situacao: str = Field(..., description="NO_ESTOQUE, EM_PEDIDO ou FALTA")
    pedidos: list[PedidoDaOS] = Field(default_factory=list)


class ComprasDaOS(BaseModel):
    os_id: int
    numero_os: str
    aberta: bool = Field(..., description="Falso para OS finalizada/cancelada: as peças já saíram ou não vão sair")
    data_previsao: Optional[date] = None
    itens: list[CompraDaOSItem]
    # Marcenaria-fábrica (F3): instalação manda no aviso de atraso, e sem
    # sinal o material fica reservado mas fora das Necessidades.
    data_instalacao: Optional[date] = None
    compra_bloqueada: bool = Field(False, description="OS da fábrica aguardando o sinal: não gera compra ainda")
