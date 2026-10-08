from datetime import datetime
from typing import Optional
from typing import Literal

from pydantic import BaseModel, Field, field_validator

REGRAS_DE_PRECO = ("R1", "R2", "R3")


class ConfiguracaoVendasRead(BaseModel):
    id: int
    empresa_id: int

    permitir_desconto: bool
    desconto_maximo_percent: int
    exigir_cliente_identificado: bool
    valor_minimo_venda: int
    permitir_parcelamento: bool
    parcelas_maximas: int

    # Controle de caixa. Sao lidas pela TELA DE VENDAS, e nao so pela de
    # configuracoes: e por `controlar_caixa` que o PDV decide se mostra o botao
    # do caixa. Sem expor aqui, o frontend nao teria como saber e o caixa
    # apareceria para todo mundo.
    controlar_caixa: bool
    exigir_caixa_aberto: bool
    fechamento_cego: bool
    requer_pin_abrir_caixa: bool
    usar_fila_do_caixa: bool

    # Regras de preço por quantidade (§6.1). Lidas também pelo PDV: é por elas
    # que a linha sabe se mostra a regra aplicada.
    regra_embalagem_avulsas: bool = False
    regra_faixas_quantidade: bool = False
    regra_leve_pague: bool = False
    regra_conflito: str = "MENOR_PRECO"
    regra_ordem: str = "R1,R2,R3"
    bloquear_desconto_com_regra: bool = False

    data_atualizacao: datetime

    model_config = {"from_attributes": True}


class ConfiguracaoVendasUpdate(BaseModel):
    permitir_desconto: Optional[bool] = None
    desconto_maximo_percent: Optional[int] = Field(None, ge=0, le=100)
    exigir_cliente_identificado: Optional[bool] = None
    valor_minimo_venda: Optional[int] = Field(None, ge=0)
    permitir_parcelamento: Optional[bool] = None
    parcelas_maximas: Optional[int] = Field(None, ge=1, le=48)

    controlar_caixa: Optional[bool] = None
    exigir_caixa_aberto: Optional[bool] = None
    fechamento_cego: Optional[bool] = None
    requer_pin_abrir_caixa: Optional[bool] = None
    usar_fila_do_caixa: Optional[bool] = None

    regra_embalagem_avulsas: Optional[bool] = None
    regra_faixas_quantidade: Optional[bool] = None
    regra_leve_pague: Optional[bool] = None
    regra_conflito: Optional[Literal["MENOR_PRECO", "ORDEM"]] = None
    regra_ordem: Optional[str] = Field(None, max_length=20)
    bloquear_desconto_com_regra: Optional[bool] = None

    @field_validator("regra_ordem")
    @classmethod
    def _ordem(cls, v: Optional[str]) -> Optional[str]:
        """As três regras, cada uma uma vez: 'R2,R1,R3'."""
        if v is None:
            return None
        partes = [p.strip().upper() for p in v.split(",") if p.strip()]
        if sorted(partes) != sorted(REGRAS_DE_PRECO):
            raise ValueError("A ordem precisa ter R1, R2 e R3, cada uma uma vez (ex.: R2,R1,R3).")
        return ",".join(partes)
