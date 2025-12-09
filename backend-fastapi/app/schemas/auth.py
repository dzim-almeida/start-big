# ---------------------------------------------------------------------------
# ARQUIVO: auth.py
# DESCRIÇÃO: Schemas Pydantic para requisição e resposta de Login/Autenticação.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict, Field

class UsuarioLogin(BaseModel):
    """
    Schema de entrada para a requisição de login.

    Attributes:
        email (str): E-mail do usuário.
        senha (str): Senha em texto plano do usuário.
    """
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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "teste@gmail.com",
                "senha": "string123"
            }
        }
    )

class UsuarioLoginResponse(BaseModel):
    """
    Schema de saída para a resposta de login (retorna o token JWT).

    Attributes:
        access_token (str): O JWT (JSON Web Token) de curta duração.
        token_type (str): O esquema de autenticação (padrão é "bearer").
        expires_in (int): Tempo de vida (em segundos) do Access Token.
    """
    access_token: str = Field(
        ...,
        description="O JWT de curta duração para acesso à API."
    )
    token_type: str = Field(
        "bearer",
        description="O esquema de autenticação do token."
    )
    expires_in: int = Field(
        ...,
        description="Tempo de vida (em segundos) do Access Token."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900 # 15 minutos
            }
        }
    )