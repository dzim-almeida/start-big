# ---------------------------------------------------------------------------
# ARQUIVO: services/fornecedor/validacao.py
# DESCRICAO: Fornecedor - excecoes e campos unicos (CNPJ, IE).
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from app.db.crud import fornecedor as fornecedor_crud


# Definição de exceções padrão para reutilização
conflict_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Fornecedor já cadastrado no sistema"
)


not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Fornecedor não encontrado no sistema"
)


# Nota: O Pydantic V2 permite que o 'detail' seja '...' para listas/erros customizados
validation_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail=...
)


# Campos que exigem verificação de unicidade no banco
unique_fields = ["cnpj", "ie"]


# Mapa de validadores mapeando campo -> função de busca no CRUD
validators = {
    "cnpj": fornecedor_crud.get_fornecedor_by_cnpj,
    "ie": fornecedor_crud.get_fornecedor_by_ie
}
