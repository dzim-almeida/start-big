# ---------------------------------------------------------------------------
# ARQUIVO: services/ordem_servico/regras.py
# DESCRICAO: Ordem de servico - helpers privados (OS editavel, item coerente,
#            forma de pagamento da entrada, recalculo do total).
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.db.models.ordem_servico import OrdemServico as OSModel
from app.db.models.ordem_servico_item import OrdemServicoItem as OSItemModel
from app.db.crud import ordem_servico as os_crud
from app.db.crud.forma_pagamento import formas as fp_crud
from app.core.enum import (
    OrdemServicoStatus,
    OrdemServicoItemAprovacao,
)
from app.services.ordem_servico.excecoes import forma_pagamento_not_found_exce, os_fechada_exce, os_not_found_exce


def _assert_forma_pagamento_entrada(db: Session, fp_id: int | None) -> None:
    """
    Valida a forma de pagamento do adiantamento.

    Mesma regra dos pagamentos da finalizacao (existir e estar ativa). A coluna
    e um FK sem constraint no SQLite (ver a migration d3e4f5a6b7c8), entao um id
    invalido passaria direto e so apareceria como forma vazia no resumo.

    None e valido: adiantamento sem forma declarada e o estado de toda OS
    anterior a este campo.
    """
    if fp_id is None:
        return
    forma_pagamento = fp_crud.get_forma_pagamento_by_id(db, fp_id=fp_id)
    if not forma_pagamento or not forma_pagamento.ativo:
        raise forma_pagamento_not_found_exce


# ===========================================================================
# HELPERS PRIVADOS
# ===========================================================================

def _get_os_or_raise(db: Session, numero_os: str) -> OSModel:
    """Busca OS pelo número ou lança 404."""
    os_in_db = os_crud.get_ordem_servico_by_numero_os(db, numero_os=numero_os)
    if not os_in_db:
        raise os_not_found_exce
    return os_in_db


def _assert_os_editavel(os_in_db: OSModel) -> None:
    """Lança 409 se a OS estiver FINALIZADA ou CANCELADA."""
    if os_in_db.status in (OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA):
        raise os_fechada_exce


def _assert_sem_itens_pendentes(os_in_db: OSModel) -> None:
    """Lanca 422 se a OS tem item aguardando resposta do cliente.

    PENDENTE quer dizer que o cliente ainda nao disse se aprova ou recusa.
    Fechar a OS assim decide por ele: hoje o item entra no total (ele paga por
    peca que nao autorizou) e nao baixa do estoque (a peca sai da conta mas
    continua na prateleira). Ou aprova, ou recusa — nao da para entregar o
    veiculo com a pergunta em aberto.

    Nao afeta segmento sem aprovacao por item: la o default e APROVADO e nenhum
    item nasce PENDENTE.
    """
    pendentes = [
        item.nome for item in os_in_db.itens
        if item.status_aprovacao == OrdemServicoItemAprovacao.PENDENTE
    ]
    if pendentes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Ha itens aguardando aprovacao do cliente: "
                + ", ".join(pendentes)
                + ". Aprove ou reprove cada um antes de finalizar."
            ),
        )


def _assert_item_coerente(item: OSItemModel) -> None:
    """Peça embutida vale zero; item cobrado vale mais que zero.

    Espelha o validador de OSItemBase, para a regra valer também no PATCH — ver
    a explicação da invariante no modelo do item.
    """
    if not item.visivel_cliente and (item.valor_total or 0) != 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Peça embutida no serviço não é cobrada à parte: o valor dela deve ser zero",
        )
    if item.visivel_cliente and (item.valor_total or 0) <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Item cobrado do cliente precisa de valor maior que zero",
        )


def _assert_item_nao_gerado_pela_fabrica(item: OSItemModel) -> None:
    """409 no item que a aprovação do orçamento da fábrica gerou.

    Ele é a cópia congelada de uma versão aprovada: mexer aqui faria a OS
    divergir do orçamento que o cliente aceitou. Muda-se por uma nova versão
    (docs/marcenaria-fabrica-plano.md, D12). Item lançado à mão — o de toda OS
    fora da fábrica — tem `fabrica_orcamento_id` nulo e passa direto.
    """
    if item.fabrica_orcamento_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este item veio do orçamento aprovado da fábrica. Para mudá-lo, faça uma nova versão do orçamento.",
        )


def _item_conta_no_total(status: OrdemServicoItemAprovacao) -> bool:
    """Um item entra no total da OS a menos que esteja REPROVADO."""
    return status != OrdemServicoItemAprovacao.REPROVADO


def _recalcular_valor_total_os(os_in_db: OSModel) -> None:
    """
    Recalcula valor_bruto e valor_total com base nos itens atuais da OS.
    Itens REPROVADO são excluídos do total (fluxo de orçamento/oficina).
    Deve ser chamado sempre que itens ou desconto forem alterados.
    """
    valor_bruto = sum(
        item.valor_total for item in os_in_db.itens
        if _item_conta_no_total(item.status_aprovacao)
    )
    os_in_db.valor_bruto = valor_bruto
    os_in_db.valor_total = max(0, valor_bruto - (os_in_db.desconto or 0) + (os_in_db.taxa_entrega or 0) + (os_in_db.acrescimo or 0))
