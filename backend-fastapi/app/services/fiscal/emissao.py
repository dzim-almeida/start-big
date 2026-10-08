# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/emissao.py
# DESCRIÇÃO: Porta de entrada da emissão fiscal (NF-e, NFC-e, OS, eventos).
#
# Até a F5 (07/10/2026) este arquivo tinha 1400 linhas com tudo junto. O código
# foi MOVIDO, sem reescrever, para um módulo por assunto:
#   emissao_nucleo.py    — aplicar resultado, arquivar DANFE/XML, settings
#   emissao_nfe_venda.py — NF-e de venda e lote
#   emissao_nfce.py      — NFC-e
#   emissao_nfe_os.py    — NF-e da Ordem de Serviço
#   emissao_eventos.py   — consulta, polling, cancelamento, histórico
#   emissao_teste.py     — NF-e de teste de homologação
#
# Aqui só se reexporta, para que `from app.services.fiscal.emissao import X`
# continue valendo em endpoints, reemissão, devolução e testes.
#
# ⚠️ Patch de teste vai no módulo onde a função MORA, não aqui: trocar
# `emissao.get_fiscal_client` não alcança quem chama de dentro do emissao_nfce.
# ---------------------------------------------------------------------------

from app.db.crud import fiscal as crud  # noqa: F401 — testes fazem patch em `emissao.crud.*`

from .emissao_nucleo import (  # noqa: F401
    STATUS_CONSULTAVEIS,
    STATUS_NAO_TRANSMITIDA,
    _fiscais_efetivos,
    _arquivar_danfe,
    _arquivar_xml,
    _aplicar_resultado,
    _obter_fiscal_settings,
    _avisos,
)
from .emissao_nfe_venda import (  # noqa: F401
    _preparar_dados_emissao,
    preview_nfe_venda,
    emitir_nfe_venda,
    emitir_nfe_batch,
)
from .emissao_nfce import (  # noqa: F401
    preview_nfce_venda,
    _reais,
    _documento_do_consumidor,
    _assert_consumidor_identificado,
    _assert_csc_configurado,
    _completar_tributos_pelo_xml,
    emitir_nfce_venda,
)
from .emissao_nfe_os import (  # noqa: F401
    _preparar_dados_emissao_os,
    preview_nfe_os,
    emitir_nfe_os,
)
from .emissao_eventos import (  # noqa: F401
    consultar_documento,
    poll_nfe_status_async,
    JANELA_CANCELAMENTO_NFE,
    JANELA_CANCELAMENTO_NFCE,
    JANELA_CANCELAMENTO_POR_TIPO,
    _descrever_janela,
    _descrever_decorrido,
    _assert_dentro_da_janela_de_cancelamento,
    cancelar_documento,
    obter_historico_tentativas,
)
from .emissao_teste import (  # noqa: F401
    emitir_teste_nfe,
)
