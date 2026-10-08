# ---------------------------------------------------------------------------
# ARQUIVO: app/schemas/fabrica.py
# DESCRIÇÃO: Schemas da marcenaria-fábrica (docs/marcenaria-fabrica-plano.md).
# ---------------------------------------------------------------------------

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

UnidadeConsumo = Literal["M2", "M", "UN"]

# Teto do INTEGER: 2.147.483.647 mm² = 2.147 m² por unidade — sobra.
CONSUMO_MAXIMO = 2_147_483_647


class InsumoRead(BaseModel):
    """Como o produto entra no orçamento da fábrica (F1, D2)."""

    model_config = ConfigDict(from_attributes=True)

    produto_id: int
    unidade_medida: Optional[str] = Field(None, description="Unidade do ESTOQUE (a de compra: chapa, rolo, UN).")
    unidade_consumo: Optional[UnidadeConsumo] = Field(None, description="Nulo = o produto não é insumo.")
    consumo_por_unidade: Optional[int] = Field(
        None, description="Rendimento de uma unidade de estoque: mm² (M2), mm (M) ou unidades (UN)."
    )
    sofre_perda: bool = False


class InsumoBusca(BaseModel):
    """Um insumo para pôr na lista de material do móvel."""

    id: int
    nome: str
    codigo_produto: Optional[str] = None
    unidade_medida: Optional[str] = None
    unidade_consumo: UnidadeConsumo
    consumo_por_unidade: int
    sofre_perda: bool
    custo_unitario: Optional[int] = Field(None, description="Custo de hoje por unidade de compra. Nulo sem permissão de custo")


class InsumoEscrita(BaseModel):
    """Grava o insumo. `unidade_consumo` nulo desliga: o produto volta a ser comum."""

    unidade_consumo: Optional[UnidadeConsumo] = None
    consumo_por_unidade: Optional[int] = Field(None, ge=1, le=CONSUMO_MAXIMO)
    sofre_perda: bool = False

    @model_validator(mode="after")
    def _coerente(self):
        if self.unidade_consumo is None:
            # Desligar limpa tudo: rendimento sem unidade não significa nada.
            self.consumo_por_unidade = None
            self.sofre_perda = False
        elif self.consumo_por_unidade is None:
            raise ValueError("Informe quanto uma unidade do estoque rende (área da chapa, comprimento do rolo...).")
        return self


# ---------------------------------------------------------------------------
# F2 — orçamento por móvel (árvore versão → ambiente → móvel → material)
# ---------------------------------------------------------------------------

MEDIDA_MAXIMA_MM = 100_000      # 100 m: acima disso é digitação errada
DINHEIRO_MAXIMO = 2_000_000_000  # centavos, cabe no INTEGER


class MaterialEscrita(BaseModel):
    # O id da linha já gravada: com ele (e o mesmo produto) o custo copiado na
    # inclusão é mantido; sem ele, o custo é o de hoje (plano, §4).
    id: Optional[int] = None
    produto_id: int = Field(..., ge=1)
    consumo: int = Field(..., ge=1, le=CONSUMO_MAXIMO, description="Na unidade de consumo do insumo: mm², mm ou un")


class MovelEscrita(BaseModel):
    nome: str = Field(..., min_length=1, max_length=120)
    largura_mm: Optional[int] = Field(None, ge=1, le=MEDIDA_MAXIMA_MM)
    altura_mm: Optional[int] = Field(None, ge=1, le=MEDIDA_MAXIMA_MM)
    profundidade_mm: Optional[int] = Field(None, ge=1, le=MEDIDA_MAXIMA_MM)
    preco_venda: int = Field(0, ge=0, le=DINHEIRO_MAXIMO)
    terceirizado: bool = False
    custo_terceiro: Optional[int] = Field(None, ge=0, le=DINHEIRO_MAXIMO)
    materiais: list[MaterialEscrita] = Field(default_factory=list, max_length=200)


class AmbienteEscrita(BaseModel):
    nome: str = Field(..., min_length=1, max_length=60)
    moveis: list[MovelEscrita] = Field(default_factory=list, max_length=200)


