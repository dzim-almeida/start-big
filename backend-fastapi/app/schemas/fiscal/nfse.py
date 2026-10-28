# ---------------------------------------------------------------------------
# ARQUIVO: schemas/fiscal/nfse.py
# DESCRIÇÃO: Configuração da NFS-e (docs/nfse-fase2-plano.md, G3): as decisões
#            que dependem do contador viram opção, com o padrão da fase 1.
# ---------------------------------------------------------------------------

import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NfseConfiguracao(BaseModel):
    regime_tributacao_iss: Optional[int] = Field(
        None, ge=1, le=6,
        description="Regime especial do ISS (código ABRASF: 1 ME municipal, 2 estimativa, "
                    "3 sociedade de profissionais, 4 cooperativa, 5 MEI, 6 ME/EPP do Simples).",
    )
    nfse_reter_iss_pj: bool = Field(False, description="Tomador PJ retém o ISS.")
    nfse_uma_nota_por_codigo: bool = Field(
        False, description="OS com códigos nacionais diferentes vira uma NFS-e por código.",
    )
    nfse_ibs_cbs_cst: Optional[str] = Field(None, description="CST IBS/CBS padrão (3 dígitos).")
    nfse_ibs_cbs_cclass: Optional[str] = Field(None, description="cClassTrib IBS/CBS padrão (6 dígitos).")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("nfse_ibs_cbs_cst", mode="before")
    @classmethod
    def _cst(cls, v):
        if v in (None, ""):
            return None
        d = re.sub(r"\D", "", str(v))
        if len(d) not in (2, 3):
            raise ValueError("CST IBS/CBS deve ter 2 ou 3 dígitos")
        return d.zfill(3)

    @field_validator("nfse_ibs_cbs_cclass", mode="before")
    @classmethod
    def _cclass(cls, v):
        if v in (None, ""):
            return None
        d = re.sub(r"\D", "", str(v))
        if len(d) != 6:
            raise ValueError("cClassTrib deve ter 6 dígitos")
        return d
