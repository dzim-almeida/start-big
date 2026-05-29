# ---------------------------------------------------------------------------
# ARQUIVO: cargo_schema.py
# DESCRIÇÃO: Schemas Pydantic para gestão de Cargos e Permissões.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any

# =========================
# Schema Base
# =========================
class CargoBase(BaseModel):
    """
    Campos comuns: nome e o dicionário de permissões.
    """
    nome: str = Field(
        ..., 
        max_length=50, 
        description="Nome do cargo (ex: Gerente, Caixa)"
    )
    # Permissões é um Dict genérico, ex: {"venda": true, "relatorio": false}
    permissoes: Dict[str, Any] = Field(
        default_factory=dict, # Usar default_factory=dict para valores mutáveis
        description="Objeto JSON definindo as regras de acesso"
    )
    
    model_config = ConfigDict(from_attributes=True)

# =========================
# Create (Entrada)
# =========================
class CargoCreate(CargoBase):
    """
    Estrutura para a criação de um novo cargo.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "Gerente",
                "permissoes": {
                    "funcionario": True,
                    "cargo": True
                }
            }
        }
    )

# =========================
# Read (Saída)
# =========================
class CargoRead(CargoBase):
    """
    Formato de resposta da API para Cargo.
    """
    id: int = Field(..., description="ID do cargo")
    empresa_id: int = Field(..., description="ID da empresa vinculada")

# =========================
# Update (Edição Parcial)
# =========================
class CargoUpdate(BaseModel):
    """
    Campos opcionais para edição de cargo.
    """
    nome: Optional[str] = Field(None, max_length=50)
    # Permite atualizar todo o dicionário de permissões ou deixar nulo
    permissoes: Optional[Dict[str, Any]] = Field(None)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "nome": "Caixa Sênior",
                "permissoes": {"desconto_maximo": 10, "cancelar_venda": True}
            }
        }
    )