# ---------------------------------------------------------------------------
# ARQUIVO: cliente.py
# DESCRIÇÃO: Schemas Pydantic para validação de dados de Cliente.
#            Define as estruturas de entrada (ClientePFCreate, ClientePJCreate)
#            e saída (ClientePFRead, ClientePJRead).
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
    Schema base com campos comuns a todos os tipos de clientes (PF e PJ).
    """
    email: Optional[EmailStr] = Field(
        None,
        max_length=255,
        description="Email do cliente"
    )
    contato: Optional[str] = Field(
        None,
        max_length=255, # Nota: Pode ser melhor validar como telefone (ex: max_length=20)
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
# Schemas Pessoa Física (PF)
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
                "nome": "João Silva",
                "cpf": "12345678901",
                # ... (resto do exemplo PF) ...
            }
        }
    )

class ClientePFRead(ClientePFCreate):
    """
    Schema para formatar os dados de SAÍDA (resposta da API)
    de um Cliente Pessoa Física.
    
    Herda de ClientePFCreate para incluir TODOS os campos (base e PF).
    """
    id: int = Field(
        ...,
        description="ID do cliente"
    )
    tipo: ClientType = Field(
        ...,
        description="Tipo do cliente (PF)"
    )
    
    # Sobrescreve 'endereco' para usar o schema 'EnderecoRead' (que inclui ID)
    endereco: Optional[List[EnderecoRead]] = Field(
        None,
        description="Endereco do cliente"
    )

# =========================
# Schemas Pessoa Jurídica (PJ)
# =========================
class ClientePJCreate(ClienteBase):
    """
    Schema para validar os dados de ENTRADA ao criar um
    novo Cliente Pessoa Jurídica. Herda os campos comuns de ClienteBase.
    """
    razao_social: str = Field(
        ...,
        max_length=255,
        description="Razão social do cliente jurídico"
    )
    cnpj: str = Field(
        ...,
        pattern=r"^\d{14}$", # Validação de formato (14 dígitos numéricos)
        description="CPNJ com 14 dígitos"
    )
    nome_fantasia: str = Field(
        ...,
        max_length=255,
        description="Nome fantasia do cliente jurídico"
    )
    ie: Optional[str] = Field(
        None,
        pattern=r"^\d{9,14}$",
        description="Número de inscrição estadual do cliente jurídico"
    )
    responsavel: Optional[str] = Field(
        None,
        max_length=255,
        description="Nome do responsável pela empresa"
    )

    # Exemplo para documentação OpenAPI (Swagger)
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "razao_social": "Minha Empresa de Tecnologia LTDA",
                "cnpj": "12345678000199",
                "nome_fantasia": "Tech Solutions",
                "ie": "123456789",
                "responsavel": "Ana Gerente",
                "email": "contato@techsolutions.com",
                "contato": "1155554444",
                "observacoes": "Primeiro contato feito na feira de tecnologia.",
                "endereco": [
                    {
                        "logradouro": "Avenida das Nações",
                        "numero": "1001",
                        "complemento": "Andar 15, Sala 1502",
                        "bairro": "Distrito Empresarial",
                        "cidade": "São Paulo",
                        "estado": "SP",
                        "cep": "04578-000"
                    }
                ]
            }
        }
    )

class ClientePJRead(ClientePJCreate):
    """
    Schema para formatar os dados de SAÍDA (resposta da API)
    de um Cliente Pessoa Jurídica.
    
    Herda de ClientePJCreate para incluir TODOS os campos (base e PJ).
    """
    id: int = Field(
        ...,
        description="ID do cliente"
    )
    tipo: ClientType = Field(
        ...,
        description="Tipo do cliente (PJ)"
    )
    
    # Sobrescreve 'endereco' para usar o schema 'EnderecoRead' (que inclui ID)
    endereco: Optional[List[EnderecoRead]] = Field(
        None,
        description="Endereco do cliente"
    )