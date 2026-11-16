# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/financeiro/conciliacao.py
# DESCRICAO: Financeiro (banco) - baixa automatica vencida e as formas de
#            pagamento de origem (conciliacao).
# ---------------------------------------------------------------------------

from datetime import date
from typing import Sequence, Tuple
from sqlalchemy.orm import Session
from app.core.enum import (
    ContaReceberStatus,
)
from app.db.models.conta_receber import ContaReceber
from app.db.models.forma_pagamento import FormaPagamento
from app.db.models.ordem_servico_pagamento import OrdemServicoPagamento
from app.db.models.venda_pagamento import PagamentoVenda


def listar_baixas_automaticas_vencidas(
    db: Session, *, hoje: date, limite: int = 500
) -> Sequence[ContaReceber]:
    """Cobrancas marcadas para entrar sozinhas cujo dia ja chegou.

    `<= hoje` e nao `== hoje`: e o que permite a tarefa se recuperar sozinha
    depois de um fim de semana com a maquina desligada. Ver
    `financeiro_receber.baixar_automaticas`.

    ORDENADAS PELO VENCIMENTO, da mais antiga para a mais nova, para o extrato
    contar a historia na ordem em que ela aconteceu.

    O limite existe para o primeiro boot depois de a loja declarar um prazo: se
    houver represa, ela escoa em levas em vez de uma transacao gigante.
    """
    return (
        db.query(ContaReceber)
        .filter(
            ContaReceber.status == ContaReceberStatus.PENDENTE.value,
            ContaReceber.baixa_automatica.is_(True),
            ContaReceber.vencimento <= hoje,
        )
        .order_by(ContaReceber.vencimento.asc(), ContaReceber.id.asc())
        .limit(limite)
        .all()
    )


def formas_de_origem_completas(
    db: Session, *, venda_pagamento_ids: Sequence[int], os_pagamento_ids: Sequence[int]
) -> dict:
    """pagamento_id -> a FormaPagamento inteira (nao so o nome).

    A gemea `formas_de_origem` devolve o nome, que e o que a tela mostra. A
    baixa automatica precisa do OBJETO: e nele que estao `conta_bancaria_id` (em
    que conta o dinheiro cai) e o proprio id, para o movimento nascer sabendo
    como o cliente pagou.

    Chave unica para os dois lados porque ids de pagamento de venda e de OS
    vivem em tabelas diferentes e podem colidir -- quem chama sabe qual dos dois
    a cobranca tem, e so um deles e nao-nulo em cada linha.
    """
    mapa: dict = {}

    if venda_pagamento_ids:
        linhas = (
            db.query(PagamentoVenda.id, FormaPagamento)
            .join(FormaPagamento, FormaPagamento.id == PagamentoVenda.forma_pagamento_id)
            .filter(PagamentoVenda.id.in_(venda_pagamento_ids))
            .all()
        )
        mapa.update({pid: forma for pid, forma in linhas})

    if os_pagamento_ids:
        linhas = (
            db.query(OrdemServicoPagamento.id, FormaPagamento)
            .join(
                FormaPagamento,
                FormaPagamento.id == OrdemServicoPagamento.forma_pagamento_id,
            )
            .filter(OrdemServicoPagamento.id.in_(os_pagamento_ids))
            .all()
        )
        mapa.update({pid: forma for pid, forma in linhas})

    return mapa


def formas_de_origem(
    db: Session, *, venda_pagamento_ids: Sequence[int], os_pagamento_ids: Sequence[int]
) -> Tuple[dict, dict]:
    """Nome da forma que originou cada cobranca, em DUAS consultas para a lista toda.

    A conta a receber nao guarda a forma de origem -- ela nasce do pagamento, e
    e o pagamento que sabe se foi cartao, PIX ou dinheiro a prazo. Perguntar
    item a item seria o N+1 classico numa tela que lista o mes inteiro.
    """
    por_venda: dict = {}
    por_os: dict = {}

    if venda_pagamento_ids:
        linhas = (
            db.query(PagamentoVenda.id, FormaPagamento.nome)
            .join(FormaPagamento, FormaPagamento.id == PagamentoVenda.forma_pagamento_id)
            .filter(PagamentoVenda.id.in_(venda_pagamento_ids))
            .all()
        )
        por_venda = {pid: nome for pid, nome in linhas}

    if os_pagamento_ids:
        linhas = (
            db.query(OrdemServicoPagamento.id, FormaPagamento.nome)
            .join(FormaPagamento, FormaPagamento.id == OrdemServicoPagamento.forma_pagamento_id)
            .filter(OrdemServicoPagamento.id.in_(os_pagamento_ids))
            .all()
        )
        por_os = {pid: nome for pid, nome in linhas}

    return por_venda, por_os
