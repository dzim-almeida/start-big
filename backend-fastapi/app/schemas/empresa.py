# ---------------------------------------------------------------------------
# ARQUIVO: schemas/empresa.py
# DESCRICAO: Schemas Pydantic para validacao de dados de Empresa.
# ---------------------------------------------------------------------------

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.endereco import Endereco, EnderecoRead, EnderecoUpdate

# NOTA ARQUITETURA:
# Para evitar referencias circulares em schemas aninhados, usamos o nome
# da classe como string literal ("NomeDaClasse").
# E necessario importar os schemas abaixo para que o Pydantic os encontre
# e use no tempo de execucao.

# =========================
# Schema Base
# =========================
class EmpresaBase(BaseModel):
    """
    Campos comuns para criar, ler ou atualizar uma empresa.

    Attributes:
        razao_social (str): Razao Social da empresa (obrigatorio).
        nome_fantasia (Optional[str]): Nome Fantasia (comercial).
        is_cnpj (bool): Indica se o documento e CPF ou CNPJ.
        documento (str): Documento CPF/CNPJ (apenas numeros, 11 a 14 digitos).
        inscricao_estadual (Optional[str]): Inscricao Estadual.
        inscricao_municipal (Optional[str]): Inscricao Municipal.
        regime_tributario (Optional[str]): Regime Tributario (ex: Simples Nacional).
        cnae_principal (Optional[str]): CNAE Principal.
        telefone (Optional[str]): Telefone fixo.
        celular (Optional[str]): Celular / WhatsApp.
        email (Optional[str]): Email principal para contato.
        url_logo (Optional[str]): URL ou caminho relativo da logo da empresa.
    """

    # Identificacao
    razao_social: str = Field(
        ...,
        max_length=255,
        description="Razao Social da empresa",
    )
    nome_fantasia: Optional[str] = Field(
        None,
        max_length=255,
        description="Nome Fantasia (comercial)",
    )
    is_cnpj: bool = Field(
        ...,
        description="Define se o documento e um CPF ou CNPJ",
    )
    documento: str = Field(
        ...,
        pattern=r"^\d{11,14}$",
        description="Documento CPF/CNPJ (apenas numeros, 11 a 14 digitos)",
    )
    inscricao_estadual: Optional[str] = Field(
        None,
        max_length=50,
        description="Inscricao Estadual",
    )
    inscricao_municipal: Optional[str] = Field(
        None,
        max_length=50,
        description="Inscricao Municipal",
    )
    regime_tributario: Optional[str] = Field(
        None,
        max_length=50,
        description="Regime Tributario (ex: Simples Nacional)",
    )
    cnae_principal: Optional[str] = Field(
        None,
        max_length=50,
        description="CNAE Principal",
    )

    # Contato
    telefone: Optional[str] = Field(
        None,
        max_length=20,
        description="Telefone fixo",
    )
    celular: Optional[str] = Field(
        None,
        max_length=20,
        description="Celular / WhatsApp",
    )
    email: Optional[str] = Field(
        None,
        max_length=255,
        description="Endereco de email principal para contato",
    )

    # Outros
    url_logo: Optional[str] = Field(
        None,
        max_length=255,
        description="URL ou caminho da logo da empresa",
    )

    model_config = ConfigDict(from_attributes=True)

# =========================
# Create (Entrada)
# =========================
class EmpresaCreate(EmpresaBase):
    """
    Dados necessarios para cadastrar uma nova empresa (Sign Up).
    Aninha a lista opcional de enderecos.

    Attributes:
        endereco (Optional[List[Endereco]]): Lista opcional de enderecos da empresa.
    """

    endereco: Optional[List["Endereco"]] = Field(
        None,
        description="Lista de enderecos da empresa (Principal, Entrega, etc)",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "razao_social": "Solucoes Tecnologicas Alpha S.A.",
                "nome_fantasia": "Alpha Tech",
                "is_cnpj": True,
                "documento": "68056674073060",
                "inscricao_estadual": "ISENTA",
                "inscricao_municipal": "001.234/2025-0",
                "regime_tributario": "Simples Nacional",
                "cnae_principal": "6201-5/01",
                "telefone": "6832104000",
                "celular": "68999887766",
                "email": "contato@alphatech.com",
                "endereco": [
                    {
                        "logradouro": "Avenida Cicero Pompeu",
                        "numero": "1500",
                        "bairro": "Centro",
                        "cidade": "Rio Branco",
                        "estado": "AC",
                        "cep": "69900-000",
                        "complemento": "Sala 101, Predio Comercial",
                    }
                ],
            }
        },
    )

