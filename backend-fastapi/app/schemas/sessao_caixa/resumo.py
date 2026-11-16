# ---------------------------------------------------------------------------
# ARQUIVO: schemas/sessao_caixa/resumo.py
# DESCRICAO: Schemas do caixa - movimentos, totais por forma, resumo, historico e leitura.
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.core.enum import SessaoCaixaStatus


# ===========================================================================
# LEITURA
# ===========================================================================

class MovimentoCaixaRead(BaseModel):
    """Uma linha do livro do dinheiro, como o extrato do turno mostra."""

    id: int
    tipo: str
    origem: str
    valor: int
    motivo: Optional[str] = None
    forma_pagamento_id: Optional[int] = None
    funcionario_nome: Optional[str] = None
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class TotalPorForma(BaseModel):
    """Quanto entrou por cada forma de pagamento no turno.

    O fechamento confere forma a forma, e não só o total: dinheiro é o único que
    se conta na mão, e juntar tudo num número só esconde a diferença que importa.
    """

    forma_pagamento_id: Optional[int] = None
    forma_pagamento_nome: str
    total: int


class SessaoCaixaResumo(BaseModel):
    """O espelho do turno: o que entrou, o que saiu e o que tem que estar lá."""

    sessao_id: int
    status: SessaoCaixaStatus
    funcionario_id: int
    funcionario_nome: Optional[str] = None
    terminal_hwid: Optional[str] = None
    terminal_nome: Optional[str] = None

    data_abertura: datetime
    data_fechamento: Optional[datetime] = None

    saldo_inicial: int
    total_vendas: int = Field(..., description="Tudo que entrou por venda/OS, em qualquer forma")
    total_suprimentos: int
    total_sangrias: int

    # A conta da gaveta:
    #   saldo_inicial + entradas em DINHEIRO + suprimentos - sangrias
    # Cartão e PIX não entram aqui de propósito: eles não estão na gaveta.
    #
    # `None` significa OCULTO, não vazio. No fechamento cego o operador não pode
    # ver este número antes de contar — mas mandar `0` no lugar fazia a barra do
    # PDV anunciar "Em dinheiro na gaveta: R$ 0,00" com a gaveta cheia, e o que
    # chega para quem está no balcão é "o sistema não está somando minhas
    # vendas". Esconder é legítimo; mentir um valor não é.
    saldo_esperado_dinheiro: Optional[int] = Field(
        None, description="Dinheiro esperado na gaveta. None = oculto pelo fechamento cego"
    )

    # Só preenchidos depois do fechamento. Antes dele, no modo cego, nem o
    # esperado é devolvido ao operador (ver `fechamento_cego`).
    saldo_contado: Optional[int] = None
    diferenca: Optional[int] = Field(
        None, description="contado - esperado. Negativo = falta dinheiro"
    )

    por_forma: List[TotalPorForma] = []
    movimentos: List[MovimentoCaixaRead] = []

    model_config = ConfigDict(from_attributes=True)


class SessaoCaixaHistoricoItem(BaseModel):
    """Uma linha do histórico de turnos, na visão do dono.

    Responde as duas perguntas que ele faz: **quem fechou faltando dinheiro** e
    **quem fechou sobrando**. As duas saem do mesmo campo — `diferenca` negativa
    é falta, positiva é sobra — e as duas importam: sobra costuma ser troco não
    registrado ou venda não lançada, que é problema tanto quanto a falta.

    Os valores de fechamento são LIDOS da sessão, não recalculados: foram
    congelados no momento em que o operador conferiu. Recalcular depois faria o
    passado mudar quando um lançamento atrasado entrasse.
    """

    sessao_id: int
    status: SessaoCaixaStatus

    funcionario_id: int
    funcionario_nome: Optional[str] = None
    terminal_hwid: Optional[str] = None
    terminal_nome: Optional[str] = None

    data_abertura: datetime
    data_fechamento: Optional[datetime] = None

    saldo_inicial: int
    saldo_esperado: Optional[int] = Field(
        None, description="O que o sistema calculou que deveria estar na gaveta"
    )
    saldo_contado: Optional[int] = Field(
        None, description="O que o operador declarou ter contado"
    )
    diferenca: Optional[int] = Field(
        None, description="contado - esperado. Negativo = faltou; positivo = sobrou"
    )

    model_config = ConfigDict(from_attributes=True)


class SessaoCaixaRead(BaseModel):
    """A sessão em si, sem o resumo financeiro."""

    id: int
    status: SessaoCaixaStatus
    funcionario_id: int
    terminal_hwid: Optional[str] = None
    saldo_inicial: int
    saldo_final_esperado: Optional[int] = None
    saldo_final_informado: Optional[int] = None
    data_abertura: datetime
    data_fechamento: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
