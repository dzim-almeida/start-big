# ---------------------------------------------------------------------------
# ARQUIVO: schemas/produto/importacao.py
# DESCRICAO: Importação de produtos por planilha Excel (prévia e resultado).
# ---------------------------------------------------------------------------

from typing import Literal, Optional

from pydantic import BaseModel, Field


class LinhaImportacao(BaseModel):
    """Uma linha da planilha, já conferida."""

    linha: int = Field(..., description="Número da linha no Excel.")
    codigo: str = ""
    nome: str = ""
    unidade: Optional[str] = None
    ncm: Optional[str] = None
    custo: Optional[int] = Field(None, description="Em centavos.")
    preco: Optional[int] = Field(None, description="Em centavos.")
    estoque: float = 0
    situacao: Literal["novo", "existe", "ignorado", "erro"]
    mensagens: list[str] = Field(default_factory=list)


class PreviaImportacao(BaseModel):
    """O que aconteceria se importasse agora. Nada foi gravado."""

    novos: int
    ja_existem: int
    ignorados: int
    com_erro: int
    # Sem o fiscal configurado, NCM, CFOP e CSOSN da planilha não são gravados.
    fiscal_disponivel: bool
    planilha_tem_fiscal: bool
    linhas: list[LinhaImportacao]


class ResultadoImportacaoPlanilha(BaseModel):
    criados: int
    ja_existiam: int
    ignorados: int
    com_erro: int
