# ---------------------------------------------------------------------------
# ARQUIVO: schemas/ordem_servico.py
# DESCRICAO: Schemas Pydantic para Ordens de Serviço (OS).
#
# Hierarquia de schemas:
#   OSItemCreate/Read/Update    → itens de peças e serviços dentro de uma OS
#   OSEquipamentoCreate/Read    → equipamento registrado no ato de abertura
#   OSEquipamentoUpdate         → atualização parcial do equipamento/cliente
#   OSPagamentoCreate/Read      → pagamentos criados apenas ao finalizar
#   OSFotoRead                  → fotos de diagnóstico
#   OrdemServicoBase            → campos comuns a criação e leitura
#   OrdemServicoCreate          → payload de abertura de OS
#   OrdemServicoUpdate          → atualização parcial da OS
#   OrdemServicoRead            → resposta completa com relacionamentos
#   OrdemServicoFinalizar       → payload de finalização com pagamentos
#   OrdemServicoCancelar        → payload de cancelamento
#   OrdemServicoFilterParams    → query params de listagem
#   OrdemServicoQuery           → resposta paginada
#   OrdemServicoStats           → estatísticas agregadas
# ---------------------------------------------------------------------------

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Sequence, List

from app.core.enum import (
    OrdemServicoItemTipo,
    UnidadeMedida,
    OrdemServicoStatus,
    TipoEquipamento,
    OrdemServicoPrioridade
)

from app.schemas.cliente import ClienteRead
from app.schemas.funcionario import FuncionarioRead
from app.schemas.forma_pagamento import FormaPagamentoRead
from app.schemas.pagination import PaginationBase as Pagination

from app.schemas.examples.os_payload import os_example


# ===========================================================================
# ITENS DA OS
# ===========================================================================

class OSItemBase(BaseModel):
    """Payload para adicionar um item (produto ou serviço) a uma OS."""
    tipo: OrdemServicoItemTipo = Field(..., description="Tipo do item: PRODUTO ou SERVICO")
    nome: str = Field(..., max_length=255, min_length=3, description="Descrição do item")
    unidade_medida: UnidadeMedida = Field(..., description="Unidade de medida")
    quantidade: int = Field(..., gt=0, description="Quantidade")
    valor_unitario: int = Field(..., gt=0, description="Valor unitário em centavos")

    model_config = ConfigDict(from_attributes=True)

class OSItemCreate(OSItemBase):
    item_id: Optional[int] = Field(None, description="ID do item no catálogo (produto ou serviço). None para item avulso.")

class OSItemRead(OSItemBase):
    """Resposta de um item de OS. Inclui IDs de referência no catálogo."""
    id: int = Field(..., description="ID único do item na OS")
    ordem_servico_id: int = Field(..., description="ID da OS à qual o item pertence")
    produto_id: Optional[int] = Field(None, description="ID do produto no catálogo (se tipo=PRODUTO)")
    servico_id: Optional[int] = Field(None, description="ID do serviço no catálogo (se tipo=SERVICO)")
    valor_total: int = Field(..., description="Valor total do item (quantidade × valor_unitario) em centavos")


class OSItemUpdate(BaseModel):
    """Payload para atualização parcial de um item de OS. Todos os campos são opcionais."""
    nome: Optional[str] = Field(None, max_length=255, min_length=3, description="Nova descrição")
    unidade_medida: Optional[UnidadeMedida] = Field(None, description="Nova unidade de medida")
    quantidade: Optional[int] = Field(None, gt=0, description="Nova quantidade")
    valor_unitario: Optional[int] = Field(None, gt=0, description="Novo valor unitário em centavos")

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# EQUIPAMENTO DA OS
# ===========================================================================

class OSEquipamentoCreate(BaseModel):
    """Payload para registrar um equipamento ao abrir uma OS."""
    tipo_equipamento: TipoEquipamento = Field(..., description="Tipo do equipamento")
    marca: str = Field(..., max_length=100, description="Marca do equipamento")
    modelo: str = Field(..., max_length=100, description="Modelo do equipamento")
    numero_serie: str = Field(..., max_length=100, description="Número de série")
    imei: str = Field(..., max_length=20, description="IMEI (use '0' para equipamentos sem IMEI)")
    cor: Optional[str] = Field(None, max_length=50, description="Cor do equipamento")

    model_config = ConfigDict(from_attributes=True)


