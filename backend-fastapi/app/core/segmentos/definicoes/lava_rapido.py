# ---------------------------------------------------------------------------
# ARQUIVO: app/core/segmentos/definicoes/lava_rapido.py
# DESCRICAO: Definicao do segmento LAVA-RAPIDO / ESTETICA AUTOMOTIVA (dado,
#            nao motor). docs/lava-rapido/SPEC-00 e Spec 01A.
#
# O NEGOCIO: o veiculo entra, e lavado e sai no mesmo dia -- muitas vezes em
# menos de uma hora. Nao ha conserto, peca, laudo nem garantia em dias. O que
# muda o preco e o PORTE do veiculo (hatch, SUV, caminhao de 3 eixos), e o que
# mais da dor de cabeca e a reclamacao de avaria ("esse risco nao estava
# aqui") -- por isso a vistoria com foto na entrada.
#
# "Qualquer transporte" (resposta do primeiro cliente, 12/11/2026): carro,
# moto, caminhao, onibus e tambem o que nao tem placa (barco, jet ski,
# maquina agricola). Por isso quatro tipos de trabalho, e por isso o
# identificador e "placa quando houver, gerado quando nao" (gerado_se_vazio).
# ---------------------------------------------------------------------------

from typing import Any, Dict, List

from ..campos import campo, grupo_vistoria, tipo_de_trabalho
from ..capacidades import CAP_IMAGEM_NA_ENTRADA, CAP_VISTORIA

SEGMENTO_LAVA_RAPIDO = "lava_rapido"

# Cabecalhos das secoes do formulario. Constantes para nao divergirem por erro
# de digitacao -- o renderizador agrupa por igualdade de string.
GRUPO_VEICULO = "Dados do Veículo"
GRUPO_ENTRADA = "Entrada"

# Portes iniciais de cada tipo (SPEC-00 P2a). Sao a lista que a loja recebe
# no primeiro uso; a Spec 02A passa a lista para uma tabela que o dono edita.
# Ate la, o campo `porte` usa exatamente estes textos como opcoes.
PORTES_CARRO = ["Hatch", "Sedã", "SUV", "Picape", "Van / utilitário"]
PORTES_MOTO = ["Até 300 cc", "Acima de 300 cc"]
PORTES_PESADO = [
    "Caminhão 2 eixos", "Caminhão 3 eixos", "Caminhão 4 eixos",
    "Caminhão 5 eixos ou mais", "Ônibus / micro-ônibus",
]
PORTES_OUTROS = ["Pequeno", "Médio", "Grande"]

# O caminhao e lavado com a carroceria, e ela muda o trabalho (um bau por
# dentro, um tanque por fora). "Outra" fecha a lista sem obrigar o atendente a
# escolher algo errado.
CARROCERIAS = ["Baú", "Sider", "Graneleiro", "Tanque", "Cegonha", "Basculante", "Outra"]


def _campos_do_veiculo(portes: List[str], placa_obrigatoria: bool = True,
                       rotulo_modelo: str = "Modelo") -> List[Dict[str, Any]]:
    """Campos que todo veiculo tem, seja qual for o tipo.

    ATENCAO a `origem`: placa, marca, modelo e cor sao COLUNAS reais de
    objetos_servico (a placa e a coluna `numero_serie`). O porte vive no JSON,
    e e do VEICULO (escopo objeto), nao da OS: o carro nao muda de porte entre
    uma lavagem e outra, entao na segunda visita ele ja vem preenchido (P3).

    `placa_obrigatoria=False` so no tipo "Outros": barco e jet ski nao tem
    placa, e o sistema gera o codigo (identificador.gerado_se_vazio). Nos
    outros tipos a placa e pedida pelo formulario; o backend aceita vazia nos
    quatro (Spec 01A, D6).
    """
    return [
        campo("placa", "Placa", "texto", obrigatorio=placa_obrigatoria,
              escopo="objeto", grupo=GRUPO_VEICULO, origem="coluna",
              coluna="numero_serie"),
        campo("marca", "Marca", "texto", obrigatorio=True, escopo="objeto",
              grupo=GRUPO_VEICULO, origem="coluna"),
        campo("modelo", rotulo_modelo, "texto", obrigatorio=True, escopo="objeto",
              grupo=GRUPO_VEICULO, origem="coluna"),
        campo("cor", "Cor", "texto", escopo="objeto", grupo=GRUPO_VEICULO,
              origem="coluna"),
        campo("porte", "Porte", "opcao", obrigatorio=True, opcoes=list(portes),
              escopo="objeto", grupo=GRUPO_VEICULO),
    ]


def _campos_da_entrada() -> List[Dict[str, Any]]:
    """O que fica registrado na OS no momento em que o veiculo entra.

    Pertences: o celular esquecido no console e a outra reclamacao classica do
    ramo, ao lado do risco. Anotar na entrada protege a loja e o cliente.
    """
    return [
        campo("pertences", "Pertences deixados no veículo", "texto", escopo="os",
              grupo=GRUPO_ENTRADA, largura="inteira",
              placeholder="Ex: óculos no porta-luvas, cadeirinha no banco de trás"),
    ]


_CARRO = tipo_de_trabalho("carro", "Carro", [
    *_campos_do_veiculo(PORTES_CARRO),
    *_campos_da_entrada(),
])

