# ---------------------------------------------------------------------------
# ARQUIVO: services/ordem_servico/__init__.py
# DESCRICAO: Regras de negócio para Ordens de Serviço.
#
# Fluxo de status permitidos:
#   ABERTA → EM_ANDAMENTO → AGUARDANDO_PECAS → AGUARDANDO_APROVACAO
#          → AGUARDANDO_RETIRADA → FINALIZADA
#   Qualquer status ativo → CANCELADA
#   FINALIZADA / CANCELADA → EM_ANDAMENTO  (via /reabrir)
#
# Regras financeiras:
#   valor_bruto = soma dos itens (quantidade × valor_unitario)
#   valor_total = valor_bruto - desconto
#   Finalização só é permitida se sum(pagamentos) + valor_entrada == valor_total
#
# Era um arquivo so (ordem_servico.py, 63 KB, no limite do PyArmor trial) ate
# 13/10/2026; virou pacote:
#   excecoes.py    - excecoes reutilizaveis
#   regras.py      - helpers privados (OS editavel, item coerente, total)
#   regras_tipo.py - tipo de trabalho e item vindo de outro documento
#                    (era services/ordem_servico_regras_tipo.py)
#   criacao.py     - abrir a OS (e o identificador gerado do objeto)
#   consultas.py   - leitura, busca, estatisticas, abandono e atrasadas
#   atualizacao.py - editar a OS e o equipamento/objeto
#   objeto.py      - historico de KM, revisoes, identificador do objeto
#   itens.py       - incluir, editar e remover item
#   estoque.py     - baixa e estorno de estoque das pecas da OS
#   status.py      - finalizar, cancelar e reabrir
#   foto.py        - fotos da OS (era services/ordem_servico_foto.py)
#   nota_fiscal.py - dados fiscais da OS (era services/ordem_servico_nota_fiscal.py)
#   ganchos.py     - quem reage ao ciclo da OS (era services/ordem_servico_ganchos.py)
#
# Este __init__ reexporta o que era ordem_servico.py e ordem_servico_regras_tipo.py:
# `from app.services import ordem_servico` continua valendo como antes.
# foto, nota_fiscal e ganchos ficam nos submodulos, sem reexport:
# `from app.services.ordem_servico import ganchos as ganchos_os`. Os ganchos
# PRECISAM ser um modulo so: as listas (ao_finalizar...) moram nele, e uma copia
# reexportada aqui seria trocada sem efeito.
# ---------------------------------------------------------------------------

from app.services.ordem_servico.excecoes import (
    os_not_found_exce,
    cliente_not_found_exce,
    funcionario_not_found_exce,
    item_not_found_exce,
    forma_pagamento_not_found_exce,
    os_fechada_exce,
    os_nao_pode_reabrir_exce,
    pagamento_valor_invalido_exce,
    status_invalido_exce,
)

from app.services.ordem_servico.regras import (
    _assert_forma_pagamento_entrada,
    _get_os_or_raise,
    _assert_os_editavel,
    _assert_sem_itens_pendentes,
    _assert_item_coerente,
    _assert_item_nao_gerado_pela_fabrica,
    _item_conta_no_total,
    _recalcular_valor_total_os,
)

from app.services.ordem_servico.regras_tipo import (
    item_de_outro_documento_exce,
    _assert_item_sem_origem,
    CHAVE_TIPO_TRABALHO,
    _assert_tipo_pode_ser_criado,
    _assert_tipo_pode_ser_trocado,
)

from app.services.ordem_servico.criacao import (
    _preencher_identificador_gerado,
    _exigir_campos_do_objeto,
    create_ordem_servico,
)

from app.services.ordem_servico.consultas import (
    get_ordem_servico_by_numero_os,
    get_ordem_servico_by_search,
    get_ordens_servico_by_cliente_id,
    get_ordem_servico_stats,
    get_os_abandono,
    get_os_atrasadas,
)

from app.services.ordem_servico.atualizacao import (
    _CAMPOS_TEXTO,
    update_ordem_servico,
    update_equipamento_os,
)

from app.services.ordem_servico.objeto import (
    get_historico_km,
    _ultimo_km_conhecido,
    get_revisoes_pendentes,
    _cliente_contato,
    verificar_identificador_objeto,
    BUSCA_OBJETO_LIMITE,
    BUSCA_OBJETO_MIN_CARACTERES,
    buscar_objetos_por_identificador,
)

from app.services.ordem_servico.itens import (
    add_item_to_os,
    update_item_os,
    remove_item_from_os,
)

from app.services.ordem_servico.estoque import (
    _itens_de_produto,
    _quantidade_a_movimentar,
    _movimentar_estoque_os,
)

from app.services.ordem_servico.status import (
    finalizar_ordem_servico,
    cancelar_ordem_servico,
    reabrir_ordem_servico,
)

__all__ = [
    "os_not_found_exce",
    "cliente_not_found_exce",
    "funcionario_not_found_exce",
    "item_not_found_exce",
    "forma_pagamento_not_found_exce",
    "os_fechada_exce",
    "os_nao_pode_reabrir_exce",
    "pagamento_valor_invalido_exce",
    "status_invalido_exce",
    "_assert_forma_pagamento_entrada",
    "_get_os_or_raise",
    "_assert_os_editavel",
    "_assert_sem_itens_pendentes",
    "_assert_item_coerente",
    "_assert_item_nao_gerado_pela_fabrica",
    "_item_conta_no_total",
    "_recalcular_valor_total_os",
    "item_de_outro_documento_exce",
    "_assert_item_sem_origem",
    "CHAVE_TIPO_TRABALHO",
    "_assert_tipo_pode_ser_criado",
    "_assert_tipo_pode_ser_trocado",
    "_preencher_identificador_gerado",
    "_exigir_campos_do_objeto",
    "create_ordem_servico",
    "get_ordem_servico_by_numero_os",
    "get_ordem_servico_by_search",
    "get_ordens_servico_by_cliente_id",
    "get_ordem_servico_stats",
    "get_os_abandono",
    "get_os_atrasadas",
    "_CAMPOS_TEXTO",
    "update_ordem_servico",
    "update_equipamento_os",
    "get_historico_km",
    "_ultimo_km_conhecido",
    "get_revisoes_pendentes",
    "_cliente_contato",
    "verificar_identificador_objeto",
    "BUSCA_OBJETO_LIMITE",
    "BUSCA_OBJETO_MIN_CARACTERES",
    "buscar_objetos_por_identificador",
    "add_item_to_os",
    "update_item_os",
    "remove_item_from_os",
    "_itens_de_produto",
    "_quantidade_a_movimentar",
    "_movimentar_estoque_os",
    "finalizar_ordem_servico",
    "cancelar_ordem_servico",
    "reabrir_ordem_servico",
]
