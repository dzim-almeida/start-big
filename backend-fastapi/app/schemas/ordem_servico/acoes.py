# ---------------------------------------------------------------------------
# ARQUIVO: schemas/ordem_servico/acoes.py
# DESCRICAO: Schemas da OS - payloads de finalizar, cancelar e reabrir.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from app.core.enum import (
    SituacaoEquipamento,
)
from app.schemas.ordem_servico.pagamento import OSPagamentoCreate


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
    situacao_equipamento: Optional[SituacaoEquipamento] = Field(None, description="Situação final do equipamento: REPARADO, SEM_REPARO ou CONDENADO")
    garantia: Optional[str] = Field(None, max_length=20, description="Prazo de garantia do serviço (ex: '90 dias', '6 meses')")
    solucao: Optional[str] = Field(None, max_length=500, description="Descrição da solução aplicada")
    observacoes: Optional[str] = Field(None, max_length=500, description="Observações adicionais de finalização")
    desconto: Optional[int] = Field(None, ge=0, description="Desconto final em centavos (recalcula valor_total se informado)")
    valor_entrada: Optional[int] = Field(None, ge=0, description="Valor de entrada/adiantamento em centavos (abatido do valor a pagar)")
    taxa_entrega: Optional[int] = Field(None, ge=0, description="Taxa de entrega/frete em centavos")
    acrescimo: Optional[int] = Field(None, ge=0, description="Acréscimo de juros/cartão em centavos")
    pagamentos: List[OSPagamentoCreate] = Field(
        default=[],
        description="Lista de pagamentos. A soma dos valores deve ser igual ao valor_total da OS."
    )
    zerar_adiantamento: Optional[bool] = Field(
        False,
        description="Se True, o adiantamento foi devolvido em dinheiro. Se False, vira crédito para o cliente (apenas para SEM_REPARO/CONDENADO)."
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
    zerar_adiantamento: Optional[bool] = Field(False, description="Se True, zera o valor_entrada (adiantamento devolvido ao cliente)")
    codigo_gerente: Optional[str] = Field(None, description="PIN do gerente para aprovar cancelamento")

    model_config = ConfigDict(
        json_schema_extra={"example": {"motivo": "Cliente desistiu do serviço.", "zerar_adiantamento": True}}
    )


class OrdemServicoReabrir(BaseModel):
    """Payload para reabrir uma OS."""
    codigo_gerente: Optional[str] = Field(None, description="PIN do gerente para aprovar reabertura")
    cliente_pagou: bool = Field(
        True,
        description=(
            "Se o cliente já pagou o valor da finalização anterior. True (padrão): o "
            "valor pago é preservado como crédito da OS e abatido do novo total. False: "
            "o pagamento não era real (ex.: reaberta na hora, antes de o cliente pagar) — "
            "os pagamentos são apagados e a OS recobra o valor cheio."
        ),
    )
