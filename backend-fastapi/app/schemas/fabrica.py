# ---------------------------------------------------------------------------
# ARQUIVO: app/schemas/fabrica.py
# DESCRIÇÃO: Schemas da marcenaria-fábrica (docs/marcenaria-fabrica-plano.md).
# ---------------------------------------------------------------------------

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

UnidadeConsumo = Literal["M2", "M", "UN"]

# Teto do INTEGER: 2.147.483.647 mm² = 2.147 m² por unidade — sobra.
CONSUMO_MAXIMO = 2_147_483_647


class InsumoRead(BaseModel):
    """Como o produto entra no orçamento da fábrica (F1, D2)."""

    model_config = ConfigDict(from_attributes=True)

    produto_id: int
    unidade_medida: Optional[str] = Field(None, description="Unidade do ESTOQUE (a de compra: chapa, rolo, UN).")
    unidade_consumo: Optional[UnidadeConsumo] = Field(None, description="Nulo = o produto não é insumo.")
    consumo_por_unidade: Optional[int] = Field(
        None, description="Rendimento de uma unidade de estoque: mm² (M2), mm (M) ou unidades (UN)."
    )
    sofre_perda: bool = False


class InsumoEscrita(BaseModel):
    """Grava o insumo. `unidade_consumo` nulo desliga: o produto volta a ser comum."""

    unidade_consumo: Optional[UnidadeConsumo] = None
    consumo_por_unidade: Optional[int] = Field(None, ge=1, le=CONSUMO_MAXIMO)
    sofre_perda: bool = False

    @model_validator(mode="after")
    def _coerente(self):
        if self.unidade_consumo is None:
            # Desligar limpa tudo: rendimento sem unidade não significa nada.
            self.consumo_por_unidade = None
            self.sofre_perda = False
        elif self.consumo_por_unidade is None:
            raise ValueError("Informe quanto uma unidade do estoque rende (área da chapa, comprimento do rolo...).")
        return self
