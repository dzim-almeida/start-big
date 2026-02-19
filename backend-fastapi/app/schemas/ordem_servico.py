# ---------------------------------------------------------------------------
# ARQUIVO: schemas/ordem_servico.py
# DESCRICAO: Schemas Pydantic para validacao de entrada e saida da API
#            de Ordens de Servico.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Sequence
from datetime import datetime

from app.core.enum import OrdemServicoStatus, OrdemServicoPrioridade
from app.schemas.pagination import PaginationBase


# ===========================================================================
# SCHEMAS DE ITEM
# ===========================================================================

class OrdemServicoItemCreate(BaseModel):
    """Schema para criar um item dentro de uma OS."""
    servico_id: Optional[int] = Field(None, description="ID do servico do catalogo (nullable para itens customizados)")
    descricao: str = Field(..., max_length=255, description="Descricao do item/servico")
    quantidade: int = Field(..., ge=1, description="Quantidade")
    valor_unitario: int = Field(..., ge=0, description="Valor unitario (centavos)")

    model_config = ConfigDict(from_attributes=True)


class OrdemServicoItemRead(OrdemServicoItemCreate):
    """Schema para leitura de um item de OS."""
    id: int = Field(..., description="ID do item")
    ordem_servico_id: int = Field(..., description="ID da OS")
    valor_total: int = Field(..., description="Valor total (centavos)")


class OrdemServicoItemUpdate(BaseModel):
    """Schema para atualizar um item de OS."""
    id: Optional[int] = Field(None, description="ID do item existente (null para novo item)")
    servico_id: Optional[int] = Field(None, description="ID do servico do catalogo")
    descricao: Optional[str] = Field(None, max_length=255, description="Descricao")
    quantidade: Optional[int] = Field(None, ge=1, description="Quantidade")
    valor_unitario: Optional[int] = Field(None, ge=0, description="Valor unitario (centavos)")

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# SCHEMAS DE PAGAMENTO
# ===========================================================================

class OSPagamentoCreate(BaseModel):
    """Schema para registrar um pagamento na finalizacao."""
    forma_pagamento_id: int = Field(..., description="ID da forma de pagamento")
    valor: int = Field(..., ge=0, description="Valor pago (centavos)")
    parcelas: int = Field(1, ge=1, description="Numero de parcelas")
    bandeira_cartao: Optional[str] = Field(None, max_length=50, description="Bandeira do cartao")
    detalhes: Optional[dict] = Field(None, description="Detalhes adicionais")

    model_config = ConfigDict(from_attributes=True)


class OSPagamentoRead(OSPagamentoCreate):
    """Schema para leitura de um pagamento."""
    id: int = Field(..., description="ID do pagamento")


# ===========================================================================
# SCHEMAS DE FOTO
# ===========================================================================

class OrdemServicoFotoRead(BaseModel):
    """Schema para leitura de uma foto de OS."""
    id: int = Field(..., description="ID da foto")
    ordem_servico_id: int = Field(..., description="ID da OS")
    nome_arquivo: str = Field(..., description="Nome original do arquivo")
    url: str = Field(..., description="URL/caminho do arquivo")
    data_criacao: datetime = Field(..., description="Data de upload")

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# SCHEMAS DE CLIENTE/FUNCIONARIO RESUMO (para leitura aninhada)
# ===========================================================================

class ClienteResumoRead(BaseModel):
    """Resumo do cliente para exibicao na OS."""
    id: int
    tipo: str
    nome: Optional[str] = None
    cpf: Optional[str] = None
    razao_social: Optional[str] = None
    cnpj: Optional[str] = None
    nome_fantasia: Optional[str] = None
    celular: Optional[str] = None
    telefone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FuncionarioResumoRead(BaseModel):
    """Resumo do funcionario para exibicao na OS."""
    id: int
    nome: str
    cargo_id: Optional[int] = None
    ativo: bool

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# SCHEMAS DE ORDEM DE SERVICO
# ===========================================================================

