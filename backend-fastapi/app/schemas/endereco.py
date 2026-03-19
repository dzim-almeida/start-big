# ---------------------------------------------------------------------------
# ARQUIVO: endereco.py
# DESCRIÇÃO: Schemas Pydantic para validação de dados de Endereço.
#            Define as estruturas de entrada (Endereco), saída (EnderecoRead)
#            e atualização (EnderecoUpdate).
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field, ConfigDict
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
    estado: Optional[State] = Field(None, description="Estado do endereço (UF)")
    cep: str = Field(..., max_length=10, description="CEP do endereço")
    
    # Campo opcional (definido com None)
    complemento: Optional[str] = Field(None, max_length=100, description="Complemento do endereço")

    model_config = ConfigDict(
        from_attributes=True
    )


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

# =========================
# Schema Pydantic: EnderecoUpdate (Atualização)
# =========================
class EnderecoUpdate(BaseModel):
    """
    Schema para atualizar um Endereço existente.
    Todos os campos são opcionais, permitindo atualizações parciais.
    
    O 'id' é obrigatório para identificar qual endereço na lista deve ser
    atualizado (lógica a ser implementada no serviço).
    """
    id: Optional[int] = Field(
        None,
        description="ID do endereço a ser atualizado"
    )
    logradouro: Optional[str] = Field(
        None, max_length=255, description="Logradouro do endereço"
    )
    numero: Optional[str] = Field(
        None, max_length=20, description="Número do endereço"
    )
    bairro: Optional[str] = Field(
        None, max_length=100, description="Bairro do endereço"
    )
    cidade: Optional[str] = Field(
        None, max_length=100, description="Cidade do endereço"
    )
    estado: Optional[State] = Field(
        None, description="Estado do endereço (UF)"
    )
    cep: Optional[str] = Field(
        None, max_length=10, description="CEP do endereço"
    )
    complemento: Optional[str] = Field(
        None, max_length=100, description="Complemento do endereço"
    )