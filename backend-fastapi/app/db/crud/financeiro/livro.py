# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/financeiro/livro.py
# DESCRICAO: Financeiro (banco) - o que entrou e saiu do caixa (origens de
#            receita e de saldo).
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Tuple
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from app.core.enum import (
    MovimentacaoFinanceiraOrigem,
    MovimentacaoFinanceiraTipo,
)
from app.db.models.movimentacao_financeira import MovimentacaoFinanceira
from app.db.crud.financeiro.extrato import _query_extrato


# Origens que representam dinheiro de CLIENTE. Abertura, sangria e suprimento
# ficam de fora: são movimento da gaveta, não receita -- somar o troco inicial
# faria a loja "receber" o próprio dinheiro toda manhã.
ORIGENS_DE_RECEITA = (
    MovimentacaoFinanceiraOrigem.VENDA.value,
    MovimentacaoFinanceiraOrigem.ORDEM_SERVICO.value,
    MovimentacaoFinanceiraOrigem.RECEBIMENTO.value,
)


# As origens que MUDAM QUANTO A LOJA TEM. É a receita mais a despesa paga.
#
# O QUE FICA DE FORA, e é a regra inteira desta lista: ABERTURA, SANGRIA e
# SUPRIMENTO são TRANSFERÊNCIA, não dinheiro entrando ou saindo da loja. O troco
# da abertura já estava no cofre ontem; a sangria tira da gaveta e põe no cofre.
# Somá-los ao saldo criaria dinheiro do nada todo dia em que o caixa abre, e o
# erro cresceria sem parar -- porque o troco de abertura entra de novo amanhã.
#
# E é pior no caso da sangria feita para pagar um boleto: o pagamento já sai
# como DESPESA, então contar a sangria também tiraria o mesmo dinheiro duas
# vezes. É a mesma razão pela qual `pagar_conta` deixa `sessao_caixa_id` nulo de
# propósito -- "pagar fornecedor não é sangria".
ORIGENS_DE_SALDO = ORIGENS_DE_RECEITA + (MovimentacaoFinanceiraOrigem.DESPESA.value,)


def entradas_e_saidas_desde(
    db: Session,
    empresa_id: int,
    *,
    conta_id: int,
    desde: datetime,
    incluir_sem_conta: bool = False,
) -> Tuple[int, int]:
    """(entrou, saiu) nesta conta DEPOIS de `desde`. Os dois positivos.

    DEVOLVE AS DUAS METADES, e nao o liquido, porque a tela mostra as duas: o
    dono perguntou "cade o dinheiro que entrou?" olhando um card que so dizia
    quanto o saldo tinha mudado no total. Um numero liquido de zero pode ser
    "nada aconteceu" ou "entraram 500 e sairam 500", e as duas leituras exigem
    reacoes opostas.

    É a segunda metade do saldo: a primeira é a âncora que o dono declarou, e
    esta é tudo que aconteceu desde então. Entrada soma, saída subtrai.

    `incluir_sem_conta` recolhe as linhas com `conta_bancaria_id` NULO. Elas
    existem por dois motivos e nenhum deles é dinheiro de mentira: as antigas,
    lançadas quando `registrar_movimento` nem aceitava conta, e as de uma loja
    que apagou a conta para onde apontavam (a FK é SET NULL, para linha de
    dinheiro nunca sumir). Descartá-las faria o saldo derivado ficar ABAIXO do
    real, que é justamente o defeito que este código veio corrigir -- então elas
    caem na conta PRINCIPAL, que é para onde os lançamentos novos vão.

    O corte é EXCLUSIVO (`>`), não inclusivo: o movimento do mesmo instante da
    declaração já está dentro do número que o dono contou na gaveta.
    """
    alvo = MovimentacaoFinanceira.conta_bancaria_id == conta_id
    if incluir_sem_conta:
        alvo = or_(alvo, MovimentacaoFinanceira.conta_bancaria_id.is_(None))

    def _soma(tipo: str) -> int:
        return int(
            db.query(func.coalesce(func.sum(MovimentacaoFinanceira.valor), 0))
            .filter(
                alvo,
                MovimentacaoFinanceira.criado_em > desde,
                MovimentacaoFinanceira.tipo == tipo,
                MovimentacaoFinanceira.origem.in_(ORIGENS_DE_SALDO),
            )
            .scalar()
            or 0
        )

    return (
        _soma(MovimentacaoFinanceiraTipo.ENTRADA.value),
        _soma(MovimentacaoFinanceiraTipo.SAIDA.value),
    )


def total_entrou_no_caixa(db: Session, empresa_id: int, inicio, fim) -> int:
    """Quanto dinheiro de cliente ANDOU no período, pelo livro.

    É o contraponto de `faturamento` (que sai das tabelas de venda e OS, por
    COMPETÊNCIA): aqui só conta o que passou pelo caixa, venha da venda de hoje
    ou do fiado do mês passado.

    Desconta as SAÍDAS das mesmas origens, que são os estornos -- sem isso, uma
    OS reaberta deixaria para trás dinheiro que voltou para o cliente.
    """
    def _soma(tipo: str) -> int:
        return int(
            _query_extrato(db, empresa_id, inicio=inicio, fim=fim, tipo=tipo)
            .filter(MovimentacaoFinanceira.origem.in_(ORIGENS_DE_RECEITA))
            .with_entities(func.coalesce(func.sum(MovimentacaoFinanceira.valor), 0))
            .scalar()
            or 0
        )

    return _soma(MovimentacaoFinanceiraTipo.ENTRADA.value) - _soma(
        MovimentacaoFinanceiraTipo.SAIDA.value
    )


def total_saiu_do_caixa(db: Session, empresa_id: int, inicio, fim) -> int:
    """Quanto dinheiro SAIU da loja no período, pelo livro.

    O espelho de `total_entrou_no_caixa`, e lido do livro pelo mesmo motivo:
    somar `contas_pagar.valor_pago` responderia quase igual, mas erraria no
    estorno -- o pagamento desfeito continuaria contado como saída até alguém
    reparar. Aqui a saída volta sozinha, porque o estorno é uma ENTRADA com a
    mesma origem.

    Sangria fica de fora: ver `ORIGENS_DE_SALDO`.
    """
    def _soma(tipo: str) -> int:
        return int(
            _query_extrato(db, empresa_id, inicio=inicio, fim=fim, tipo=tipo)
            .filter(
                MovimentacaoFinanceira.origem
                == MovimentacaoFinanceiraOrigem.DESPESA.value
            )
            .with_entities(func.coalesce(func.sum(MovimentacaoFinanceira.valor), 0))
            .scalar()
            or 0
        )

    return _soma(MovimentacaoFinanceiraTipo.SAIDA.value) - _soma(
        MovimentacaoFinanceiraTipo.ENTRADA.value
    )