class OrdemServicoCreate(BaseModel):
    """Schema para criar uma nova OS."""
    cliente_id: int = Field(..., description="ID do cliente")
    funcionario_id: Optional[int] = Field(None, description="ID do funcionario responsavel")
    prioridade: Optional[OrdemServicoPrioridade] = Field(OrdemServicoPrioridade.NORMAL, description="Prioridade da OS")
    equipamento: str = Field(..., max_length=255, description="Nome/tipo do equipamento")
    marca: Optional[str] = Field(None, max_length=100, description="Marca do equipamento")
    modelo: Optional[str] = Field(None, max_length=100, description="Modelo do equipamento")
    numero_serie: Optional[str] = Field(None, max_length=100, description="Numero de serie")
    imei: Optional[str] = Field(None, max_length=20, description="IMEI do aparelho")
    cor: Optional[str] = Field(None, max_length=50, description="Cor do equipamento")
    senha_aparelho: Optional[str] = Field(None, max_length=100, description="Senha do aparelho")
    acessorios: Optional[str] = Field(None, description="Acessorios entregues")
    condicoes_aparelho: Optional[str] = Field(None, description="Condicoes fisicas do aparelho")
    defeito_relatado: str = Field(..., description="Defeito relatado pelo cliente")
    diagnostico: Optional[str] = Field(None, description="Diagnostico tecnico")
    observacoes: Optional[str] = Field(None, description="Observacoes gerais")
    data_previsao: Optional[datetime] = Field(None, description="Data prevista para conclusao")
    desconto: Optional[int] = Field(0, ge=0, description="Desconto (centavos)")
    valor_entrada: Optional[int] = Field(0, ge=0, description="Valor de entrada (centavos)")
    forma_pagamento: Optional[str] = Field(None, max_length=50, description="Forma de pagamento")
    garantia: Optional[str] = Field(None, max_length=20, description="Garantia em dias")
    itens: Optional[list[OrdemServicoItemCreate]] = Field(None, description="Itens/servicos da OS")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "cliente_id": 1,
                "equipamento": "iPhone 15 Pro Max",
                "defeito_relatado": "Tela trincada e bateria viciada",
                "prioridade": "NORMAL",
                "itens": [
                    {"descricao": "Troca de tela", "quantidade": 1, "valor_unitario": 35000}
                ]
            }
        }
    )


class OrdemServicoRead(BaseModel):
    """Schema completo para leitura de uma OS (com todos os relacionamentos)."""
    id: int
    numero: str
    cliente_id: int
    funcionario_id: Optional[int] = None
    status: OrdemServicoStatus
    prioridade: OrdemServicoPrioridade
    equipamento: str
    marca: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    imei: Optional[str] = None
    cor: Optional[str] = None
    senha_aparelho: Optional[str] = None
    acessorios: Optional[str] = None
    condicoes_aparelho: Optional[str] = None
    defeito_relatado: str
    diagnostico: Optional[str] = None
    solucao: Optional[str] = None
    observacoes: Optional[str] = None
    valor_total: int
    desconto: int
    valor_entrada: int
    forma_pagamento: Optional[str] = None
    garantia: Optional[str] = None
    data_previsao: Optional[datetime] = None
    data_finalizacao: Optional[datetime] = None
    data_criacao: datetime
    data_atualizacao: datetime
    ativo: bool
    cliente: Optional[ClienteResumoRead] = None
    funcionario: Optional[FuncionarioResumoRead] = None
    itens: list[OrdemServicoItemRead] = []
    pagamentos: list[OSPagamentoRead] = []
    fotos: list[OrdemServicoFotoRead] = []

    model_config = ConfigDict(from_attributes=True)


