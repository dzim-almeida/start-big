# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/sessao_caixa/livro_dinheiro.py
# DESCRICAO: Caixa (crud) - movimentos e somas do livro do dinheiro.
# ---------------------------------------------------------------------------

from typing import List, Optional, Sequence
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.enum import (
    MovimentacaoFinanceiraOrigem,
    MovimentacaoFinanceiraTipo,
)
from app.db.models.forma_pagamento import FormaPagamento
from app.db.models.movimentacao_financeira import MovimentacaoFinanceira


# ===========================================================================
# LIVRO DO DINHEIRO
# ===========================================================================

def registrar_movimento(
    db: Session,
    tipo: MovimentacaoFinanceiraTipo,
    origem: MovimentacaoFinanceiraOrigem,
    valor: int,
    sessao_caixa_id: Optional[int] = None,
    conta_bancaria_id: Optional[int] = None,
    forma_pagamento_id: Optional[int] = None,
    venda_pagamento_id: Optional[int] = None,
    ordem_servico_pagamento_id: Optional[int] = None,
    funcionario_id: Optional[int] = None,
    funcionario_nome: Optional[str] = None,
    motivo: Optional[str] = None,
) -> MovimentacaoFinanceira:
    """O ÚNICO lugar que escreve no livro do dinheiro.

    Mesmo papel do `registrar_movimentacao()` no estoque: concentrar a escrita
    num ponto só é o que impede uma linha de dinheiro nascer sem origem ou sem
    dono, e é o que permite auditar depois.

    `conta_bancaria_id` chegou em 02/09/2026, quando o saldo da conta deixou de
    ser foto declarada e passou a ser derivado do livro. Antes disso o parâmetro
    não existia e só `pagar_conta` preenchia a coluna à mão, depois de gravar --
    ou seja, TODA venda e TODA OS nasciam sem endereço, e um saldo derivado
    dessas linhas ignoraria a receita inteira.

    Continua opcional, e NULO é resposta legítima em dois casos: a abertura e a
    sangria, que mexem na gaveta e não no total da loja (ver `ORIGENS_DE_SALDO`
    em crud/financeiro_receber.py), e a loja que ainda não tem conta cadastrada.
    """
    movimento = MovimentacaoFinanceira(
        tipo=tipo.value,
        origem=origem.value,
        valor=valor,
        sessao_caixa_id=sessao_caixa_id,
        conta_bancaria_id=conta_bancaria_id,
        forma_pagamento_id=forma_pagamento_id,
        venda_pagamento_id=venda_pagamento_id,
        ordem_servico_pagamento_id=ordem_servico_pagamento_id,
        funcionario_id=funcionario_id,
        funcionario_nome=funcionario_nome,
        motivo=motivo,
    )
    db.add(movimento)
    db.flush()
    return movimento


def listar_movimentos_da_sessao(db: Session, sessao_id: int) -> Sequence[MovimentacaoFinanceira]:
    return (
        db.query(MovimentacaoFinanceira)
        .filter(MovimentacaoFinanceira.sessao_caixa_id == sessao_id)
        .order_by(MovimentacaoFinanceira.criado_em.asc(), MovimentacaoFinanceira.id.asc())
        .all()
    )


def somar_por_origem(db: Session, sessao_id: int) -> dict:
    """Totais do turno agrupados por origem. Chaves ausentes valem zero."""
    linhas = (
        db.query(
            MovimentacaoFinanceira.origem,
            func.coalesce(func.sum(MovimentacaoFinanceira.valor), 0),
        )
        .filter(MovimentacaoFinanceira.sessao_caixa_id == sessao_id)
        .group_by(MovimentacaoFinanceira.origem)
        .all()
    )
    return {origem: total for origem, total in linhas}


