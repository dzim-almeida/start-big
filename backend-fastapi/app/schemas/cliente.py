# ---------------------------------------------------------------------------
# ARQUIVO: cliente.py
# DESCRIÇÃO: Schemas Pydantic para validação de dados de Cliente.
#            Define as estruturas de entrada (Create/Update) e saída (Read)
#            para Clientes Pessoa Física (PF) e Pessoa Jurídica (PJ).
# ---------------------------------------------------------------------------

from datetime import date
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List, Annotated, Union, Literal
# Importa Enums necessários
from app.core.enum import Gender, ClientType
# Importa schemas de Endereço
from app.schemas.endereco import Endereco, EnderecoRead

# =========================
# Schema Pydantic: ClienteBase
# =========================
class ClienteBase(BaseModel):
    """
    Schema base com campos comuns a todos os tipos de clientes (PF e PJ).
    """
    email: Optional[EmailStr] = Field(
        None,
        max_length=255,
        description="Email do cliente"
    )
    contato: Optional[str] = Field(
        None,
        max_length=255, # Nota: Pode ser melhor validar como telefone (ex: max_length=20)
        description="Telefone de contato"
    )
    observacoes: Optional[str] = Field(
        None,
        max_length=500,
        description="Observações sobre o cliente"
    )
    
    # Na criação/atualização, espera uma lista de schemas 'Endereco' (sem ID)
    endereco: Optional[List[Endereco]] = Field(
        None,
        description="Endereço(s) do cliente"
    )

    # Permite que o Pydantic crie instâncias a partir de objetos ORM (SQLAlchemy)
    model_config = ConfigDict(from_attributes=True)

# =========================
# Schemas Pessoa Física (PF)
# =========================
class ClientePFCreate(ClienteBase):
    """
    Schema para validar os dados de ENTRADA ao criar um
    novo Cliente Pessoa Física. Herda os campos comuns de ClienteBase.
    """
    nome: str = Field(
        ..., # Indica que o campo é obrigatório
        max_length=255,
        description="Nome completo do cliente"
    )
    cpf: str = Field(
        ..., # Obrigatório
        pattern=r"^\d{11}$", # Validação de formato (11 dígitos numéricos)
        description="CPF com 11 dígitos"
    )
    rg: Optional[str] = Field(
        None,
        pattern=r"^\d{5,20}$",
        description="RG com 5 a 20 dígitos"
    )
    genero: Optional[Gender] = Field(
        None,
        description="Gênero do cliente"
    )
    data_nascimento: Optional[date] = Field(
        None,
        description="Data de nascimento do cliente"
    )

    # Exemplo para documentação OpenAPI (Swagger)
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "João Pedro Silva",
                "cpf": "98765432101",
                "rg": "12345678",
                "genero": "MASCULINO",
                "data_nascimento": "1995-12-15",
                "email": "joao.silva@meu-pdv.com",
                "contato": "11987654321",
                "observacoes": "Cliente novo, aceita e-mail marketing.",
                "endereco": [
                    {
                        "logradouro": "Rua das Flores",
                        "numero": "456A",
                        "complemento": "Casa",
                        "bairro": "Jardim América",
                        "cidade": "Campinas",
                        "estado": "SP",
                        "cep": "13010-000"
                    }
                ]
            }
        }
    )

class ClientePFRead(ClientePFCreate):
    """
    Schema para formatar os dados de SAÍDA (resposta da API)
    de um Cliente Pessoa Física.
    
    Herda de ClientePFCreate para incluir TODOS os campos (base e PF).
    """
    id: int = Field(
        ..., # Obrigatório na resposta
        description="ID do cliente"
    )
    # Define o valor literal esperado para o campo 'tipo'
    tipo: Literal[ClientType.PF] = Field(
        default=ClientType.PF, # Garante que o valor padrão seja consistente
        description="Tipo do cliente (PF)"
    )
    # Sobrescreve 'endereco' para usar o schema 'EnderecoRead' (que inclui ID)
    endereco: Optional[List[EnderecoRead]] = Field(
        None,
        description="Endereco do cliente"
    )

class ClientePFUpdate(ClienteBase):
    """
    Schema para validar os dados de ENTRADA ao ATUALIZAR um
    Cliente Pessoa Física existente. TODOS os campos são opcionais,
    EXCETO 'tipo' que é necessário para a discriminação da Union.
    """
    # Campo 'tipo' obrigatório para o discriminator funcionar na entrada
    tipo: Literal[ClientType.PF] = Field(
        # default=ClientType.PF, # Default não é necessário se for obrigatório
        description="Tipo do cliente (PF)"
    )

    # Campos específicos de PF agora são opcionais
    nome: Optional[str] = Field(
        None, # <-- Default None o torna opcional
        max_length=255,
        description="Novo nome completo do cliente"
    )
    cpf: Optional[str] = Field( # Nota: CPF geralmente não é editável
        None,
        pattern=r"^\d{11}$",
        description="Novo CPF"
    )
    rg: Optional[str] = Field(
        None,
        pattern=r"^\d{5,20}$",
        description="Novo RG do cliente"
    )
    genero: Optional[Gender] = Field(
        None,
        description="Novo gênero do cliente"
    )
    data_nascimento: Optional[date] = Field(
        None,
        description="Nova data de nascimento do cliente"
    )

    # Exemplo para documentação OpenAPI (Swagger) mostrando atualização parcial
    model_config = ConfigDict(
        json_schema_extra= {
            "example": {
                "tipo": "PF", # Deve incluir o tipo na atualização
                "nome": "João Pedro Silva Santos", # Exemplo de alteração
                "email": "joao.silva.novo@meu-pdv.com",
                "contato": "11988887777",
                "observacoes": "Cliente VIP.",
                "endereco": [ # Exemplo: substituindo a lista de endereços
                    {
                        "logradouro": "Nova Rua",
                        "numero": "789",
                        "complemento": None,
                        "bairro": "Novo Bairro",
                        "cidade": "Campinas",
                        "estado": "SP",
                        "cep": "13011-000"
                    }
                ]
                # CPF, RG, genero, data_nascimento não enviados = não alterados
            }
        }
    )

