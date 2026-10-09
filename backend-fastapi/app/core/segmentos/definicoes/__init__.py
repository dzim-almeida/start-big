# ---------------------------------------------------------------------------
# ARQUIVO: app/core/segmentos/definicoes/__init__.py
# DESCRICAO: Reune as definicoes declaradas e responde consultas sobre elas.
#
#            ACRESCENTAR UM SEGMENTO = criar o arquivo ao lado e somar duas
#            linhas aqui (o import e a entrada na tupla). Nada mais no projeto
#            precisa saber que ele existe.
# ---------------------------------------------------------------------------

from typing import Any, Dict, Optional

from .assistencia import ASSISTENCIA, SEGMENTO_ASSISTENCIA
from .marcenaria import MARCENARIA, SEGMENTO_MARCENARIA
from .oficina import OFICINA, PLACA_REGEX, SEGMENTO_OFICINA
from .pdv import PDV, SEGMENTO_PDV
from .serigrafia import SEGMENTO_SERIGRAFIA, SERIGRAFIA

# Cada definicao carrega o proprio identificador na chave "segmento", entao o
# mapa se monta sozinho -- nao ha uma segunda lista de nomes para esquecer de
# atualizar.
DEFINICOES: Dict[str, Dict[str, Any]] = {
    d["segmento"]: d
    for d in (OFICINA, ASSISTENCIA, SERIGRAFIA, PDV, MARCENARIA)
}


def get_definicao_segmento(segmento: Optional[str]) -> Optional[Dict[str, Any]]:
    """Retorna a definicao de campos de um segmento, ou None se nao houver
    definicao especifica (segmentos genericos usam apenas dados_adicionais livre)."""
    if not segmento:
        return None
    return DEFINICOES.get(segmento)


def segmento_tem_definicao(segmento: Optional[str]) -> bool:
    """True se o segmento possui uma definicao dedicada de campos."""
    return get_definicao_segmento(segmento) is not None


def segmento_usa_ordem_servico(segmento: Optional[str]) -> bool:
    """True se a loja deste segmento trabalha com Ordem de Servico.

    O PADRAO E TER OS, e isso e a coisa mais importante desta funcao. Quem
    responde False e SO quem declara `usa_ordem_servico: False` -- hoje, apenas
    o PDV.

    Fosse ao contrario -- "so tem OS quem declarar que tem" -- ligar esta regra
    apagaria o modulo de Ordem de Servico de toda loja cujo segmento nao tivesse
    arquivo de definicao (marcenaria, eletricista, outros, e qualquer empresa
    cadastrada sem segmento). O sintoma chegaria como "sumiu o menu de
    Servicos", numa loja que estava trabalhando normalmente.

    Segmento nulo tambem responde True: empresa sem segmento definido e uma
    instalacao antiga, e antiga sempre teve OS.
    """
    definicao = get_definicao_segmento(segmento)
    if not definicao:
        return True
    return definicao.get("usa_ordem_servico", True)


def get_identificador_segmento(segmento: Optional[str]) -> Optional[Dict[str, Any]]:
    """Descricao do identificador principal do segmento (nome/label/regex), se houver."""
    definicao = get_definicao_segmento(segmento)
    return definicao.get("identificador") if definicao else None


def identificador_e_gerado(segmento: Optional[str]) -> bool:
    """True se o SISTEMA cria o identificador, em vez de pedir ao usuario.

    Placa e numero de serie existem no mundo -- estao escritos no bem, e o
    atendente so copia. Codigo de arte nao existe ate alguem inventar, e campo
    obrigatorio que o usuario nao tem como preencher vira lixo ("1", "teste").
    """
    return bool((get_identificador_segmento(segmento) or {}).get("gerado"))


def gerar_identificador(segmento: Optional[str], numero_os: str) -> Optional[str]:
    """Identificador derivado do numero da OS. Ex: ART-2026-000001.

    Nasce do numero da OS de proposito: ele ja e sequencial e unico, entao nao
    ha contador novo para manter nem corrida entre terminais para tratar.

    O "OS-" do numero e removido antes de compor: o numero real e
    "OS-2026-000001", e concatenar direto produzia "ART-OS-2026-000001" -- dois
    prefixos empilhados, feio de ler e pior ainda de escrever no quadro da tela,
    que e justamente para o que este codigo serve.
    """
    identificador = get_identificador_segmento(segmento) or {}
    if not identificador.get("gerado"):
        return None

    prefixo = identificador.get("prefixo") or "ID"
    numero = (numero_os or "").strip()
    if numero.upper().startswith("OS-"):
        numero = numero[3:]
    return f"{prefixo}-{numero}"