class OSEquipamentoRead(OSEquipamentoCreate):
    """Resposta completa do equipamento de uma OS."""
    id: int = Field(..., description="ID único do equipamento")
    cliente_id: int = Field(..., description="ID do cliente proprietário do equipamento")
    ativo: bool = Field(..., description="Status ativo do equipamento")
    data_criacao: datetime = Field(..., description="Data de cadastro")
    data_atualizacao: datetime = Field(..., description="Data da última atualização")


class OSEquipamentoUpdate(BaseModel):
    """
    Payload para atualização parcial do equipamento de uma OS.
    Permite também trocar o cliente proprietário via cliente_id.
    Somente aplicável em OS com status não-finalizado e não-cancelado.
    """
    tipo_equipamento: Optional[TipoEquipamento] = Field(None, description="Novo tipo de equipamento")
    marca: Optional[str] = Field(None, max_length=100, description="Nova marca")
    modelo: Optional[str] = Field(None, max_length=100, description="Novo modelo")
    numero_serie: Optional[str] = Field(None, max_length=100, description="Novo número de série")
    imei: Optional[str] = Field(None, max_length=20, description="Novo IMEI")
    cor: Optional[str] = Field(None, max_length=50, description="Nova cor")
    cliente_id: Optional[int] = Field(None, description="Novo ID do cliente proprietário do equipamento")

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# PAGAMENTOS DA OS
# ===========================================================================

class OSPagamentoCreate(BaseModel):
    """
    Payload para registrar um pagamento.
    Pagamentos são criados exclusivamente no ato de finalização da OS.
    Uma OS pode ter múltiplos pagamentos (ex: parte em Dinheiro + parte em PIX).
    A soma dos valores deve ser exatamente igual ao valor_total da OS.
    """
    forma_pagamento_id: int = Field(..., description="ID da forma de pagamento do catálogo")
    valor: int = Field(..., gt=0, description="Valor pago nesta forma de pagamento (centavos)")
    parcelas: int = Field(1, ge=1, description="Número de parcelas (mínimo 1)")
    bandeira_cartao: Optional[str] = Field(None, max_length=50, description="Bandeira do cartão (VISA, MASTERCARD, etc.)")
    detalhes: Optional[dict] = Field(None, description="Dados adicionais do pagamento em formato JSON")

    model_config = ConfigDict(from_attributes=True)


class OSPagamentoRead(BaseModel):
    """Resposta de um pagamento de OS. Inclui dados aninhados da forma de pagamento."""
    id: int = Field(..., description="ID único do pagamento")
    ordem_servico_id: int = Field(..., description="ID da OS associada")
    forma_pagamento: FormaPagamentoRead = Field(..., description="Forma de pagamento utilizada")
    valor: int = Field(..., description="Valor pago (centavos)")
    parcelas: int = Field(..., description="Número de parcelas")
    bandeira_cartao: Optional[str] = Field(None, description="Bandeira do cartão")
    detalhes: Optional[dict] = Field(None, description="Dados adicionais")

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# FOTOS DA OS
# ===========================================================================

class OSFotoRead(BaseModel):
    """Resposta de uma foto de diagnóstico de OS."""
    id: int = Field(..., description="ID único da foto")
    ordem_servico_id: int = Field(..., description="ID da OS associada")
    nome_arquivo: str = Field(..., description="Nome original do arquivo enviado")
    url: str = Field(..., description="Caminho/URL do arquivo no servidor")
    data_criacao: datetime = Field(..., description="Data de upload")

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# ORDEM DE SERVICO — BASE, CREATE, UPDATE, READ
# ===========================================================================

