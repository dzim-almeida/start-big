# ---------------------------------------------------------------------------
# ARQUIVO: schemas/licenca/__init__.py
# DESCRICAO: Schemas da licenca do sistema.
#
# Era um arquivo so (licenca.py) ate 13/10/2026; virou pacote:
#   cadastro.py  - auto-cadastro, chave publica e leitura da licenca
#   terminal.py  - conectar, heartbeat e desconectar
#   status.py    - status, erro e validacao
#   renovacao.py - renovacao paga (periodos, planos, cobranca)
#
# Este __init__ reexporta tudo: `from app.schemas.licenca import ...` continua
# valendo como antes.
# ---------------------------------------------------------------------------

from app.schemas.licenca.cadastro import (
    LicencaEnderecoPayload,
    AutoCadastroPayload,
    AutoCadastroResponse,
    ChavePublicaResponse,
    LicencaRead,
)

from app.schemas.licenca.terminal import (
    ConectarPayload,
    HeartbeatPayload,
    DesconectarPayload,
)

from app.schemas.licenca.status import (
    LicencaStatusResponse,
    LicencaErroResponse,
    ValidarPayload,
    ValidarResponse,
    ValidarErroResponse,
)

from app.schemas.licenca.renovacao import (
    RenovacaoCredenciaisPayload,
    RenovacaoPeriodoRead,
    RenovacaoPlanosRead,
    CobrancaCreate,
    CobrancaRead,
    CobrancaStatusRead,
)

__all__ = [
    "LicencaEnderecoPayload",
    "AutoCadastroPayload",
    "AutoCadastroResponse",
    "ChavePublicaResponse",
    "LicencaRead",
    "ConectarPayload",
    "HeartbeatPayload",
    "DesconectarPayload",
    "LicencaStatusResponse",
    "LicencaErroResponse",
    "ValidarPayload",
    "ValidarResponse",
    "ValidarErroResponse",
    "RenovacaoCredenciaisPayload",
    "RenovacaoPeriodoRead",
    "RenovacaoPlanosRead",
    "CobrancaCreate",
    "CobrancaRead",
    "CobrancaStatusRead",
]
