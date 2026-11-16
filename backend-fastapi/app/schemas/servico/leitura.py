# ---------------------------------------------------------------------------
# ARQUIVO: schemas/servico/leitura.py
# DESCRICAO: Schemas de servico - saida e estatisticas.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field
from app.schemas.servico.cadastro import ServicoCreate


# =========================
# Schema: Ler Serviço
# =========================
class ServicoRead(ServicoCreate):
    """
    Schema usado para formatar os dados ao **ler** (retornar) um serviço.
    Herda os campos de 'ServicoCreate' (descricao, valor) e adiciona o 'id'.
    """
    id: int = Field(
        ..., # O ID é sempre esperado em uma resposta de leitura
        description="ID único de cada serviço."
    )

    ativo: bool = Field(
        ...,
        description="Status de persistência do produto."
    )


# =========================
# Schema: Estatísticas
# =========================
class ServicoStats(BaseModel):
    """Estatísticas agregadas dos serviços."""
    total: int = Field(..., description="Total de serviços cadastrados")
    ativos: int = Field(..., description="Serviços ativos")
    inativos: int = Field(..., description="Serviços inativos")
    media_valor: int = Field(..., description="Valor médio dos serviços (em centavos)")
