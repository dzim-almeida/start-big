from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ComunicadoCreate(BaseModel):
    titulo: str = Field(..., max_length=100)
    mensagem: str = Field(..., max_length=2000)


class AutorRead(BaseModel):
    id: int
    nome: str
    model_config = {"from_attributes": True}


class ComunicadoRead(BaseModel):
    id: int
    titulo: str
    mensagem: str
    criado_em: datetime
    autor: Optional[AutorRead] = None
    lido: bool = False

    model_config = {"from_attributes": True}
