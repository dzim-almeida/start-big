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
    # Padrão para serviços novos (M2): só preenche o cadastro, não a nota.
    nfse_padrao_codigo_nacional: Optional[str] = Field(None, description="Código nacional (6 dígitos).")
    nfse_padrao_nbs: Optional[str] = Field(None, description="NBS (9 dígitos).")
    nfse_padrao_aliquota_iss: Optional[int] = Field(None, ge=0, le=10000, description="ISS em centésimos (500 = 5%).")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("nfse_padrao_codigo_nacional", "nfse_padrao_nbs", mode="before")
    @classmethod
    def _codigo(cls, v, info):
        if v in (None, ""):
            return None
        d = re.sub(r"\D", "", str(v))
        tamanho = 6 if info.field_name == "nfse_padrao_codigo_nacional" else 9
        if len(d) != tamanho:
            raise ValueError(f"Deve ter {tamanho} dígitos")
        return d

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


class NfseAvulsaRequest(BaseModel):
    """NFS-e sem OS (G4). Valores em centavos.

    O serviço vem do catálogo (`servico_id`, com os códigos dele) ou só dos
    códigos digitados; os digitados vencem os do catálogo nesta nota.
    """
    servico_id: Optional[int] = None
    codigo_tributacao_nacional: Optional[str] = None
    codigo_nbs: Optional[str] = None
    descricao: str = Field(..., min_length=3, max_length=1000)
    valor: int = Field(..., gt=0, description="Centavos")
    desconto: int = Field(0, ge=0, description="Centavos")
    tomador_documento: Optional[str] = Field(None, max_length=18)
    tomador_nome: Optional[str] = Field(None, max_length=150)
    tomador_email: Optional[str] = Field(None, max_length=80)

    @field_validator("codigo_tributacao_nacional", mode="before")
    @classmethod
    def _codigo(cls, v):
        if v in (None, ""):
            return None
        d = re.sub(r"\D", "", str(v))
        if len(d) != 6:
            raise ValueError("Código de tributação nacional deve ter 6 dígitos")
        return d

    @field_validator("codigo_nbs", mode="before")
    @classmethod
    def _nbs(cls, v):
        if v in (None, ""):
            return None
        d = re.sub(r"\D", "", str(v))
        if len(d) != 9:
            raise ValueError("NBS deve ter 9 dígitos")
        return d
