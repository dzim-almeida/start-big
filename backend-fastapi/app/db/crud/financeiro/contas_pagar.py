# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/financeiro/contas_pagar.py
# DESCRICAO: Financeiro (banco) - contas a pagar: consulta, totais, criacao,
#            recorrencia, parcelas e exclusao.
# ---------------------------------------------------------------------------

from datetime import date
from typing import Optional, Sequence, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.core.enum import (
    ContaPagarStatus,
)
from app.db.models.conta_pagar import ContaPagar


# ===========================================================================
# CONTAS A PAGAR
# ===========================================================================

def _query_contas(
    db: Session,
    empresa_id: int,
    *,
    status: Optional[str] = None,
    inicio: Optional[date] = None,
    fim: Optional[date] = None,
    plano_conta_id: Optional[int] = None,
    fornecedor_id: Optional[int] = None,
    busca: Optional[str] = None,
    vencidas: bool = False,
    sem_categoria: bool = False,
    hoje: Optional[date] = None,
):
    """Base compartilhada pela listagem e pelos totais.

    Os dois PRECISAM sair da mesma query: se a soma usasse um filtro e a lista
    outro, o rodapé mostraria um total que não corresponde ao que está na tela —
    e ninguém confia num módulo financeiro depois de ver isso uma vez.
    """
    q = db.query(ContaPagar).filter(ContaPagar.empresa_id == empresa_id)

    if status:
        q = q.filter(ContaPagar.status == status)
    # O período filtra por VENCIMENTO, não por criação: a pergunta da tela é
    # "o que vence neste mês", não "o que eu digitei neste mês".
    if inicio:
        q = q.filter(ContaPagar.vencimento >= inicio)
    if fim:
        q = q.filter(ContaPagar.vencimento <= fim)
    if plano_conta_id:
        q = q.filter(ContaPagar.plano_conta_id == plano_conta_id)
    if fornecedor_id:
        q = q.filter(ContaPagar.fornecedor_id == fornecedor_id)
    if busca:
        termo = f"%{busca.strip()}%"
        q = q.filter(ContaPagar.descricao.ilike(termo))

    # Os dois recortes que o painel de atenção usa para levar o dono DIRETO às
    # linhas do alerta. Sem eles, "Ver contas a pagar" abre a lista inteira e o
    # dono procura a agulha que o sistema já sabia apontar.
    if vencidas:
        q = q.filter(
            ContaPagar.status == ContaPagarStatus.PENDENTE.value,
            ContaPagar.vencimento < (hoje or date.today()),
        )
    if sem_categoria:
        q = q.filter(ContaPagar.plano_conta_id.is_(None))

    return q


