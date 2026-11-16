# ---------------------------------------------------------------------------
# ARQUIVO: schemas/cliente/pessoa_fisica.py
# DESCRICAO: Clientes - schemas de pessoa fisica.
# ---------------------------------------------------------------------------

from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Sequence, Literal
from app.core.enum import Gender, ClientType
from app.schemas.endereco import Endereco, EnderecoRead, EnderecoUpdate
from app.schemas.cliente.comum import ClienteBase


# ===========================================================================
# PESSOA FÍSICA (PF)
# ===========================================================================


class ClientePFCreate(ClienteBase):
    """Modelo de entrada para criação de Pessoa Física."""
    tipo: Literal[ClientType.PF] = ClientType.PF

    nome: str = Field(
        ...,
        max_length=255,
        description="Nome civil completo."
    )
    cpf: Optional[str] = Field(
        None,
        pattern=r"^\d{11}$",
        description="CPF (apenas números, 11 dígitos)."
    )
    rg: Optional[str] = Field(
        None,
        pattern=r"^\d{5,20}$",
        description="Registro Geral (apenas números)."
    )
    genero: Optional[Gender] = Field(
        None,
        description="Gênero conforme enumeração do sistema."
    )
    data_nascimento: Optional[date] = Field(
        None,
        description="Data de nascimento (YYYY-MM-DD)."
    )
    endereco: Optional[List[Endereco]] = Field(
        None, 
        description="Lista de endereços para o cadastro inicial."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "João Pedro Silva",
                "cpf": "98765432101",
                "rg": "12345678",
                "genero": "MASCULINO",
                "data_nascimento": "1995-12-15",
                "email": "joao.silva@startbig.com.br",
                "celular": "11987654321",
                "observacoes": "Cliente novo.",
                "tipo": "PF",
                "endereco": [
                    {
                        "logradouro": "Rua das Flores",
                        "numero": "100",
                        "bairro": "Centro",
                        "cidade": "Campinas",
                        "estado": "SP",
                        "cep": "13010-000"
                    }
                ]
            }
        }
    )


class ClientePFRead(ClientePFCreate):
    """Modelo de saída (Response) para Pessoa Física."""

    id: int = Field(..., description="Identificador único do cliente.")
    tipo: Literal[ClientType.PF] = Field(
        default=ClientType.PF,
        description="Discriminador de tipo: PF"
    )
    cpf: Optional[str] = Field(None, description="CPF do cliente.")
    endereco: Optional[List[EnderecoRead]] = Field(None)
    ativo: bool = Field(..., description="Status do cadastro.")
    saldo_credito: int = Field(default=0, description="Saldo de crédito disponível em centavos.")


class ClientePFSimpleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Identificador único do cliente.")
    tipo: Literal[ClientType.PF] = Field(default=ClientType.PF, description="Discriminador de tipo: PF")
    nome: str = Field(..., description="Nome do cliente.")
    cpf: Optional[str] = Field(None, description="CPF do cliente.")
    telefone: Optional[str] = Field(None, description="Telefone do cliente.")
    celular: Optional[str] = Field(None, description="Celular do cliente.")
    endereco: Optional[Sequence[EnderecoRead]] = Field(None, description="Endereços do cliente.")
    saldo_credito: int = Field(default=0, description="Saldo de crédito disponível em centavos.")


class ClientePFUpdate(ClienteBase):
    """Modelo de entrada para atualização parcial de Pessoa Física."""
    
    tipo: Literal[ClientType.PF] = Field(description="Obrigatório para identificar o schema.")
    
    nome: Optional[str] = Field(None, max_length=255)
    cpf: Optional[str] = Field(None, pattern=r"^\d{11}$")
    rg: Optional[str] = Field(None, pattern=r"^\d{5,20}$")
    genero: Optional[Gender] = Field(None)
    data_nascimento: Optional[date] = Field(None)
    endereco: Optional[List[EnderecoUpdate]] = Field(None)
