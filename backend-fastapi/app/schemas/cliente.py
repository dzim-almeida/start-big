# ---------------------------------------------------------------------------
# ARQUIVO: cliente_schema.py
# MÓDULO: Schemas Pydantic (DTOs)
# DESCRIÇÃO: Define regras de validação, tipos e documentação OpenAPI.
# ---------------------------------------------------------------------------

from datetime import date
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List, Annotated, Union, Literal
from app.core.enum import Gender, ClientType, State
from app.schemas.endereco import Endereco, EnderecoRead, EnderecoUpdate

# ===========================================================================
# SCHEMA BASE (CAMPOS COMUNS)
# ===========================================================================

class ClienteBase(BaseModel):
    """Atributos compartilhados entre PF e PJ."""
    
    email: Optional[str] = Field(
        None,
        max_length=255,
        description="Endereço de e-mail principal para contato."
    )
    telefone: Optional[str] = Field(
        None,
        max_length=255,
        description="Telefone principal."
    )
    celular: Optional[str] = Field(
        None,
        max_length=255,
        description="Celular principal."
    )
    observacoes: Optional[str] = Field(
        None,
        max_length=500,
        description="Notas internas ou observações sobre o cliente."
    )
    endereco: Optional[List[Endereco]] = Field(
        None,
        description="Lista de endereços vinculados."
    )

    model_config = ConfigDict(from_attributes=True)

# ===========================================================================
# PESSOA FÍSICA (PF)
# ===========================================================================

class ClientePFCreate(ClienteBase):
    """Modelo de entrada para criação de Pessoa Física."""
    
    nome: str = Field(
        ...,
        max_length=255,
        description="Nome civil completo."
    )
    cpf: str = Field(
        ...,
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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "João Pedro Silva",
                "cpf": "98765432101",
                "rg": "12345678",
                "genero": "MASCULINO",
                "data_nascimento": "1995-12-15",
                "email": "joao.silva@meu-pdv.com",
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
    endereco: Optional[List[EnderecoRead]] = Field(None)
    ativo: bool = Field(..., description="Status do cadastro.")

class ClientePFUpdate(ClienteBase):
    """Modelo de entrada para atualização parcial de Pessoa Física."""
    
    tipo: Literal[ClientType.PF] = Field(description="Obrigatório para identificar o schema.")
    
    nome: Optional[str] = Field(None, max_length=255)
    cpf: Optional[str] = Field(None, pattern=r"^\d{11}$")
    rg: Optional[str] = Field(None, pattern=r"^\d{5,20}$")
    genero: Optional[Gender] = Field(None)
    data_nascimento: Optional[date] = Field(None)
    endereco: Optional[List[EnderecoUpdate]] = Field(None)

# ===========================================================================
# PESSOA JURÍDICA (PJ)
# ===========================================================================

class ClientePJCreate(ClienteBase):
    """Modelo de entrada para criação de Pessoa Jurídica."""
    
    razao_social: str = Field(..., max_length=255, description="Razão Social da empresa.")
    cnpj: str = Field(..., pattern=r"^\d{14}$", description="CNPJ (apenas números, 14 dígitos).")
    nome_fantasia: str = Field(..., max_length=255, description="Nome Fantasia / Marca.")
    ie: Optional[str] = Field(None, pattern=r"^\d{9,14}$", description="Inscrição Estadual.")
    im: Optional[str] = Field(None, pattern=r"^\d{9,14}$", description="Inscrição Municipal.")
    regime_tributario: Optional[str] = Field(None, description="Código do Regime Tributário.")
    responsavel: Optional[str] = Field(None, max_length=255, description="Pessoa de contato na empresa.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "razao_social": "Tech Solutions LTDA",
                "cnpj": "12345678000199",
                "nome_fantasia": "Tech Soluções",
                "ie": "123456789",
                "im": "234567654344",
                "regime_tributario": "Simples Nacional",
                "responsavel": "Ana Gerente",
                "email": "contato@tech.com",
                "telefone": "1155554444",
                "tipo": "PJ",
                "endereco": [
                    {
                        "logradouro": "Av. Empresarial",
                        "numero": "200",
                        "bairro": "Distrito Ind.",
                        "cidade": "São Paulo",
                        "estado": "SP",
                        "cep": "04000-000"
                    }
                ]
            }
        }
    )

class ClientePJRead(ClientePJCreate):
    """Modelo de saída (Response) para Pessoa Jurídica."""
    
    id: int = Field(..., description="Identificador único do cliente.")
    tipo: Literal[ClientType.PJ] = Field(default=ClientType.PJ, description="Discriminador de tipo: PJ")
    endereco: Optional[List[EnderecoRead]] = Field(None)
    ativo: bool = Field(..., description="Status do cadastro.")

class ClientePJUpdate(ClienteBase):
    """Modelo de entrada para atualização parcial de Pessoa Jurídica."""
    
    tipo: Literal[ClientType.PJ] = Field(description="Obrigatório para identificar o schema.")
    
    razao_social: Optional[str] = Field(None, max_length=255)
    cnpj: Optional[str] = Field(None, pattern=r"^\d{14}$")
    nome_fantasia: Optional[str] = Field(None, max_length=255)
    ie: Optional[str] = Field(None, pattern=r"^\d{9,14}$")
    responsavel: Optional[str] = Field(None, max_length=255)
    endereco: Optional[List[EnderecoUpdate]] = Field(None)

# ===========================================================================
# UNIÕES POLIMÓRFICAS
# ===========================================================================

ClienteRead = Annotated[
    Union[ClientePFRead, ClientePJRead],
    Field(discriminator="tipo")
]

ClienteUpdate = Annotated[
    Union[ClientePFUpdate, ClientePJUpdate],
    Field(discriminator="tipo")
]