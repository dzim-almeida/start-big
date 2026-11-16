# ---------------------------------------------------------------------------
# ARQUIVO: schemas/orcamentos/cadastro.py
# DESCRICAO: Schemas do orcamento - criar, editar e ler.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Sequence
from app.schemas.funcionario import CargoBase
from app.schemas.orcamentos.itens import OrcamentoProdutoRead


class OrcamentoCreate(BaseModel):
    funcionario_id: int = Field(..., description="ID do funcionario")


class OrcamentoUpdate(BaseModel):
    funcionario_id: Optional[int] = Field(None, description="ID do funcionario")
    entrega: Optional[int] = Field(None, ge=0, description="Valor da entrega")
    desconto: Optional[int] = Field(None, ge=0, description="Desconto do orcamento")
    observacao: Optional[str] = Field(None, max_length=500, description="Observacao do orcamento")


class FuncionarioOrcamentoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID do funcionario")
    nome: str = Field(..., description="Nome do funcionario")
    cargo: Optional[CargoBase] = Field(None, description="Cargo do funcionario")


class OrcamentoSimpleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID do orcamento (numero do orcamento)")
    funcionario_id: int = Field(..., description="ID do funcionario responsavel")
    total: int = Field(0, ge=0, description="Total do orcamento")
    convertido: bool = Field(False, description="Se foi convertido em venda")
    venda_id: Optional[int] = Field(None, description="ID da venda criada a partir deste orcamento")
    criado_em: datetime = Field(..., description="Data de criacao do orcamento")
    atualizado_em: datetime = Field(..., description="Data da ultima atualizacao do orcamento")
    funcionario: Optional[FuncionarioOrcamentoRead] = Field(None, description="Dados do funcionario responsavel")


class OrcamentoRead(OrcamentoSimpleRead):
    entrega: int = Field(0, ge=0, description="Valor da entrega")
    subtotal: int = Field(0, ge=0, description="Subtotal do orcamento")
    descontos: int = Field(0, ge=0, description="Total de descontos do orcamento")
    observacao: Optional[str] = Field(None, max_length=500, description="Observacao do orcamento")
    produtos: Optional[Sequence[OrcamentoProdutoRead]] = Field(default_factory=list, validation_alias="itens", description="Lista de produtos do orcamento")