class OrcamentoEscrita(BaseModel):
    """A árvore INTEIRA: o que não vier sai (só em RASCUNHO)."""

    perda_bp: int = Field(1000, ge=0, le=5000, description="1000 = 10%")
    sinal_bp: int = Field(5000, ge=0, le=10000, description="5000 = 50%")
    validade: Optional[date] = None
    observacao: Optional[str] = Field(None, max_length=2000)
    ambientes: list[AmbienteEscrita] = Field(default_factory=list, max_length=50)


class NovaVersao(BaseModel):
    copiar_de: Optional[int] = Field(None, ge=1, description="Id da versão a copiar; nulo = versão vazia")


class MotivoRecusa(BaseModel):
    motivo: str = Field(..., min_length=1, max_length=255)


class MaterialRead(BaseModel):
    id: int
    produto_id: Optional[int]
    descricao: str
    consumo: int
    unidade_consumo: Optional[UnidadeConsumo] = None
    consumo_por_unidade: Optional[int] = None
    sofre_perda: bool = False
    unidade_medida: Optional[str] = None
    custo_unitario: Optional[int] = Field(None, description="Por unidade de compra (chapa, rolo), copiado ao incluir")
    custo: Optional[int] = Field(None, description="Custo da fração usada neste móvel, já com a perda")


class MovelRead(BaseModel):
    id: int
    nome: str
    largura_mm: Optional[int]
    altura_mm: Optional[int]
    profundidade_mm: Optional[int]
    medidas: Optional[str]
    preco_venda: int
    terceirizado: bool
    custo_terceiro: Optional[int]
    custo: Optional[int] = Field(None, description="Materiais + terceiro. Nulo sem permissão de custo")
    materiais: list[MaterialRead]
    # F5: o pedido de serviço à central de corte (móvel terceirizado).
    pedido_compra_id: Optional[int] = None
    pedido_codigo: Optional[str] = None
    pedido_situacao: Optional[str] = None


class AmbienteRead(BaseModel):
    id: int
    nome: str
    moveis: list[MovelRead]


class InsumoDaAprovacao(BaseModel):
    """O que a aprovação vai escrever na OS para este insumo (somado em todos os móveis)."""

    produto_id: int
    descricao: str
    unidade_medida: Optional[str]
    consumo_total: int = Field(..., description="Já com a perda, na unidade de consumo")
    quantidade: int = Field(..., description="Unidades de compra inteiras (chapas, rolos)")
    custo_unitario: Optional[int] = None


class OrcamentoResumo(BaseModel):
    id: int
    versao: int
    situacao: str = Field(..., description="RASCUNHO, ENVIADO, APROVADO, RECUSADO ou VENCIDO")
    total: int
    criado_em: datetime
    enviado_em: Optional[datetime]
    aprovado_em: Optional[datetime]


class OrcamentoRead(OrcamentoResumo):
    os_id: int
    numero_os: str
    perda_bp: int
    sinal_bp: int
    sinal_valor: int = Field(..., description="⌈ total × sinal ⌉, centavos")
    validade: Optional[date]
    custo_total: Optional[int] = Field(None, description="Nulo sem permissão de custo")
    observacao: Optional[str]
    aprovado_por: Optional[str]
    recusado_motivo: Optional[str]
    editavel: bool = Field(..., description="Só RASCUNHO se edita")
    ambientes: list[AmbienteRead]
    insumos: list[InsumoDaAprovacao]


# ---------------------------------------------------------------------------
# F3 — o trilho (as 10 etapas)
# ---------------------------------------------------------------------------

class TravaRead(BaseModel):
    codigo: str
    texto: str
    ok: bool


class EtapaRead(BaseModel):
    fase: str
    rotulo: str
    situacao: Literal["FEITA", "ATUAL", "A_FAZER"]


class LogFaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fase_anterior: Optional[str]
    fase_nova: Optional[str]
    evento: str
    motivo: Optional[str]
    usuario: Optional[str]
    ocorrido_em: datetime


