# ---------------------------------------------------------------------------
# ARQUIVO: app/schemas/marcenaria/terceirizado.py
# DESCRICAO: O que a API RECEBE nas acoes dos moveis terceirizados da OS
#            (Spec 11A, secao 6). As saidas sao dicionarios montados no servico.
# ---------------------------------------------------------------------------

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MoveisEntrada(BaseModel):
    """Conferir (e a base das outras): os moveis da acao, pelo menos um."""
    model_config = ConfigDict(extra="forbid")

    movel_ids: list[int] = Field(..., min_length=1, max_length=300)

    @field_validator("movel_ids")
    @classmethod
    def _sem_repetir(cls, ids: list[int]) -> list[int]:
        """O mesmo movel duas vezes na lista conta uma (a ordem fica)."""
        return list(dict.fromkeys(ids))


class PedidoCentralEntrada(MoveisEntrada):
    """POST /terceirizados/pedir: um pedido de SERVICO no Compras (D9)."""
    previsao_entrega: Optional[date] = None
    observacao: Optional[str] = Field(None, max_length=500)


class EnviarManualEntrada(MoveisEntrada):
    """POST /terceirizados/enviar-manual: sem o Compras, anota o pedido (D3)."""
    pedido: Optional[str] = Field(None, max_length=60)      # o numero que a central deu
    previsao: Optional[date] = None


class ReceberManualEntrada(MoveisEntrada):
    """POST /terceirizados/receber-manual: sem o Compras, a data da chegada (D3)."""
    data: Optional[date] = None                              # padrao: hoje


class ProblemaEntrada(BaseModel):
    """POST /terceirizados/{movel_id}/problema: o que veio errado (D4)."""
    model_config = ConfigDict(extra="forbid")

    texto: str = Field(..., min_length=1, max_length=500)

    @field_validator("texto")
    @classmethod
    def _limpo(cls, texto: str) -> str:
        """Texto so de espacos nao conta como problema."""
        texto = texto.strip()
        if not texto:
            raise ValueError("Descreva o problema.")
        return texto
