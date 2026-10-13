# ---------------------------------------------------------------------------
# ARQUIVO: schemas/ordem_servico/item.py
# DESCRICAO: Schemas da OS - itens de pecas e servicos.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional
from app.core.enum import (
    OrdemServicoItemTipo,
    OrdemServicoItemAprovacao,
    UnidadeMedida,
)


# ===========================================================================
# ITENS DA OS
# ===========================================================================

class OSItemBase(BaseModel):
    """Payload para adicionar um item (produto ou serviço) a uma OS."""
    tipo: OrdemServicoItemTipo = Field(..., description="Tipo do item: PRODUTO ou SERVICO")
    nome: str = Field(..., max_length=255, min_length=3, description="Descrição do item")
    unidade_medida: UnidadeMedida = Field(..., description="Unidade de medida")
    quantidade: float = Field(..., gt=0, description="Quantidade (fracionada para unidades de peso, ex: 2.5 kg)")
    valor_unitario: int = Field(
        ...,
        ge=0,
        description="Valor unitário em centavos. Zero SÓ é aceito em peça embutida (visivel_cliente=False)."
    )

    # Aprovação e garantia por item (fluxo de orçamento / oficina).
    # Default APROVADO preserva o comportamento atual (item conta no total).
    status_aprovacao: OrdemServicoItemAprovacao = Field(
        OrdemServicoItemAprovacao.APROVADO,
        description="Status de aprovação do item. REPROVADO não entra no total da OS."
    )
    garantia_dias: Optional[int] = Field(None, ge=0, description="Garantia do item em dias (opcional)")
    garantia_km: Optional[int] = Field(None, ge=0, description="Garantia do item em KM, ex: oficina (opcional)")

    visivel_cliente: bool = Field(
        True,
        description=(
            "Se False, a peça está EMBUTIDA no serviço: sai do estoque e entra no custo "
            "(CMV), mas não aparece nas vias impressas do cliente. Exige valor zero — "
            "o dinheiro fica na linha do serviço."
        )
    )
    custo_unitario: Optional[int] = Field(
        None,
        ge=0,
        description=(
            "Quanto a loja PAGOU por unidade deste item, em centavos. Campo interno: "
            "nunca sai em via impressa. Serve para o caso em que o serviço é lançado "
            "sem cadastrar a peça — sem ele o lucro do mês fica maior do que foi. "
            "Ignorado quando o item vem do catálogo de produtos: aí o custo é o do "
            "livro de estoque."
        )
    )

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def _validar_peca_embutida(self):
        """Amarra visibilidade e valor: exatamente um dos dois estados.

        A via do cliente lista as linhas visíveis e imprime o total da OS. Se uma
        linha escondida carregasse valor, as linhas impressas somariam menos que
        o total impresso, e o cliente receberia um documento que não fecha —
        pior do que ver a peça. Por isso peça embutida vale zero, e o valor dela
        vai para a linha do serviço.
        """
        if not self.visivel_cliente and self.valor_unitario != 0:
            raise ValueError(
                "Peça embutida no serviço não é cobrada à parte: o valor dela deve ser zero"
            )
        if self.visivel_cliente and self.valor_unitario <= 0:
            raise ValueError(
                "Item cobrado do cliente precisa de valor maior que zero"
            )
        return self


class OSItemCreate(OSItemBase):
    item_id: Optional[int] = Field(None, description="ID do item no catálogo (produto ou serviço). None para item avulso.")


class OSItemRead(OSItemBase):
    """Resposta de um item de OS. Inclui IDs de referência no catálogo."""
    id: int = Field(..., description="ID único do item na OS")
    ordem_servico_id: int = Field(..., description="ID da OS à qual o item pertence")
    produto_id: Optional[int] = Field(None, description="ID do produto no catálogo (se tipo=PRODUTO)")
    servico_id: Optional[int] = Field(None, description="ID do serviço no catálogo (se tipo=SERVICO)")
    valor_total: int = Field(..., description="Valor total do item (quantidade × valor_unitario) em centavos")
    # Marcenaria-fábrica: o item foi gerado pela aprovação do orçamento e só
    # muda por ele (nulo em todo item lançado à mão).
    fabrica_orcamento_id: Optional[int] = Field(None, description="Versão do orçamento da fábrica que gerou o item")
    fabrica_movel_id: Optional[int] = Field(None, description="Móvel do orçamento da fábrica (item do móvel)")
    quantidade_separada: Optional[float] = Field(None, description="Fábrica (F4): o que já saiu do estoque na separação")
    # Só LEITURA (Spec 08A da marcenaria, D19): o OSItemCreate não tem o campo,
    # então ninguém cria item "travado" pela API. Nulo em todo item comum.
    origem: Optional[str] = Field(None, description="Documento que gerou o item (ex.: ORCAMENTO_MARCENARIA). Nulo = item comum")


class OSItemUpdate(BaseModel):
    """Payload para atualização parcial de um item de OS. Todos os campos são opcionais."""
    nome: Optional[str] = Field(None, max_length=255, min_length=3, description="Nova descrição")
    unidade_medida: Optional[UnidadeMedida] = Field(None, description="Nova unidade de medida")
    quantidade: Optional[float] = Field(None, gt=0, description="Nova quantidade (fracionada para unidades de peso)")
    valor_unitario: Optional[int] = Field(None, ge=0, description="Novo valor unitário em centavos")
    status_aprovacao: Optional[OrdemServicoItemAprovacao] = Field(None, description="Novo status de aprovação do item")
    garantia_dias: Optional[int] = Field(None, ge=0, description="Nova garantia do item em dias")
    garantia_km: Optional[int] = Field(None, ge=0, description="Nova garantia do item em KM")
    # A coerência entre visibilidade e valor é validada no serviço, e não aqui:
    # num PATCH os dois campos podem vir separados, e só depois de aplicados
    # sobre o item existente dá para saber em que estado ele ficou.
    visivel_cliente: Optional[bool] = Field(
        None,
        description="Alterna entre cobrada do cliente e embutida no serviço (valor zero)."
    )
    custo_unitario: Optional[int] = Field(
        None,
        ge=0,
        description="Novo custo interno por unidade, em centavos. Nunca impresso."
    )

    model_config = ConfigDict(from_attributes=True)
