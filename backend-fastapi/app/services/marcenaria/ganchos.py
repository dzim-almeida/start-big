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
from app.services.marcenaria import rt, separacao, terceirizado


def registrar() -> None:
    """Liga a marcenaria a finalizacao, reabertura e cancelamento da OS."""
    # Spec 09A: a conta a pagar do RT do arquiteto.
    ganchos_os.registrar(ganchos_os.ao_finalizar, rt.criar_contas_ao_finalizar)
    ganchos_os.registrar(ganchos_os.ao_reabrir, rt.cancelar_pendentes_ao_reabrir)
    ganchos_os.registrar(ganchos_os.ao_cancelar, rt.tratar_cancelamento)
    # Spec 10A D24: o material retirado continua fora do estoque (so o aviso).
    ganchos_os.registrar(ganchos_os.ao_cancelar, separacao.avisar_material_no_cancelamento)
    # Spec 11A D16: moveis pedidos a central (o pedido e as contas ficam).
    ganchos_os.registrar(ganchos_os.ao_cancelar, terceirizado.avisar_no_cancelamento)
