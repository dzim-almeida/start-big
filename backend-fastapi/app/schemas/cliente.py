# Modelos Pydantic para Clientes

from pydantic import BaseModel, ConfigDict, EmailStr, Date, Field # type: ignore
from typing import Optional, List
from app.core.enum import Genero
from app.schemas.endereco import Endereco

# Base para Cliente, usado para herança nos modelos de entrada e saída
class ClienteBase(BaseModel):
    email: Optional[EmailStr] = Field(
        None,
        max_length=255,
        description="Email do cliente"
    )
    contato: Optional[str] = Field(
        None,
        max_length=255,
        description="Telefone de contato"
    )
    observacoes: Optional[str] = Field(
        None,
        max_length=500,
        description="Observações sobre o cliente"
    )
    endereco: Optional[List[Endereco]] = Field(
        None,
        description="Endereço(s) do cliente"
    )

    # Permite criar instâncias a partir de objetos ORM
    model_config = ConfigDict(from_attributes=True)

# Modelo para criação de Cliente Pessoa Física
class ClientePFCreate(ClienteBase):
    nome: str = Field(
        ...,
        max_length=255,
        description="Nome completo do cliente"
    )
    cpf: str = Field(
        ...,
        pattern=r"^\d{11}$",
        description="CPF com 11 dígitos"
    )
    rg: Optional[str] = Field(
        None,
        pattern=r"^\d{5,20}$",
        description="RG com 5 a 20 dígitos"
    )
    genero: Optional[Genero] = Field(
        None,
        description="Gênero do cliente"
    )
    data_nascimento: Optional[Date] = Field(
        None,
        description="Data de nascimento do cliente"
    )

    # Exemplo para documentação OpenAPI
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tipo": "PF",
                "email": "joao@email.com",
                "contato": "11999999999",
                "observacoes": "Cliente VIP",
                "endereco": [
                    {
                        "logradouro": "Rua Exemplo",
                        "numero": "123",
                        "complemento": "Apto 10",
                        "bairro": "Centro",
                        "cidade": "São Paulo",
                        "estado": "SP",
                        "cep": "01234-567"
                    },
                    {
                        "logradouro": "Avenida Teste",
                        "numero": "456",
                        "complemento": None,
                        "bairro": "Bairro Teste",
                        "cidade": "Rio de Janeiro",
                        "estado": "RJ",
                        "cep": "12345-678"
                    }
                ],
                "nome": "João Silva",
                "cpf": "12345678901",
                "rg": "1234567",
                "genero": "MASCULINO",
                "data_nascimento": "1990-05-20"
            }
        }
    )

# Modelo para leitura de Cliente Pessoa Física (inclui o ID)
class ClientePFRead(ClientePFCreate):
    id: int = Field(
        ...,
        description="ID do cliente"
    )
