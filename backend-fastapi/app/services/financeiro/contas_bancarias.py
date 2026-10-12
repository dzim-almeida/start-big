# ---------------------------------------------------------------------------
# ARQUIVO: services/financeiro/contas_bancarias.py
# DESCRICAO: Financeiro - contas bancarias (padrao semeado, listar, criar,
#            atualizar) e a conta padrao dos lancamentos.
# ---------------------------------------------------------------------------

from typing import Optional, Sequence
from sqlalchemy.orm import Session
from app.core.enum import (
    ContaBancariaTipo,
)
from app.core.tempo import agora_utc, hoje_local
from app.db.crud import financeiro as financeiro_crud
from app.db.models.conta_bancaria import ContaBancaria
from app.helpers.exceptions import BadRequestException, NotFoundException
from app.schemas.financeiro import ContaBancariaCreate, ContaBancariaUpdate


# ===========================================================================
# CONTAS BANCÁRIAS
# ===========================================================================

def _semear_conta_padrao(db: Session, empresa_id: int) -> None:
    """Garante ao menos 'Caixa da loja'.

    Sem nenhuma conta cadastrada, dar baixa exigiria criar uma antes -- e o
    lojista que só usa dinheiro nunca vai querer cadastrar banco nenhum. A
    gaveta é o mínimo que toda loja tem.
    """
    if db.query(ContaBancaria).filter(ContaBancaria.empresa_id == empresa_id).first():
        return
    financeiro_crud.criar_conta_bancaria(
        db,
        ContaBancaria(
            empresa_id=empresa_id,
            nome="Caixa da loja",
            tipo=ContaBancariaTipo.CAIXA.value,
            principal=True,
        ),
    )


def _conta_padrao_id(db: Session, empresa_id: int) -> Optional[int]:
    """A conta que recebe o dinheiro quando o lançamento não escolheu uma.

    Existe porque o saldo deixou de ser declarado e passou a ser derivado do
    livro: linha sem conta é dinheiro que entrou ou saiu e não aparece em saldo
    nenhum. Antes disso o campo era só um detalhe de auditoria e ficar nulo não
    custava nada.

    Semeia 'Caixa da loja' se não houver nenhuma, pela mesma razão de sempre --
    o lojista que só trabalha com dinheiro nunca vai cadastrar banco.
    """
    _semear_conta_padrao(db, empresa_id)
    conta = financeiro_crud.get_conta_principal(db, empresa_id)
    return conta.id if conta else None


def listar_contas_bancarias(
    db: Session, empresa_id: int, apenas_ativas: bool = False
) -> Sequence[ContaBancaria]:
    _semear_conta_padrao(db, empresa_id)
    return financeiro_crud.listar_contas_bancarias(db, empresa_id, apenas_ativas)


def criar_conta_bancaria(
    db: Session, empresa_id: int, dados: ContaBancariaCreate
) -> ContaBancaria:
    nome = dados.nome.strip()
    ja_existe = any(
        c.nome.lower() == nome.lower()
        for c in financeiro_crud.listar_contas_bancarias(db, empresa_id)
    )
    if ja_existe:
        raise BadRequestException(detail=f"Já existe uma conta chamada '{nome}'.")

    if dados.principal:
        financeiro_crud.limpar_principal(db, empresa_id)

    return financeiro_crud.criar_conta_bancaria(
        db,
        ContaBancaria(
            empresa_id=empresa_id, nome=nome, tipo=dados.tipo.value,
            principal=dados.principal,
        ),
    )


def atualizar_conta_bancaria(
    db: Session, empresa_id: int, conta_id: int, dados: ContaBancariaUpdate
) -> ContaBancaria:
    conta = financeiro_crud.get_conta_bancaria(db, empresa_id, conta_id)
    if not conta:
        raise NotFoundException(detail="Conta não encontrada")

    if dados.nome is not None:
        conta.nome = dados.nome.strip()
    if dados.tipo is not None:
        conta.tipo = dados.tipo.value
    if dados.ativo is not None:
        conta.ativo = dados.ativo
    if dados.principal is not None:
        if dados.principal:
            financeiro_crud.limpar_principal(db, empresa_id, exceto_id=conta.id)
        conta.principal = dados.principal

    if dados.saldo_informado is not None:
        # A data é carimbada AQUI, e não recebida do cliente: ela é a prova de
        # quando o retrato foi tirado, e o Fluxo de Caixa avisa quando envelhece.
        # Deixar o cliente mandar a data permitiria declarar hoje um saldo
        # "de ontem" e o aviso nunca aparecer.
        conta.saldo_informado = dados.saldo_informado
        conta.saldo_informado_em = hoje_local()
        # E o INSTANTE, que é o corte de verdade do saldo derivado: só entra no
        # saldo o movimento posterior a ele. Sem isto, quem declara o saldo às
        # 15h veria a venda das 10h somada de novo -- ela já estava dentro do
        # número que ele contou na gaveta.
        conta.saldo_informado_instante = agora_utc()

    db.flush()
    return conta
