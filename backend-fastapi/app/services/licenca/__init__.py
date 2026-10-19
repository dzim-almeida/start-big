# ---------------------------------------------------------------------------
# ARQUIVO: services/licenca/__init__.py
# MÓDULO: Regras de Negócio (Service Layer)
# DESCRIÇÃO: Serviço de licenciamento - auto-cadastro na API StartBig,
#            criptografia AES-256-GCM e persistência local.
#
# Era um arquivo so (licenca.py, 52 KB) ate 13/10/2026; virou pacote:
#   constantes.py   - URLs da API e tempos de espera
#   cripto.py       - AES-256-GCM com chave derivada do HWID
#   cadastro.py     - auto-cadastro e chave publica
#   transferencia.py - login da conta: primeiro acesso e troca de servidor
#   recusa.py       - erro padrao, vencimento x recusa, bloqueio local, carencia
#   validacao.py    - validacao online/offline e modulos liberados
#   terminal.py     - conectar e desconectar terminal
#   sincronizacao.py - heartbeat e renovacao do token em segundo plano
#   renovacao.py    - renovacao paga pela loja (era services/licenca_renovacao.py)
#
# Este __init__ reexporta o que era licenca.py: `from app.services import licenca`
# continua valendo como antes. A renovacao fica no submodulo, sem reexport:
# `from app.services.licenca import renovacao`.
#
# ATENCAO para testes: trocar uma funcao AQUI (monkeypatch no pacote) so vale
# para quem a chama como `licenca_service.funcao(...)`. Quem a chama por dentro
# do pacote usa o nome do proprio submodulo: troque nele (ex.: obter_hwid e
# decriptar_valor do login -> app.services.licenca.terminal).
# ---------------------------------------------------------------------------

from app.services.licenca.constantes import (
    API_AUTO_CADASTRO_URL,
    API_CONECTAR_URL,
    API_HEARTBEAT_URL,
    API_VALIDAR_URL,
    API_DESCONECTAR_URL,
    API_CHAVE_PUBLICA_URL,
    API_ERP_LOGIN_URL,
    TIMEOUT_SECONDS,
    CONECTAR_TIMEOUT_SECONDS,
    HEARTBEAT_TIMEOUT,
    DESCONECTAR_TIMEOUT,
    MAX_RETRIES,
)

from app.services.licenca.cripto import (
    _derivar_chave,
    encriptar_valor,
    decriptar_valor,
)

from app.services.licenca.cadastro import (
    _chamar_api_auto_cadastro,
    _buscar_chave_publica_online,
    resgatar_chave_publica_online,
    registrar_licenca,
)

from app.services.licenca.transferencia import (
    licenca_ativada_nesta_maquina,
    reconnect_licenca,
    transferir_para_esta_maquina,
    situacao_desta_maquina,
    desativar_esta_maquina,
)

from app.services.licenca.recusa import (
    CODIGO_LICENCA_DE_OUTRA_MAQUINA,
    erro_licenca_de_outra_maquina,
    _erro_licenca,
    _CODIGOS_DE_VENCIMENTO,
    _TERMOS_DE_VENCIMENTO,
    _limpar_bloqueio,
    _detalhe_da_recusa,
    _plano_vencido_localmente,
    _recusa_por_vencimento,
    _sem_acentos,
    _carencia_vigente,
)

from app.services.licenca.validacao import (
    _tentar_conexao_remota,
    _decifrar_public_key,
    ler_modulos_liberados,
    modulos_da_licenca,
    _validar_offline,
    verificar_licenca_ativa,
)

from app.services.licenca.terminal import (
    conectar_terminal,
    desconectar_terminal,
)

from app.services.licenca.sincronizacao import (
    _enviar_heartbeat_terminal,
    enviar_heartbeat,
    LIMIAR_RENOVACAO,
    renovar_licenca_background,
)

__all__ = [
    "API_AUTO_CADASTRO_URL",
    "API_CONECTAR_URL",
    "API_HEARTBEAT_URL",
    "API_VALIDAR_URL",
    "API_DESCONECTAR_URL",
    "API_CHAVE_PUBLICA_URL",
    "API_ERP_LOGIN_URL",
    "TIMEOUT_SECONDS",
    "CONECTAR_TIMEOUT_SECONDS",
    "HEARTBEAT_TIMEOUT",
    "DESCONECTAR_TIMEOUT",
    "MAX_RETRIES",
    "_derivar_chave",
    "encriptar_valor",
    "decriptar_valor",
    "_chamar_api_auto_cadastro",
    "_buscar_chave_publica_online",
    "resgatar_chave_publica_online",
    "registrar_licenca",
    "reconnect_licenca",
    "licenca_ativada_nesta_maquina",
    "transferir_para_esta_maquina",
    "situacao_desta_maquina",
    "desativar_esta_maquina",
    "CODIGO_LICENCA_DE_OUTRA_MAQUINA",
    "erro_licenca_de_outra_maquina",
    "_erro_licenca",
    "_CODIGOS_DE_VENCIMENTO",
    "_TERMOS_DE_VENCIMENTO",
    "_limpar_bloqueio",
    "_detalhe_da_recusa",
    "_plano_vencido_localmente",
    "_recusa_por_vencimento",
    "_sem_acentos",
    "_carencia_vigente",
    "_tentar_conexao_remota",
    "_decifrar_public_key",
    "ler_modulos_liberados",
    "modulos_da_licenca",
    "_validar_offline",
    "verificar_licenca_ativa",
    "conectar_terminal",
    "desconectar_terminal",
    "_enviar_heartbeat_terminal",
    "enviar_heartbeat",
    "LIMIAR_RENOVACAO",
    "renovar_licenca_background",
]
