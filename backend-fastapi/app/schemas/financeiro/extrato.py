# ---------------------------------------------------------------------------
# ARQUIVO: schemas/financeiro/extrato.py
# DESCRICAO: Financeiro - schemas do extrato.
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


# ===========================================================================
# EXTRATO (o livro do dinheiro, linha a linha)
# ===========================================================================

class ExtratoLinha(BaseModel):
    """Um movimento que JÁ aconteceu. O oposto do Fluxo de Caixa.

    Vem de `movimentacoes_financeiras`, que só recebe INSERT: um pagamento
    lançado por engano não some daqui, ele ganha uma linha contrária. É o que
    torna esta tela auditável — o extrato conta a história inteira, inclusive
    a parte que alguém preferiria esquecer.
    """

    id: int
    criado_em: datetime = Field(..., description="Instante do movimento, em UTC")
    tipo: str = Field(..., description="ENTRADA ou SAIDA")
    origem: str = Field(
        ..., description="VENDA, ORDEM_SERVICO, ABERTURA, SANGRIA, SUPRIMENTO, RECEBIMENTO ou DESPESA"
    )
    valor: int = Field(..., description="Sempre positivo (centavos); o sinal é o `tipo`")

    motivo: str | None = None
    funcionario_nome: str | None = None
    conta_bancaria_nome: str | None = None
    forma_pagamento_nome: str | None = None
    sessao_caixa_id: int | None = Field(
        None, description="Turno de caixa; NULL = não passou pela gaveta"
    )
    documento: str | None = Field(
        None, description="Venda ou OS que originou, quando houve uma"
    )


class Extrato(BaseModel):
    """A lista com os totais do MESMO filtro.

    Os dois saem da mesma query base de propósito: um rodapé que não fecha com
    a lista acima destrói a confiança na tela inteira -- e num extrato isso é
    fatal, porque ele existe justamente para ser conferido contra o banco.
    """

    total_itens: int
    total_entradas: int
    total_saidas: int
    saldo: int = Field(..., description="entradas - saidas no filtro (pode ser negativo)")
    itens: List[ExtratoLinha] = Field(default_factory=list)
