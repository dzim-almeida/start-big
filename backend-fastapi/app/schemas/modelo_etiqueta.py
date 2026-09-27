# ---------------------------------------------------------------------------
# ARQUIVO: schemas/modelo_etiqueta.py
# MÓDULO: Schemas Pydantic — Modelos de etiqueta (Central de Etiquetas)
# ---------------------------------------------------------------------------
"""
O modelo chega e sai inteiro: nome + fonte + definição (página e elementos,
tudo em milímetros). O espelho deste contrato no frontend é
`shared/etiquetas/modelo.ts` — mexeu num, mexa no outro.

O que o schema garante e o banco não:
- a página tem medidas plausíveis (uma etiqueta de 0 mm ou de 2 m é erro de
  digitação, não etiqueta);
- numa folha (Pimaco), as colunas e linhas CABEM na folha — senão a última
  coluna sai cortada no papel sem erro nenhum na tela;
- todo elemento começa dentro da etiqueta.

Os campos de cada elemento além da posição (fonte, simbologia, campo...) são
do renderizador do terminal e passam sem validação fina: o backend guarda, não
desenha.
"""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Folga de arredondamento: o editor trabalha em décimos de mm.
TOLERANCIA_MM = 0.5

MAX_ELEMENTOS = 50

# produto: etiqueta de estoque; volume: etiqueta de envio (OS/venda).
FonteEtiqueta = Literal["produto", "volume"]
TipoElemento = Literal["texto", "barras", "qr", "linha", "caixa", "imagem"]


class FolhaEtiqueta(BaseModel):
    """A folha inteira, quando a página é uma folha de etiquetas (ex.: Pimaco A4)."""

    largura_mm: float = Field(..., gt=0, le=500)
    altura_mm: float = Field(..., gt=0, le=500)
    linhas: int = Field(..., ge=1, le=60)


class PaginaEtiqueta(BaseModel):
    """Uma etiqueta (largura × altura) e como ela se repete no papel."""

    tipo: Literal["bobina", "folha"]
    largura_mm: float = Field(..., ge=5, le=300)
    altura_mm: float = Field(..., ge=5, le=300)
    colunas: int = Field(1, ge=1, le=10)
    espaco_colunas_mm: float = Field(0, ge=0, le=50)
    espaco_linhas_mm: float = Field(0, ge=0, le=50)
    margem_esq_mm: float = Field(0, ge=0, le=100)
    margem_topo_mm: float = Field(0, ge=0, le=100)
    folha: Optional[FolhaEtiqueta] = None

    @model_validator(mode="after")
    def _folha_coerente(self) -> "PaginaEtiqueta":
        if self.tipo == "folha" and self.folha is None:
            raise ValueError("Página do tipo folha precisa das medidas da folha.")
        if self.tipo == "bobina":
            self.folha = None
            return self

        folha = self.folha
        largura = self.margem_esq_mm + self.colunas * self.largura_mm + (self.colunas - 1) * self.espaco_colunas_mm
        altura = self.margem_topo_mm + folha.linhas * self.altura_mm + (folha.linhas - 1) * self.espaco_linhas_mm
        if largura > folha.largura_mm + TOLERANCIA_MM:
            raise ValueError(
                f"As {self.colunas} colunas ocupam {largura:.1f} mm e a folha tem {folha.largura_mm:g} mm de largura."
            )
        if altura > folha.altura_mm + TOLERANCIA_MM:
            raise ValueError(
                f"As {folha.linhas} linhas ocupam {altura:.1f} mm e a folha tem {folha.altura_mm:g} mm de altura."
            )
        return self


class ElementoEtiqueta(BaseModel):
    """Um item desenhado na etiqueta. Posição em mm a partir do canto superior esquerdo."""

    model_config = ConfigDict(extra="allow")

    tipo: TipoElemento
    x: float = Field(..., ge=0)
    y: float = Field(..., ge=0)
    w: float = Field(..., ge=0)
    h: float = Field(..., ge=0)


class DefinicaoEtiqueta(BaseModel):
    pagina: PaginaEtiqueta
    elementos: list[ElementoEtiqueta] = Field(..., max_length=MAX_ELEMENTOS)
    # Opções do layout automático (quais campos entram) que GERARAM os
    # elementos. Presente: o formulário de modelo reabre com elas e regera os
    # elementos. Ausente: os elementos foram posicionados à mão (editor visual).
    layout_auto: Optional[dict[str, Any]] = None

    @model_validator(mode="after")
    def _elementos_dentro(self) -> "DefinicaoEtiqueta":
        largura, altura = self.pagina.largura_mm, self.pagina.altura_mm
        for i, el in enumerate(self.elementos, start=1):
            if el.x + el.w > largura + TOLERANCIA_MM or el.y + el.h > altura + TOLERANCIA_MM:
                raise ValueError(
                    f"O elemento {i} ({el.tipo}) sai da etiqueta de {largura:g} × {altura:g} mm."
                )
        return self


class ModeloEtiquetaBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=80)
    fonte: FonteEtiqueta = "produto"
    definicao: DefinicaoEtiqueta

    @model_validator(mode="after")
    def _nome_limpo(self) -> "ModeloEtiquetaBase":
        self.nome = self.nome.strip()
        if not self.nome:
            raise ValueError("Informe o nome do modelo.")
        return self


class ModeloEtiquetaCreate(ModeloEtiquetaBase):
    pass


class ModeloEtiquetaUpdate(ModeloEtiquetaBase):
    pass


class ModeloEtiquetaRead(ModeloEtiquetaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    data_criacao: datetime
    data_atualizacao: datetime
