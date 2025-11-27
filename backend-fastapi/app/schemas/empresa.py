# ---------------------------------------------------------------------------
# ARQUIVO: empresa_schema.py
# DESCRIÇÃO: Schemas Pydantic para validação de dados de Empresa.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from typing import Optional, List
# Importa os schemas aninhados
from app.schemas.endereco import Endereco, EnderecoRead
from app.schemas.usuario import UsuarioCreate, UsuarioRead

# =========================
# Schema Base
# =========================
class EmpresaBase(BaseModel):
    """
    Campos comuns para criar ou ler uma empresa.
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
    # Validação estrita de 14 dígitos para o CNPJ (apenas números)
    cnpj: str = Field(
        ..., 
        pattern=r"^\d{14}$", 
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
    # Nota: O uso de `str` em vez de `HttpUrl` é apropriado para caminhos relativos de imagem
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
    Aninha o Usuário Master e os Endereços.
    """
    # Aninhamento do schema de criação de Usuário Master (obrigatório)
    usuario: UsuarioCreate = Field(
        ...,
        description="Usuário Master/Responsável pela empresa (credenciais de login)."
    )
    
    # Aninhamento do schema de Endereço (lista opcional)
    endereco: Optional[List["Endereco"]] = Field(
        None,
        description="Lista de endereços da empresa (Principal, Entrega, etc)"
    )

    model_config = ConfigDict(
        # Exemplo de payload mantido
        json_schema_extra={
            "example": {
                "razao_social": "Tech Soluções LTDA",
                "cnpj": "12345678000199",
                "usuario": {
                    "nome": "Admin Master",
                    "email": "admin@empresa.com",
                    "senha": "SenhaForte123!",
                }
            }
        }
    )

# =========================
# Read (Saída)
# =========================
class EmpresaRead(EmpresaBase):
    """
    Formato de resposta da API para Empresa.
    """
    id: int = Field(..., description="ID único da empresa")
    ativo: bool = Field(..., description="Status da empresa")

    # Retorna os endereços completos (com ID)
    enderecos: Optional[List["EnderecoRead"]] = Field(None, description="Endereços cadastrados")

    # Retorna a lista de usuários (para visualização dos usuários vinculados)
    usuarios: list[UsuarioRead] = Field(..., description="Usuários vinculados a essa empresa")