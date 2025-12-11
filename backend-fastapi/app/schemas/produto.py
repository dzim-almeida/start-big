# ---------------------------------------------------------------------------
# ARQUIVO: schemas/produto_schema.py
# MÓDULO: Schemas Pydantic (DTOs)
# ---------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Sequence
from app.schemas.estoque import EstoqueCreate, EstoqueRead, EstoqueUpdate
from app.schemas.produto_fotos import ProdutoFotoRead

class ProdutoCreate(BaseModel):
    """Modelo de entrada para criação de Produto."""
    
    nome: str = Field(..., max_length=255, description="Nome comercial.")
    codigo_produto: str = Field(..., max_length=50, description="Código SKU único.")
    codigo_barras: Optional[str] = Field(None, description="Código de barras para NF-e")
    
    unidade_medida: Optional[str] = Field(None, max_length=10)
    observacao: Optional[str] = Field(None, max_length=500)
    
    categoria: Optional[str] = Field(None, max_length=100)
    marca: Optional[str] = Field(None, max_length=100)
    
    fornecedor_id: Optional[int] = Field(None, description="ID do fornecedor vinculado.")

    estoque: EstoqueCreate = Field(..., description="Dados iniciais de estoque.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "nome": "Café Gourmet 500g",
                "codigo_produto": "CFG-001",
                
                "unidade_medida": "UN",
                "categoria": "Bebidas",
                "estoque": {
                    "valor_varejo": 2999,
                    "quantidade": 100,
                    "quantidade_minima": 20
                }
            }
        }
    )

class ProdutoRead(ProdutoCreate):
    """Modelo de saída (Response) para Produto."""
    
    id: int = Field(..., description="ID único do sistema.")
    fotos: Optional[Sequence[ProdutoFotoRead]] = Field(default=[], description="Galeria de imagens.")
    estoque: EstoqueRead = Field(..., description="Dados atuais de estoque.")
    ativo: bool = Field(..., description="Estado do produto no sistema.")

class ProdutoUpdate(BaseModel):
    """Modelo de entrada para atualização parcial de Produto."""
    
    nome: Optional[str] = Field(None, max_length=255)
    codigo_produto: Optional[str] = Field(None, max_length=50)
    
    unidade_medida: Optional[str] = Field(None, max_length=10)
    observacao: Optional[str] = Field(None, max_length=500)
    
    nota_fiscal: Optional[str] = Field(None, max_length=100)
    categoria: Optional[str] = Field(None, max_length=100)
    marca: Optional[str] = Field(None, max_length=100)
    
    fornecedor_id: Optional[int] = Field(None)

    estoque: Optional[EstoqueUpdate] = Field(None, description="Atualização parcial de estoque.")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "nome": "Café Premium 500g",
                "estoque": {
                    "valor_varejo": 3500
                }
            }
        }
    )