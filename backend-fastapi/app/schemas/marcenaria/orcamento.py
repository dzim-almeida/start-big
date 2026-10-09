# ---------------------------------------------------------------------------
# ARQUIVO: app/schemas/marcenaria/orcamento.py
# DESCRICAO: O que a API do orcamento de marcenaria RECEBE (Spec 06A, secao 6).
#
# So entradas. As SAIDAS (detalhe, lista) sao montadas como dicionario no
# servico (orcamento_detalhe.py) porque dependem da permissao: quem nao ve
# custo recebe a resposta SEM as chaves de custo (D23) -- ausentes, e nao
# nulas. Um schema de saida do Pydantic escreveria `null` nelas.
#
# Unidades (D10): centavos, basis points (9000 = 90%), milesimos de insumo
# (1,4 chapa = 1400), centesimos de hora (2,5 h = 250), milimetros. Tudo int.
#
# `extra="forbid"`: campo desconhecido responde 422. Um erro de digitacao no
# frontend ("markup" em vez de "markup_bp") apareceria em vez de sumir calado.
# ---------------------------------------------------------------------------

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# Formas aceitas (as mesmas do motor da Spec 05).
ModoAjuste = Literal["PERCENTUAL", "VALOR"]           # desconto e sinal
ModoMaoObra = Literal["FIXA", "HORAS", "NENHUMA"]
TipoProducao = Literal["INTERNA", "TERCEIRIZADA"]
ModoRT = Literal["MARGEM", "PRECO"]


def _texto(valor: Optional[str]) -> Optional[str]:
    """Tira espacos das pontas; texto vazio vira None (campo limpo)."""
    if valor is None:
        return None
    limpo = valor.strip()
    return limpo or None


def _entre(valor: Optional[int], minimo: int, maximo: Optional[int], mensagem: str) -> Optional[int]:
    """Recusa numero fora de [minimo, maximo] com a mensagem dada. None passa."""
    if valor is None:
        return None
    if valor < minimo or (maximo is not None and valor > maximo):
        raise ValueError(mensagem)
    return valor


class _Entrada(BaseModel):
    """Base de todas as entradas: campo desconhecido = 422."""
    model_config = ConfigDict(extra="forbid")


# ===========================================================================
# CABECALHO
# ===========================================================================

class OrcamentoCriar(_Entrada):
    """POST / -- tudo opcional; o orcamento nasce em RASCUNHO."""
    cliente_id: Optional[int] = None
    objeto_id: Optional[int] = None          # projeto ja cadastrado do cliente (D6)
    projeto_nome: Optional[str] = Field(None, max_length=100)
    endereco_obra: Optional[str] = Field(None, max_length=255)
    funcionario_id: Optional[int] = None     # vendedor; sem ele, o do usuario logado

    _limpar = field_validator("projeto_nome", "endereco_obra")(lambda cls, v: _texto(v))


class AjusteEntrada(_Entrada):
    """Desconto ou sinal: forma + valor (bp no PERCENTUAL, centavos no VALOR).

    Os limites (nao negativo, ate 100%, nao maior que o total) sao do MOTOR:
    o erro volta com `campo` (desconto/sinal) para a tela mostrar no lugar
    certo (secao 6.9).
    """
    modo: ModoAjuste
    valor: int


