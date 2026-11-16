# ---------------------------------------------------------------------------
# ARQUIVO: app/schemas/lava_rapido/porte.py
# DESCRICAO: Contrato dos portes da loja e do preco por porte (Spec 02A).
# ---------------------------------------------------------------------------

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _texto_limpo(valor: Optional[str]) -> Optional[str]:
    """Nome sem espacos nas pontas; vazio e recusado pelo `min_length`."""
    return valor.strip() if isinstance(valor, str) else valor


# =========================
# Portes
# =========================

class PorteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo_veiculo: str
    nome: str
    ordem: int
    ativo: bool


class PorteCreate(BaseModel):
    tipo_veiculo: str = Field(..., min_length=1, max_length=30)
    nome: str = Field(..., min_length=1, max_length=60)

    _limpar = field_validator("nome", mode="before")(_texto_limpo)


class PorteUpdate(BaseModel):
    """PUT parcial: so o que vier muda. Desativar e `ativo: false` (nunca apagar)."""
    nome: Optional[str] = Field(None, min_length=1, max_length=60)
    ordem: Optional[int] = Field(None, ge=0)
    ativo: Optional[bool] = None

    _limpar = field_validator("nome", mode="before")(_texto_limpo)


# =========================
# Preco do servico por porte
# =========================

class PrecoPorteItem(BaseModel):
    """Uma linha da grade do cadastro de servico."""
    porte_id: int
    valor: int = Field(..., ge=0, description="Centavos")
    duracao_minutos: Optional[int] = Field(None, ge=0, le=24 * 60)


class PrecosServicoUpdate(BaseModel):
    """A grade INTEIRA do servico: porte fora da lista perde o preco proprio
    e volta a usar o preco padrao do servico."""
    precos: List[PrecoPorteItem]


class PrecoPorteRead(PrecoPorteItem):
    model_config = ConfigDict(from_attributes=True)


class ServicoDoPorte(BaseModel):
    """Servico ativo com o preco que vale para um porte (botoes da comanda)."""
    servico_id: int
    descricao: str
    valor: int = Field(..., description="Centavos: o do porte ou, sem linha, o padrao")
    duracao_minutos: Optional[int] = None
    # False = nao ha preco cadastrado para o porte; a tela mostra o padrao.
    preco_do_porte: bool
