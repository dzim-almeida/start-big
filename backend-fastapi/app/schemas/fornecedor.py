# ---------------------------------------------------------------------------
# ARQUIVO: schemas/fornecedor.py
# DESCRIÇÃO: Schemas Pydantic para validação de dados de Fornecedor.
#            Define as estruturas de entrada (Create/Update) e saída (Read).
# ---------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List # Corrigido: 'list' para 'List'

# Importa os schemas de Endereço necessários
from app.schemas.endereco import Endereco, EnderecoRead, EnderecoUpdate

# =========================
# Schema Pydantic: FornecedorCreate (Criação)
# =========================
class FornecedorCreate(BaseModel):
    """
    Schema para validar os dados de ENTRADA ao criar um novo Fornecedor.
    """
    nome: str = Field(
        ..., # Indica que o campo é obrigatório
        max_length=255,
        description="Nome da empresa fornecedora"
    )
    cnpj: str = Field(
        ..., # Obrigatório
        max_length=14,
        pattern=r"^\d{14}$", # Adicionada validação de 14 dígitos
        description="CNPJ da empresa fornecedora (apenas números)"
    )
    nome_fantasia: Optional[str] = Field(
        None,
        max_length=255,
        description="Nome fantasia da empresa fornecedora"
    )
    ie: Optional[str] = Field(
        None,
        max_length=14,
        description="Inscrição Estadual do fornecedor"
    )
    telefone: Optional[str] = Field(
        None,
        description="Telefone para contato"
    )
    celular: Optional[str] = Field(
        None,
        description="Celular para contato"
    ),
    email: Optional[str] = Field(
        None,
        description="Email para contato"
    )
    representante: Optional[str] = Field(
        None,
        description="Nome do representante da empresa fornecedora"
    )
    # Na criação, espera uma lista de schemas 'Endereco' (sem ID)
    endereco: Optional[List[Endereco]] = Field(
        None,
        description="Endereço da empresa fornecedora"
    )

    # Configuração do Pydantic
    model_config = ConfigDict(
        from_attributes=True, # Permite criar a partir de objetos ORM
        json_schema_extra={ # Define um exemplo para a documentação (Swagger)
            "example": {
                "nome": "Distribuidora de Componentes Eletrônicos LTDA",
                "cnpj": "72345734000132",
                "nome_fantasia": "BigTech Componentes",
                "ie": "123456789012",
                "telefone": "8535667788",
                "representante": "Mauro Filho",
                "endereco": [
                    {
                        "logradouro": "Rua dos Fornecedores",
                        "numero": "1000",
                        "complemento": "Galpão 2",
                        "bairro": "Distrito Industrial",
                        "cidade": "Joinville",
                        "estado": "SC",
                        "cep": "89200-000"
                    }
                ],
            }
        }
    )

# =========================
# Schema Pydantic: FornecedorRead (Leitura/Resposta)
# =========================
class FornecedorRead(FornecedorCreate):
    """
    Schema para formatar os dados de SAÍDA (resposta da API) de um Fornecedor.
    Herda todos os campos de FornecedorCreate e adiciona o ID.
    """
    id: int = Field(
        ..., # Obrigatório na resposta
        description="ID do fornecedor"
    )
    ativo: bool = Field(
        ...,
        description="Detalhe do status do fornecedor"
    )
    # Sobrescreve 'endereco' para usar o schema 'EnderecoRead' (que inclui ID)
    endereco: Optional[List[EnderecoRead]] = Field(
        None, 
        description="Endereço da empresa fornecedora"
    )

# =========================
# Schema Pydantic: FornecedorUpdate (Atualização)
# =========================
class FornecedorUpdate(BaseModel):
    """
    Schema para ATUALIZAR um fornecedor existente.
    Todos os campos são opcionais, permitindo atualizações parciais (PATCH).
    """
    nome: Optional[str] = Field(
        None,  # Alterado para None (opcional)
        max_length=255,
        description="Nome da empresa fornecedora"
    )
    cnpj: Optional[str] = Field(
        None,  # Alterado para None (opcional)
        max_length=14,
        pattern=r"^\d{14}$",
        description="CNPJ da empresa fornecedora"
    )
    nome_fantasia: Optional[str] = Field(
        None,
        max_length=255,
        description="Nome fantasia da empresa fornecedora"
    )
    ie: Optional[str] = Field(
        None,
        max_length=14,
        description="Inscrição Estadual do fornecedor"
    )
    # Na atualização, espera uma lista de schemas 'EnderecoUpdate'
    endereco: Optional[List[EnderecoUpdate]] = Field(
        None,
        description="Endereço da empresa fornecedora"
    )

    # Configuração do Pydantic
    model_config = ConfigDict(
        from_attributes=True, # Permite ler de objetos ORM
        json_schema_extra={ # Exemplo de atualização parcial
            "example": {
                "nome_fantasia": "Novo Nome Fantasia Tech",
                "ie": "123456789"
            }
        }
    )