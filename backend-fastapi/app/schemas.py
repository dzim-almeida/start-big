# Modelos Pydantic para entrada/saída de dados

from pydantic import BaseModel, ConfigDict # Modelo de entrada do Pydantic
from typing import Optional # Tipagem: opcional

# Herda de BaseModel do Pydantic para validação
class Produto(BaseModel):
    nome: str   
    preco: float
    codigo_barras: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "nome": "Carregador Waidi",
                "preco": 15.90,
                "codigo_barras": "98766544334566"
            }
        }
    )