_MOTO = tipo_de_trabalho("moto", "Moto", [
    *_campos_do_veiculo(PORTES_MOTO),
    *_campos_da_entrada(),
])

_PESADO = tipo_de_trabalho("pesado", "Caminhão / ônibus", [
    *_campos_do_veiculo(PORTES_PESADO),
    campo("carroceria", "Carroceria", "opcao", opcoes=list(CARROCERIAS),
          escopo="objeto", grupo=GRUPO_VEICULO),
    # A carreta tem placa propria; anotar evita confundir dois implementos do
    # mesmo cavalo mecanico na proxima visita.
    campo("placa_implemento", "Placa do implemento", "texto",
          escopo="objeto", grupo=GRUPO_VEICULO),
    *_campos_da_entrada(),
])

# "Modelo" vira "Descricao" porque e o que identifica um barco ou um jet ski
# para quem esta no balcao ("Lancha 21 pes", "Jet ski VX").
_OUTROS = tipo_de_trabalho("outros", "Outros (sem placa)", [
    *_campos_do_veiculo(PORTES_OUTROS, placa_obrigatoria=False,
                        rotulo_modelo="Descrição"),
    *_campos_da_entrada(),
])


LAVA_RAPIDO = {
    "segmento": SEGMENTO_LAVA_RAPIDO,
    "rotulo_objeto_singular": "Veículo",
    "rotulo_objeto_plural": "Veículos",

    # `defeito_relatado` aqui e o PEDIDO do cliente, como na serigrafia: nao
    # ha defeito, ha um servico encomendado. Sai impresso na via.
    "rotulo_defeito": "Pedido do cliente",
    "rotulo_responsavel": "Responsável",
    "placeholder_defeito": "Ex: lavagem completa, cuidado com o adesivo do capô",

    # O desfecho e o MESMO enum de sempre (REPARADO/SEM_REPARO/CONDENADO); so
    # os rotulos mudam. SEM_REPARO e CONDENADO dispensam o pagamento integral
    # -- aqui e o cliente que desiste, ou a loja que recusa o veiculo (barro
    # demais, avaria que ela nao quer assumir).
    "rotulo_situacao": "Situação do Serviço",
    "rotulos_situacao": {
        "REPARADO": "Concluído",
        "SEM_REPARO": "Não realizado",
        "CONDENADO": "Recusado",
    },

    # So "Aguardando Retirada" muda de nome: no patio, o carro lavado
    # esperando o dono esta PRONTO (SPEC-00 O2b). Aberta, Em Andamento e
    # Finalizada ficam com o texto que o sistema inteiro ja usa (Spec 01A, D10).
    "rotulos_status": {
        "AGUARDANDO_RETIRADA": {"rotulo": "Pronto", "curto": "Pronto"},
    },

    # Os status que este segmento usa (Spec 01A, D8). Nao ha peca para
    # esperar nem orcamento para aprovar; os outros dois somem da tela e o
    # backend os recusa na edicao da OS. CANCELADA continua pelo cancelamento
    # de sempre. Segmento que nao declara esta chave usa todos.
    "status_usados": [
        "ABERTA",
        "EM_ANDAMENTO",
        "AGUARDANDO_RETIRADA",
        "FINALIZADA",
        "CANCELADA",
    ],

    # A placa e a chave do veiculo, mas SEM regex (Spec 01A, D4): com o regex
    # da oficina, placa estrangeira (caminhao do Mercosul) e o codigo gerado
    # nao valeriam como chave, e cada visita criaria um veiculo novo.
    #
    # `gerado_se_vazio` (D5): diferente do `gerado` da serigrafia, o campo
    # continua no formulario. Placa digitada vale; em branco (barco, jet ski),
    # o sistema gera VEI-AAAA-NNNNNN do numero da OS.
    "identificador": {
        "nome": "placa",
        "label": "Placa",
        "regex": None,
        "gerado_se_vazio": True,
        "prefixo": "VEI",
    },

    # vistoria: as avarias do veiculo antes de lavar -- a defesa da loja
    #   contra "esse risco nao estava aqui" (SPEC-00 O5).
    # imagem_na_entrada: as fotos entram ja na abertura da OS, antes de o
    #   veiculo ir para o box, e saem na via de entrada.
    # Sem diagnostico, garantia (prazo ou item), aprovacao de itens e revisoes
    # por KM: lavagem nao e conserto (SPEC-00 O6).
    "capacidades": [CAP_VISTORIA, CAP_IMAGEM_NA_ENTRADA],

    # Vazios porque este segmento declara por tipo de trabalho. O guard
    # (test/core/test_registry_segmentos.py) proibe usar os dois caminhos.
    "veiculo": [],
    "checkin": [],
    "acessorios": [],

    # A vistoria NAO e por tipo: a avaria e do veiculo, seja carro, moto ou
    # caminhao. Os itens sao genericos de proposito (Spec 01A, secao 4.2).
    "vistoria": [
        grupo_vistoria("Inspeção externa", [
            "pintura_riscos", "amassados", "vidros_para_brisa",
            "farois_lanternas", "rodas_aros", "retrovisores",
            "para_choques_carenagem", "adesivos_envelopamento",
        ]),
        grupo_vistoria("Inspeção interna", [
            "bancos_estofados", "painel", "tapetes_assoalho",
            "manchas_odores", "objetos_de_valor",
        ]),
    ],

    "tipos": [_CARRO, _MOTO, _PESADO, _OUTROS],
}
