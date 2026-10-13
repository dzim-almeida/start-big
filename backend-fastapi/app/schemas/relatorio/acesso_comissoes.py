# ---------------------------------------------------------------------------
# ARQUIVO: schemas/relatorio/acesso_comissoes.py
# DESCRICAO: Schemas de relatorio - quais cargos o Master liberou para ver as
#            comissoes (e o extrato) de toda a equipe.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field


class AcessoComissoesCargo(BaseModel):
    id: int
    nome: str
    liberado: bool = Field(..., description="O cargo ve as comissoes e o extrato de toda a equipe")
    abre_relatorios: bool = Field(
        ..., description="O cargo tem acesso a tela de Relatorios (sem ela, a liberacao nao aparece)"
    )


class AcessoComissoes(BaseModel):
    cargos: list[AcessoComissoesCargo] = Field(default_factory=list)


class AcessoComissoesUpdate(BaseModel):
    cargo_ids: list[int] = Field(
        default_factory=list, description="Cargos liberados; os que ficarem de fora perdem a liberacao"
    )
