# ---------------------------------------------------------------------------
# ARQUIVO: app/schemas/marcenaria/aprovacao.py
# DESCRICAO: O que a API RECEBE para simular, aprovar e desfazer a aprovacao
#            do orcamento de marcenaria (Spec 08A, secoes 6.2 e 6.5).
#
# As saidas sao dicionarios montados no servico, com o recorte de custos da
# 06A (D23): sem `view_custos_marcenaria`, as chaves de custo nem aparecem.
# ---------------------------------------------------------------------------

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.marcenaria.orcamento import AjusteEntrada


class SinalEntrada(BaseModel):
    """O sinal na aprovacao (D15): so entra na OS o que foi RECEBIDO.

    `valor_entrada` da OS e dinheiro que entrou: gravar o combinado como
    recebido faria o cliente pagar menos na entrega se o PIX nunca chegou.
    """
    model_config = ConfigDict(extra="forbid")

    recebido: bool = False
    valor_centavos: Optional[int] = Field(None, ge=0)     # padrao: o sinal calculado
    forma_pagamento_id: Optional[int] = None              # obrigatoria se recebido e sem credito
    usar_credito_cliente: bool = False                    # D16: baixa do saldo de credito


class AprovacaoEntrada(BaseModel):
    """POST /{id}/aprovacao/simular e /{id}/aprovar."""
    model_config = ConfigDict(extra="forbid")

    movel_ids: list[int] = Field(default_factory=list)   # pelo menos um (D9)
    incluir_instalacao: bool = True
    desconto: Optional[AjusteEntrada] = None              # D11: renegociado; ausente = o do orcamento
    sinal: Optional[SinalEntrada] = None                  # so no /aprovar

    @field_validator("movel_ids")
    @classmethod
    def _algum_movel(cls, v):
        if not v:
            raise ValueError("Escolha pelo menos um móvel.")
        if len(set(v)) != len(v):
            raise ValueError("O mesmo móvel aparece duas vezes.")
        return v


class DesfazerEntrada(BaseModel):
    """POST /{id}/desfazer-aprovacao (D20)."""
    model_config = ConfigDict(extra="forbid")

    motivo: str = Field("", validate_default=True)
    destino_sinal: Literal["CREDITO", "DEVOLVIDO"] = "CREDITO"   # o sinal recebido vira credito, ou foi devolvido
    codigo_gerente: Optional[str] = None                         # PIN, quando a loja exige para cancelar OS

    @field_validator("motivo")
    @classmethod
    def _motivo(cls, v):
        limpo = (v or "").strip()
        if not limpo:
            raise ValueError("Informe o motivo para desfazer a aprovação.")
        if len(limpo) > 300:
            raise ValueError("O motivo pode ter até 300 caracteres.")
        return limpo
