# ---------------------------------------------------------------------------
# ARQUIVO: schemas/perfil_tributario.py
# MÓDULO: Schemas Pydantic — Perfil tributário interestadual e suas regras
# ---------------------------------------------------------------------------
"""
O perfil chega e sai em bloco: descrição + lista completa de regras. Não há
endpoint para uma regra isolada — o PUT é replace-all, o que evita o estado
"perfil sem fallback" no meio de uma edição.

O que o banco não garante e o schema garante:
- exatamente UMA regra de fallback (UF e NCM vazios) — a UNIQUE do SQLite
  trata NULL como distinto e deixaria passar duas;
- nenhuma combinação (UF, NCM) repetida.

Percentuais em centésimos de ponto percentual (1200 = 12,00%).
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

UFS_VALIDAS = frozenset({
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
    "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
    "RO", "RR", "RS", "SC", "SE", "SP", "TO",
})

# Tetos de sanidade: acima disto é erro de digitação, não alíquota real.
MAX_ALIQUOTA_INTERESTADUAL = 2500   # 25%
MAX_ALIQUOTA_INTERNA = 3500         # 35%
MAX_FCP = 600                       # 6%
MAX_MVA = 50000                     # 500%
MAX_REDUCAO_BASE = 10000            # 100%


class RegraPerfilTributarioBase(BaseModel):
    """Uma regra do perfil: as alíquotas para uma UF de destino (e NCM)."""

    uf_destino: Optional[str] = Field(None, description="UF de destino. Vazio = fallback")
    ncm_excecao: Optional[str] = Field(None, description="NCM de 8 dígitos. Vazio = todos os NCMs")
    aliquota_interestadual: int = Field(..., ge=0, le=MAX_ALIQUOTA_INTERESTADUAL)
    aliquota_interna_destino: int = Field(..., ge=0, le=MAX_ALIQUOTA_INTERNA)
    percentual_fcp: int = Field(0, ge=0, le=MAX_FCP)
    calculo_base_dupla: bool = False
    mva_st: Optional[int] = Field(None, ge=0, le=MAX_MVA, description="Preenchido = há ST")
    reducao_base_calculo: Optional[int] = Field(None, ge=0, le=MAX_REDUCAO_BASE)

    @field_validator("uf_destino")
    @classmethod
    def _valida_uf(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        uf = v.strip().upper()
        if uf not in UFS_VALIDAS:
            raise ValueError(f"UF '{uf}' não é válida.")
        return uf

    @field_validator("ncm_excecao")
    @classmethod
    def _valida_ncm(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        ncm = v.strip()
        if not ncm.isdigit() or len(ncm) != 8:
            raise ValueError("NCM deve conter exatamente 8 dígitos numéricos.")
        return ncm

    @property
    def e_fallback(self) -> bool:
        return self.uf_destino is None and self.ncm_excecao is None

    model_config = ConfigDict(from_attributes=True)


class PerfilTributarioCreate(BaseModel):
    """Perfil com a lista completa de regras (POST e PUT)."""

    descricao: str = Field(..., min_length=3, max_length=120)
    regras: list[RegraPerfilTributarioBase] = Field(..., min_length=1)

    @field_validator("descricao")
    @classmethod
    def _apara_descricao(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Descrição deve ter ao menos 3 caracteres.")
        return v

    @model_validator(mode="after")
    def _valida_regras(self):
        fallbacks = sum(1 for r in self.regras if r.e_fallback)
        if fallbacks == 0:
            raise ValueError(
                "O perfil deve conter uma regra de fallback (UF e NCM vazios) "
                "que será usada quando não houver regra específica para o destino."
            )
        if fallbacks > 1:
            raise ValueError("O perfil não pode ter mais de uma regra de fallback.")

        chaves = [(r.uf_destino, r.ncm_excecao) for r in self.regras]
        if len(chaves) != len(set(chaves)):
            raise ValueError(
                "Existem regras duplicadas (mesma UF e mesmo NCM). "
                "Cada combinação de UF e NCM deve aparecer apenas uma vez."
            )
        return self


# O PUT é replace-all: mesmo contrato do POST.
PerfilTributarioUpdate = PerfilTributarioCreate


class RegraPerfilTributarioRead(RegraPerfilTributarioBase):
    id: int


class PerfilTributarioRead(BaseModel):
    id: int
    descricao: str
    regras: list[RegraPerfilTributarioRead]
    data_criacao: datetime
    data_atualizacao: datetime

    model_config = ConfigDict(from_attributes=True)


class PerfilTributarioListItem(BaseModel):
    """Linha da listagem — sem as regras, só quantas são."""

    id: int
    descricao: str
    quantidade_regras: int
    data_atualizacao: datetime

    model_config = ConfigDict(from_attributes=True)
