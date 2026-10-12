# ---------------------------------------------------------------------------
# ARQUIVO: schemas/empresa/fiscal.py
# DESCRICAO: Empresa - schemas da configuracao fiscal.
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Optional


from pydantic import BaseModel, ConfigDict, Field, field_serializer



# =========================
# Fiscal Settings Schemas
# =========================

class FiscalSettingsBase(BaseModel):
    """
    Campos comuns para configurações fiscais.
    Usados para leitura e atualização.
    """
    ambiente_emissao: int = Field(
        default=2,
        ge=1,
        le=2,
        description="Ambiente: 1=Produção, 2=Homologação"
    )
    serie_nfe: int = Field(default=1, ge=0, description="Série da NFe")
    ultimo_numero_nfe: int = Field(default=0, ge=0, description="Último número NFe")
    serie_nfce: int = Field(default=1, ge=0, description="Série da NFCe")
    ultimo_numero_nfce: int = Field(default=0, ge=0, description="Último número NFCe")
    numeracao_confirmada: bool = Field(
        default=False,
        description="Série e último número confirmados formalmente (trava da Rejeição 204)",
    )
    # SEM max_length: na LEITURA este campo carrega o texto CIFRADO vindo do
    # banco (~180 chars), não o CSC digitado. Um limite de 100 aqui rejeitaria
    # a própria configuração salva. O limite de entrada fica no
    # FiscalSettingsUpdate, que é por onde o usuário digita.
    csc_token: Optional[str] = Field(None, description="Token CSC para NFCe (cifrado)")
    csc_id: Optional[str] = Field(None, max_length=10, description="ID do Token CSC")
    rps_serie: Optional[str] = Field(None, max_length=10, description="Série do RPS")
    rps_ultimo_numero: int = Field(default=0, ge=0, description="Último número RPS")
    prefeitura_login: Optional[str] = Field(None, max_length=50, description="Login prefeitura")
    prefeitura_senha: Optional[str] = Field(None, max_length=100, description="Senha prefeitura")
    prefeitura_token_api: Optional[str] = Field(None, max_length=200, description="Token API prefeitura")
    regime_tributacao_iss: Optional[int] = Field(None, ge=1, le=6, description="Regime ISS (1-6)")
    tipo_certificado: str = Field(default="ARQUIVO", description="Tipo: ARQUIVO, WINDOWS, NENHUM")

    model_config = ConfigDict(from_attributes=True)


class FiscalSettingsUpdate(BaseModel):
    """
    Schema para atualização parcial de configurações fiscais.
    Todos os campos são opcionais.
    """
    ambiente_emissao: Optional[int] = Field(None, ge=1, le=2)
    serie_nfe: Optional[int] = Field(None, ge=0)
    ultimo_numero_nfe: Optional[int] = Field(None, ge=0)
    serie_nfce: Optional[int] = Field(None, ge=0)
    ultimo_numero_nfce: Optional[int] = Field(None, ge=0)
    numeracao_confirmada: Optional[bool] = Field(
        None, description="True destrava a emissão; alterar série/número também confirma",
    )
    csc_token: Optional[str] = Field(None, max_length=100)
    csc_id: Optional[str] = Field(None, max_length=10)
    limite_consumidor_anonimo: Optional[int] = Field(
        None, ge=0,
        description="Teto em centavos para NFC-e sem CPF/CNPJ do comprador",
    )
    rps_serie: Optional[str] = Field(None, max_length=10)
    rps_ultimo_numero: Optional[int] = Field(None, ge=0)
    prefeitura_login: Optional[str] = Field(None, max_length=50)
    prefeitura_senha: Optional[str] = Field(None, max_length=100)
    prefeitura_token_api: Optional[str] = Field(None, max_length=200)
    regime_tributacao_iss: Optional[int] = Field(None, ge=1, le=6)
    tipo_certificado: Optional[str] = Field(None)

    model_config = ConfigDict(from_attributes=True)


class FiscalSettingsRead(FiscalSettingsBase):
    """
    Schema de leitura completo das configurações fiscais.
    Inclui metadados read-only do certificado.
    """
    id: int = Field(..., description="ID único das configurações")
    empresa_id: int = Field(..., description="ID da empresa")
    certificado_digital_path: Optional[str] = Field(None, description="Caminho do certificado A1")
    certificado_validade: Optional[datetime] = Field(None, description="Validade do certificado")
    certificado_subject: Optional[str] = Field(None, description="Subject/CN do certificado")
    certificado_thumbprint: Optional[str] = Field(None, description="Thumbprint (Windows)")
    certificado_status: Optional[str] = Field(None, description="Status da conexão na nuvem")
    certificado_cnpj: Optional[str] = Field(None, description="CNPJ do certificado")

    @field_serializer("csc_token")
    def serializar_csc_token(self, valor: Optional[str]) -> Optional[str]:
        """Mascara o CSC em QUALQUER resposta que carregue estas configurações.

        Fica no schema, e não no endpoint, porque `FiscalSettingsRead` viaja
        dentro de `EmpresaRead` — mascarar só no Centro Fiscal deixaria o
        segredo saindo pela tela de empresa.

        Também é o que impede a interface de exibir o blob cifrado: o valor
        vem do banco já criptografado, e sem isto o campo mostraria
        `gAAAAAB...` para o lojista.
        """
        from app.services.fiscal.helpers import decifrar_csc, mascarar_csc

        return mascarar_csc(decifrar_csc(valor))

    model_config = ConfigDict(from_attributes=True)


FiscalSettingsRead.model_rebuild()
