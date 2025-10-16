# ---------------------------------------------------------------------------
# ARQUIVO: config.py
# DESCRIÇÃO: Centraliza as configurações da aplicação, carregando variáveis
#            de ambiente de forma segura e validada.
# ---------------------------------------------------------------------------

from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    """
    Define as configurações da aplicação que serão carregadas de variáveis de ambiente.
    Utiliza o Pydantic para validar os tipos de dados de cada variável.
    """

    # URL de conexão com o banco de dados. Ex: "sqlite:///./pdv.db"
    DATABASE_URL: str

    # Chave secreta para a codificação de tokens JWT.
    SECRET_KEY: str

    # Tempo de expiração do token de acesso em minutos.
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Algoritmo utilizado para assinar o token JWT.
    ALGORITHM: str

    # Configuração para o Pydantic carregar as variáveis de um arquivo .env
    model_config = ConfigDict(env_file=".env")


# Cria uma instância única das configurações que será importada em outros módulos.
settings = Settings()
