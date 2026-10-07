# ---------------------------------------------------------------------------
# ARQUIVO: endpoints/fiscal.py
# DESCRIÇÃO: Router do Centro Fiscal. As rotas estão em fiscal_documentos,
#            fiscal_emissao, fiscal_eventos e fiscal_config (F5, 07/10/2026).
#
# Tres camadas de acesso (ver app/core/depends.py):
#   leitura/regularizacao -> get_current_active_user
#   configuracao          -> requer_configuracao_fiscal (master, sem plano)
#   emissao               -> requer_modulo_fiscal (exige plano contratado)
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends
from app.core.modulos import requer_modulo
from . import fiscal_config, fiscal_documentos, fiscal_emissao, fiscal_eventos
from .fiscal_documentos import (  # noqa: F401 — reexportado: testes e serviços importam daqui
    obter_resumo,
    obter_pendencias,
    listar_documentos,
    exportar_xml_periodo,
    obter_documento,
    obter_historico,
    _cliente_fiscal,
    baixar_xml_documento,
    baixar_pdf_documento,
    sincronizar_arquivos_fiscais,
)
from .fiscal_emissao import (  # noqa: F401 — reexportado: testes e serviços importam daqui
    reemitir_documento,
    preview_nfe,
    emitir_nfe,
    preview_nfce,
    emitir_nfce,
    emitir_nfe_batch,
    emitir_teste_nfe,
    consultar_documento,
    emitir_devolucao,
)
from .fiscal_eventos import (  # noqa: F401 — reexportado: testes e serviços importam daqui
    cancelar_documento,
    registrar_carta_correcao,
    listar_cartas_correcao,
    _arquivo_da_carta,
    baixar_pdf_carta_correcao,
    baixar_xml_carta_correcao,
    listar_gaps_numeracao,
    listar_inutilizacoes,
    ajustar_numeracao_duplicidade,
    inutilizar_numeracao,
)
from .fiscal_config import (  # noqa: F401 — reexportado: testes e serviços importam daqui
    obter_configuracao,
    _montar_configuracao,
    obter_tributacao_padrao,
    salvar_tributacao_padrao,
    listar_regras_ncm,
    salvar_regra_ncm,
    remover_regra_ncm,
    listar_perfis_tributarios,
    criar_perfil_tributario,
    obter_perfil_tributario,
    atualizar_perfil_tributario,
    excluir_perfil_tributario,
    atualizar_configuracao,
    obter_diagnostico_plataforma,
    upload_certificado_focus_endpoint,
    reconferir_certificado_endpoint,
)


# A LOJA contratou a NF-e? Trava de licenca, no router inteiro, como no
# /financeiro. NFE NEGA por padrao: licenca sem resposta nao libera (ver
# app/core/modulos.py).
#
# Ela fica ACIMA das tres camadas descritas no topo. A camada de configuracao
# e deliberadamente frouxa quanto a plano -- a ideia sendo deixar preparar
# certificado antes de contratar --, mas no nosso fluxo isso nao se aplica: o
# menu inteiro do Centro Fiscal fica escondido ate a licenca conceder o NFE,
# entao nao existe "configurar antes de ter". Manter a trava aqui e o que
# sustenta a promessa do nega-por-padrao: nenhuma rota fiscal responde sem a
# concessao.
router = APIRouter(dependencies=[Depends(requer_modulo("NFE"))])


# Desde a F5 (07/10/2026) as rotas moram em um arquivo por assunto. A ordem dos
# include_router importa: o FastAPI responde com a PRIMEIRA rota que casa, e a
# tabela final foi conferida contra a de antes da divisão.
router.include_router(fiscal_documentos.router)
router.include_router(fiscal_emissao.router)
router.include_router(fiscal_eventos.router)
router.include_router(fiscal_config.router)
