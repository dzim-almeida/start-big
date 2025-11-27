# ---------------------------------------------------------------------------
# ARQUIVO: funcionario_schema.py
# DESCRIÇÃO: Schemas Pydantic para dados de RH e perfil de funcionário.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List
# Importa os schemas aninhados
from app.schemas.endereco import Endereco, EnderecoRead, EnderecoUpdate
from app.schemas.usuario import UsuarioCreate, UsuarioRead

# =========================
# Schema Base
# =========================
class FuncionarioBase(BaseModel):
    """
    Campos comuns e documentos do funcionário.
    """
    nome: str = Field(..., max_length=255)
    contato: Optional[str] = Field(None, max_length=20)
    # Validação de email aqui pode ser opcional, pois o Usuário já tem
    email: Optional[EmailStr] = Field(None, description="Email de contato do funcionário")

    # Documentos
    # Validação de 11 dígitos estrita para o CPF
    cpf: str = Field(..., pattern=r"^\d{11}$", description="CPF (apenas números)")
    rg: Optional[str] = Field(None, max_length=20)
    carteira_trabalho: Optional[str] = Field(None, max_length=50)
    cnh: Optional[str] = Field(None, max_length=20)

    # Dados Bancários
    banco: Optional[str] = Field(None, max_length=50)
    agencia: Optional[str] = Field(None, max_length=10)
    conta: Optional[str] = Field(None, max_length=20)

    # Filiação / Obs
    mae: Optional[str] = Field(None, max_length=255)
    pai: Optional[str] = Field(None, max_length=255)
    observacao: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(from_attributes=True)

# =========================
# Create (Entrada)
# =========================
class FuncionarioCreate(FuncionarioBase):
    """
    Criação aninhada: inclui os dados de Usuário de acesso e Endereço(s).
    """
    # Aninhamento do schema de criação de Usuário
    usuario: UsuarioCreate = Field(
        ...,
        description="Dados do Usuário de acesso (login e senha) associado ao funcionário."
    )
    
    # Campo obrigatório para Multi-tenancy (empresa à qual o funcionário pertence)
    empresa_id: int = Field(...)

    cargo_id: Optional[int] = Field(None, description="ID do Cargo (Permissões)")

    # Aninhamento do schema de Endereço (lista)
    endereco: Optional[List[Endereco]] = Field(None)

    model_config = ConfigDict(
        # Exemplo de payload mantido
        json_schema_extra={
            "example": {
                "nome": "João Vendedor",
                "cpf": "12345678901",
                "email": "funcionario@empresa.com",
                "usuario": {
                    "nome": "João",
                    "email": "funcionario@empresa.com",
                    "senha": "SenhaForte123!",
                },
                "empresa_id": 1,
                "cargo_id": None,
                "endereco": [{"logradouro": "Rua 1", "cep": "60000-000", "numero": "10", "bairro": "Centro", "cidade": "Fortaleza", "estado": "CE"}]
            }
        }
    )

# =========================
# Read (Saída)
# =========================
class FuncionarioRead(FuncionarioBase):
    """
    Formato de resposta da API para Funcionário, incluindo as relações.
    """
    id: int
    ativo: bool
    cargo_id: Optional[int] 

    # Aninhamento do schema de leitura de Usuário
    usuario: UsuarioRead = Field(
        ...,
        description="Usuário de acesso anexado ao funcionário"
    )
    
    # Aninhamento do schema de leitura de Endereços
    enderecos: Optional[List[EnderecoRead]] = Field(None, alias="enderecos")

# =========================
# Update (Edição Parcial)
# =========================
class FuncionarioUpdate(BaseModel):
    """
    Campos opcionais para atualização parcial do funcionário.
    """
    # Campos simples (opcionais)
    nome: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = Field(None)
    contato: Optional[str] = Field(None)
    cargo_id: Optional[int] = Field(None, description="Atualizar cargo")
    
    # Documentos e Bancários (opcionais)
    rg: Optional[str] = Field(None)
    cnh: Optional[str] = Field(None)
    carteira_trabalho: Optional[str] = Field(None)
    banco: Optional[str] = Field(None)
    agencia: Optional[str] = Field(None)
    conta: Optional[str] = Field(None)
    ativo: Optional[bool] = Field(None)

    # Permite enviar uma lista de atualizações/criações/deleções de endereço
    endereco: Optional[List[EnderecoUpdate]] = Field(None)

    model_config = ConfigDict(from_attributes=True)