def somar_por_forma_pagamento(db: Session, sessao_id: int) -> List[tuple]:
    """(forma_id, nome, total) das ENTRADAS do turno.

    Só entradas: é o que o operador confere contra o que recebeu. Sangria e
    suprimento aparecem separados no resumo, porque não são recebimento de
    ninguém.
    """
    return (
        db.query(
            MovimentacaoFinanceira.forma_pagamento_id,
            func.coalesce(FormaPagamento.nome, "Não informada"),
            func.coalesce(func.sum(MovimentacaoFinanceira.valor), 0),
        )
        .outerjoin(
            FormaPagamento,
            FormaPagamento.id == MovimentacaoFinanceira.forma_pagamento_id,
        )
        .filter(
            MovimentacaoFinanceira.sessao_caixa_id == sessao_id,
            MovimentacaoFinanceira.tipo == MovimentacaoFinanceiraTipo.ENTRADA.value,
            MovimentacaoFinanceira.origem.in_(
                [
                    MovimentacaoFinanceiraOrigem.VENDA.value,
                    MovimentacaoFinanceiraOrigem.ORDEM_SERVICO.value,
                    MovimentacaoFinanceiraOrigem.RECEBIMENTO.value,
                ]
            ),
        )
        .group_by(MovimentacaoFinanceira.forma_pagamento_id, FormaPagamento.nome)
        .all()
    )


def somar_dinheiro_em_especie(db: Session, sessao_id: int, formas_dinheiro: Sequence[int]) -> int:
    """Entradas do turno que foram em DINHEIRO — as únicas que estão na gaveta.

    Cartão e PIX entram no faturamento mas não no que se conta na mão. Sem essa
    separação o fechamento acusaria diferença todo dia.
    """
    return _somar_em_especie(
        db, sessao_id, formas_dinheiro, MovimentacaoFinanceiraTipo.ENTRADA
    )


def somar_saidas_em_especie(
    db: Session, sessao_id: int, formas_dinheiro: Sequence[int]
) -> int:
    """Saídas do turno que tiraram dinheiro da gaveta.

    A sangria é a mais comum, mas não é a única: o estorno de uma OS reaberta
    sem pagamento real também devolve dinheiro que nunca entrou. Somar por TIPO
    em vez de por origem faz qualquer saída futura já entrar na conta certa,
    sem alguém precisar lembrar de acrescentá-la aqui.
    """
    return _somar_em_especie(
        db, sessao_id, formas_dinheiro, MovimentacaoFinanceiraTipo.SAIDA
    )


def _somar_em_especie(
    db: Session,
    sessao_id: int,
    formas_dinheiro: Sequence[int],
    tipo: MovimentacaoFinanceiraTipo,
) -> int:
    if not formas_dinheiro:
        return 0
    total = (
        db.query(func.coalesce(func.sum(MovimentacaoFinanceira.valor), 0))
        .filter(
            MovimentacaoFinanceira.sessao_caixa_id == sessao_id,
            MovimentacaoFinanceira.tipo == tipo.value,
            MovimentacaoFinanceira.forma_pagamento_id.in_(formas_dinheiro),
        )
        .scalar()
    )
    return int(total or 0)


def existe_movimento_do_pagamento(
    db: Session,
    *,
    venda_pagamento_id: Optional[int] = None,
    ordem_servico_pagamento_id: Optional[int] = None,
) -> bool:
    """Este pagamento já virou ENTRADA no livro?

    É a prova de que o dinheiro chegou a entrar, e substitui o antigo atalho
    "tem sessão, logo entrou" -- que deixou de valer quando venda e OS passaram
    a lançar também sem caixa aberto. O estorno precisa desta resposta: devolver
    o que nunca entrou criaria uma saída sem par no extrato.

    Só ENTRADA: a linha de estorno é SAIDA e não carrega o id do pagamento, mas
    filtrar pelo tipo deixa a intenção explícita para quem ler depois.
    """
    q = db.query(MovimentacaoFinanceira.id).filter(
        MovimentacaoFinanceira.tipo == MovimentacaoFinanceiraTipo.ENTRADA.value
    )
    if venda_pagamento_id is not None:
        q = q.filter(MovimentacaoFinanceira.venda_pagamento_id == venda_pagamento_id)
    elif ordem_servico_pagamento_id is not None:
        q = q.filter(
            MovimentacaoFinanceira.ordem_servico_pagamento_id == ordem_servico_pagamento_id
        )
    else:
        return False
    return q.first() is not None