# =========================
# Schemas Pessoa Jurídica (PJ)
# =========================
class ClientePJCreate(ClienteBase):
    """
    Schema para validar os dados de ENTRADA ao criar um
    novo Cliente Pessoa Jurídica. Herda os campos comuns de ClienteBase.
    """
    razao_social: str = Field(
        ..., # Obrigatório
        max_length=255,
        description="Razão social do cliente jurídico"
    )
    cnpj: str = Field(
        ..., # Obrigatório
        pattern=r"^\d{14}$", # Validação de formato (14 dígitos numéricos)
        description="CPNJ com 14 dígitos"
    )
    nome_fantasia: str = Field(
        ..., # Obrigatório
        max_length=255,
        description="Nome fantasia do cliente jurídico"
    )
    ie: Optional[str] = Field(
        None,
        pattern=r"^\d{9,14}$",
        description="Número de inscrição estadual do cliente jurídico"
    )
    responsavel: Optional[str] = Field(
        None,
        max_length=255,
        description="Nome do responsável pela empresa"
    )

    # Exemplo para documentação OpenAPI (Swagger)
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "razao_social": "Minha Empresa de Tecnologia LTDA",
                "cnpj": "12345678000199",
                "nome_fantasia": "Tech Solutions",
                "ie": "123456789",
                "responsavel": "Ana Gerente",
                "email": "contato@techsolutions.com",
                "contato": "1155554444",
                "observacoes": "Primeiro contato feito na feira de tecnologia.",
                "endereco": [
                    {
                        "logradouro": "Avenida das Nações",
                        "numero": "1001",
                        "complemento": "Andar 15, Sala 1502",
                        "bairro": "Distrito Empresarial",
                        "cidade": "São Paulo",
                        "estado": "SP",
                        "cep": "04578-000"
                    }
                ]
            }
        }
    )

class ClientePJRead(ClientePJCreate):
    """
    Schema para formatar os dados de SAÍDA (resposta da API)
    de um Cliente Pessoa Jurídica.
    
    Herda de ClientePJCreate para incluir TODOS os campos (base e PJ).
    """
    id: int = Field(
        ..., # Obrigatório na resposta
        description="ID do cliente"
    )
    # Define o valor literal esperado para o campo 'tipo'
    tipo: Literal[ClientType.PJ] = Field(
        default=ClientType.PJ, # Garante que o valor padrão seja consistente
        description="Tipo do cliente (PJ)"
    )
    
    # Sobrescreve 'endereco' para usar o schema 'EnderecoRead' (que inclui ID)
    endereco: Optional[List[EnderecoRead]] = Field(
        None,
        description="Endereco do cliente"
    )

class ClientePJUpdate(ClienteBase):
    """
    Schema para validar os dados de ENTRADA ao ATUALIZAR um
    Cliente Pessoa Jurídica existente. TODOS os campos são opcionais,
    EXCETO 'tipo' que é necessário para a discriminação da Union.
    """
    # Campo 'tipo' obrigatório para o discriminator funcionar na entrada
    tipo: Literal[ClientType.PJ] = Field(
        # default=ClientType.PJ, # Default não é necessário se for obrigatório
        description="Tipo do cliente (PJ)"
    )

    # Campos específicos de PJ agora são opcionais
    razao_social: Optional[str] = Field(
        None,
        max_length=255,
        description="Nova razão social do cliente jurídico"
    )
    cnpj: Optional[str] = Field( # Nota: CNPJ geralmente não é editável
        None,
        pattern=r"^\d{14}$",
        description="Novo CNPJ")
    nome_fantasia: Optional[str] = Field(
        None,
        max_length=255,
        description="Novo nome fantasia do cliente jurídico"
    )
    ie: Optional[str] = Field(
        None,
        pattern=r"^\d{9,14}$",
        description="Novo número de inscrição estadual"
    )
    responsavel: Optional[str] = Field(
        None,
        max_length=255,
        description="Novo nome do responsável pela empresa"
    )

    # Exemplo para documentação OpenAPI (Swagger) mostrando atualização parcial
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "tipo": "PJ", # Deve incluir o tipo na atualização
                "razao_social": "Minha Empresa de Tecnologia S.A.", # Exemplo de alteração
                "nome_fantasia": "Tech Solutions Global",
                "responsavel": "Novo Responsável",
                "email": "financeiro@techsolutions.com",
                "contato": "11977776666",
                "observacoes": "Contrato renovado.",
                # CNPJ, IE, Endereco não enviados = não alterados
            }
        }
    )

# =================================
# Uniões Discriminadas (Polimorfismo)
# =================================
ClienteRead = Annotated[
    Union[ClientePFRead, ClientePJRead], # Define que a resposta pode ser PF ou PJ
    Field(discriminator="tipo") # Usa o campo 'tipo' para determinar qual schema usar
]

ClienteUpdate = Annotated[
    Union[ClientePFUpdate, ClientePJUpdate], # Define que a entrada pode ser PF ou PJ
    Field(discriminator="tipo") # Usa o campo 'tipo' para validar o schema correto
]