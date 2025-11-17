# ---------------------------------------------------------------------------
# ARQUIVO: funcionario_schema.py
# DESCRIÇÃO: Schemas Pydantic para validação de dados de Funcionario.
#            Define as estruturas de entrada (Create/Update) e saída (Read).
# ---------------------------------------------------------------------------

from datetime import date
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List
# Importa schemas de Endereço (Assumindo que estão no mesmo path do cliente.py)
from app.schemas.endereco import Endereco, EnderecoRead, EnderecoUpdate

# =========================
# Schema Pydantic: FuncionarioCreate
# =========================
class FuncionarioCreate(BaseModel):
    """
    Schema base com campos comuns para criação/atualização de Funcionário.
    """
    nome: str = Field(
        ...,
        max_length=255,
        description="Nome completo do funcionário"
    )
    email: Optional[EmailStr] = Field(
        None,
        max_length=255,
        description="E-mail de contato (deve ser único se fornecido)"
    )
    contato: Optional[str] = Field(
        None,
        max_length=20,
        description="Telefone de contato"
    )
    observacao: Optional[str] = Field(
        None,
        max_length=500,
        description="Observações internas sobre o funcionário"
    )
    
    # Documentos
    cpf: str = Field(
        ..., # Obrigatório
        pattern=r"^\d{11}$",
        description="CPF com 11 dígitos"
    )
    rg: Optional[str] = Field(
        None,
        max_length=20,
        description="RG do funcionário"
    )
    carteira_trabalho: Optional[str] = Field(
        None,
        max_length=50,
        description="Número da Carteira de Trabalho"
    )
    cnh: Optional[str] = Field(
        None,
        max_length=20,
        description="Número da CNH"
    )
    
    # Hierarquia e Parentesco
    funcao: Optional[str] = Field(
        None,
        max_length=100,
        description="Cargo ou função atual"
    )
    mae: Optional[str] = Field(
        None,
        max_length=255,
        description="Nome completo da mãe"
    )
    pai: Optional[str] = Field(
        None,
        max_length=255,
        description="Nome completo do pai"
    )

    # Dados Bancários
    banco: Optional[str] = Field(
        None,
        max_length=50,
        description="Nome do Banco"
    )
    agencia: Optional[str] = Field(
        None,
        max_length=10,
        description="Número da agência"
    )
    conta: Optional[str] = Field(
        None,
        max_length=20,
        description="Número da conta"
    )
    
    # Endereços (Esperando Endereco de entrada - sem ID)
    endereco: Optional[List[Endereco]] = Field(
        None,
        description="Endereço(s) do funcionário"
    )

    usuario_id: int = Field(
        ...,
        description="ID do usuário de acesso associado (FK 1:1)"
    )

    # Permite que o Pydantic crie instâncias a partir de objetos ORM (SQLAlchemy)
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "nome": "João Pedro Silva",
                "cpf": "98765432101",
                "email": "joao.silva@empresa.com",
                "funcao": "Analista Júnior",
                "carteira_trabalho": "98765-43",
                "rg": "12345678",
                "usuario_id": 1,
                "endereco": [
                    {
                        "logradouro": "Rua das Flores",
                        "numero": "456",
                        "bairro": "Centro",
                        "cidade": "Iguatu",
                        "estado": "CE",
                        "cep": "63500-000"
                    }
                ]
            }
        }
    )

# =========================
# Schema Pydantic: FuncionarioRead (Saída)
# =========================
class FuncionarioRead(FuncionarioCreate):
    """
    Schema para formatar os dados de SAÍDA (resposta da API) de um Funcionário.
    """
    id: int = Field(
        ...,
        description="ID do funcionário (PK)"
    )
    ativo: bool = Field(
        ...,
        description="Status de atividade do funcionário"
    )
    # Sobrescreve 'endereco' para usar o schema 'EnderecoRead' (que inclui ID)
    endereco: Optional[List[EnderecoRead]] = Field(
        None,
        description="Endereço(s) do funcionário"
    )

# =========================
# Schema Pydantic: FuncionarioUpdate (Atualização Parcial)
# =========================
class FuncionarioUpdate(BaseModel):
    """
    Schema para validar os dados de ENTRADA ao ATUALIZAR um
    Funcionário existente (todos os campos são opcionais).
    """
    # Todos os campos são redefinidos como opcionais (None), exceto o endereço
    nome: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = Field(None, max_length=255)
    contato: Optional[str] = Field(None, max_length=20)
    observacao: Optional[str] = Field(None, max_length=500)
    
    # Documentos - Normalmente não editáveis, mas opcionais aqui
    cpf: Optional[str] = Field(None, pattern=r"^\d{11}$")
    rg: Optional[str] = Field(None, max_length=20)
    carteira_trabalho: Optional[str] = Field(None, max_length=50)
    cnh: Optional[str] = Field(None, max_length=20)
    
    # Outros
    funcao: Optional[str] = Field(None, max_length=100)
    mae: Optional[str] = Field(None, max_length=255)
    pai: Optional[str] = Field(None, max_length=255)

    # Dados Bancários
    banco: Optional[str] = Field(None, max_length=50)
    agencia: Optional[str] = Field(None, max_length=10)
    conta: Optional[str] = Field(None, max_length=20)

    # Endereços (Esperando EnderecoUpdate para lidar com IDs)
    endereco: Optional[List[EnderecoUpdate]] = Field(
        None,
        description="Endereço(s) para atualização (deve incluir ID para edição)"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra = {
            "example": {
                "funcao": "Gerente de Filial",
                "email": "joao.editado@empresa.com",
                "endereco": [ 
                    {
                        "id": 1, 
                        "logradouro": "Nova Avenida Principal",
                        "numero": "1234",
                        "cep": "63501-000"
                    }
                ]
            }
        }
    )