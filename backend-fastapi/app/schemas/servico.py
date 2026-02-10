# ---------------------------------------------------------------------------
# ARQUIVO: schemas/servico.py
# DESCRIÇÃO: Schemas Pydantic (modelos de dados) para validação de
#            entrada (Create/Update) e saída (Read) da API de Serviços.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Sequence
from app.schemas.pagination import PaginationBase as Pagination

# =========================
# Schema: Criar Serviço
# =========================
class ServicoCreate(BaseModel):
    """
    Schema usado para validar os dados ao **criar** um novo serviço.
    Define os campos obrigatórios no corpo da requisição POST.
    """
    descricao: str = Field(
        ..., # '...' indica que o campo é obrigatório
        max_length=255,
        description="Descrição do serviço disponibilizado."
    )

    valor: int = Field(
        ..., # Campo obrigatório
        description="Valor do serviço ofertado (em centavos)."
    )

    # Configurações do modelo Pydantic
    model_config = ConfigDict(
        from_attributes=True, # Permite mapear de atributos de objetos (ex: SQLAlchemy)
        json_schema_extra={
            # Define um exemplo para a documentação da API (Swagger/OpenAPI)
            "example": {
                "descricao": "Troca de tela do Iphone 16",
                "valor": 75049 # Exemplo de valor em centavos
            }
        }
    )

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
    
    # Nota: O 'model_config' e o 'example' são herdados de ServicoCreate
    # e podem ser sobrescritos aqui se necessário.

class ServicoQuery(BaseModel):
    servicos: Sequence[ServicoRead]
    pagination: Pagination = Field(
        ...,
        description="Informações sobre paginação"
    )

    model_config = ConfigDict(
        from_attributes=True,
    )

# =========================
# Schema: Atualizar Serviço
# =========================
class ServicoUpdate(BaseModel):
    """
    Schema usado para validar os dados ao **atualizar** um serviço (PUT/PATCH).
    Todos os campos são opcionais, permitindo atualizações parciais.
    """
    descricao: Optional[str] = Field(
        None, # Valor padrão 'None', tornando o campo opcional
        max_length=255,
        description="Descrição do serviço disponibilizado."
    )

    valor: Optional[int] = Field(
        None, # Valor padrão 'None', tornando o campo opcional
        description="Valor do serviço ofertado (em centavos)."
    )

    # Configurações do modelo Pydantic
    model_config = ConfigDict(
        from_attributes=True, # Permite mapear de atributos de objetos
        json_schema_extra={
            # Exemplo de payload para a documentação (atualização parcial)
            "example": {
                "valor": 80049
            }
        }
    )