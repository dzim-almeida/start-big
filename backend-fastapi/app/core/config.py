# Arquivo para configurações

# Configurações das variáveis com Pydantic Settings Model
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str

    class Config:
        env_file = ".env"

settings = Settings()