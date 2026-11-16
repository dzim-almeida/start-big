# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/financeiro/contas_bancarias.py
# DESCRICAO: Financeiro (banco) - contas bancarias e a conta principal.
# ---------------------------------------------------------------------------

from typing import Optional, Sequence
from sqlalchemy.orm import Session
from app.db.models.conta_bancaria import ContaBancaria


# ===========================================================================
# CONTAS BANCÁRIAS
# ===========================================================================

def listar_contas_bancarias(
    db: Session, empresa_id: int, apenas_ativas: bool = False
) -> Sequence[ContaBancaria]:
    q = db.query(ContaBancaria).filter(ContaBancaria.empresa_id == empresa_id)
    if apenas_ativas:
        q = q.filter(ContaBancaria.ativo.is_(True))
    return q.order_by(ContaBancaria.principal.desc(), ContaBancaria.nome.asc()).all()


def get_conta_principal(db: Session, empresa_id: int) -> Optional[ContaBancaria]:
    """A conta para onde o dinheiro vai quando ninguém escolheu uma.

    Venda e OS não perguntam em que conta o dinheiro caiu -- e não devem
    perguntar: ninguém vai responder isso no balcão, com o cliente esperando. O
    lançamento precisa de um endereço mesmo assim, senão o saldo derivado
    ignora a venda inteira.

    A marcada como principal; na falta dela, a primeira ativa (a listagem já
    ordena com a principal na frente). NULL só numa empresa sem conta nenhuma,
    e isso não acontece na prática: `_semear_conta_padrao` cria 'Caixa da loja'
    na primeira listagem.
    """
    return (
        db.query(ContaBancaria)
        .filter(
            ContaBancaria.empresa_id == empresa_id,
            ContaBancaria.ativo.is_(True),
        )
        .order_by(ContaBancaria.principal.desc(), ContaBancaria.id.asc())
        .first()
    )


def get_conta_bancaria(
    db: Session, empresa_id: int, conta_id: int
) -> Optional[ContaBancaria]:
    return (
        db.query(ContaBancaria)
        .filter(ContaBancaria.id == conta_id, ContaBancaria.empresa_id == empresa_id)
        .first()
    )


def criar_conta_bancaria(db: Session, conta: ContaBancaria) -> ContaBancaria:
    db.add(conta)
    db.flush()
    return conta


def limpar_principal(db: Session, empresa_id: int, exceto_id: Optional[int] = None) -> None:
    """Tira a marca de principal das demais contas.

    Só uma conta pode ser a sugerida. Sem isto, marcar a segunda deixaria duas
    principais e a tela escolheria pela ordem do banco, que é arbitrária.
    """
    q = db.query(ContaBancaria).filter(
        ContaBancaria.empresa_id == empresa_id,
        ContaBancaria.principal.is_(True),
    )
    if exceto_id is not None:
        q = q.filter(ContaBancaria.id != exceto_id)
    q.update({ContaBancaria.principal: False}, synchronize_session=False)
