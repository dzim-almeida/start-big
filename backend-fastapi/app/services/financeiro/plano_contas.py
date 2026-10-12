# ---------------------------------------------------------------------------
# ARQUIVO: services/financeiro/plano_contas.py
# DESCRICAO: Financeiro - plano de contas (padrao semeado, listar, criar, atualizar).
# ---------------------------------------------------------------------------

from typing import Any, Dict, List
from sqlalchemy.orm import Session
from app.core.enum import (
    PlanoContaTipo,
)
from app.db.crud import financeiro as financeiro_crud
from app.db.models.plano_conta import PlanoConta
from app.helpers.exceptions import BadRequestException, NotFoundException
from app.schemas.financeiro import PlanoContaCreate, PlanoContaUpdate


# ===========================================================================
# PLANO DE CONTAS
# ===========================================================================

# Semeadas no primeiro acesso. Não é adivinhação de negócio: são as despesas que
# TODA loja tem, independente do segmento -- a oficina, a assistência e a
# serigrafia pagam aluguel, luz e fornecedor igual.
#
# Existem porque um plano de contas vazio trava o módulo no primeiro uso: o
# lojista abre Contas a Pagar, vê que precisa de categoria, vai criar categoria,
# e desiste no meio. Ele pode apagar as que não usa; ver a lista e cortar é
# muito mais fácil do que encarar o branco.
# A PRIMEIRA É CUSTO, e não despesa: comprar mercadoria não empobrece a loja,
# converte dinheiro em estoque. Ela sai do caixa no dia da compra e só sai do
# LUCRO no dia em que a peça é vendida, pelo CMV -- classificá-la como despesa
# descontava a mesma peça duas vezes. Ver PlanoContaTipo e a migration
# f4a5b6c7d8e9, que reclassificou as lojas que já existiam.
PLANO_CONTAS_PADRAO: List[tuple[str, PlanoContaTipo]] = [
    ("Fornecedores / Mercadoria", PlanoContaTipo.CUSTO),
    ("Aluguel", PlanoContaTipo.DESPESA),
    ("Água, luz e internet", PlanoContaTipo.DESPESA),
    ("Salários e encargos", PlanoContaTipo.DESPESA),
    ("Impostos e taxas", PlanoContaTipo.DESPESA),
    ("Manutenção e equipamentos", PlanoContaTipo.DESPESA),
    ("Marketing", PlanoContaTipo.DESPESA),
    ("Outras despesas", PlanoContaTipo.DESPESA),
]


def _semear_plano_padrao(db: Session, empresa_id: int) -> None:
    """Cria as categorias padrão, uma única vez na vida da empresa.

    Roda na LISTAGEM, e não na criação da empresa, para alcançar também as lojas
    que já existem -- nenhuma delas passou por um `setup` que soubesse do módulo
    financeiro.

    A condição é "nunca semeou", e não "a lista está vazia": semear pela lista
    vazia faria as categorias ressuscitarem toda vez que o lojista apagasse
    todas, e ele nunca conseguiria dizer "não quero nenhuma dessas".
    """
    ja_semeou = (
        db.query(PlanoConta)
        .filter(PlanoConta.empresa_id == empresa_id, PlanoConta.padrao.is_(True))
        .first()
    )
    if ja_semeou:
        return

    # Se a loja já criou categoria à mão, ela não é uma instalação virgem —
    # semear por cima só empurraria itens que ela não pediu.
    tem_alguma = (
        db.query(PlanoConta).filter(PlanoConta.empresa_id == empresa_id).first()
    )
    if tem_alguma:
        return

    for nome, tipo in PLANO_CONTAS_PADRAO:
        financeiro_crud.criar_plano_conta(
            db,
            PlanoConta(
                empresa_id=empresa_id, nome=nome, tipo=tipo.value, padrao=True, ativo=True
            ),
        )


def listar_planos_conta(
    db: Session, empresa_id: int, apenas_ativos: bool = False
) -> List[Dict[str, Any]]:
    _semear_plano_padrao(db, empresa_id)

    planos = financeiro_crud.listar_planos_conta(db, empresa_id, apenas_ativos)
    em_uso = financeiro_crud.ids_de_planos_em_uso(db, empresa_id)

    return [
        {
            "id": p.id,
            "nome": p.nome,
            "tipo": p.tipo,
            "padrao": p.padrao,
            "ativo": p.ativo,
            "criado_em": p.criado_em,
            "em_uso": p.id in em_uso,
        }
        for p in planos
    ]


def criar_plano_conta(
    db: Session, empresa_id: int, dados: PlanoContaCreate
) -> Dict[str, Any]:
    nome = dados.nome.strip()
    if financeiro_crud.get_plano_conta_por_nome(db, empresa_id, nome):
        raise BadRequestException(detail=f"Já existe uma categoria chamada '{nome}'.")

    plano = financeiro_crud.criar_plano_conta(
        db, PlanoConta(empresa_id=empresa_id, nome=nome, tipo=dados.tipo.value)
    )
    return {
        "id": plano.id, "nome": plano.nome, "tipo": plano.tipo, "padrao": plano.padrao,
        "ativo": plano.ativo, "criado_em": plano.criado_em, "em_uso": False,
    }


def atualizar_plano_conta(
    db: Session, empresa_id: int, plano_id: int, dados: PlanoContaUpdate
) -> Dict[str, Any]:
    plano = financeiro_crud.get_plano_conta(db, empresa_id, plano_id)
    if not plano:
        raise NotFoundException(detail="Categoria não encontrada")

    if dados.nome is not None:
        nome = dados.nome.strip()
        existente = financeiro_crud.get_plano_conta_por_nome(db, empresa_id, nome)
        if existente and existente.id != plano.id:
            raise BadRequestException(detail=f"Já existe uma categoria chamada '{nome}'.")
        plano.nome = nome

    if dados.tipo is not None and dados.tipo.value != plano.tipo:
        # DESPESA <-> CUSTO é correção de classificação: as duas são saída, e o
        # que muda é QUANDO o gasto sai do lucro (no dia da compra ou no dia da
        # venda, pelo CMV). Recalcular meses passados com a regra certa é o
        # ponto, não um efeito colateral.
        #
        # Envolver RECEITA numa categoria já lançada é outra coisa: inverte o
        # sinal do dinheiro e transformaria despesa em receita no relatório sem
        # ninguém ter tocado numa conta.
        vira_receita = PlanoContaTipo.RECEITA.value in (dados.tipo.value, plano.tipo)
        if vira_receita and plano.id in financeiro_crud.ids_de_planos_em_uso(
            db, empresa_id
        ):
            raise BadRequestException(
                detail=(
                    "Esta categoria já tem contas lançadas e não pode virar (ou "
                    "deixar de ser) receita. Crie uma categoria nova."
                )
            )
        plano.tipo = dados.tipo.value

    if dados.ativo is not None:
        plano.ativo = dados.ativo

    db.flush()
    em_uso = plano.id in financeiro_crud.ids_de_planos_em_uso(db, empresa_id)
    return {
        "id": plano.id, "nome": plano.nome, "tipo": plano.tipo, "padrao": plano.padrao,
        "ativo": plano.ativo, "criado_em": plano.criado_em, "em_uso": em_uso,
    }
