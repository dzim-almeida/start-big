# ---------------------------------------------------------------------------
# ARQUIVO: schemas/produto_regra_preco.py
# MÓDULO: Schemas Pydantic — Regras de preço por quantidade do produto (R2, R3)
# ---------------------------------------------------------------------------
"""
Chegam e saem EM BLOCO (replace-all, como as embalagens): a tela manda a lista
inteira, e o que não veio sai. Espelho no frontend:
`modules/products/inventory/types/regrasPreco.types.ts`.

- FAIXA (R2): `quantidade` ≥ 2 e `preco` obrigatório; sem duas faixas com a
  mesma quantidade.
- LEVE_PAGUE (R3): `quantidade` (leve) > `pague` ≥ 1.
- Vigência opcional nas duas; `inicio` ≤ `fim`.
"""

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_REGRAS = 20


class RegraPrecoBase(BaseModel):
    tipo: Literal["FAIXA", "LEVE_PAGUE"]
    quantidade: int = Field(..., ge=2, le=100000, description="FAIXA: a partir de N un. LEVE_PAGUE: leve X.")
    preco: Optional[int] = Field(None, ge=0, description="FAIXA: preço de cada unidade (centavos)")
    pague: Optional[int] = Field(None, ge=1, description="LEVE_PAGUE: pague Y")
    inicio: Optional[date] = None
    fim: Optional[date] = None
    ativo: bool = True

    @model_validator(mode="after")
    def _coerente(self) -> "RegraPrecoBase":
        if self.tipo == "FAIXA":
            if self.preco is None:
                raise ValueError("Informe o preço da unidade na faixa.")
            self.pague = None
        else:
            if self.pague is None or self.pague >= self.quantidade:
                raise ValueError("No 'leve X, pague Y', Y precisa ser menor que X (ex.: leve 3, pague 2).")
            self.preco = None
        if self.inicio and self.fim and self.inicio > self.fim:
            raise ValueError("A data de início é depois da data de fim.")
        return self


class RegraPrecoEscrita(RegraPrecoBase):
    # Presente = atualiza a existente; ausente = cria.
    id: Optional[int] = None


class RegrasPrecoSalvar(BaseModel):
    regras: list[RegraPrecoEscrita] = Field(default_factory=list, max_length=MAX_REGRAS)

    @model_validator(mode="after")
    def _faixas_distintas(self) -> "RegrasPrecoSalvar":
        vistas: set[int] = set()
        for regra in self.regras:
            if regra.tipo != "FAIXA" or not regra.ativo:
                continue
            if regra.quantidade in vistas:
                raise ValueError(f"Há duas faixas 'a partir de {regra.quantidade}'.")
            vistas.add(regra.quantidade)
        return self


class RegraPrecoRead(RegraPrecoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    produto_id: int
    data_criacao: datetime
    data_atualizacao: datetime
