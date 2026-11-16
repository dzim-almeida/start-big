# ---------------------------------------------------------------------------
# ARQUIVO: schemas/cliente/pessoa_juridica.py
# DESCRICAO: Clientes - schemas de pessoa juridica.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Sequence, Literal
from app.core.enum import ClientType
from app.schemas.endereco import Endereco, EnderecoRead, EnderecoUpdate
from app.schemas.cliente.comum import ClienteBase


# ===========================================================================
# PESSOA JURÍDICA (PJ)
# ===========================================================================

class ClientePJCreate(ClienteBase):
    """Modelo de entrada para criação de Pessoa Jurídica."""
    tipo: Literal[ClientType.PJ] = ClientType.PJ
    razao_social: str = Field(..., max_length=255, description="Razão Social da empresa.")
    cnpj: Optional[str] = Field(None, pattern=r"^\d{14}$", description="CNPJ (apenas números, 14 dígitos).")
    nome_fantasia: Optional[str] = Field(None, max_length=255, description="Nome Fantasia / Marca.")
    ie: Optional[str] = Field(None, pattern=r"^\d{9,14}$", description="Inscrição Estadual.")
    im: Optional[str] = Field(None, pattern=r"^\d{9,14}$", description="Inscrição Municipal.")
    regime_tributario: Optional[str] = Field(None, description="Código do Regime Tributário.")
    responsavel: Optional[str] = Field(None, max_length=255, description="Pessoa de contato na empresa.")
    endereco: Optional[List[Endereco]] = Field(
        None, 
        description="Lista de endereços para o cadastro inicial da empresa."
    )
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
    cnpj: Optional[str] = Field(None, description="CNPJ da empresa.")
    endereco: Optional[List[EnderecoRead]] = Field(None)
    ativo: bool = Field(..., description="Status do cadastro.")
    saldo_credito: int = Field(default=0, description="Saldo de crédito disponível em centavos.")


class ClientePJSimpleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Identificador único do cliente.")
    tipo: Literal[ClientType.PJ] = Field(default=ClientType.PJ, description="Discriminador de tipo: PJ")
    razao_social: str = Field(..., description="Razão Social da empresa.")
    cnpj: Optional[str] = Field(None, description="CNPJ da empresa.")
    telefone: Optional[str] = Field(None, description="Telefone do cliente.")
    celular: Optional[str] = Field(None, description="Celular do cliente.")
    endereco: Optional[Sequence[EnderecoRead]] = Field(None, description="Endereços do cliente.")
    saldo_credito: int = Field(default=0, description="Saldo de crédito disponível em centavos.")


class ClientePJUpdate(ClienteBase):
    """Modelo de entrada para atualização parcial de Pessoa Jurídica."""
    
    tipo: Literal[ClientType.PJ] = Field(description="Obrigatório para identificar o schema.")
    
    razao_social: Optional[str] = Field(None, max_length=255)
    cnpj: Optional[str] = Field(None, pattern=r"^\d{14}$")
    nome_fantasia: Optional[str] = Field(None, max_length=255)
    ie: Optional[str] = Field(None, pattern=r"^\d{9,14}$")
    responsavel: Optional[str] = Field(None, max_length=255)
    endereco: Optional[List[EnderecoUpdate]] = Field(None)
