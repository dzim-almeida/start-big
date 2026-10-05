# ---------------------------------------------------------------------------
# ARQUIVO: schemas/compras.py
# MÓDULO: Schemas Pydantic — Compras (docs/compras-plano.md)
# ---------------------------------------------------------------------------
"""
Fase 1: fornecedores do produto. Chegam e saem EM BLOCO (replace-all, como
as embalagens): a tela manda a lista inteira, e o que não veio sai.
Espelho no frontend: `modules/compras/shared/types/compras.types.ts`.

Preço em centavos por UNIDADE DE COMPRA (o fardo, se compra em fardo).
Campos de preço saem nulos para quem não pode ver custo (D14).
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

MAX_FORNECEDORES_POR_PRODUTO = 30


class FornecedorResumo(BaseModel):
    """Para o seletor da tela — só o que ela mostra."""

    id: int
    nome: str
    nome_fantasia: Optional[str] = None


class FornecedorDoProdutoRead(BaseModel):
    """Uma linha da aba Fornecedores do produto.

    `id` nulo = o fornecedor principal do cadastro do produto, que ainda não
    tem linha aqui (aparece para o lojista completar código, embalagem e preço).
    """

    id: Optional[int] = None
    fornecedor_id: int
    fornecedor_nome: str
    codigo_fornecedor: Optional[str] = None
    embalagem_id: Optional[int] = None
    embalagem_sigla: Optional[str] = None
    fator: int = 1
    ultimo_preco: Optional[int] = Field(None, description="Centavos por unidade de compra; nulo sem permissão de custo")
    preco_unidade: Optional[float] = Field(None, description="Centavos por unidade do produto (só para exibir)")
    ultima_compra_em: Optional[date] = None
    prazo_dias: Optional[int] = None
    padrao: bool = Field(False, description="É o fornecedor principal do produto")
    mais_barato: bool = Field(False, description="Menor preço por unidade entre os fornecedores com preço (D18)")
    acima_do_menor_bp: int = Field(0, description="Quanto está acima do mais barato, em pontos-base (1000 = 10%)")


class FornecedorDoProdutoEscrita(BaseModel):
    fornecedor_id: int = Field(..., ge=1)
    codigo_fornecedor: Optional[str] = Field(None, max_length=60)
    embalagem_id: Optional[int] = Field(None, ge=1)
    fator: int = Field(1, ge=1, le=100_000)
    ultimo_preco: Optional[int] = Field(None, ge=0, le=100_000_000)
    prazo_dias: Optional[int] = Field(None, ge=0, le=365)
    padrao: bool = False

    @field_validator("codigo_fornecedor")
    @classmethod
    def _codigo_limpo(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return None
        valor = valor.strip()
        return valor or None


class FornecedoresDoProdutoSalvar(BaseModel):
    fornecedores: list[FornecedorDoProdutoEscrita] = Field(default_factory=list, max_length=MAX_FORNECEDORES_POR_PRODUTO)

    @model_validator(mode="after")
    def _sem_repeticao(self) -> "FornecedoresDoProdutoSalvar":
        ids = [f.fornecedor_id for f in self.fornecedores]
        if len(ids) != len(set(ids)):
            raise ValueError("O mesmo fornecedor aparece duas vezes na lista.")
        if sum(1 for f in self.fornecedores if f.padrao) > 1:
            raise ValueError("Só um fornecedor pode ser o principal.")
        return self


# ---------------------------------------------------------------------------
# Fase 2 — pedido de compra e necessidades
# ---------------------------------------------------------------------------
#
# Custos (custo_unitario, valores, parcelas) saem NULOS para quem não pode ver
# preço (D14) — o corte é no service, não na tela.

MAX_ITENS_POR_PEDIDO = 300
MAX_PARCELAS_POR_PEDIDO = 24


class PedidoItemEscrita(BaseModel):
    produto_id: int = Field(..., ge=1)
    embalagem_id: Optional[int] = Field(None, ge=1)
    fator: int = Field(1, ge=1, le=100_000)
    quantidade: int = Field(..., ge=1, le=1_000_000, description="Na unidade de compra")
    custo_unitario: int = Field(0, ge=0, le=100_000_000, description="Centavos por unidade de compra")


class PedidoParcelaEscrita(BaseModel):
    dias: int = Field(..., ge=0, le=365)
    valor: int = Field(..., ge=0)


class PedidoEscrita(BaseModel):
    """Criar ou substituir um RASCUNHO inteiro."""

    fornecedor_id: int = Field(..., ge=1)
    previsao_entrega: Optional[date] = None
    condicao_pagamento: Optional[str] = Field(None, max_length=60)
    frete: int = Field(0, ge=0, le=100_000_000)
    desconto: int = Field(0, ge=0, le=100_000_000)
    observacao: Optional[str] = Field(None, max_length=2000)
    itens: list[PedidoItemEscrita] = Field(default_factory=list, max_length=MAX_ITENS_POR_PEDIDO)
    # None = gerar pela condição de pagamento; lista = as parcelas como vieram.
    parcelas: Optional[list[PedidoParcelaEscrita]] = Field(None, max_length=MAX_PARCELAS_POR_PEDIDO)

    @model_validator(mode="after")
    def _sem_produto_repetido(self) -> "PedidoEscrita":
        ids = [i.produto_id for i in self.itens]
        if len(ids) != len(set(ids)):
            raise ValueError("O mesmo produto aparece duas vezes no pedido. Some as quantidades numa linha só.")
        return self


class PedidoDadosEscrita(BaseModel):
    """O que ainda dá para mudar num pedido ENVIADO: data e observação."""

    previsao_entrega: Optional[date] = None
    observacao: Optional[str] = Field(None, max_length=2000)


class MotivoEscrita(BaseModel):
    motivo: str = Field(..., min_length=3, max_length=255)

    @field_validator("motivo")
    @classmethod
    def _limpo(cls, valor: str) -> str:
        valor = valor.strip()
        if len(valor) < 3:
            raise ValueError("Diga o motivo (ao menos 3 letras).")
        return valor


class PedidoItemRead(BaseModel):
    id: int
    produto_id: Optional[int] = None
    descricao: str
    codigo_fornecedor: Optional[str] = None
    embalagem_id: Optional[int] = None
    unidade_compra: str
    fator: int
    quantidade: int
    quantidade_recebida: int
    quantidade_cancelada: int
    custo_unitario: Optional[int] = None
    subtotal: Optional[int] = None
    pendente: int = Field(0, description="Unidades de compra que ainda não chegaram nem foram encerradas")
    codigos_barras: list[str] = Field(
        default_factory=list, description="O que o leitor pode bipar para este item (embalagem e produto)"
    )


class PedidoParcelaRead(BaseModel):
    numero: int
    dias: int
    valor: Optional[int] = None


class CompraLogRead(BaseModel):
    acao: str
    situacao_anterior: Optional[str] = None
    situacao_nova: Optional[str] = None
    motivo: Optional[str] = None
    usuario_nome: Optional[str] = None
    ocorrido_em: datetime


class RecebimentoItemRead(BaseModel):
    descricao: str
    unidade_compra: str
    fator: int
    quantidade: int
    unidades: float
    custo_unitario: Optional[int] = None


class RecebimentoRead(BaseModel):
    id: int
    recebido_em: datetime
    recebido_por_nome: Optional[str] = None
    numero_nota: Optional[str] = None
    observacao: Optional[str] = None
    valor_itens: Optional[int] = None
    valor_ajuste: Optional[int] = None
    valor_total: Optional[int] = None
    contas_pagar_lancadas: int = 0
    itens: list[RecebimentoItemRead]


class PedidoResumo(BaseModel):
    id: int
    numero: int
    codigo: str
    situacao: str
    fornecedor_id: Optional[int] = None
    fornecedor_nome: str
    previsao_entrega: Optional[date] = None
    atrasado: bool = Field(False, description="Enviado e com a previsão já passada")
    quantidade_itens: int
    valor_total: Optional[int] = None
    criado_em: datetime
    enviado_em: Optional[datetime] = None


class PedidoRead(PedidoResumo):
    tipo: str
    condicao_pagamento: Optional[str] = None
    frete: Optional[int] = None
    desconto: Optional[int] = None
    valor_itens: Optional[int] = None
    observacao: Optional[str] = None
    motivo_cancelamento: Optional[str] = None
    criado_por_nome: Optional[str] = None
    fornecedor_telefone: Optional[str] = None
    itens: list[PedidoItemRead]
    parcelas: list[PedidoParcelaRead]
    historico: list[CompraLogRead]
    recebimentos: list[RecebimentoRead] = Field(default_factory=list)


class PedidoListagem(BaseModel):
    itens: list[PedidoResumo]
    total_itens: int


class MensagemFornecedor(BaseModel):
    """Texto pronto para mandar o pedido por WhatsApp."""

    texto: str
    telefone: Optional[str] = Field(None, description="Com DDI 55, só dígitos; nulo se o fornecedor não tem")


class SimularParcelas(BaseModel):
    total: int = Field(..., ge=0)
    condicao: Optional[str] = Field(None, max_length=60)


class ParcelaSimulada(BaseModel):
    numero: int
    dias: int
    valor: int


class AlternativaMaisBarata(BaseModel):
    """D18: outro fornecedor do produto vende mais barato por unidade."""

    fornecedor_id: int
    fornecedor_nome: str
    preco_unidade: float = Field(..., description="Centavos por unidade do produto")
    economia_bp: int = Field(..., description="Quanto é mais barato, em pontos-base (1000 = 10%)")


class OpcaoFornecedor(BaseModel):
    fornecedor_id: int
    fornecedor_nome: str
    embalagem_id: Optional[int] = None
    unidade_compra: str
    fator: int
    ultimo_preco: Optional[int] = None
    prazo_dias: Optional[int] = None


class DemandaOSRead(BaseModel):
    """Uma OS aberta que usa o produto (fase 6)."""

    os_id: int
    numero_os: str
    quantidade: float = Field(..., description="Unidades do produto que a OS precisa")
    data_previsao: Optional[date] = None
    data_instalacao: Optional[date] = None
    aguardando_sinal: bool = Field(False, description="Fábrica sem sinal: reserva, mas não entra na compra")


class NecessidadeItem(BaseModel):
    produto_id: int
    produto_nome: str
    codigo_produto: Optional[str] = None
    unidade_medida: str
    saldo: float
    minimo: Optional[float] = Field(None, description="Nulo quando o produto entra só pela venda (base VENDAS)")
    ideal: Optional[float] = None
    em_pedido: float = Field(..., description="A caminho (pedidos enviados), na unidade do produto")
    em_rascunho: float = Field(0, description="Em rascunhos ainda não enviados — NÃO desconta da sugestão")
    rascunhos: list[str] = Field(default_factory=list, description="Códigos dos rascunhos que já têm o produto")
    fornecedor_id: Optional[int] = None
    fornecedor_nome: Optional[str] = None
    embalagem_id: Optional[int] = None
    unidade_compra: str
    fator: int
    sugestao: int = Field(..., description="Unidades de compra")
    ultimo_preco: Optional[int] = None
    alternativa: Optional[AlternativaMaisBarata] = None
    opcoes: list[OpcaoFornecedor] = Field(default_factory=list, description="Outros fornecedores do produto")
    # Fase 5: de onde veio a sugestão, e o giro do produto quando a base é VENDAS.
    origem: str = Field("MINIMO", description="MINIMO, VENDAS ou OS (peça de OS aberta que falta)")
    media_diaria: Optional[float] = Field(None, description="Vendido por dia na janela (unidade do produto)")
    dura_dias: Optional[float] = Field(None, description="Para quantos dias o estoque de hoje dá, nesse ritmo")
    # Fase 6: o que as OS abertas já comprometeram (reserva CALCULADA).
    reservado_os: float = Field(0, description="Unidades comprometidas com OS abertas; o saldo livre é saldo − isto")
    ordens: list[DemandaOSRead] = Field(default_factory=list, description="As OS que usam o produto, a mais antiga 1º")


class NecessidadeGrupo(BaseModel):
    fornecedor_id: Optional[int] = None
    fornecedor_nome: str
    itens: list[NecessidadeItem]


class GerarPedidoItem(BaseModel):
    produto_id: int = Field(..., ge=1)
    fornecedor_id: int = Field(..., ge=1)
    quantidade: int = Field(..., ge=1, le=1_000_000, description="Unidades de compra")


class GerarPedidos(BaseModel):
    itens: list[GerarPedidoItem] = Field(..., min_length=1, max_length=MAX_ITENS_POR_PEDIDO)


class EmbalagemResumo(BaseModel):
    id: int
    sigla: str
    fator: int


class ProdutoParaPedido(BaseModel):
    """O mínimo para pôr um produto no pedido, sem depender da permissão de Produtos."""

    id: int
    nome: str
    codigo_produto: Optional[str] = None
    codigo_barras: Optional[str] = None
    unidade_medida: str
    saldo: float
    embalagens: list[EmbalagemResumo] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Fase 3 — recebimento
# ---------------------------------------------------------------------------


class RecebimentoItemEscrita(BaseModel):
    pedido_item_id: int = Field(..., ge=1)
    quantidade: int = Field(..., ge=0, le=1_000_000, description="Na unidade de compra; 0 = não chegou")
    # Custo REAL, por unidade de compra. Nulo = o do pedido. Ignorado para quem
    # não pode ver custo (o almoxarife confere quantidade, não preço — D14).
    custo_unitario: Optional[int] = Field(None, ge=0, le=100_000_000)


class RecebimentoEscrita(BaseModel):
    itens: list[RecebimentoItemEscrita] = Field(..., min_length=1, max_length=MAX_ITENS_POR_PEDIDO)
    numero_nota: Optional[str] = Field(None, max_length=20)
    observacao: Optional[str] = Field(None, max_length=2000)
    lancar_contas_pagar: bool = Field(True, description="Gera as contas a pagar proporcionais (D8), com o Financeiro")
    encerrar_saldo: bool = Field(False, description="O que não chegou agora não vem mais (D5)")

    @model_validator(mode="after")
    def _sem_item_repetido(self) -> "RecebimentoEscrita":
        ids = [i.pedido_item_id for i in self.itens]
        if len(ids) != len(set(ids)):
            raise ValueError("O mesmo item aparece duas vezes no recebimento.")
        return self


# ---------------------------------------------------------------------------
# Fase 5 — relatórios
# ---------------------------------------------------------------------------


class RelatorioFornecedor(BaseModel):
    fornecedor_id: Optional[int] = None
    fornecedor_nome: str
    pedidos_enviados: int
    recebimentos: int
    valor_recebido: int = Field(..., description="Centavos")
    prazo_medio_dias: Optional[float] = Field(None, description="Do envio do pedido à primeira chegada")
    entregas_com_previsao: int = 0
    entregas_no_prazo: int = 0


class VariacaoPreco(BaseModel):
    produto_id: int
    descricao: str
    fornecedor_nome: str = Field(..., description="Da última compra")
    compras: int
    primeiro_custo_unidade: float = Field(..., description="Centavos por unidade, na 1ª chegada do período")
    ultimo_custo_unidade: float
    variacao_bp: int = Field(..., description="Pontos-base (1000 = 10%); positivo = subiu")


class RelatorioCompras(BaseModel):
    inicio: date
    fim: date
    pedidos_enviados: int
    valor_recebido: int
    por_fornecedor: list[RelatorioFornecedor]
    variacao_precos: list[VariacaoPreco]



# ---------------------------------------------------------------------------
# Fase 6 — compras de uma OS
# ---------------------------------------------------------------------------


class PedidoDaOS(BaseModel):
    pedido_id: int
    codigo: str
    situacao: str
    previsao_entrega: Optional[date] = None
    quantidade: float = Field(..., description="Unidades deste pedido que são desta OS")
    atrasa_os: bool = Field(False, description="A entrega prevista é depois da previsão da OS (RC08)")


class CompraDaOSItem(BaseModel):
    produto_id: int
    descricao: str
    unidade: str
    necessario: float
    no_estoque: float = Field(..., description="Quanto do estoque livre fica para esta OS (fila: a OS mais antiga 1º)")
    em_pedido: float = Field(..., description="Em pedidos ainda não recebidos, ligados a esta OS")
    falta: float = Field(..., description="O que ninguém cobre ainda: precisa comprar")
    situacao: str = Field(..., description="NO_ESTOQUE, EM_PEDIDO ou FALTA")
    pedidos: list[PedidoDaOS] = Field(default_factory=list)


class ComprasDaOS(BaseModel):
    os_id: int
    numero_os: str
    aberta: bool = Field(..., description="Falso para OS finalizada/cancelada: as peças já saíram ou não vão sair")
    data_previsao: Optional[date] = None
    itens: list[CompraDaOSItem]
    # Marcenaria-fábrica (F3): instalação manda no aviso de atraso, e sem
    # sinal o material fica reservado mas fora das Necessidades.
    data_instalacao: Optional[date] = None
    compra_bloqueada: bool = Field(False, description="OS da fábrica aguardando o sinal: não gera compra ainda")
