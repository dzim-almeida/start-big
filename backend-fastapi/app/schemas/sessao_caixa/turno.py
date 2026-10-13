# ---------------------------------------------------------------------------
# ARQUIVO: schemas/sessao_caixa/turno.py
# DESCRICAO: Schemas do caixa - abrir, movimento (suprimento/sangria) e fechar.
# ---------------------------------------------------------------------------

from typing import Optional
from pydantic import BaseModel, Field


# ===========================================================================
# ABERTURA
# ===========================================================================

class SessaoCaixaAbrir(BaseModel):
    """Dados para abrir o turno."""

    saldo_inicial: int = Field(
        ...,
        ge=0,
        description="Dinheiro de troco colocado na gaveta na abertura (centavos)",
    )
    # O HWID identifica a máquina e é o que permite dois caixas operando ao
    # mesmo tempo. Vem do cliente porque o token não o carrega — e não vale
    # mexer no login, que as três lojas em produção usam todo dia.
    terminal_hwid: Optional[str] = Field(
        None,
        max_length=255,
        description="HWID do terminal. Omitir só faz sentido em loja de um PC só",
    )
    # Preenchido quando a loja exige autorização para abrir o caixa e quem opera
    # não é gerente: o supervisor digita o PIN ali na hora e libera aquela
    # abertura, sem trocar o operador do turno. Mesmo campo e mesmo contrato da
    # sangria — o `pin_gerente` de `configuracoes_seguranca` é um só.
    codigo_gerente: Optional[str] = Field(
        None, description="PIN do gerente, quando a abertura exigir autorização"
    )


# ===========================================================================
# SANGRIA E SUPRIMENTO
# ===========================================================================

class MovimentoCaixaCreate(BaseModel):
    """Dinheiro entrando ou saindo da gaveta sem que haja venda por trás."""

    valor: int = Field(..., gt=0, description="Valor movimentado (centavos)")
    # Obrigatório e sem default: é o que transforma "sumiu dinheiro" em
    # "saiu R$ 200 às 14h para o cofre". Um motivo opcional viraria motivo vazio.
    motivo: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Por que o dinheiro entrou ou saiu",
    )
    # Preenchido quando a sangria exige autorização e quem opera não é gerente:
    # o supervisor digita o PIN ali na hora e libera aquela retirada, sem trocar
    # o operador do caixa. Reusa o mesmo PIN que já protege cancelamento,
    # reabertura e desconto (configuracoes_seguranca.pin_gerente) — inventar um
    # segundo segredo seria mais uma coisa para o lojista esquecer.
    codigo_gerente: Optional[str] = Field(
        None, description="PIN do gerente, quando a sangria exigir autorização"
    )


# ===========================================================================
# FECHAMENTO
# ===========================================================================

class SessaoCaixaFechar(BaseModel):
    """Conferência da gaveta no fim do turno."""

    saldo_contado: int = Field(
        ...,
        ge=0,
        description="Dinheiro efetivamente contado na gaveta (centavos)",
    )
    observacao: Optional[str] = Field(
        None, max_length=500, description="Observação do fechamento"
    )