class TrilhoRead(BaseModel):
    numero_os: str
    fase: str
    rotulo: str
    status_os: str
    aberta: bool = Field(..., description="Falso com a OS finalizada ou cancelada")
    travar_etapas: bool = Field(..., description="True: pendência bloqueia. False: vira aviso com motivo")
    etapas: list[EtapaRead]
    proxima: Optional[str] = None
    proxima_rotulo: Optional[str] = None
    avanco_por_acao: Optional[str] = Field(None, description="Se sair desta etapa é uma ação própria, qual")
    travas: list[TravaRead]
    sinal_exigido: int
    recebido: int
    pode_comprar: bool = Field(..., description="O material desta OS já vira necessidade de compra (RC04)")
    compra_liberada_em: Optional[datetime] = None
    compra_liberada_por: Optional[str] = None
    compra_liberada_motivo: Optional[str] = None
    data_instalacao: Optional[date] = None
    log: list[LogFaseRead]


class Avancar(BaseModel):
    motivo: Optional[str] = Field(None, max_length=500, description="Obrigatório quando há pendência e as etapas só avisam")


class Voltar(BaseModel):
    fase: str = Field(..., max_length=30)
    motivo: str = Field(..., min_length=3, max_length=500)


class LiberarCompra(BaseModel):
    motivo: str = Field(..., min_length=3, max_length=500)


class Instalacao(BaseModel):
    data_instalacao: Optional[date] = None


# ---------------------------------------------------------------------------
# F4 — separação bipada e margem
# ---------------------------------------------------------------------------

class ItemSeparacao(BaseModel):
    """Uma linha da tela do almoxarife. Sem preço (DC5)."""

    item_id: int
    produto_id: int
    descricao: str
    unidade: str
    localizacao: Optional[str] = None
    codigos: list[str] = Field(default_factory=list, description="O que o leitor pode bipar")
    quantidade: float
    separada: float
    falta: float
    saldo_estoque: float


class SeparacaoRead(BaseModel):
    numero_os: str
    cliente: Optional[str] = None
    projeto: Optional[str] = None
    fase: str
    pode_separar: bool
    completa: bool
    itens: list[ItemSeparacao]


class Separar(BaseModel):
    """Um bipe (`codigo`) ou um item escolhido na lista (`item_id`)."""

    codigo: Optional[str] = Field(None, max_length=100)
    item_id: Optional[int] = Field(None, ge=1)
    quantidade: float = Field(1, gt=0, le=100_000, description="Na unidade bipada (embalagem conta o fator)")


class EstornoSeparacao(BaseModel):
    item_id: int = Field(..., ge=1)
    quantidade: float = Field(..., gt=0, le=100_000)
    motivo: str = Field(..., min_length=3, max_length=500)


class InsumoMargem(BaseModel):
    produto_id: int
    descricao: str
    quantidade: float
    separada: float
    custo_orcado: int = Field(..., description="A fração usada (com a perda) ao custo congelado")
    custo_real: Optional[int] = Field(None, description="Separado × custo do dia da separação; nulo sem separação")
    custo_unitario_orcado: Optional[int] = None
    custo_unitario_real: Optional[int] = None


class MovelMargem(BaseModel):
    movel_id: int
    nome: str
    custo_orcado: int
    custo_real: Optional[int] = Field(None, description="O que foi recebido do pedido de serviço; nulo sem recebimento")
    pedido_compra_id: Optional[int] = None


class MargemRead(BaseModel):
    numero_os: str
    versao: int
    preco: int
    custo_orcado: int
    custo_real: int = Field(..., description="Soma do que já é real (separado + serviços recebidos)")
    margem_orcada_bp: Optional[int] = None
    margem_real_bp: Optional[int] = Field(None, description="Só quando tudo foi separado e recebido")
    completo: bool
    insumos: list[InsumoMargem]
    terceirizados: list[MovelMargem]


# ---------------------------------------------------------------------------
# F5 — terceirizados (central de corte)
# ---------------------------------------------------------------------------

class PedidoServicoEscrita(BaseModel):
    fornecedor_id: int = Field(..., ge=1)
    valor: int = Field(..., gt=0, le=2_000_000_000, description="O que a central de corte vai cobrar, centavos")
    previsao_entrega: Optional[date] = None
    condicao_pagamento: Optional[str] = Field(None, max_length=60)
    observacao: Optional[str] = Field(None, max_length=2000, description="O que vai para a central (arquivo, medidas)")


class PedidoServicoRead(BaseModel):
    movel_id: int
    pedido_compra_id: int
    codigo: str
    situacao: str
    fornecedor_nome: str
    valor_total: int
