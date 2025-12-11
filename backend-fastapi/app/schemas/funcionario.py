# ---------------------------------------------------------------------------
# ARQUIVO: schemas/funcionario_schema.py
# MÓDULO: Schemas Pydantic (DTOs)
# DESCRIÇÃO: Definição de contratos de entrada e saída para Funcionários.
# ---------------------------------------------------------------------------

from datetime import date
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List
from app.schemas.endereco import Endereco, EnderecoRead, EnderecoUpdate
from app.schemas.usuario import UsuarioCreate, UsuarioRead

# ===========================================================================
# SCHEMA BASE
# ===========================================================================

class FuncionarioBase(BaseModel):
    """Atributos comuns do perfil de Funcionário."""
    
    nome: str = Field(..., max_length=255, description="Nome completo.")
    telefone: Optional[str] = Field(None, max_length=20, description="Telefone para contato")
    celular: Optional[str] = Field(None, max_length=20, description="Celular para contato.")
    email: Optional[EmailStr] = Field(None, description="Email corporativo ou pessoal.")

    # Documentos
    cpf: str = Field(..., pattern=r"^\d{11}$", description="CPF (11 dígitos numéricos).")
    rg: Optional[str] = Field(None, max_length=20, description="Registro Geral.")
    carteira_trabalho: Optional[str] = Field(None, max_length=50, description="Número da CTPS.")
    cnh: Optional[str] = Field(None, max_length=20, description="Carteira de Motorista.")
    tipo_contrato: Optional[str] = Field(None, description="Tipo de contrato do funcionário.")
 
    # Financeiro
    banco: Optional[str] = Field(None, max_length=50)
    agencia: Optional[str] = Field(None, max_length=10)
    conta: Optional[str] = Field(None, max_length=20)

    # Pessoal
    data_nascimento: Optional[date] = Field(None, description="Data de nascimento do funcionário.")
    mae: Optional[str] = Field(None, max_length=255, description="Nome da mãe.")
    pai: Optional[str] = Field(None, max_length=255, description="Nome do pai.")
    observacao: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(from_attributes=True)

# ===========================================================================
# CREATE (Entrada)
# ===========================================================================

class FuncionarioCreate(FuncionarioBase):
    """Payload para criação de novo funcionário."""
    
    usuario: UsuarioCreate = Field(..., description="Dados para criar o login do funcionário.")
    cargo_id: Optional[int] = Field(None, description="ID do cargo inicial (opcional).")
    endereco: Optional[List[Endereco]] = Field(None, description="Lista de endereços residenciais.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "João Silva",
                "cpf": "12345678901",
                "usuario": {
                    "nome": "joao.silva",
                    "email": "joao@empresa.com",
                    "senha": "SenhaForte123!"
                },
                "endereco": [
                    {
                        "logradouro": "Rua Teste Unitario",
                        "numero": "123",
                        "cep": "12345-678",
                        "bairro": "Centro",
                        "cidade": "Lab City",
                        "estado": "SP"
                    }
                ]
            }
        }
    )

# ===========================================================================
# READ (Saída)
# ===========================================================================

class FuncionarioRead(FuncionarioBase):
    """Payload de resposta com dados persistidos."""
    
    id: int = Field(..., description="ID único do funcionário.")
    ativo: bool = Field(..., description="Status do cadastro.")
    cargo_id: Optional[int] = Field(None)

    usuario: UsuarioRead = Field(..., description="Dados do usuário de login associado.")
    endereco: Optional[List[EnderecoRead]] = Field(None, description="Endereços vinculados.")

# ===========================================================================
# UPDATE (Edição)
# ===========================================================================

class FuncionarioUpdate(BaseModel):
    """Payload para atualização parcial (PATCH behavior)."""
    
    nome: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = Field(None)
    contato: Optional[str] = Field(None)
    cargo_id: Optional[int] = Field(None)
    
    rg: Optional[str] = Field(None)
    cnh: Optional[str] = Field(None)
    carteira_trabalho: Optional[str] = Field(None)
    
    banco: Optional[str] = Field(None)
    agencia: Optional[str] = Field(None)
    conta: Optional[str] = Field(None)
    
    ativo: Optional[bool] = Field(None)

    endereco: Optional[List[EnderecoUpdate]] = Field(
        None, 
        description="Lista de endereços. Envie ID para editar, sem ID para criar."
    )

    model_config = ConfigDict(from_attributes=True)