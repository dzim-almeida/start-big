# ---------------------------------------------------------------------------
# ARQUIVO: usuario_schema.py
# DESCRIÇÃO: Schemas Pydantic para autenticação e gestão de usuários (login).
# ---------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.schemas.empresa import EmpresaUserRead
from typing import Optional
from datetime import datetime

# =========================
# Schema Base
# =========================
class UsuarioBase(BaseModel):
    """
    Campos básicos e comuns para identificação do usuário.

    Attributes:
        nome (str): Nome completo do usuário.
        email (EmailStr): E-mail de login, validado automaticamente como formato de e-mail.
    """
    nome: str = Field(..., max_length=255, description="Nome completo")
    email: EmailStr = Field(..., max_length=255, description="E-mail de login")

    model_config = ConfigDict(from_attributes=True)

# =========================
# Create (Entrada)
# =========================
class UsuarioCreate(UsuarioBase):
    """
    Dados de criação, incluindo a senha em texto plano, para um novo usuário.

    Attributes:
        senha (str): Senha em texto plano (será hashada no Service/CRUD). Deve ter entre 8 e 72 caracteres.
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
                "email": "test@test.com",
                "senha": "test1234",
            }
        }
    )

# =========================
# Read (Saída)
# =========================
class UsuarioRead(UsuarioBase):
    """
    Formato de resposta da API para Usuário (exclui a senha).

    Attributes:
        id (int): ID único do usuário.
        ativo (bool): Status de ativo/inativo do usuário.
        is_master (bool): Indica se o usuário é o Master/Administrador da empresa.
        empresa (EmpresaUserRead) : Dados da empresa.
    """
    id: int = Field(..., description="ID do usuário")
    ativo: bool = Field(..., description="Status de ativo/inativo")
    is_master: bool = Field(..., description="Define se é o usuário Master da empresa")
    url_perfil: Optional[str] = Field(None, description="URL da foto de perfil")
    empresa: Optional[EmpresaUserRead] = Field(None, description="Dados da empresa do usuario")
    # Nota: data_criacao é comum em retornos, mantive o comentário.

# =========================
# Update (Edição Parcial)
# =========================
class UsuarioUpdate(BaseModel):
    """
    Campos opcionais para edição parcial do usuário (PUT/PATCH).

    Attributes:
        nome (Optional[str]): Novo nome completo.
        email (Optional[EmailStr]): Novo e-mail de login.
        senha (Optional[str]): Nova senha (será hashada, se fornecida).
    """
    nome: Optional[str] = Field(None, max_length=255, description="Novo nome")
    email: Optional[EmailStr] = Field(None, max_length=255, description="Novo e-mail")
    senha: Optional[str] = Field(
        None, 
        min_length=8, 
        description="Nova senha (opcional)"
    )

    model_config = ConfigDict(from_attributes=True)