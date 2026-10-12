# ---------------------------------------------------------------------------
# ARQUIVO: app/schemas/marcenaria/entrega.py
# DESCRICAO: O que a API RECEBE na entrega e na agenda de instalacao
#            (Spec 13A, secao 6). As saidas sao dicionarios montados no servico.
# ---------------------------------------------------------------------------

import re
from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _texto_opcional(valor: Optional[str]) -> Optional[str]:
    """Tira os espacos das pontas; texto vazio vira nulo (campo nao informado)."""
    if valor is None:
        return None
    valor = valor.strip()
    return valor or None


class ChecklistEntrada(BaseModel):
    """PUT .../checklist: a lista inteira de textos, na ordem nova (D2).

    As regras (1 a 30 itens, ate 120 caracteres, sem repetir) sao conferidas no
    servico, com as mesmas frases da configuracao (04A).
    """
    model_config = ConfigDict(extra="forbid")

    itens: list[str] = Field(default_factory=list, max_length=100)


class RegistroEntrada(BaseModel):
    """POST .../registrar: o resultado do termo que voltou da obra (D4; secao 6.2)."""
    model_config = ConfigDict(extra="forbid")

    situacao: Literal["CONFORME", "COM_RESSALVAS"]
    data_entrega: Optional[date] = None                     # padrao: hoje
    montadores: list[int] = Field(default_factory=list, max_length=20)    # funcionarios (I4)
    recebido_por: Optional[str] = Field(None, max_length=150)
    # Uma marcacao por item do checklist, na ordem dele. Nulo = nao mexe (correcao).
    checklist: Optional[list[Optional[Literal["ok", "nao_ok"]]]] = Field(None, max_length=100)
    observacoes: Optional[str] = Field(None, max_length=1000)
    pendencias: list[str] = Field(default_factory=list, max_length=50)    # obrigatorio com ressalvas (D4)

    _limpar = field_validator("recebido_por", "observacoes")(_texto_opcional)

    @field_validator("montadores")
    @classmethod
    def _sem_repetir(cls, ids: list[int]) -> list[int]:
        """O mesmo montador duas vezes conta uma (a ordem fica)."""
        return list(dict.fromkeys(ids))

    @field_validator("pendencias")
    @classmethod
    def _pendencias(cls, textos: list[str]) -> list[str]:
        """Linhas em branco nao sao pendencia; cada uma ate 300 caracteres (D6)."""
        limpas = [t.strip() for t in textos if t and t.strip()]
        if any(len(t) > 300 for t in limpas):
            raise ValueError("Cada pendência pode ter até 300 caracteres.")
        return limpas


class PendenciaEntrada(BaseModel):
    """POST .../pendencias: uma pendencia nova (D6)."""
    model_config = ConfigDict(extra="forbid")

    descricao: str = Field(..., min_length=1, max_length=300)

    @field_validator("descricao")
    @classmethod
    def _limpa(cls, texto: str) -> str:
        texto = texto.strip()
        if not texto:
            raise ValueError("Descreva a pendência.")
        return texto


class ResolverEntrada(BaseModel):
    """POST .../pendencias/{pid}/resolver: como foi resolvida e quando (D6)."""
    model_config = ConfigDict(extra="forbid")

    resolucao: str = Field(..., min_length=1, max_length=300)
    data: Optional[date] = None                             # padrao: hoje

    @field_validator("resolucao")
    @classmethod
    def _limpa(cls, texto: str) -> str:
        texto = texto.strip()
        if not texto:
            raise ValueError("Conte como a pendência foi resolvida.")
        return texto


# "08:00" ate "23:59": horas e minutos com dois digitos.
_HORA = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class AgendamentoEntrada(BaseModel):
    """POST/PUT .../agendamentos: a visita de instalacao (D9)."""
    model_config = ConfigDict(extra="forbid")

    data: date
    hora_inicio: Optional[str] = None
    ambiente_ids: list[int] = Field(default_factory=list, max_length=100)
    montadores: list[int] = Field(default_factory=list, max_length=20)
    observacao: Optional[str] = Field(None, max_length=300)

    _limpar = field_validator("observacao")(_texto_opcional)

    @field_validator("hora_inicio")
    @classmethod
    def _hora(cls, valor: Optional[str]) -> Optional[str]:
        """Hora no formato "08:00" (vazio = sem hora marcada)."""
        valor = _texto_opcional(valor)
        if valor is not None and not _HORA.match(valor):
            raise ValueError("Informe a hora no formato 08:00.")
        return valor

    @field_validator("ambiente_ids", "montadores")
    @classmethod
    def _sem_repetir(cls, ids: list[int]) -> list[int]:
        return list(dict.fromkeys(ids))