class OrdemServicoBase(BaseModel):
    """Campos base compartilhados entre criação e leitura de OS."""

    # Status e prioridade
    prioridade: OrdemServicoPrioridade = Field(..., description="Prioridade da OS: BAIXA, NORMAL, ALTA ou URGENTE")

    # Descrição técnica
    defeito_relatado: str = Field(..., max_length=500, description="Defeito descrito pelo cliente")
    diagnostico: Optional[str] = Field(None, max_length=500, description="Diagnóstico técnico realizado")
    solucao: Optional[str] = Field(None, max_length=500, description="Solução aplicada")

    # Observações operacionais
    senha_aparelho: Optional[str] = Field(None, max_length=100, description="Senha de desbloqueio do aparelho")
    acessorios: Optional[str] = Field(None, max_length=500, description="Acessórios entregues junto ao equipamento")
    condicoes_aparelho: Optional[str] = Field(None, max_length=500, description="Estado físico do aparelho na entrada")
    observacoes: Optional[str] = Field(None, max_length=500, description="Observações gerais")

    # Financeiro
    desconto: Optional[int] = Field(None, ge=0, description="Desconto aplicado em centavos")

    # Prazos e garantia
    garantia: Optional[str] = Field(None, max_length=20, description="Prazo de garantia (ex: '90 dias')")
    data_previsao: Optional[datetime] = Field(None, description="Data prevista para conclusão")

    model_config = ConfigDict(from_attributes=True)


class OrdemServicoCreate(OrdemServicoBase):
    """
    Payload completo para abertura de uma nova OS.
    Cria a OS, o equipamento associado e os itens iniciais em uma única transação.
    """
    # Vínculos
    cliente_id: int = Field(..., description="ID do cliente que trouxe o equipamento")
    funcionario_id: Optional[int] = Field(None, description="ID do funcionário responsável. Se omitido, fica sem responsável.")

    # Dados aninhados criados junto com a OS
    equipamento: OSEquipamentoCreate = Field(..., description="Dados do equipamento a ser cadastrado")
    itens: Sequence[OSItemCreate] = Field(default=[], description="Lista de itens/serviços da OS")

    model_config = ConfigDict(
        json_schema_extra=os_example,
    )


class OrdemServicoUpdate(BaseModel):
    """
    Payload para atualização parcial da OS. Todos os campos são opcionais.
    Não é permitido atualizar OS com status FINALIZADA ou CANCELADA.

    Para alterar o funcionário responsável, informe funcionario_id.
    Para alterar status de forma manual (ex: ABERTA → EM_ANDAMENTO), informe status.
    Transições FINALIZADA e CANCELADA têm endpoints dedicados: /finalizar e /cancelar.
    """
    # Status e prioridade
    prioridade: Optional[OrdemServicoPrioridade] = Field(None, description="Nova prioridade")
    status: Optional[OrdemServicoStatus] = Field(
        None,
        description="Novo status manual. Não use FINALIZADA ou CANCELADA aqui — use /finalizar ou /cancelar."
    )

    # Descrição técnica
    defeito_relatado: Optional[str] = Field(None, max_length=500, description="Novo defeito relatado")
    diagnostico: Optional[str] = Field(None, max_length=500, description="Novo diagnóstico")
    solucao: Optional[str] = Field(None, max_length=500, description="Nova solução")

    # Observações
    senha_aparelho: Optional[str] = Field(None, max_length=100, description="Nova senha do aparelho")
    acessorios: Optional[str] = Field(None, max_length=500, description="Novos acessórios")
    condicoes_aparelho: Optional[str] = Field(None, max_length=500, description="Novas condições do aparelho")
    observacoes: Optional[str] = Field(None, max_length=500, description="Novas observações gerais")

    # Financeiro e datas
    desconto: Optional[int] = Field(None, ge=0, description="Novo desconto em centavos (recalcula valor_total automaticamente)")
    garantia: Optional[str] = Field(None, max_length=20, description="Nova garantia")
    data_previsao: Optional[datetime] = Field(None, description="Nova data prevista")
    funcionario_id: Optional[int] = Field(None, description="ID do novo funcionário responsável")

    model_config = ConfigDict(from_attributes=True)


