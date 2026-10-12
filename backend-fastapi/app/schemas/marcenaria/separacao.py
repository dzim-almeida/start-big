# ---------------------------------------------------------------------------
# ARQUIVO: app/schemas/marcenaria/separacao.py
# DESCRICAO: O que a API RECEBE nas acoes da separacao de material da OS
#            (Spec 10A, secao 6.1).
#
# Quantidades em MILESIMOS (int, PR4): 1,5 chapa = 1500. O item da OS e o
# estoque guardam Float; a conversao acontece so na borda (no servico).
# As saidas sao dicionarios montados no servico (secoes 6.2 e 6.3).
# ---------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict, Field


class ConferenciaEntrada(BaseModel):
    """Concluir e reabrir: so a trava de concorrencia (D16)."""
    model_config = ConfigDict(extra="forbid")

    # O `separada_milesimos` que a tela tinha. Se outra pessoa retirou ou
    # devolveu nesse meio-tempo, o valor gravado e outro e a acao responde 409.
    separada_esperada_milesimos: int = Field(..., ge=0)


class MovimentoEntrada(ConferenciaEntrada):
    """Retirar e devolver: quanto, alem da trava (D6, D9, D16).

    `ge=0` e nao `gt=0` de proposito: o zero chega ao servico, que responde
    com a frase da spec ("A quantidade deve ser maior que zero."), e nao com
    a mensagem generica do pydantic.
    """
    quantidade_milesimos: int = Field(..., ge=0, le=100_000_000)   # teto: 100 mil unidades
