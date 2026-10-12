# ---------------------------------------------------------------------------
# ARQUIVO: services/empresa/__init__.py
# DESCRICAO: Empresa - cadastro, configuracao fiscal e certificado digital.
#
# Era um arquivo so (empresa.py) ate 12/10/2026; virou pacote:
#   cadastro.py    - criar, logo, ler e editar a empresa (singleton)
#   fiscal.py      - configuracao fiscal (inclusive a confirmacao da numeracao)
#   certificado.py - certificado para a plataforma (focus) e do Windows
#
# Este __init__ reexporta tudo: `from app.services import empresa` continua
# valendo como antes.
# ---------------------------------------------------------------------------

from app.services.empresa.cadastro import (
    CONFLICT_EXCE,
    NOT_FOUND_EXCE,
    create_empresa,
    create_image_empresa,
    get_empresa_by_id,
    update_empresa,
)

from app.services.empresa.fiscal import (
    CAMPOS_QUE_CONFIRMAM_NUMERACAO,
    get_or_create_fiscal_settings,
    update_fiscal_settings,
)

from app.services.empresa.certificado import (
    upload_certificado_focus,
    list_windows_certificates,
    vincular_certificado_windows,
)

__all__ = [
    "CONFLICT_EXCE",
    "NOT_FOUND_EXCE",
    "create_empresa",
    "create_image_empresa",
    "get_empresa_by_id",
    "update_empresa",
    "CAMPOS_QUE_CONFIRMAM_NUMERACAO",
    "get_or_create_fiscal_settings",
    "update_fiscal_settings",
    "upload_certificado_focus",
    "list_windows_certificates",
    "vincular_certificado_windows",
]