class OrdemServicoRead(OrdemServicoBase):
    """Resposta completa de uma OS com todos os relacionamentos carregados."""

    # Identificação
    id: int = Field(..., description="ID interno da OS")
    numero_os: str = Field(..., description="Número sequencial público (ex: OS-2026-000001)")

    # Estado
    status: OrdemServicoStatus = Field(..., description="Status atual da OS")

    # Financeiro
    valor_bruto: int = Field(..., description="Soma dos valores dos itens antes do desconto (centavos)")
    valor_total: int = Field(..., description="Valor final após desconto (centavos)")

    # Datas
    data_finalizacao: Optional[datetime] = Field(None, description="Data de finalização efetiva")
    data_criacao: datetime = Field(..., description="Data de abertura da OS")
    data_atualizacao: datetime = Field(..., description="Data da última modificação")

    # Status lógico
    ativo: bool = Field(..., description="Indica se a OS está ativa (False = cancelada/desativada)")

    # Relacionamentos
    cliente: ClienteRead = Field(..., description="Cliente proprietário do equipamento")
    funcionario: Optional[FuncionarioRead] = Field(None, description="Funcionário responsável")
    equipamento: OSEquipamentoRead = Field(..., description="Equipamento em serviço")
    itens: Sequence[OSItemRead] = Field(..., description="Itens e serviços da OS")
    pagamentos: Sequence[OSPagamentoRead] = Field(default=[], description="Pagamentos registrados (populado após finalização)")
    fotos: Sequence[OSFotoRead] = Field(default=[], description="Fotos de diagnóstico da OS")


# ===========================================================================
# AÇÕES DE STATUS
# ===========================================================================

class OrdemServicoFinalizar(BaseModel):
    """
    Payload para finalizar uma OS.

    Regras de negócio:
    - A soma de todos os pagamentos.valor deve ser igual ao valor_total da OS.
    - Cada forma_pagamento_id deve existir e estar ativo no catálogo.
    - A OS não pode estar com status FINALIZADA ou CANCELADA.
    - Uma OS só é finalizada se for integralmente paga.
    """
    solucao: str = Field(..., min_length=5, max_length=500, description="Descrição da solução aplicada")
    observacoes: Optional[str] = Field(None, max_length=500, description="Observações adicionais de finalização")
    desconto: Optional[int] = Field(None, ge=0, description="Desconto final em centavos (recalcula valor_total se informado)")
    pagamentos: List[OSPagamentoCreate] = Field(
        ...,
        min_length=1,
        description="Lista de pagamentos. A soma dos valores deve ser igual ao valor_total da OS."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "solucao": "Substituição do módulo frontal e reconexão do flex do display.",
                "observacoes": "Testado e aprovado pelo cliente.",
                "desconto": 0,
                "pagamentos": [
                    {"forma_pagamento_id": 1, "valor": 45000, "parcelas": 1},
                    {"forma_pagamento_id": 2, "valor": 12000, "parcelas": 1}
                ]
            }
        }
    )


class OrdemServicoCancelar(BaseModel):
    """Payload para cancelar uma OS. O motivo é registrado nas observações da OS."""
    motivo: Optional[str] = Field(None, max_length=500, description="Motivo do cancelamento (acrescentado às observações)")

    model_config = ConfigDict(
        json_schema_extra={"example": {"motivo": "Cliente desistiu do serviço."}}
    )


# ===========================================================================
# FILTROS E PAGINAÇÃO
# ===========================================================================

class OrdemServicoFilterParams(BaseModel):
    """Query parameters para listagem e busca de OS."""
    search: Optional[str] = Field(
        None,
        description="Busca por número da OS, nome ou razão social do cliente"
    )
    status: Optional[OrdemServicoStatus] = Field(
        None,
        description="Filtro por status: ABERTA, EM_ANDAMENTO, AGUARDANDO_PECAS, AGUARDANDO_APROVACAO, AGUARDANDO_RETIRADA, FINALIZADA ou CANCELADA"
    )
    priority_sort: Optional[bool] = Field(
        None,
        description="Se true, ordena por prioridade (URGENTE → ALTA → NORMAL → BAIXA)"
    )


class OrdemServicoQuery(Pagination):
    """Resposta paginada de listagem de OS."""
    filters: OrdemServicoFilterParams
    items: Sequence[OrdemServicoRead]


# ===========================================================================
# ESTATÍSTICAS
# ===========================================================================

class OrdemServicoStats(BaseModel):
    """Estatísticas agregadas das Ordens de Serviço."""
    total: int = Field(..., description="Total de OS no sistema")
    abertas: int = Field(..., description="OS com status ABERTA")
    finalizadas: int = Field(..., description="OS com status FINALIZADA")
    ticket_medio: int = Field(..., description="Valor médio das OS finalizadas em centavos")
