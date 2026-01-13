# ---------------------------------------------------------------------------
# ARQUIVO: empresa_schema.py
# DESCRIÇÃO: Schemas Pydantic para validação de dados de Empresa.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from typing import Optional, List, Type # Importamos Type para a reconstrução (melhor prática em v2)

# NOTA ARQUITETURA:
# Para evitar referências circulares em schemas aninhados, usamos o nome
# da classe como string literal ("NomeDaClasse").
# É necessário importar os schemas abaixo para que o Pydantic os encontre
# e use no tempo de execução.
from app.schemas.endereco import Endereco, EnderecoRead

# =========================
# Schema Base
# =========================
class EmpresaBase(BaseModel):
    """
    Campos comuns para criar ou ler uma empresa.

    Attributes:
        razao_social (str): Razão Social da empresa (obrigatório).
        nome_fantasia (Optional[str]): Nome Fantasia (comercial).
        cnpj (str): CNPJ (apenas números, 14 dígitos, obrigatório).
        inscricao_estadual (Optional[str]): Inscrição Estadual.
        inscricao_municipal (Optional[str]): Inscrição Municipal.
        regime_tributario (Optional[str]): Regime Tributário (ex: Simples Nacional).
        telefone (Optional[str]): Telefone fixo.
        celular (Optional[str]): Celular / WhatsApp.
        url_logo (Optional[str]): URL ou caminho relativo da logo da empresa.
    """
    razao_social: str = Field(
        ..., 
        max_length=255, 
        description="Razão Social da empresa"
    )
    nome_fantasia: Optional[str] = Field(
        None, 
        max_length=255, 
        description="Nome Fantasia (comercial)"
    )
    is_cnpj: bool = Field(
        ...,
        description="Define se o documento é um CPF ou CNPJ"
    )
    documento: str = Field(
        ..., 
        pattern=r"^\d{11,14}$", 
        description="CNPJ (apenas números, 14 dígitos)"
    )
    inscricao_estadual: Optional[str] = Field(
        None, 
        max_length=50, 
        description="Inscrição Estadual"
    )
    inscricao_municipal: Optional[str] = Field(
        None, 
        max_length=50, 
        description="Inscrição Municipal"
    )
    regime_tributario: Optional[str] = Field(
        None, 
        max_length=50, 
        description="Regime Tributário (ex: Simples Nacional)"
    )
    telefone: Optional[str] = Field(
        None, 
        max_length=20, 
        description="Telefone fixo"
    )
    celular: Optional[str] = Field(
        None, 
        max_length=20, 
        description="Celular / WhatsApp"
    )
    url_logo: Optional[str] = Field(
        None, 
        max_length=255, 
        description="URL ou caminho da logo da empresa"
    )

    model_config = ConfigDict(from_attributes=True)

# =========================
# Create (Entrada)
# =========================
class EmpresaCreate(EmpresaBase):
    """
    Dados necessários para cadastrar uma nova empresa (processo de Sign Up).
    Aninha a lista opcional de endereços.

    Attributes:
        endereco (Optional[List[Endereco]]): Lista opcional de endereços da empresa.
    """
    
    # Referência de string para Endereco (Forward Reference)
    endereco: Optional[List["Endereco"]] = Field(
        None,
        description="Lista de endereços da empresa (Principal, Entrega, etc)"
    )

    model_config = ConfigDict(
        # Exemplo de payload mantido
        json_schema_extra={
            "example": {
                "razao_social": "Soluções Tecnológicas Alpha S.A.",
                "nome_fantasia": "Alpha Tech",
                "is_cnpj": True,
                "documento": "68056674073060",
                "inscricao_estadual": "ISENTA",
                "inscricao_municipal": "001.234/2025-0",
                "regime_tributario": "Simples Nacional",
                "telefone": "6832104000",
                "celular": "68999887766",
                "endereco": [
                    {
                        "logradouro": "Avenida Cícero Pompeu",
                        "numero": "1500",
                        "bairro": "Centro",
                        "cidade": "Rio Branco",
                        "estado": "AC",
                        "cep": "69900-000",
                        "complemento": "Sala 101, Prédio Comercial"
                    }
                ]
            }
        }
    )

# =========================
# Admin Read (Saída)
# =========================
class EmpresaAdminRead(EmpresaBase):
    """
    Formato de resposta da API para Empresa. Inclui dados internos (id, ativo)
    e listas aninhadas de endereços e usuários.

    Attributes:
        id (int): ID único da empresa.
        ativo (bool): Status de ativo/inativo da empresa.
        enderecos (Optional[List[EnderecoRead]]): Lista de endereços cadastrados, incluindo seus IDs.
    """
    id: int = Field(..., description="ID único da empresa")
    ativo: bool = Field(..., description="Status da empresa")

    # Referência de string para EnderecoRead e UsuarioRead
    endereco: Optional[List["EnderecoRead"]] = Field(None, description="Endereços cadastrados")

# =========================
# User Read (Saída)
# =========================
class EmpresaUserRead(BaseModel):
    id: int = Field(
        ...,
        description="ID unico da empresa"
    )
    ativo: bool = Field(
        ...,
        description="Status da empresa"
    )
    razao_social: str = Field(
        ..., 
        max_length=255, 
        description="Razão Social da empresa"
    )
    nome_fantasia: Optional[str] = Field(
        None, 
        max_length=255, 
        description="Nome Fantasia (comercial)"
    )
    url_logo: Optional[str] = Field(
        None, 
        max_length=255, 
        description="URL ou caminho da logo da empresa"
    )

    model_config = ConfigDict(from_attributes=True)

EmpresaCreate.model_rebuild()
EmpresaAdminRead.model_rebuild()