def listar_contas_pagar(
    db: Session,
    empresa_id: int,
    *,
    status: Optional[str] = None,
    inicio: Optional[date] = None,
    fim: Optional[date] = None,
    plano_conta_id: Optional[int] = None,
    fornecedor_id: Optional[int] = None,
    busca: Optional[str] = None,
    vencidas: bool = False,
    sem_categoria: bool = False,
    limit: int = 200,
    offset: int = 0,
) -> Tuple[Sequence[ContaPagar], int]:
    """Devolve a página e a contagem TOTAL do filtro (não a da página)."""
    q = _query_contas(
        db, empresa_id, status=status, inicio=inicio, fim=fim,
        plano_conta_id=plano_conta_id, fornecedor_id=fornecedor_id, busca=busca,
        vencidas=vencidas, sem_categoria=sem_categoria,
    )
    total = q.count()

    itens = (
        q.options(
            # Sem isto a serialização dispara uma consulta por linha só para ler
            # o nome da categoria e do fornecedor.
            joinedload(ContaPagar.plano_conta),
            joinedload(ContaPagar.fornecedor),
            joinedload(ContaPagar.conta_bancaria),
        )
        # Mais urgente primeiro: quem abre a tela quer ver o que vence antes.
        .order_by(ContaPagar.vencimento.asc(), ContaPagar.id.asc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return itens, total


def totais_contas_pagar(
    db: Session,
    empresa_id: int,
    *,
    hoje: date,
    inicio: Optional[date] = None,
    fim: Optional[date] = None,
    plano_conta_id: Optional[int] = None,
    fornecedor_id: Optional[int] = None,
    busca: Optional[str] = None,
    vencidas: bool = False,
    sem_categoria: bool = False,
) -> Tuple[int, int, int]:
    """(pendente, pago, vencido) do filtro — sem o recorte de status.

    O status é excluído aqui de propósito: o rodapé mostra os três números lado
    a lado, e aplicar o filtro de status faria dois deles virarem zero sempre
    que o usuário filtrasse por um.
    """
    def _soma(coluna, *extra):
        q = _query_contas(
            db, empresa_id, inicio=inicio, fim=fim,
            plano_conta_id=plano_conta_id, fornecedor_id=fornecedor_id, busca=busca,
            vencidas=vencidas, sem_categoria=sem_categoria, hoje=hoje,
        )
        for condicao in extra:
            q = q.filter(condicao)
        return q.with_entities(func.coalesce(func.sum(coluna), 0)).scalar() or 0

    pendente = _soma(ContaPagar.valor, ContaPagar.status == ContaPagarStatus.PENDENTE.value)
    # Soma `valor_pago` e não `valor`: o que interessa no realizado é o que saiu
    # do bolso, com juros de atraso e desconto já dentro.
    pago = _soma(ContaPagar.valor_pago, ContaPagar.status == ContaPagarStatus.PAGA.value)
    vencido = _soma(
        ContaPagar.valor,
        ContaPagar.status == ContaPagarStatus.PENDENTE.value,
        ContaPagar.vencimento < hoje,
    )
    return int(pendente), int(pago), int(vencido)


def get_conta_pagar(db: Session, empresa_id: int, conta_id: int) -> Optional[ContaPagar]:
    return (
        db.query(ContaPagar)
        .options(
            joinedload(ContaPagar.plano_conta),
            joinedload(ContaPagar.fornecedor),
            joinedload(ContaPagar.conta_bancaria),
        )
        .filter(ContaPagar.id == conta_id, ContaPagar.empresa_id == empresa_id)
        .first()
    )


def criar_conta_pagar(db: Session, conta: ContaPagar) -> ContaPagar:
    db.add(conta)
    db.flush()
    return conta


def get_ocorrencia_gerada(
    db: Session, empresa_id: int, conta_id: int
) -> Optional[ContaPagar]:
    """A ocorrência que a baixa desta conta gerou pela recorrência, se houver.

    Serve para os dois lados do problema: impedir que pagar de novo crie uma
    segunda, e permitir que o estorno remova a que aquele pagamento criou.
    """
    return (
        db.query(ContaPagar)
        .filter(
            ContaPagar.empresa_id == empresa_id,
            ContaPagar.gerada_por_id == conta_id,
        )
        .first()
    )


def apagar_conta(db: Session, conta: ContaPagar) -> None:
    """Remove a linha de vez.

    EXCEÇÃO ÚNICA à regra de "cancela, não exclui" -- e as três condições são
    verificadas pelo serviço antes de chegar aqui: a conta foi criada pelo
    SISTEMA (não por uma pessoa), continua PENDENTE (nenhum dinheiro andou), e
    está sendo removida ao desfazer exatamente o pagamento que a criou.

    Cancelar em vez de apagar deixaria um fantasma "Cancelada" na lista a cada
    estorno, de uma conta que ninguém lançou -- ruído sem verdade nenhuma dentro.
    """
    db.delete(conta)
    db.flush()


def proximas_a_vencer(
    db: Session, empresa_id: int, *, ate: date, limite: int = 5
) -> Sequence[ContaPagar]:
    """Pendentes vencendo até `ate`, incluindo as JÁ vencidas.

    As atrasadas entram na mesma lista porque são as mais urgentes de todas —
    separá-las num painel próprio esconderia justamente o que não pode ser
    esquecido.
    """
    return (
        db.query(ContaPagar)
        .options(joinedload(ContaPagar.plano_conta), joinedload(ContaPagar.fornecedor))
        .filter(
            ContaPagar.empresa_id == empresa_id,
            ContaPagar.status == ContaPagarStatus.PENDENTE.value,
            ContaPagar.vencimento <= ate,
        )
        .order_by(ContaPagar.vencimento.asc(), ContaPagar.id.asc())
        .limit(limite)
        .all()
    )


def listar_parcelas_seguintes(
    db: Session, empresa_id: int, parcelamento_id: int, numero_atual: int
) -> Sequence[ContaPagar]:
    """As parcelas DEPOIS desta, do MESMO parcelamento, que ainda estao em aberto.

    Os tres recortes existem para a correcao em massa nao causar estrago: outra
    divida do mesmo fornecedor nao e alcancada, o passado nao se reescreve, e
    parcela paga fica congelada porque ja virou lancamento no livro.
    """
    return (
        db.query(ContaPagar)
        .filter(
            ContaPagar.empresa_id == empresa_id,
            ContaPagar.parcelamento_id == parcelamento_id,
            ContaPagar.parcela_numero > numero_atual,
            ContaPagar.status == ContaPagarStatus.PENDENTE.value,
        )
        .order_by(ContaPagar.parcela_numero.asc())
        .all()
    )
