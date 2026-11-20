# ---------------------------------------------------------------------------
# ARQUIVO: services/licenca/constantes.py
# DESCRICAO: Licenca - URLs da API StartBig e tempos de espera.
# ---------------------------------------------------------------------------

import httpx


API_AUTO_CADASTRO_URL = "https://api.startbig.com.br/erp/auto-cadastro"


API_CONECTAR_URL = "https://api.startbig.com.br/licenca/conectar"


API_HEARTBEAT_URL = "https://api.startbig.com.br/licenca/heartbeat"


API_VALIDAR_URL = "https://api.startbig.com.br/licenca/validar"


API_DESCONECTAR_URL = "https://api.startbig.com.br/licenca/desconectar"


API_CHAVE_PUBLICA_URL = "https://api.startbig.com.br/licenca/chave-publica"


# Login da conta StartBig (e-mail + senha + HWID): ativa ESTE computador.
# Usado no primeiro acesso e na troca de servidor (services/licenca/transferencia.py).
API_ERP_LOGIN_URL = "https://api.startbig.com.br/erp/auth/login"

# Dados do titular da conta: GET para pré-preencher o setup, PUT para atualizar
# a nuvem antes de criar a empresa local (LIC-03 §4.3, LIC-06 §4.5 e §4.6).
API_TITULAR_URL = "https://api.startbig.com.br/erp/usuario/titular"

# Reenvio do link de confirmação ou de nova senha (LIC-06 §4.4). Sempre 202.
API_REENVIAR_LINK_URL = "https://api.startbig.com.br/erp/auth/reenviar-link"


TIMEOUT_SECONDS = 30


CONECTAR_TIMEOUT_SECONDS = 3


HEARTBEAT_TIMEOUT = httpx.Timeout(
    connect=10.0,   # DNS + TCP + TLS (operação mais lenta)
    read=5.0,       # Aguardar resposta do servidor
    write=5.0,      # Enviar payload (pequeno)
    pool=5.0,       # Aguardar conexão do pool
)


DESCONECTAR_TIMEOUT = httpx.Timeout(connect=1.0, read=0.5, write=0.5, pool=0.5)


MAX_RETRIES = 3
