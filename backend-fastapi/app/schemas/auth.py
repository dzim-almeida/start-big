# Modelos Pydantic para Login

from pydantic import BaseModel, ConfigDict, Field  # type: ignore

class UsuarioLogin(BaseModel):
    email: str = Field(
        ...,
        max_length=255,
        description="Email do usuário"
    )
    senha: str = Field(
        ...,
        min_length=8,
        max_length=72,
        description="Senha do usuário"
    )

    # Permite criar instâncias a partir de objetos ORM
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "teste@gmail.com",
                "senha": "string123"
            }
        }
    )

class UsuarioLoginResponse(BaseModel):
    access_token: str = Field(
        ...,
        description="O JWT de curta duração para acesso à API."
    )
    # refresh_token: str = Field(
    #     ...,
    #     description="O JWT de longa duração usado para obter novos access tokens."
    # )
    token_type: str = Field(
        "bearer",
        description="O esquema de autenticação do token."
    )
    expires_in: int = Field(
        ...,
        description="Tempo de vida (em segundos) do Access Token."
    )

    # Permite criar instâncias a partir de objetos ORM
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                # "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh...",
                "token_type": "bearer",
                "expires_in": 900 # 15 minutos
            }
        }
    )
    