# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/ganchos.py
# DESCRICAO: Liga a marcenaria aos ganchos do ciclo de vida da OS (Spec 09A).
#
# Chamado UMA vez pelo api.py, junto com as rotas da marcenaria. Registrar
# duas vezes nao duplica (ordem_servico_ganchos.registrar confere).
#
# Por que aqui e nao no __init__ do pacote: varios lugares importam so as
# permissoes da marcenaria (ex.: Configuracoes); registrar no __init__ faria
# cada um desses imports carregar tambem o Financeiro. Uma chamada explicita
# deixa claro quando e por quem os ganchos sao ligados.
# ---------------------------------------------------------------------------

from app.services import ordem_servico_ganchos as ganchos_os
from app.services.marcenaria import rt


def registrar() -> None:
    """Liga o RT do arquiteto a finalizacao, reabertura e cancelamento da OS."""
    ganchos_os.registrar(ganchos_os.ao_finalizar, rt.criar_contas_ao_finalizar)
    ganchos_os.registrar(ganchos_os.ao_reabrir, rt.cancelar_pendentes_ao_reabrir)
    ganchos_os.registrar(ganchos_os.ao_cancelar, rt.tratar_cancelamento)
