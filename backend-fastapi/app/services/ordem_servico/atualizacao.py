# ---------------------------------------------------------------------------
# ARQUIVO: services/ordem_servico/atualizacao.py
# DESCRICAO: Ordem de servico - editar a OS e o equipamento/objeto.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.schemas.ordem_servico import (
    OrdemServicoUpdate,
    OSEquipamentoUpdate,
)
from app.db.models.ordem_servico import OrdemServico as OSModel
from app.db.crud import ordem_servico as os_crud
from app.db.crud import cliente as cliente_crud
from app.db.crud import funcionario as funcionario_crud
from app.services.sistema.segmentos import (
    validar_objeto_por_segmento,
)
from app.services.fabrica import trilho as trilho_fabrica
from app.core.enum import (
    OrdemServicoStatus,
)
from app.services.ordem_servico.excecoes import cliente_not_found_exce, funcionario_not_found_exce, status_invalido_exce
from app.services.ordem_servico.regras import _assert_forma_pagamento_entrada, _assert_os_editavel, _get_os_or_raise, _recalcular_valor_total_os
from app.services.ordem_servico.regras_tipo import _assert_tipo_pode_ser_trocado


# ===========================================================================
# ATUALIZAÇÃO (UPDATE)
# ===========================================================================

_CAMPOS_TEXTO = frozenset({
    'defeito_relatado', 'diagnostico', 'solucao',
    'observacoes', 'senha_aparelho', 'acessorios', 'condicoes_aparelho',
    'dados_adicionais'
})


def update_ordem_servico(db: Session, numero_os: str, data: OrdemServicoUpdate) -> OSModel:
    """
    Atualiza campos gerais de uma OS.

    Restrições:
    - OS FINALIZADA ou CANCELADA só aceita atualização de campos de texto.
    - Transições para FINALIZADA e CANCELADA são bloqueadas (use /finalizar ou /cancelar).
    - Se desconto mudar, valor_total é recalculado automaticamente.
    - Se funcionario_id mudar, o funcionário é validado no banco.
    """
    os_in_db = _get_os_or_raise(db, numero_os)

    update_data = data.model_dump(exclude_unset=True)

    # A OS não troca de tipo quando o antigo OU o novo só nasce de outro
    # documento (Spec 03A, D8). Roda antes de mesclar `dados_adicionais`.
    _assert_tipo_pode_ser_trocado(db, os_in_db.dados_adicionais, update_data.get("dados_adicionais"))

    # Extrai campos legados e move para dados_adicionais.
    # dict(...) cria um novo objeto para que o SQLAlchemy detecte a mudança
    # (JSON não é rastreado in-place; reatribuir a mesma referência não persiste).
    dados_adicionais = dict(getattr(os_in_db, "dados_adicionais", None) or {})
    if "dados_adicionais" in update_data:
        sent_data = update_data.pop("dados_adicionais") or {}
        dados_adicionais.update(sent_data)

    # O campo legado `acessorios` (texto, da informática) colide de nome com o
    # `dados_adicionais.acessorios` (Record de checkboxes da vistoria da oficina):
    # um "" vindo do form apagava o Record a cada update. Guarda: não sobrescreve
    # quando o valor já existente é um Record (dict) — condição que só a oficina
    # tem. Para a informática (sempre texto), o comportamento fica idêntico ao de
    # antes (inclusive continua podendo limpar o campo com string vazia).
    for legacy_field in ["senha_aparelho", "acessorios", "condicoes_aparelho"]:
        if legacy_field in update_data:
            val = update_data.pop(legacy_field)
            if val is not None and not isinstance(dados_adicionais.get(legacy_field), dict):
                dados_adicionais[legacy_field] = val

    os_in_db.dados_adicionais = dados_adicionais

    is_texto_only = update_data.keys() <= _CAMPOS_TEXTO
    if not is_texto_only:
        _assert_os_editavel(os_in_db)

    # Bloqueia transições que têm endpoints próprios
    new_status = update_data.get("status")
    if new_status in (OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA):
        raise status_invalido_exce
    # Marcenaria-fábrica: o status vem da etapa (no-op nas outras OS).
    if new_status is not None and new_status != os_in_db.status:
        trilho_fabrica.assert_status_manual(os_in_db)

    if "forma_pagamento_entrada_id" in update_data:
        _assert_forma_pagamento_entrada(db, update_data["forma_pagamento_entrada_id"])

    # Adiantamento zerado nao pode manter forma de pagamento pendurada.
    if update_data.get("valor_entrada") == 0:
        update_data["forma_pagamento_entrada_id"] = None

    # Valida novo funcionário se informado
    novo_funcionario_id = update_data.pop("funcionario_id", None)
    if novo_funcionario_id is not None:
        funcionario_in_db = funcionario_crud.get_funcionario_by_id(db, funcionario_id=novo_funcionario_id)
        if not funcionario_in_db:
            raise funcionario_not_found_exce
        os_in_db.funcionario = funcionario_in_db

    # Aplica os demais campos
    for key, value in update_data.items():
        setattr(os_in_db, key, value)

    # Recalcula total se desconto foi alterado
    if "desconto" in update_data:
        _recalcular_valor_total_os(os_in_db)

    return os_crud.update_ordem_servico(db, os_to_update=os_in_db)


def update_equipamento_os(db: Session, numero_os: str, data: OSEquipamentoUpdate) -> OSModel:
    """
    Atualiza informações do equipamento de uma OS.

    Permite também trocar o cliente proprietário via cliente_id.
    Restrição: OS FINALIZADA ou CANCELADA não pode ser editada.
    """
    os_in_db = _get_os_or_raise(db, numero_os)
    _assert_os_editavel(os_in_db)

    equipamento = os_in_db.equipamento
    update_data = data.model_dump(exclude_unset=True)

    # Valida e troca o cliente se solicitado
    novo_cliente_id = update_data.pop("cliente_id", None)
    if novo_cliente_id is not None:
        cliente_in_db = cliente_crud.get_cliente_by_id(db, cliente_id=novo_cliente_id)
        if not cliente_in_db:
            raise cliente_not_found_exce
        equipamento.cliente = cliente_in_db

    # Extrai dados_adicionais e campos de retrocompatibilidade do objeto.
    # dict(...) garante um novo objeto para o SQLAlchemy detectar a mudança.
    obj_dados_adicionais = dict(getattr(equipamento, "dados_adicionais", None) or {})
    if "dados_adicionais" in update_data:
        sent_data = update_data.pop("dados_adicionais") or {}
        obj_dados_adicionais.update(sent_data)

    for legacy_field in ["tipo_equipamento", "imei"]:
        if legacy_field not in update_data:
            continue
        val = update_data.pop(legacy_field)
        if val is None:
            # Nao informado: preserva o que ja existe (semantica de PATCH).
            continue
        valor = val.value if hasattr(val, 'value') else val
        if valor == "":
            # String vazia = limpar de proposito. Gravar "" era o bug: o form
            # devolve "" para campo nao preenchido e isso sobrescrevia o dado real.
            obj_dados_adicionais.pop(legacy_field, None)
        else:
            obj_dados_adicionais[legacy_field] = valor

    equipamento.dados_adicionais = obj_dados_adicionais

    for key, value in update_data.items():
        setattr(equipamento, key, value)

    # Validacao especifica de segmento sobre o estado final do objeto (gated).
    validar_objeto_por_segmento(
        db,
        numero_serie=equipamento.numero_serie,
        dados_adicionais=equipamento.dados_adicionais,
    )

    return os_crud.update_ordem_servico(db, os_to_update=os_in_db)
