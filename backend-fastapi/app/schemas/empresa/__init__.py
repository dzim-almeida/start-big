# ---------------------------------------------------------------------------
# ARQUIVO: schemas/empresa/__init__.py
# DESCRICAO: Schemas Pydantic da empresa.
#
# Era um arquivo so (empresa.py) ate 12/10/2026; virou pacote:
#   cadastro.py    - Empresa* (base, criar, editar, leitura admin e usuario)
#   fiscal.py      - FiscalSettings* (configuracao fiscal)
#   certificado.py - certificado do Windows (listar e vincular)
#
# Este __init__ reexporta tudo: `from app.schemas.empresa import ...` continua
# valendo como antes.
# ---------------------------------------------------------------------------

from app.schemas.empresa.fiscal import (
    FiscalSettingsBase,
    FiscalSettingsUpdate,
    FiscalSettingsRead,
)

from app.schemas.empresa.certificado import (
    WindowsCertificateRead,
    CertificadoWindowsVincular,
)

from app.schemas.empresa.cadastro import (
    EmpresaBase,
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaAdminRead,
    EmpresaUserRead,
)

__all__ = [
    "FiscalSettingsBase",
    "FiscalSettingsUpdate",
    "FiscalSettingsRead",
    "WindowsCertificateRead",
    "CertificadoWindowsVincular",
    "EmpresaBase",
    "EmpresaCreate",
    "EmpresaUpdate",
    "EmpresaAdminRead",
    "EmpresaUserRead",
]
