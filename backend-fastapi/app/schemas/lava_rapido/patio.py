# ---------------------------------------------------------------------------
# ARQUIVO: app/schemas/lava_rapido/patio.py
# DESCRICAO: Contrato do patio do lava-rapido (SPEC-00 U3, Spec 04A).
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.lava_rapido.lavador import LavadorRead


class CartaoPatio(BaseModel):
    """Um veiculo no patio: o que o cartao mostra, sem abrir a OS."""
    numero_os: str
    status: str                                 # codigo do enum (ABERTA, EM_ANDAMENTO...)
    tipo_veiculo: Optional[str] = None          # id do tipo ("carro", "moto"...)
    placa: Optional[str] = None
    modelo: Optional[str] = None
    marca: Optional[str] = None
    cor: Optional[str] = None
    porte: Optional[str] = None
    cliente_nome: Optional[str] = None
    # Celular (ou telefone) para o WhatsApp do "Pronto" (O8).
    cliente_contato: Optional[str] = None
    servicos: List[str]
    valor_total: int                            # centavos
    lavadores: List[LavadorRead]
    responsavel: Optional[str] = None
    avarias: List[str]
    entrada: datetime                           # data_criacao (UTC)
    previsao: Optional[datetime] = None
    finalizada_em: Optional[datetime] = None


class PatioRead(BaseModel):
    """Os veiculos do dia, ja separados nas colunas do quadro."""
    aguardando: List[CartaoPatio]               # ABERTA
    lavando: List[CartaoPatio]                  # EM_ANDAMENTO
    pronto: List[CartaoPatio]                   # AGUARDANDO_RETIRADA
    entregues_hoje: List[CartaoPatio]           # FINALIZADA hoje
