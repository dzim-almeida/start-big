# ---------------------------------------------------------------------------
# ARQUIVO: usuario_schema.py
# DESCRIÇÃO: Schemas Pydantic para autenticação e gestão de usuários (login).
# ---------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional
from datetime import datetime

# =========================
# Schema Base
# =========================
class UsuarioBase(BaseModel):
    """
    Campos básicos e comuns para identificação do usuário.
    """
    nome: str = Field(..., max_length=255, description="Nome completo")
    # Usa EmailStr para garantir validação de formato de e-mail automática
    email: EmailStr = Field(..., max_length=255, description="E-mail de login")

    model_config = ConfigDict(from_attributes=True)

# =========================
# Create (Entrada)
# =========================
class UsuarioCreate(UsuarioBase):
    """
    Dados de criação, incluindo a senha em texto plano.
    """
    senha: str = Field(
        ..., 
        min_length=8, 
        max_length=72, 
        description="Senha em texto plano (será hashada)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "Admin Master",
                "email": "admin@empresa.com",
                "senha": "SenhaForte123!",
            }
        }
    )

# =========================
# Read (Saída)
# =========================
class UsuarioRead(UsuarioBase):
    """
    Formato de resposta da API para Usuário (exclui a senha).
    """
    id: int = Field(..., description="ID do usuário")
    empresa_id: int = Field(..., description="ID da empresa")
    ativo: bool = Field(..., description="Status de ativo/inativo")
    is_master: bool = Field(..., description="Define se é o usuário Master da empresa")
    # data_criacao poderia ser adicionada se estiver presente no modelo ORM

# =========================
# Update (Edição Parcial)
# =========================
class UsuarioUpdate(BaseModel):
    """
    Campos opcionais para edição parcial (PUT/PATCH).
    """
    nome: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = Field(None, max_length=255)
    senha: Optional[str] = Field(None, min_length=8, description="Nova senha (opcional)")
    is_master: Optional[bool] = Field(None)
    ativo: Optional[bool] = Field(None)

    model_config = ConfigDict(from_attributes=True)