class OrdemServicoListRead(BaseModel):
    """Schema resumido para listagem de OS (sem itens/pagamentos completos)."""
    id: int
    numero: str
    cliente_id: int
    funcionario_id: Optional[int] = None
    status: OrdemServicoStatus
    prioridade: OrdemServicoPrioridade
    equipamento: str
    defeito_relatado: str
    valor_total: int
    data_previsao: Optional[datetime] = None
    data_criacao: datetime
    ativo: bool
    cliente: Optional[ClienteResumoRead] = None
    funcionario: Optional[FuncionarioResumoRead] = None

    model_config = ConfigDict(from_attributes=True)


class OrdemServicoUpdate(BaseModel):
    """Schema para atualizar uma OS existente."""
    funcionario_id: Optional[int] = None
    status: Optional[OrdemServicoStatus] = None
    prioridade: Optional[OrdemServicoPrioridade] = None
    equipamento: Optional[str] = Field(None, max_length=255)
    marca: Optional[str] = Field(None, max_length=100)
    modelo: Optional[str] = Field(None, max_length=100)
    numero_serie: Optional[str] = Field(None, max_length=100)
    imei: Optional[str] = Field(None, max_length=20)
    cor: Optional[str] = Field(None, max_length=50)
    senha_aparelho: Optional[str] = Field(None, max_length=100)
    acessorios: Optional[str] = None
    condicoes_aparelho: Optional[str] = None
    defeito_relatado: Optional[str] = None
    diagnostico: Optional[str] = None
    solucao: Optional[str] = None
    observacoes: Optional[str] = None
    data_previsao: Optional[datetime] = None
    data_finalizacao: Optional[datetime] = None
    desconto: Optional[int] = Field(None, ge=0)
    valor_entrada: Optional[int] = Field(None, ge=0)
    forma_pagamento: Optional[str] = Field(None, max_length=50)
    garantia: Optional[str] = Field(None, max_length=20)
    itens: Optional[list[OrdemServicoItemUpdate]] = None

    model_config = ConfigDict(from_attributes=True)


class OrdemServicoFinalizar(BaseModel):
    """Schema para finalizar uma OS."""
    solucao: str = Field(..., min_length=1, description="Solucao aplicada (obrigatoria)")
    observacoes: Optional[str] = Field(None, description="Observacoes adicionais")
    pagamentos: list[OSPagamentoCreate] = Field(..., description="Lista de pagamentos")
    desconto: Optional[int] = Field(None, ge=0, description="Desconto (centavos)")

    model_config = ConfigDict(from_attributes=True)


class OrdemServicoCancelar(BaseModel):
    """Schema para cancelar uma OS."""
    motivo: Optional[str] = Field(None, description="Motivo do cancelamento")

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# SCHEMAS DE FILTRO E PAGINACAO
# ===========================================================================

class OrdemServicoFilterParams(BaseModel):
    """Parametros de filtro para busca de OS."""
    buscar: Optional[str] = Field(None, description="Busca por texto")
    status: Optional[str] = Field(None, description="Filtro de status")
    cliente_id: Optional[int] = Field(None, description="Filtro por cliente")
    funcionario_id: Optional[int] = Field(None, description="Filtro por funcionario")

    model_config = ConfigDict(from_attributes=True)


class OrdemServicoQuery(PaginationBase):
    """Resposta paginada de OS."""
    filters: dict = Field(default_factory=dict, description="Filtros aplicados")
    items: Sequence[OrdemServicoListRead]


# ===========================================================================
# SCHEMAS DE ESTATISTICAS
# ===========================================================================

class OrdemServicoStats(BaseModel):
    """Estatisticas agregadas das OS."""
    total: int = Field(..., description="Total de OS")
    abertas: int = Field(..., description="OS abertas")
    em_andamento: int = Field(..., description="OS em andamento")
    finalizadas: int = Field(..., description="OS finalizadas")
    canceladas: int = Field(..., description="OS canceladas")

    model_config = ConfigDict(from_attributes=True)
