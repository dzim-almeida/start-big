# ---------------------------------------------------------------------------
# ARQUIVO: services/financeiro/saldo.py
# DESCRICAO: Financeiro - quanto a loja tem AGORA nas contas.
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.core.tempo import fim_do_dia_utc
from app.db.crud import financeiro as financeiro_crud


# ===========================================================================
# SALDO — quanto a loja tem AGORA
# ===========================================================================

class SaldoDasContas:
    """O saldo de hoje, e as duas metades que o formam.

    Guardar as metades separadas não é enfeite de tela: é o que permite o dono
    conferir. "Você declarou R$ 500 no dia 29 e desde então entrou R$ 740 e saiu
    R$ 90" é auditável na hora; "você tem R$ 1.150" só dá para acreditar ou não.
    """

    __slots__ = (
        "saldo", "ancora", "movimentado", "entrou", "saiu", "declarado", "informado_em",
    )

    def __init__(self, saldo, ancora, entrou, saiu, declarado, informado_em):
        self.saldo = saldo
        self.ancora = ancora
        self.entrou = entrou
        self.saiu = saiu
        self.movimentado = entrou - saiu
        self.declarado = declarado
        self.informado_em = informado_em


def saldo_atual_das_contas(db: Session, empresa_id: int) -> SaldoDasContas:
    """Âncora declarada + tudo que o livro moveu depois dela.

    ESTE É O NÚMERO QUE FALTAVA. Até 02/09/2026 o Fluxo de Caixa partia do
    `saldo_informado` puro, e o resultado era o dono vendendo o dia inteiro e
    vendo o saldo parado no mesmo valor -- só mudava quando ele digitava outro à
    mão. É o desenho do "saldo inicial" do Conta Azul e do Omie: declara-se uma
    vez, e daí em diante quem move o saldo são os lançamentos.

    ENQUANTO A LOJA NÃO DECLARAR NADA, não há saldo. Sem ponto de partida, somar
    movimento daria "o quanto mudou", que não é saldo -- e a loja apareceria com
    saldo negativo no primeiro boleto que pagasse.

    MAS BASTA UMA CONTA DECLARADA para todas passarem a contar, e isso foi um
    defeito real: a regra era "conta sem âncora própria não entra, nem com o
    movimento dela", e o resultado era dinheiro sumindo em silêncio. A loja que
    declarou a conta do banco e deixou a gaveta em branco via o dinheiro da OS
    cair na gaveta (que é a conta principal) e desaparecer do saldo -- o Extrato
    mostrava a entrada, o Fluxo de Caixa não se mexia.

    A conta não declarada herda o corte MAIS ANTIGO da loja e parte de zero. É o
    que o dono quis dizer: no dia em que ele declarou o que tinha, o que ele não
    declarou valia zero. Herdar o corte mais antigo (e não o mais recente) é o
    que garante que nenhum movimento fique de fora.

    SÓ CONTAS ATIVAS. Uma conta desativada é dinheiro que a loja não usa mais, e
    somá-la faria toda a projeção partir de um número alto demais.

    O corte de cada conta é o INSTANTE da declaração; nas contas declaradas
    antes de a coluna existir, o fim daquele dia (a convenção conservadora do
    Conta Azul: perde-se o movimento do próprio dia, mas nada é contado duas
    vezes).
    """
    contas = financeiro_crud.listar_contas_bancarias(db, empresa_id, apenas_ativas=True)
    principal = financeiro_crud.get_conta_principal(db, empresa_id)
    principal_id = principal.id if principal else None

    ancora = sum(int(c.saldo_informado or 0) for c in contas)
    datas = [c.saldo_informado_em for c in contas if c.saldo_informado_em]

    def _corte(conta) -> Optional[datetime]:
        if not conta.saldo_informado_em:
            return None
        return conta.saldo_informado_instante or fim_do_dia_utc(conta.saldo_informado_em)

    cortes = [c for c in (_corte(conta) for conta in contas) if c is not None]
    corte_da_loja = min(cortes) if cortes else None

    entrou = saiu = 0
    for conta in contas:
        corte = _corte(conta) or corte_da_loja
        if corte is None:
            continue  # a loja inteira nunca declarou nada
        conta_entrou, conta_saiu = financeiro_crud.entradas_e_saidas_desde(
            db,
            empresa_id,
            conta_id=conta.id,
            desde=corte,
            # As linhas órfãs (antigas, ou de uma conta apagada) caem na
            # principal -- que é para onde os lançamentos novos vão. Jogá-las
            # fora faria o saldo derivado ficar abaixo do real.
            incluir_sem_conta=(conta.id == principal_id),
        )
        entrou += conta_entrou
        saiu += conta_saiu

    return SaldoDasContas(
        saldo=ancora + entrou - saiu,
        ancora=ancora,
        entrou=entrou,
        saiu=saiu,
        declarado=bool(datas),
        # A data MAIS ANTIGA entre as contas: é ela que envelhece o número. Uma
        # loja que atualizou o Nubank hoje e esqueceu a gaveta há um mês tem uma
        # âncora de um mês atrás.
        informado_em=min(datas) if datas else None,
    )
