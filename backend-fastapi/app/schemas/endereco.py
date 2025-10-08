# Modelos Pydantic para Endereço

from pydantic import BaseModel, Field  # type: ignore # Modelo de entrada do Pydantic
from typing import Optional
from app.core.enum import Estado  # Importa o Enum Estado

class Endereco(BaseModel):
    logradouro: str = Field(..., max_length=255, description="Logradouro do endereço")
    numero: str = Field(..., max_length=20, description="Número do endereço")
    complemento: Optional[str] = Field(None, max_length=100, description="Complemento do endereço")
    bairro: str = Field(..., max_length=100, description="Bairro do endereço")
    cidade: str = Field(..., max_length=100, description="Cidade do endereço")
    estado: Estado = Field(..., description="Estado do endereço (UF)")
    cep: str = Field(..., max_length=10, description="CEP do endereço")