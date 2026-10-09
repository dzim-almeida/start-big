# ---------------------------------------------------------------------------
# ARQUIVO: app/schemas/marcenaria/producao.py
# DESCRICAO: O que a API RECEBE nas acoes da producao da OS (Spec 12A, secao 6).
#            As saidas sao dicionarios montados no servico (secao 6.1).
# ---------------------------------------------------------------------------

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LoteEntrada(BaseModel):
    """Iniciar ou concluir varias etapas de uma vez, ate de moveis diferentes (D11).

    Lista vazia chega ao servico, que responde "Escolha pelo menos uma etapa.".
    """
    model_config = ConfigDict(extra="forbid")

    etapa_ids: list[int] = Field(default_factory=list, max_length=2000)
    # Quem fez (D7). Sem ele: o funcionario do usuario logado.
    responsavel_funcionario_id: Optional[int] = Field(None, ge=1)


class ConcluirEmTodosEntrada(BaseModel):
    """"Concluir a etapa {nome} em todos os moveis da OS" (D11)."""
    model_config = ConfigDict(extra="forbid")

    nome: str = Field(..., min_length=1, max_length=60)


class EtapaDoMovel(BaseModel):
    """Uma etapa da lista editada: `id` = a que ja existia; sem `id` = nova."""
    model_config = ConfigDict(extra="forbid")

    id: Optional[int] = None
    nome: str = Field(..., max_length=200)        # o limite de verdade (60) e conferido no servico, com a frase


class EtapasDoMovelEntrada(BaseModel):
    """PUT .../moveis/{movel_id}/etapas: a lista inteira, na ordem nova (D3, D4)."""
    model_config = ConfigDict(extra="forbid")

    etapas: list[EtapaDoMovel] = Field(default_factory=list, max_length=100)
