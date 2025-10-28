# ---------------------------------------------------------------------------
# ARQUIVO: endereco.py
# DESCRIÇÃO: Schemas Pydantic para validação de dados de Endereço.
#            Define as estruturas de entrada (Endereco) e saída (EnderecoRead).
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field
from typing import Optional
from app.core.enum import State  # Importa o Enum de Estados (UF)

# =========================
# Schema Pydantic: Endereco (Base/Criação)
# =========================
class Endereco(BaseModel):
    """
    Schema base para um Endereço.
    Usado para validar os dados de um novo endereço ao criar um cliente.
    """
    logradouro: str = Field(..., max_length=255, description="Logradouro do endereço")
    numero: str = Field(..., max_length=20, description="Número do endereço")
    complemento: Optional[str] = Field(None, max_length=100, description="Complemento do endereço")
    bairro: str = Field(..., max_length=100, description="Bairro do endereço")
    cidade: str = Field(..., max_length=100, description="Cidade do endereço")
    estado: State = Field(..., description="Estado do endereço (UF)")
    cep: str = Field(..., max_length=10, description="CEP do endereço")

# =========================
# Schema Pydantic: EnderecoRead (Leitura/Resposta)
# =========================
class EnderecoRead(Endereco):
    """
    Schema para formatar a resposta da API de um Endereço.
    Herda todos os campos de 'Endereco' e adiciona os campos
    gerados pelo banco de dados (como 'id' e 'id_cliente').
    """
    id: int = Field(
        ...,
        description="ID do endereço"
    )
    id_cliente: int = Field(
        ...,
        description="ID do cliente"
    )