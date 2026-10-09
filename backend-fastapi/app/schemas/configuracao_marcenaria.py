# ---------------------------------------------------------------------------
# ARQUIVO: app/schemas/configuracao_marcenaria.py
# DESCRICAO: Contrato de GET/PUT /configuracoes/marcenaria (Spec 04A, §4.1).
#
#            Percentuais em basis points (9000 = 90,00%) e dinheiro em centavos:
#            inteiros, nunca float (SPEC-00, PR4). As mensagens de erro vao para
#            a tela, por isso em portugues.
# ---------------------------------------------------------------------------

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class RtModo(str, Enum):
    """Como a Reserva Tecnica (RT) do arquiteto entra no orcamento (SPEC-00, C5c)."""
    MARGEM = "MARGEM"   # o RT sai da margem da loja; o preco ao cliente nao muda (padrao)
    PRECO = "PRECO"     # o RT e embutido no preco


def _entre(valor: Optional[int], minimo: int, maximo: Optional[int], mensagem: str) -> Optional[int]:
    """Recusa numero fora de [minimo, maximo] com a mensagem dada. None passa (PUT parcial)."""
    if valor is None:
        return None
    if valor < minimo or (maximo is not None and valor > maximo):
        raise ValueError(mensagem)
    return valor


def _lista_de_nomes(valores: Optional[list[str]], maximo_itens: int, maximo_chars: int, nome: str) -> Optional[list[str]]:
    """Limpa espacos e recusa lista vazia, item vazio, longo demais ou repetido.

    Repetido nao diferencia maiusculas: "Corte" e "corte" sao a mesma etapa
    para quem le a OS.
    """
    if valores is None:                                        # campo nao enviado (PUT parcial)
        return None
    limpos = [v.strip() for v in valores]                      # "  Corte  " -> "Corte"
    if not 1 <= len(limpos) <= maximo_itens:
        raise ValueError(f"{nome}: informe de 1 a {maximo_itens} itens.")
    if any(not v for v in limpos):
        raise ValueError(f"{nome}: há um item vazio.")
    if any(len(v) > maximo_chars for v in limpos):
        raise ValueError(f"{nome}: cada item pode ter até {maximo_chars} caracteres.")
    if len({v.casefold() for v in limpos}) != len(limpos):    # casefold = minusculas para comparar
        raise ValueError(f"{nome}: há itens repetidos.")
    return limpos


class ConfiguracaoMarcenariaUpdate(BaseModel):
    """PUT parcial: so os campos enviados mudam."""
    model_config = ConfigDict(extra="forbid")                  # campo desconhecido = 422

    markup_padrao_bp: Optional[int] = None
    perda_padrao_bp: Optional[int] = None
    custo_hora_centavos: Optional[int] = None
    rt_padrao_bp: Optional[int] = None
    rt_modo: Optional[RtModo] = None
    validade_dias: Optional[int] = None
    prazo_entrega_dias: Optional[int] = None
    etapas_producao: Optional[list[str]] = None
    checklist_vistoria: Optional[list[str]] = None

    # --- Limites da §4.1 da Spec 04A, cada um com a sua mensagem -----------
    @field_validator("markup_padrao_bp")
    @classmethod
    def _markup(cls, v):
        return _entre(v, 0, 100_000, "O markup deve ficar entre 0% e 1000%.")

    @field_validator("perda_padrao_bp")
    @classmethod
    def _perda(cls, v):
        return _entre(v, 0, 5_000, "A perda deve ficar entre 0% e 50%.")

    @field_validator("custo_hora_centavos")
    @classmethod
    def _custo_hora(cls, v):
        return _entre(v, 0, None, "O custo por hora não pode ser negativo.")

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

    @field_validator("etapas_producao")
    @classmethod
    def _etapas(cls, v):
        return _lista_de_nomes(v, 20, 60, "Etapas de produção")

    @field_validator("checklist_vistoria")
    @classmethod
    def _checklist(cls, v):
        return _lista_de_nomes(v, 30, 120, "Checklist de vistoria")


class ConfiguracaoMarcenariaPublica(BaseModel):
    """O que QUALQUER usuario logado ve: nada de custo (D9)."""
    model_config = ConfigDict(from_attributes=True)

    validade_dias: int
    prazo_entrega_dias: int
    etapas_producao: list[str]
    checklist_vistoria: list[str]
    # Diz a tela se os campos de custo foram omitidos de proposito, para ela
    # nao confundir "sem permissao" com "zerado".
    inclui_custos: bool = False


class ConfiguracaoMarcenariaCompleta(ConfiguracaoMarcenariaPublica):
    """Com custo e margem: so para quem tem view_custos_marcenaria (D9)."""
    markup_padrao_bp: int
    perda_padrao_bp: int
    custo_hora_centavos: int
    rt_padrao_bp: int
    rt_modo: RtModo
    inclui_custos: bool = True
