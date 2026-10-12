# ---------------------------------------------------------------------------
# ARQUIVO: schemas/empresa/certificado.py
# DESCRICAO: Empresa - schemas do certificado do Windows.
# ---------------------------------------------------------------------------

from typing import Optional


from pydantic import BaseModel, ConfigDict, Field



class WindowsCertificateRead(BaseModel):
    """
    DTO para listagem de certificados do Windows Certificate Store.
    Read-only - não persiste no banco.
    """
    thumbprint: str = Field(..., description="Identificador único do certificado")
    subject: str = Field(..., description="Subject/CN do certificado")
    friendly_name: str = Field(..., description="Nome amigável")
    issuer: str = Field(..., description="Autoridade certificadora emissora")
    valid_until: Optional[str] = Field(None, description="Data de validade (ISO format)")
    serial_number: str = Field(..., description="Número de série")

    model_config = ConfigDict(from_attributes=True)


class CertificadoWindowsVincular(BaseModel):
    """
    Schema para vincular certificado Windows por thumbprint.
    """
    thumbprint: str = Field(..., min_length=40, max_length=64, description="Thumbprint do certificado")
