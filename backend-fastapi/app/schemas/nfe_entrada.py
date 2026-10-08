# ---------------------------------------------------------------------------
# ARQUIVO: app/schemas/nfe_entrada.py
# DESCRIÇÃO: Entrada de mercadoria pela XML da NF-e (docs/entrada-xml-nfe-plano.md).
#            Dinheiro em CENTAVOS; quantidades em float (a nota tem até 4 casas).
# ---------------------------------------------------------------------------

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ── Prévia (POST /ler) ───────────────────────────────────────────────────────

class FornecedorPrevia(BaseModel):
    id: Optional[int] = Field(None, description="Nulo = será cadastrado na importação")
    documento: Optional[str] = None
    nome: Optional[str] = None
    fantasia: Optional[str] = None


class ProdutoPrevia(BaseModel):
    id: int
    nome: str
    codigo_produto: Optional[str] = None
    custo_atual: Optional[int] = Field(None, description="Custo médio de hoje, por unidade")
    valor_varejo: Optional[int] = None


class FiscalSugerido(BaseModel):
    """Sugestão tirada da nota do fornecedor (D7) — só vale para produto novo."""
    ncm: Optional[str] = None
    cest: Optional[str] = None
    csosn: Optional[str] = None
    cst_icms: Optional[str] = None
    cfop_padrao: Optional[str] = None
    cst_pis: Optional[str] = None
    cst_cofins: Optional[str] = None
    icms_st: bool = False
    monofasico: bool = False


class ItemPrevia(BaseModel):
    indice: int
    codigo: str = Field(..., description="Código do fornecedor (cProd)")
    descricao: str
    ean: Optional[str] = None
    ean_tributavel: Optional[str] = None
    unidade: str
    quantidade: float
    custo_total: int = Field(..., description="Valor do item com IPI, ST, frete e desconto")
    reconhecido_por: Optional[Literal["vinculo", "embalagem", "codigo_barras"]] = None
    produto: Optional[ProdutoPrevia] = None
    embalagem_id: Optional[int] = None
    embalagem_sigla: Optional[str] = None
    fator: int = Field(1, description="Unidades do estoque por item da nota")
    fator_da_nota: int = Field(1, description="O que a própria nota diz (qTrib ÷ qCom)")
    unidade_de_embalagem: bool = Field(False, description="A unidade da nota é CX, FD, PCT…")
    fator_a_confirmar: bool = Field(
        False,
        description=(
            "A unidade da nota é de embalagem (CX, FD…) e ninguém disse quantas unidades vêm "
            "nela: a importação exige o fator ou a confirmação de que é 1"
        ),
    )
    fiscal_sugerido: FiscalSugerido
    # Módulo Compras (fase 4): conferência contra o pedido SUGERIDO. Vazio sem
    # o módulo ou sem pedido aberto do fornecedor — e a tela segue como sempre.
    pedido_avisos: list[str] = Field(default_factory=list, description="Divergências deste item com o pedido")


class PedidoAbertoPrevia(BaseModel):
    """Pedido enviado/parcial do fornecedor da nota (módulo Compras, fase 4)."""

    id: int
    codigo: str
    situacao: str
    previsao_entrega: Optional[date] = None
    quantidade_itens: int


class DuplicataPrevia(BaseModel):
    numero: str
    vencimento: date
    valor: int


class NotaPrevia(BaseModel):
    chave: str
    numero: str
    serie: str
    emissao: Optional[date] = None
    natureza: Optional[str] = None
    valor_total: int
    fornecedor: FornecedorPrevia
    itens: list[ItemPrevia]
    duplicatas: list[DuplicataPrevia] = Field(default_factory=list)
    financeiro_disponivel: bool = Field(..., description="Módulo Financeiro liberado: dá para lançar as parcelas")
    ja_importada_em: Optional[datetime] = None
    avisos: list[str] = Field(default_factory=list)
    # Módulo Compras (fase 4). Vazios sem o módulo ou sem pedido aberto.
    pedidos_abertos: list[PedidoAbertoPrevia] = Field(default_factory=list)
    pedido_sugerido_id: Optional[int] = Field(None, description="O mais recente enviado; a tela pode trocar ou não ligar")
    pedido_avisos: list[str] = Field(
        default_factory=list, description="Do pedido sugerido: o que ele esperava e não veio, itens fora dele"
    )


# ── Importação (POST /importar) ──────────────────────────────────────────────

class ProdutoNovo(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255)
    codigo_produto: str = Field(..., min_length=1, max_length=100)
    codigo_barras: Optional[str] = Field(None, max_length=20)
    unidade_medida: Optional[str] = Field("UN", max_length=10)
    valor_varejo: int = Field(0, ge=0, description="Preço de venda da unidade (centavos)")
    usar_fiscal_sugerido: bool = True


class DecisaoItem(BaseModel):
    indice: int
    acao: Literal["vincular", "criar", "ignorar"]
    produto_id: Optional[int] = None
    embalagem_id: Optional[int] = None
    fator: int = Field(1, ge=1, le=100000)
    # "É 1 mesmo": o lojista conferiu que cada CX/FD da nota é uma unidade do estoque.
    fator_confirmado: bool = False
    novo: Optional[ProdutoNovo] = None

    @model_validator(mode="after")
    def _coerente(self) -> "DecisaoItem":
        if self.acao == "vincular" and self.produto_id is None:
            raise ValueError(f"Item {self.indice}: escolha o produto.")
        if self.acao == "criar" and self.novo is None:
            raise ValueError(f"Item {self.indice}: preencha o produto novo.")
        return self


class ImportarNota(BaseModel):
    xml: str = Field(..., min_length=1, description="O mesmo XML lido na prévia (D2)")
    itens: list[DecisaoItem]
    lancar_contas_pagar: bool = False
    # Módulo Compras (fase 4): ligar a nota a um pedido aberto do fornecedor.
    pedido_id: Optional[int] = Field(None, ge=1)


class EntradaLancada(BaseModel):
    produto_id: int
    unidades: float


class ResultadoImportacao(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nota_entrada_id: int
    fornecedor_id: Optional[int] = None
    fornecedor_criado: bool = False
    itens_lancados: int
    itens_ignorados: int
    produtos_criados: int
    contas_pagar_lancadas: int
    movimentacao_ids: list[int] = Field(default_factory=list)
    # Para a tela mandar à fila de etiquetas o que acabou de entrar.
    entradas: list[EntradaLancada] = Field(default_factory=list)
    # Módulo Compras (fase 4): o pedido ligado e o que divergiu (só avisa, D11).
    pedido_codigo: Optional[str] = None
    pedido_situacao: Optional[str] = None
    pedido_avisos: list[str] = Field(default_factory=list)


class NotaEntradaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chave: str
    numero: str
    serie: str
    emissao: Optional[date] = None
    valor_total: int
    fornecedor_id: Optional[int] = None
    fornecedor_nome: Optional[str] = None
    itens_lancados: int
    contas_pagar_lancadas: int
    usuario_nome: Optional[str] = None
    importada_em: datetime
