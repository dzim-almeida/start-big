# ---------------------------------------------------------------------------
# ARQUIVO: schemas/ordem_servico/ordem.py
# DESCRICAO: Schemas da OS - a ordem em si (base, criar, editar, ler).
# ---------------------------------------------------------------------------

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Sequence
from app.core.enum import (
    OrdemServicoStatus,
    OrdemServicoPrioridade,
    SituacaoEquipamento,
)
from app.schemas.cliente import ClienteRead
from app.schemas.funcionario import FuncionarioRead
from app.schemas.forma_pagamento.formas import FormaPagamentoRead
from app.schemas.examples.os_payload import os_example
from app.schemas.ordem_servico.foto import OSFotoRead
from app.schemas.ordem_servico.item import OSItemCreate, OSItemRead
from app.schemas.ordem_servico.objeto import OSEquipamentoCreate, OSEquipamentoRead, OSObjetoCreate, OSObjetoRead
from app.schemas.ordem_servico.pagamento import OSPagamentoRead


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
    senha_aparelho: Optional[str] = Field(None, max_length=100, description="Senha de desbloqueio do aparelho (retrocompatibilidade)")
    acessorios: Optional[str] = Field(None, max_length=500, description="Acessórios entregues (retrocompatibilidade)")
    condicoes_aparelho: Optional[str] = Field(None, max_length=500, description="Estado físico do aparelho (retrocompatibilidade)")
    observacoes: Optional[str] = Field(None, max_length=500, description="Observações gerais")

    # Esquema Dinâmico
    dados_adicionais: Optional[dict] = Field(default_factory=dict, description="Dados adicionais específicos do segmento (JSON)")

    # Financeiro
    desconto: Optional[int] = Field(None, ge=0, description="Desconto aplicado em centavos")
    valor_entrada: Optional[int] = Field(None, ge=0, description="Valor de entrada/adiantamento em centavos")
    forma_pagamento_entrada_id: Optional[int] = Field(None, description="Forma de pagamento usada no adiantamento")
    taxa_entrega: Optional[int] = Field(None, ge=0, description="Taxa de entrega/frete em centavos")
    acrescimo: Optional[int] = Field(None, ge=0, description="Acréscimo de juros/cartão em centavos")

    # Prazos e garantia
    garantia: Optional[str] = Field(None, max_length=20, description="Prazo de garantia (ex: '90 dias')")
    data_previsao: Optional[datetime] = Field(None, description="Data prevista para conclusão")

    model_config = ConfigDict(from_attributes=True)


class OrdemServicoCreate(OrdemServicoBase):
    """
    Payload completo para abertura de uma nova OS.
    Cria a OS, o objeto associado e os itens iniciais em uma única transação.
    """
    # Vínculos
    cliente_id: int = Field(..., description="ID do cliente que trouxe o objeto/equipamento")
    funcionario_id: Optional[int] = Field(None, description="ID do funcionário responsável. Se omitido, fica sem responsável.")

    # Dados aninhados criados junto com a OS
    objeto: Optional[OSObjetoCreate] = Field(None, description="Dados do objeto a ser cadastrado")
    equipamento: Optional[OSEquipamentoCreate] = Field(None, description="Dados do equipamento a ser cadastrado (retrocompatibilidade)")
    itens: Sequence[OSItemCreate] = Field(default_factory=list, description="Lista de itens/serviços da OS")

    # Crédito
    usar_credito_cliente: Optional[bool] = Field(False, description="Se True, deduz valor_entrada do saldo de crédito do cliente")

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
    dados_adicionais: Optional[dict] = Field(None, description="Novos dados adicionais específicos do segmento (JSON)")

    # Financeiro e datas
    desconto: Optional[int] = Field(None, ge=0, description="Novo desconto em centavos (recalcula valor_total automaticamente)")
    valor_entrada: Optional[int] = Field(None, ge=0, description="Novo valor de entrada/adiantamento em centavos")
    forma_pagamento_entrada_id: Optional[int] = Field(None, description="Nova forma de pagamento do adiantamento")
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
    situacao_equipamento: Optional[SituacaoEquipamento] = Field(None, description="Situação final do equipamento: REPARADO, SEM_REPARO ou CONDENADO")
    fase_fabrica: Optional[str] = Field(None, description="Etapa da marcenaria-fábrica. Nulo = OS comum")

    # Financeiro
    valor_bruto: int = Field(..., description="Soma dos valores dos itens antes do desconto (centavos)")
    valor_total: int = Field(..., description="Valor final após desconto (centavos)")
    taxa_entrega: int = Field(0, description="Taxa de entrega/frete (centavos)")
    acrescimo: int = Field(0, description="Acréscimo de juros/cartão (centavos)")
    credito_anterior: Optional[int] = Field(None, description="Crédito efetivo da finalização anterior ao reabrir (centavos)")
    adiantamentos_anteriores: Optional[int] = Field(
        None,
        description="Soma dos adiantamentos das sessões anteriores (centavos). É a parte do crédito que não está em `pagamentos`.",
    )

    # Datas
    data_finalizacao: Optional[datetime] = Field(None, description="Data de finalização efetiva")
    data_criacao: datetime = Field(..., description="Data de abertura da OS")
    data_atualizacao: datetime = Field(..., description="Data da última modificação")

    # Status lógico
    ativo: bool = Field(..., description="Indica se a OS está ativa (False = cancelada/desativada)")

    # Relacionamentos
    cliente: ClienteRead = Field(..., description="Cliente proprietário")
    funcionario: Optional[FuncionarioRead] = Field(None, description="Funcionário responsável")
    objeto: OSObjetoRead = Field(..., description="Objeto de serviço associado")
    equipamento: Optional[OSEquipamentoRead] = Field(None, description="Equipamento em serviço (retrocompatibilidade)")
    itens: Sequence[OSItemRead] = Field(..., description="Itens e serviços da OS")
    pagamentos: Sequence[OSPagamentoRead] = Field(default=[], description="Pagamentos registrados (populado após finalização)")
    # O adiantamento nao vive em `pagamentos` (ver models/ordem_servico.py), entao
    # a forma dele vem por fora. None em OS aberta antes deste campo existir.
    forma_pagamento_entrada: Optional[FormaPagamentoRead] = Field(
        None, description="Forma de pagamento usada no adiantamento"
    )
    fotos: Sequence[OSFotoRead] = Field(default=[], description="Fotos de diagnóstico da OS")
