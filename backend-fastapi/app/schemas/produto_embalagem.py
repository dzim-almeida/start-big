# ---------------------------------------------------------------------------
# ARQUIVO: schemas/produto_embalagem.py
# MÓDULO: Schemas Pydantic — Embalagens do produto (fardo, caixa, pack)
# ---------------------------------------------------------------------------
"""
As embalagens de um produto chegam e saem EM BLOCO (replace-all, como as
regras do perfil tributário): a tela manda a lista inteira, e o que não veio
sai. Espelho no frontend: `modules/products/inventory/types/embalagens.types.ts`.

O que o schema garante:
- sigla curta em maiúsculas (vai no uCom da nota, fase 4);
- fator inteiro ≥ 1 (1 = código de barras adicional da unidade);
- preço próprio OU desconto sobre as unidades, nunca os dois;
- nenhum código repetido dentro da própria lista.

A unicidade do código no SISTEMA inteiro (contra produtos e outras
embalagens) é do service: depende do banco.
"""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_EMBALAGENS = 30
_SIGLA = re.compile(r"^[A-Z0-9]{1,6}$")
_CODIGO = re.compile(r"^[A-Za-z0-9\-]{1,20}$")


class EmbalagemBase(BaseModel):
    sigla: str = Field(..., min_length=1, max_length=6, description="FD, CX, PCT, UN…")
    descricao: Optional[str] = Field(None, max_length=60, description="Ex.: 'Fardo com 12'")
    fator: int = Field(..., ge=1, le=100000, description="Unidades do produto na embalagem (1 = código adicional)")
    codigo_barras: Optional[str] = Field(None, max_length=20, description="EAN/DUN da embalagem")
    preco: Optional[int] = Field(None, ge=0, description="Preço próprio, em centavos")
    desconto_bp: Optional[int] = Field(
        None, ge=0, le=9900, description="Desconto sobre fator × unidade, em centésimos de % (500 = 5%)"
    )
    vende_no_pdv: bool = True
    usa_na_entrada: bool = True
    ativo: bool = True

    @field_validator("sigla")
    @classmethod
    def _sigla(cls, v: str) -> str:
        sigla = v.strip().upper()
        if not _SIGLA.match(sigla):
            raise ValueError("A sigla tem de 1 a 6 letras ou números (ex.: FD, CX, PCT).")
        return sigla

    @field_validator("descricao")
    @classmethod
    def _descricao(cls, v: Optional[str]) -> Optional[str]:
        return (v or "").strip() or None

    @field_validator("codigo_barras")
    @classmethod
    def _codigo(cls, v: Optional[str]) -> Optional[str]:
        codigo = (v or "").strip()
        if not codigo:
            return None
        if not _CODIGO.match(codigo):
            raise ValueError("O código de barras aceita só letras, números e hífen (até 20).")
        return codigo

    @model_validator(mode="after")
    def _preco_ou_desconto(self) -> "EmbalagemBase":
        if self.preco is not None and self.desconto_bp is not None:
            raise ValueError("Informe o preço próprio OU o desconto sobre as unidades, não os dois.")
        return self


class EmbalagemEscrita(EmbalagemBase):
    # Presente = atualiza a embalagem existente; ausente = cria.
    id: Optional[int] = None
    # Sem código do fornecedor: o sistema gera um EAN-13 interno (prefixo 29).
    gerar_codigo_interno: bool = False


class EmbalagensSalvar(BaseModel):
    embalagens: list[EmbalagemEscrita] = Field(default_factory=list, max_length=MAX_EMBALAGENS)
    # A3 — mora no produto, mas é editado junto das embalagens (a seção tem o
    # próprio botão Salvar). Nulo = não mexe.
    so_embalagem_fechada: Optional[bool] = None

    @model_validator(mode="after")
    def _codigos_distintos(self) -> "EmbalagensSalvar":
        vistos: set[str] = set()
        for emb in self.embalagens:
            if emb.codigo_barras is None:
                continue
            if emb.codigo_barras in vistos:
                raise ValueError(f"O código {emb.codigo_barras} aparece em duas embalagens.")
            vistos.add(emb.codigo_barras)
        return self


class EmbalagemRead(EmbalagemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    produto_id: int
    data_criacao: datetime
    data_atualizacao: datetime
