# ---------------------------------------------------------------------------
# ARQUIVO: schemas/endereco/leitura.py
# DESCRICAO: Schemas de endereco - saida.
# ---------------------------------------------------------------------------

from pydantic import Field
from app.schemas.endereco.entrada import Endereco


# =========================
# Schema Pydantic: EnderecoRead (Leitura/Resposta)
# =========================
class EnderecoRead(Endereco):
    """
    Schema para formatar a resposta da API de um Endereço.
    Herda todos os campos de 'Endereco' e adiciona os campos
    gerados pelo banco de dados (como 'id' e 'id_entidade').
    """
    # Campo 'id' do próprio endereço
    id: int = Field(
        ...,
        description="ID do endereço"
    )
    
    # Campo 'id_entidade' da relação polimórfica
    id_entidade: int = Field(
        ...,
        description="ID da entidade (ex: Cliente ID) à qual o endereço pertence"
    )
    
    # Campo 'tipo_entidade' da relação polimórfica
    tipo_entidade: str = Field( # Nota: Poderia usar o Enum EntityType aqui
        ...,
        description="Tipo da entidade (ex: CLIENTE, FORNECEDOR)"
    )