class OrcamentoAtualizar(_Entrada):
    """PATCH /{id} -- so os campos ENVIADOS mudam.

    Campos de custo (markup, perda, custo/hora, RT padrao e modo, instalacao)
    exigem `view_custos_marcenaria` (D24); o servico confere.
    """
    cliente_id: Optional[int] = None
    funcionario_id: Optional[int] = None
    objeto_id: Optional[int] = None
    projeto_nome: Optional[str] = Field(None, max_length=100)
    endereco_obra: Optional[str] = Field(None, max_length=255)
    medicao_observacoes: Optional[str] = Field(None, max_length=4000)   # D29
    observacoes_proposta: Optional[str] = Field(None, max_length=4000)  # sai na proposta (Spec 07)

    # --- Custo (D23/D24) ---
    markup_bp: Optional[int] = None
    perda_bp: Optional[int] = None
    custo_hora_centavos: Optional[int] = None
    rt_padrao_bp: Optional[int] = None
    rt_modo: Optional[ModoRT] = None
    instalacao_custo_centavos: Optional[int] = None    # null = sem linha de instalacao

    # --- Prazos (nao sao custo) ---
    validade_dias: Optional[int] = None
    prazo_entrega_dias: Optional[int] = None

    desconto: Optional[AjusteEntrada] = None
    sinal: Optional[AjusteEntrada] = None

    _limpar = field_validator(
        "projeto_nome", "endereco_obra", "medicao_observacoes", "observacoes_proposta",
    )(lambda cls, v: _texto(v))

    @field_validator("rt_padrao_bp")
    @classmethod
    def _rt(cls, v):
        return _entre(v, 0, 3_000, "O RT deve ficar entre 0% e 30%.")

    @field_validator("validade_dias")
    @classmethod
    def _validade(cls, v):
        return _entre(v, 1, 365, "A validade deve ficar entre 1 e 365 dias.")

    @field_validator("prazo_entrega_dias")
    @classmethod
    def _prazo(cls, v):
        return _entre(v, 1, 365, "O prazo de entrega deve ficar entre 1 e 365 dias.")


class ArquitetoEntrada(_Entrada):
    """Uma linha do PUT /{id}/rt. Sem `rt_bp`, mantem o gravado ou usa o padrao (Revisao 3)."""
    fornecedor_id: int
    rt_bp: Optional[int] = None

    @field_validator("rt_bp")
    @classmethod
    def _rt(cls, v):
        return _entre(v, 0, 3_000, "O RT deve ficar entre 0% e 30%.")


class ArquitetosEntrada(_Entrada):
    """PUT /{id}/rt -- substitui a lista inteira; vazia remove o arquiteto."""
    arquitetos: list[ArquitetoEntrada] = Field(default_factory=list, max_length=10)

    @field_validator("arquitetos")
    @classmethod
    def _sem_repetir(cls, v):
        ids = [a.fornecedor_id for a in v]
        if len(set(ids)) != len(ids):
            raise ValueError("O mesmo arquiteto aparece duas vezes.")
        return v


# ===========================================================================
# AMBIENTES E MOVEIS
# ===========================================================================

class AmbienteEntrada(_Entrada):
    """POST/PATCH de ambiente: so o nome."""
    nome: str = Field(..., max_length=80)

    @field_validator("nome")
    @classmethod
    def _nome(cls, v):
        limpo = _texto(v)
        if not limpo:
            raise ValueError("Informe o nome do ambiente.")
        return limpo


class OrdemEntrada(_Entrada):
    """PUT .../ordem -- todos os ids, na ordem nova."""
    ids: list[int]


class MaoObraEntrada(_Entrada):
    """Mao de obra por unidade do movel (Spec 05, §6.2)."""
    modo: ModoMaoObra = "NENHUMA"
    centavos: int = Field(0, ge=0)              # FIXA
    horas_centesimos: int = Field(0, ge=0)      # HORAS (x custo/hora do orcamento)


class InsumoEntrada(_Entrada):
    """Um insumo do movel (secao 6.4).

    - com `id`: insumo ja gravado; mantem custo, origem, descricao e
      `sofre_perda` (O3). So a quantidade e a ordem mudam;
    - sem `id`: novo, copiado do produto (D2, D3);
    - `custo_unit_centavos` enviado: custo digitado a mao (origem MANUAL),
      exige `view_custos_marcenaria` (D24).
    """
    id: Optional[int] = None
    produto_id: Optional[int] = None
    quantidade_milesimos: int
    custo_unit_centavos: Optional[int] = None

    @field_validator("quantidade_milesimos")
    @classmethod
    def _quantidade(cls, v):
        return _entre(v, 1, 100_000_000, "A quantidade do insumo deve ser maior que zero.")

    @field_validator("custo_unit_centavos")
    @classmethod
    def _custo(cls, v):
        return _entre(v, 0, None, "O custo do insumo não pode ser negativo.")

    @model_validator(mode="after")
    def _produto_no_novo(self):
        # Insumo novo e sempre de um produto do cadastro: e de la que vem a copia.
        if self.id is None and self.produto_id is None:
            raise ValueError("Escolha o produto do insumo.")
        return self