# =========================
# Update (Entrada)
# =========================
class EmpresaUpdate(BaseModel):
    """
    Dados para atualizacao parcial de uma empresa (PATCH).
    Todos os campos sao opcionais.

    Attributes:
        endereco (Optional[List[EnderecoUpdate]]): Enderecos da empresa para atualizar.
    """

    # Identificacao
    razao_social: Optional[str] = Field(
        None,
        max_length=255,
        description="Razao Social da empresa",
    )
    nome_fantasia: Optional[str] = Field(
        None,
        max_length=255,
        description="Nome Fantasia (comercial)",
    )
    is_cnpj: Optional[bool] = Field(
        None,
        description="Define se o documento e um CPF ou CNPJ",
    )
    documento: Optional[str] = Field(
        None,
        pattern=r"^\d{11,14}$",
        description="Documento CPF/CNPJ (apenas numeros, 11 a 14 digitos)",
    )
    inscricao_estadual: Optional[str] = Field(
        None,
        max_length=50,
        description="Inscricao Estadual",
    )
    inscricao_municipal: Optional[str] = Field(
        None,
        max_length=50,
        description="Inscricao Municipal",
    )
    regime_tributario: Optional[str] = Field(
        None,
        max_length=50,
        description="Regime Tributario (ex: Simples Nacional)",
    )
    cnae_principal: Optional[str] = Field(
        None,
        max_length=50,
        description="CNAE Principal",
    )

    # Contato
    telefone: Optional[str] = Field(
        None,
        max_length=20,
        description="Telefone fixo",
    )
    celular: Optional[str] = Field(
        None,
        max_length=20,
        description="Celular / WhatsApp",
    )
    email: Optional[str] = Field(
        None,
        max_length=255,
        description="Endereco de email principal para contato",
    )

    # Outros
    url_logo: Optional[str] = Field(
        None,
        max_length=255,
        description="URL ou caminho da logo da empresa",
    )

    endereco: Optional[List["EnderecoUpdate"]] = Field(
        None,
        description="Lista de enderecos da empresa para atualizacao",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "nome_fantasia": "Alpha Tech Brasil",
                "telefone": "1132104000",
                "endereco": [
                    {
                        "id": 10,
                        "logradouro": "Avenida Cicero Pompeu",
                        "numero": "1500",
                        "bairro": "Centro",
                        "cidade": "Rio Branco",
                        "estado": "AC",
                        "cep": "69900-000",
                        "complemento": "Sala 101",
                    }
                ],
            }
        },
    )

# =========================
# Admin Read (Saida)
# =========================
class EmpresaAdminRead(EmpresaBase):
    """
    Formato de resposta da API para Empresa. Inclui dados internos (id, ativo)
    e lista aninhada de enderecos.

    Attributes:
        id (int): ID unico da empresa.
        ativo (bool): Status de ativo/inativo da empresa.
        endereco (Optional[List[EnderecoRead]]): Enderecos cadastrados (com IDs).
    """

    id: int = Field(..., description="ID unico da empresa")
    ativo: bool = Field(..., description="Status da empresa")
    enderecos: Optional[List["EnderecoRead"]] = Field(
        None,
        description="Enderecos cadastrados",
    )

# =========================
# User Read (Saida)
# =========================
class EmpresaUserRead(BaseModel):
    """Resposta simplificada de Empresa para usuarios."""

    id: int = Field(..., description="ID unico da empresa")
    ativo: bool = Field(..., description="Status da empresa")
    razao_social: str = Field(
        ...,
        max_length=255,
        description="Razao Social da empresa",
    )
    nome_fantasia: Optional[str] = Field(
        None,
        max_length=255,
        description="Nome Fantasia (comercial)",
    )
    url_logo: Optional[str] = Field(
        None,
        max_length=255,
        description="URL ou caminho da logo da empresa",
    )

    model_config = ConfigDict(from_attributes=True)


EmpresaCreate.model_rebuild()
EmpresaUpdate.model_rebuild()
EmpresaAdminRead.model_rebuild()
