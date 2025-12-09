# ---------------------------------------------------------------------------
# ARQUIVO: app/core/config.py
# DESCRIÇÃO: Configurações globais da aplicação via variáveis de ambiente.
# ---------------------------------------------------------------------------

from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    """
    Carrega e valida as variáveis de ambiente (.env).
    """
    # Banco de Dados
    DATABASE_URL: str

    # Segurança (JWT)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = ConfigDict(env_file=".env")

# Instância única (Singleton)
settings = Settings()