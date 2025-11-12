# ---------------------------------------------------------------------------
# ARQUIVO: app/schemas/produto_fotos.py (Presumido)
# DESCRIÇÃO: Define os schemas Pydantic para tipagem dos dados de fotos de
#            produto, especificamente o schema de leitura (retorno da API).
# ---------------------------------------------------------------------------

from fastapi import UploadFile, File, Form # (Importações que podem ser removidas se não usadas no schema)
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class ProdutoFotoRead(BaseModel):
    """
    Schema Pydantic usado para serializar (converter para JSON) os dados
    de uma foto de produto ao serem enviados como resposta da API.
    """
    # =========================
    # Campos (Fields)
    # =========================

    id: int = Field(
        ...,
        description="ID único da foto salva no BD" # Campo de identificação primária (PK)
    )
    produto_id: int = Field(
        ...,
        description="ID único do produto responsável pela imagem" # Chave estrangeira (FK)
    )
    nome_arquivo: str = Field(
        ...,
        max_length=255,
        description="Nome do arquivo carregado"
    )
    url: str = Field(
        ...,
        description="Url do local de salvamento" # Onde a foto pode ser acessada
    )
    principal: bool = Field(
        ...,
        description="Define se a foto é principal"
    )

    # =========================
    # Configuração (Pydantic V2+)
    # =========================
    model_config = ConfigDict(
        from_attributes=True, # Permite que o Pydantic leia atributos de objetos ORM (SQLAlchemy)
        json_schema_extra={
            "example": { # Exemplo de payload para documentação Swagger
                "nome_arquivo": "macarrao.png",
                "url": "http://macarrao.jpg",
                "principal": True,
            }
        }
    )