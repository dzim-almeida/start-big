# Modelos Pydantic para Usuários

from pydantic import BaseModel, ConfigDict, EmailStr, Field # type: ignore

# Base para Usuário, usado para herança nos modelos de entrada e saída
class UsuarioBase(BaseModel):
    nome: str = Field(
        ...,
        max_length=255,
        description="Nome completo do usuário"
    )
    email: EmailStr = Field(
        ...,
        max_length=255,
        description="Email do usuário"
    )

    # Permite criar instâncias a partir de objetos ORM
    model_config = ConfigDict(from_attributes=True)

class UsuarioCreate(UsuarioBase):
    senha: str = Field(
        ...,
        min_length=8,
        max_length=72,
        description="Senha do usuário (mínimo 8 caracteres)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "TestUser",
                "email": "test@test.com",
                "senha": "test1234"
            }
        }
    )

class UsuarioRead(UsuarioBase):
    id: int = Field(
        ...,
        description="ID único do usuário"
    )