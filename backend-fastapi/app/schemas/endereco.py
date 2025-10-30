# ---------------------------------------------------------------------------
# ARQUIVO: endereco.py
# DESCRIÇÃO: Schemas Pydantic para validação de dados de Endereço.
#            Define as estruturas de entrada (Endereco) e saída (EnderecoRead).
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field
from typing import Optional
from app.core.enum import State  # Importa o Enum de Estados (UF)

# =========================
# Schema Pydantic: Endereco (Base/Criação)
# =========================
class Endereco(BaseModel):
    """
    Schema base para um Endereço.
    Usado para validar os dados de um novo endereço ao criar uma entidade (ex: Cliente).
    """
    # Campos obrigatórios (definidos com ...)
    logradouro: str = Field(..., max_length=255, description="Logradouro do endereço")
    numero: str = Field(..., max_length=20, description="Número do endereço")
    bairro: str = Field(..., max_length=100, description="Bairro do endereço")
    cidade: str = Field(..., max_length=100, description="Cidade do endereço")
    estado: State = Field(..., description="Estado do endereço (UF)")
    cep: str = Field(..., max_length=10, description="CEP do endereço")
    
    # Campo opcional (definido com None)
    complemento: Optional[str] = Field(None, max_length=100, description="Complemento do endereço")

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
        description="Id da entidade (ex: Cliente ID) à qual o endereço pertence"
    )
    
    # Campo 'tipo_entidade' da relação polimórfica
    tipo_entidade: str = Field( # Nota: Poderia usar o Enum EntityType aqui (ex: tipo_entidade: EntityType = Field(...))
        ...,
        description="Tipo da entidade (ex: CLIENTE, FORNECEDOR)"
    )