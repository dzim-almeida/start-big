# Arquivo para configurações

# Configurações das variáveis com Pydantic Settings Model
from pydantic_settings import BaseSettings # type: ignore
from pydantic import ConfigDict # type: ignore

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    ALGORITHM: str

    model_config = ConfigDict(env_file=".env")

settings = Settings()