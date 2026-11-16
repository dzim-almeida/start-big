# ---------------------------------------------------------------------------
# ARQUIVO: app/schemas/lava_rapido/agendamento.py
# DESCRICAO: Contrato da agenda do lava-rapido (SPEC-00 O11, Spec 08A).
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

Situacao = Literal["AGENDADO", "CHEGOU", "NAO_VEIO", "CANCELADO"]


class ServicoAgendado(BaseModel):
    servico_id: Optional[int] = None
    nome: str = Field(..., min_length=1, max_length=255)
    valor: int = Field(0, ge=0, description="Centavos combinados")


class AgendamentoBase(BaseModel):
    inicio: datetime = Field(..., description="Instante marcado (UTC, ou com fuso)")
    duracao_minutos: Optional[int] = Field(None, ge=0, le=24 * 60)
    cliente_id: Optional[int] = None
    cliente_nome: str = Field(..., min_length=1, max_length=255)
    cliente_contato: Optional[str] = Field(None, max_length=20)
    placa: Optional[str] = Field(None, max_length=20)
    veiculo: Optional[str] = Field(None, max_length=120)
    tipo_veiculo: Optional[str] = Field(None, max_length=30)
    porte_id: Optional[int] = None
    servicos: List[ServicoAgendado] = Field(default_factory=list)
    observacao: Optional[str] = Field(None, max_length=1000)

    @field_validator("cliente_nome", mode="before")
    @classmethod
    def _limpar_nome(cls, valor):
        return valor.strip() if isinstance(valor, str) else valor


class AgendamentoCreate(AgendamentoBase):
    pass


class AgendamentoUpdate(BaseModel):
    """PUT parcial: so o que vier muda."""
    inicio: Optional[datetime] = None
    duracao_minutos: Optional[int] = Field(None, ge=0, le=24 * 60)
    cliente_id: Optional[int] = None
    cliente_nome: Optional[str] = Field(None, min_length=1, max_length=255)
    cliente_contato: Optional[str] = Field(None, max_length=20)
    placa: Optional[str] = Field(None, max_length=20)
    veiculo: Optional[str] = Field(None, max_length=120)
    tipo_veiculo: Optional[str] = Field(None, max_length=30)
    porte_id: Optional[int] = None
    servicos: Optional[List[ServicoAgendado]] = None
    observacao: Optional[str] = Field(None, max_length=1000)
    situacao: Optional[Situacao] = None
    numero_os: Optional[str] = Field(None, max_length=20)


class AgendamentoRead(AgendamentoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    situacao: Situacao
    numero_os: Optional[str] = None
    criado_em: datetime