def segmento_declara_coluna(segmento: Optional[str], coluna: str) -> bool:
    """True se algum campo declarado do segmento grava na coluna real `coluna`
    de objetos_servico (origem='coluna'), em qualquer forma de declarar
    (veiculo/checkin ou tipos de trabalho).

    Nasceu para a coluna `marca`: ela e NOT NULL herdada do desenho de
    veiculo/equipamento, e o servico a preenche com o nome do cliente quando o
    segmento gera o proprio identificador. Na serigrafia isso e certo -- a
    "Empresa / Marca da estampa" no caso comum E o cliente, e o campo existe
    no formulario. Na marcenaria nenhum campo grava em `marca`, e o
    preenchimento fazia a via impressa dizer "Marca: Dona Marta" num closet.
    Quem nao declara a coluna nao tem o que mostrar nela.
    """
    definicao = get_definicao_segmento(segmento)
    if not definicao:
        return False
    campos = []
    for chave in ("veiculo", "checkin"):
        campos += [c for c in definicao.get(chave, []) if isinstance(c, dict)]
    for tipo in definicao.get("tipos", []):
        campos += tipo.get("campos", [])
    return any(
        c.get("origem") == "coluna" and (c.get("coluna") or c.get("nome")) == coluna
        for c in campos
    )


def rotulo_status(
    segmento: Optional[str],      # segmento da empresa (ex.: "marcenaria"), ou None
    status: str,                  # valor do enum, ex.: "AGUARDANDO_RETIRADA"
    curto: bool = False,          # True = versao abreviada (dashboard)
) -> Optional[str]:
    """Texto que o SEGMENTO declarou para um status da OS.

    Devolve None quando o segmento nao renomeia aquele status: quem chama usa
    o texto padrao que ja tem. Nunca inventa um texto padrao aqui (Spec 01A, D6).
    """
    definicao = get_definicao_segmento(segmento)      # dicionario do segmento, ou None
    if not definicao:                                  # empresa sem segmento ou segmento generico
        return None                                    # -> quem chamou usa o padrao
    rotulos = definicao.get("rotulos_status") or {}    # chave opcional: ausente vira {}
    rotulo = rotulos.get(status)                       # so existe para os status renomeados
    if not rotulo:                                     # status que o segmento nao renomeou
        return None                                    # -> quem chamou usa o padrao
    return rotulo["curto"] if curto else rotulo["rotulo"]  # escolhe o tamanho pedido


def tipo_permite_criacao_manual(segmento: Optional[str], tipo_id: Optional[str]) -> bool:
    """Uma OS deste segmento/tipo pode ser criada pelo caminho comum? (Spec 03A, D5)

    - Tipo conhecido: vale a marcacao dele (padrao True).
    - Tipo ausente ou desconhecido: so e recusado se o segmento declara tipos e
      NENHUM deles e criavel a mao (senao omitir o tipo furaria a trava).
    - Segmento sem definicao ou sem tipos: sempre True (nada muda).
    """
    definicao = get_definicao_segmento(segmento)               # None para segmento generico
    tipos = (definicao or {}).get("tipos") or []               # [] para oficina/informatica
    if not tipos:                                              # sem tipos: comportamento de hoje
        return True
    for tipo in tipos:                                         # tipo informado e conhecido?
        if tipo["id"] == tipo_id:
            return tipo.get("criacao_manual", True)            # vale a marcacao do tipo
    # Tipo ausente/desconhecido: permitido se existir ALGUM tipo criavel a mao.
    return any(t.get("criacao_manual", True) for t in tipos)


def label_do_tipo(segmento: Optional[str], tipo_id: Optional[str]) -> str:
    """Nome do tipo para mensagens; sem tipo informado, o primeiro do segmento."""
    tipos = (get_definicao_segmento(segmento) or {}).get("tipos") or []  # [] sem tipos
    for tipo in tipos:                                         # procura o tipo informado
        if tipo["id"] == tipo_id:
            return tipo["label"]
    # Tipo omitido ou desconhecido: o primeiro tipo do segmento; sem tipos, o id cru.
    return tipos[0]["label"] if tipos else (tipo_id or "")


__all__ = [
    "DEFINICOES",
    "OFICINA",
    "ASSISTENCIA",
    "SERIGRAFIA",
    "PLACA_REGEX",
    "SEGMENTO_OFICINA",
    "SEGMENTO_ASSISTENCIA",
    "SEGMENTO_SERIGRAFIA",
    "SEGMENTO_PDV",
    "PDV",
    "get_definicao_segmento",
    "segmento_tem_definicao",
    "segmento_usa_ordem_servico",
    "get_identificador_segmento",
    "identificador_e_gerado",
    "gerar_identificador",
    "segmento_declara_coluna",
    "rotulo_status",
    "tipo_permite_criacao_manual",
    "label_do_tipo",
]
