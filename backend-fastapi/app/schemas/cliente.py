# ---------------------------------------------------------------------------
# ARQUIVO: cliente.py
# DESCRIÇÃO: Schemas Pydantic para validação de dados de Cliente.
#            Define as estruturas de entrada (ClientePFCreate) e
#            saída (ClientePFRead).
# ---------------------------------------------------------------------------

from datetime import date
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List
from app.core.enum import Gender, ClientType
from app.schemas.endereco import Endereco, EnderecoRead # Importa os dois schemas de endereço

# =========================
# Schema Pydantic: ClienteBase
# =========================
class ClienteBase(BaseModel):
    """
    Schema base com campos comuns a todos os tipos de clientes.
    """
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
    
    # Na criação, espera uma lista de schemas 'Endereco' (sem ID)
    endereco: Optional[List[Endereco]] = Field(
        None,
        description="Endereço(s) do cliente"
    )

    # Permite que o Pydantic crie instâncias a partir de objetos ORM (SQLAlchemy)
    model_config = ConfigDict(from_attributes=True)

# =========================
# Schema Pydantic: ClientePFCreate (Criação)
# =========================
class ClientePFCreate(ClienteBase):
    """
    Schema para validar os dados de ENTRADA ao criar um
    novo Cliente Pessoa Física. Herda os campos comuns de ClienteBase.
    """
    nome: str = Field(
        ...,
        max_length=255,
        description="Nome completo do cliente"
    )
    cpf: str = Field(
        ...,
        pattern=r"^\d{11}$", # Validação de formato (11 dígitos numéricos)
        description="CPF com 11 dígitos"
    )
    rg: Optional[str] = Field(
        None,
        pattern=r"^\d{5,20}$",
        description="RG com 5 a 20 dígitos"
    )
    genero: Optional[Gender] = Field(
        None,
        description="Gênero do cliente"
    )
    data_nascimento: Optional[date] = Field(
        None,
        description="Data de nascimento do cliente"
    )

    # Exemplo para documentação OpenAPI (Swagger)
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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

# =========================
# Schema Pydantic: ClientePFRead (Leitura/Resposta)
# =========================
class ClientePFRead(ClientePFCreate):
    """
    Schema para formatar os dados de SAÍDA (resposta da API)
    de um Cliente Pessoa Física.
    
    Herda de ClientePFCreate para incluir TODOS os campos
    (base e específicos de PF).
    """
    id: int = Field(
        ...,
        description="ID do cliente"
    )
    tipo: ClientType = Field(
        ...,
        description="Tipo do cliente"
    )
    
    # Sobrescreve o campo 'endereco' da classe base
    # para usar o schema 'EnderecoRead' (que inclui ID)
    endereco: List[EnderecoRead] = Field(
        ...,
        description="Endereco do cliente"
    )