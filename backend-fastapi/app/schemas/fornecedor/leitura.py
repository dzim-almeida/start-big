# ---------------------------------------------------------------------------
# ARQUIVO: schemas/fornecedor/leitura.py
# DESCRICAO: Schemas de fornecedor - saida.
# ---------------------------------------------------------------------------

from pydantic import Field
from typing import Optional, List
from app.schemas.endereco import EnderecoRead
from app.schemas.fornecedor.cadastro import FornecedorCreate


# =========================
# Schema Pydantic: FornecedorRead (Leitura/Resposta)
# =========================
class FornecedorRead(FornecedorCreate):
    """
    Schema para formatar os dados de SAÍDA (resposta da API) de um Fornecedor.
    """
    id: int = Field(..., description="ID do fornecedor")
    ativo: bool = Field(..., description="Status do fornecedor")
    endereco: Optional[List[EnderecoRead]] = Field(
        None,
        description="Endereço do fornecedor"
    )
