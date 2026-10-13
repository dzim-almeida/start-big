# ---------------------------------------------------------------------------
# ARQUIVO: schemas/sessao_caixa/__init__.py
# DESCRIÇÃO: Schemas Pydantic do turno de caixa (abertura, movimentos e
#            fechamento) e do resumo que o operador confere.
#
# Era um arquivo so (sessao_caixa.py) ate 13/10/2026; virou pacote:
#   turno.py  - abrir, movimento (suprimento/sangria) e fechar
#   resumo.py - movimentos, totais por forma, resumo, historico e leitura
#
# Este __init__ reexporta tudo: `from app.schemas.sessao_caixa import ...`
# continua valendo como antes.
# ---------------------------------------------------------------------------

from app.schemas.sessao_caixa.turno import (
    SessaoCaixaAbrir,
    MovimentoCaixaCreate,
    SessaoCaixaFechar,
)

from app.schemas.sessao_caixa.resumo import (
    MovimentoCaixaRead,
    TotalPorForma,
    SessaoCaixaResumo,
    SessaoCaixaHistoricoItem,
    SessaoCaixaRead,
)

__all__ = [
    "SessaoCaixaAbrir",
    "MovimentoCaixaCreate",
    "SessaoCaixaFechar",
    "MovimentoCaixaRead",
    "TotalPorForma",
    "SessaoCaixaResumo",
    "SessaoCaixaHistoricoItem",
    "SessaoCaixaRead",
]