_MEDIDA_MAXIMA_MM = 100_000   # 100 m: protege contra um zero a mais digitado


class MovelEntrada(_Entrada):
    """Movel completo (POST no ambiente, PUT, simular). Secao 6.4.

    D24a: chave de custo AUSENTE (`mao_obra`, `terceirizado_centavos`) mantem
    o valor gravado; por isso elas sao None quando nao vem.
    """
    nome: str = Field(..., max_length=120)
    descricao: Optional[str] = Field(None, max_length=500)
    largura_mm: Optional[int] = None
    altura_mm: Optional[int] = None
    profundidade_mm: Optional[int] = None
    quantidade: int = 1
    tipo_producao: TipoProducao = "INTERNA"
    central_fornecedor_id: Optional[int] = None
    terceirizado_centavos: Optional[int] = None
    mao_obra: Optional[MaoObraEntrada] = None
    insumos: list[InsumoEntrada] = Field(default_factory=list)
    # PUT: pode mudar o movel de ambiente (secao 6.1).
    ambiente_id: Optional[int] = None

    @field_validator("nome")
    @classmethod
    def _nome(cls, v):
        limpo = _texto(v)
        if not limpo:
            raise ValueError("Informe o nome do móvel.")
        return limpo

    @field_validator("descricao")
    @classmethod
    def _descricao(cls, v):
        return _texto(v)

    @field_validator("largura_mm", "altura_mm", "profundidade_mm")
    @classmethod
    def _medida(cls, v):
        return _entre(v, 1, _MEDIDA_MAXIMA_MM, "As medidas devem ficar entre 1 mm e 100 m.")

    @field_validator("quantidade")
    @classmethod
    def _quantidade(cls, v):
        return _entre(v, 1, 9_999, "A quantidade do móvel deve ficar entre 1 e 9999.")

    @field_validator("terceirizado_centavos")
    @classmethod
    def _terceirizado(cls, v):
        return _entre(v, 0, None, "O custo terceirizado não pode ser negativo.")

    @model_validator(mode="after")
    def _central(self):
        # Movel terceirizado e pedido a uma central parceira (E6): sem ela, nao
        # ha a quem pedir.
        if self.tipo_producao == "TERCEIRIZADA" and not self.central_fornecedor_id:
            raise ValueError("Móvel terceirizado precisa da central parceira.")
        return self


class SimularEntrada(MovelEntrada):
    """POST /{id}/moveis/simular -- o movel + (opcional) o id do movel gravado,
    para os insumos com `id` manterem o custo copiado (secao 6.6)."""
    movel_id: Optional[int] = None


# ===========================================================================
# TRANSICOES, PRECOS E ANEXOS
# ===========================================================================

class RecusarEntrada(_Entrada):
    """POST /{id}/recusar -- motivo obrigatorio (D17)."""
    motivo: str = Field("", validate_default=True)

    @field_validator("motivo")
    @classmethod
    def _motivo(cls, v):
        limpo = _texto(v)
        if not limpo:
            raise ValueError("Informe o motivo da recusa.")
        if len(limpo) > 500:
            raise ValueError("O motivo pode ter até 500 caracteres.")
        return limpo


class AtualizarPrecosEntrada(_Entrada):
    """POST /{id}/atualizar-precos -- os insumos escolhidos, ou todos."""
    insumo_ids: list[int] = Field(default_factory=list)
    todos: bool = False

    @model_validator(mode="after")
    def _algum(self):
        if not self.todos and not self.insumo_ids:
            raise ValueError("Escolha os insumos que vão receber o preço novo.")
        return self


class LegendaEntrada(_Entrada):
    """PATCH /{id}/anexos/{xid} -- so a legenda (D28)."""
    legenda: Optional[str] = Field(None, max_length=120)

    _limpar = field_validator("legenda")(lambda cls, v: _texto(v))
