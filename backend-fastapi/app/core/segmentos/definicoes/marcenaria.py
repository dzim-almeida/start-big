# ---------------------------------------------------------------------------
# ARQUIVO: app/core/segmentos/definicoes/marcenaria.py
# DESCRICAO: Definicao do segmento MARCENARIA (dado, nao motor).
#
# ESTADO: RASCUNHO DA FASE 0 (docs/segmento-marcenaria-plano.md). Este arquivo
# NAO esta somado ao __init__.py de proposito: primeiro os dois donos leem os
# campos com as palavras deles, depois liga. Ate la, uma loja cadastrada como
# marcenaria continua caindo na OS generica, exatamente como hoje.
#
# O NEGOCIO, em duas metades que compartilham o mesmo fluxo:
#
#   Planejados -- a loja FABRICA o movel para um ambiente do cliente e MONTA na
#   casa dele. O dono da fabrica descreveu o fluxo em 16/09/2026, e ele e a
#   espinha deste arquivo:
#
#     cliente liga ou vem -> solicita orcamento -> orcamento aprovado (com %
#     adiantado) -> compra o material -> producao: separacao -> corte ->
#     montagem interna -> montagem externa (na casa do cliente)
#
#   Reforma de moveis -- o cliente TRAZ o movel (ou a loja busca) e a loja
#   restaura, pinta, troca peca. Aqui "defeito relatado" faz sentido de
#   verdade: e conserto, como na oficina.
#
#   A marcenaria de bairro faz as duas coisas; a fabrica faz mais a primeira.
#   Sao dois tipos de trabalho no mesmo segmento (o modelo camisa/sacola da
#   serigrafia), nunca duas lojas com dois `if`.
#
# O QUE ESTE ARQUIVO NAO FAZ, DE PROPOSITO:
#
#   Preco. Nao ha motor de m2, de chapa nem de plano de corte. A loja cadastra
#   "Cozinha planejada -- metro linear" ou "Restauracao de cadeira" em Servicos
#   e o sistema multiplica, como faz na serigrafia. Sistemas que orcam por
#   chapa (Promob, Calcme) sao de projeto, nao de balcao.
#
#   Producao. A ETAPA aqui e informacao para o dono ("em que pe esta o movel
#   do fulano?"), nao workflow: nao avanca sozinha, nao conta no dashboard, nao
#   filtra a lista. Decisao do dono em 16/09. Se um dia pedir "me mostra tudo
#   que esta em Corte", vira capacidade -- depois de medir a demanda.
#
#   Status. "Aguardando Pecas" continua com esse nome quando a loja esta
#   comprando MDF: rotulo de status nao varia por segmento, e criar isso mexe
#   em codigo dos tres segmentos em producao. A Etapa carrega a palavra certa
#   ("Aguardando material").
# ---------------------------------------------------------------------------

from typing import Any, Dict, List

from ..campos import campo, tipo_de_trabalho
from ..capacidades import (
    CAP_APROVACAO_ITENS,
    CAP_GARANTIA_PRAZO,
    CAP_IMAGEM_NA_ENTRADA,
)

SEGMENTO_MARCENARIA = "marcenaria"

GRUPO_PROJETO = "Dados do Projeto"
GRUPO_ESPECIFICACAO = "Especificação"
GRUPO_PRODUCAO = "Produção"

# As etapas sao as PALAVRAS DO DONO, na ordem em que ele falou. Nao renomear
# depois que uma OS gravou o valor: opcao renomeada deixa a OS antiga com um
# valor fora da lista (a serigrafia mantem "Mileiro" e "Vazada" no fim da lista
# de sacolas por esse motivo). Acertar aqui, na Fase 0, com os dois donos.
ETAPAS_PLANEJADOS = [
    "Aguardando aprovação",
    "Aguardando material",
    "Separação",
    "Corte",
    "Montagem interna",
    "Montagem externa",
    "Concluído",
]

# Reforma nao tem montagem externa: o movel volta para o cliente pronto.
ETAPAS_REFORMA = [e for e in ETAPAS_PLANEJADOS if e != "Montagem externa"]

# Enum, e nao texto livre: "cozinha", "Cozinha", "COZ" sao tres ambientes
# para o banco e um so para o dono. Lista a confirmar com a fabrica (§7.3 do
# plano). "Outro" existe para o que nao couber, sem forcar o atendente a
# escolher errado.
AMBIENTES = [
    "Cozinha",
    "Dormitório",
    "Closet",
    "Banheiro",
    "Sala",
    "Escritório",
    "Área de serviço",
    "Outro",
]


def _campos_do_projeto(label_nome: str) -> List[Dict[str, Any]]:
    """O projeto e o que se repete quando o cliente volta.

    Ocupa o lugar do objeto de servico -- o mesmo mecanismo que liga veiculo ao
    dono, equipamento ao cliente e arte ao pedido. "Cozinha do apto 302" e o
    que o cliente diz ao telefone seis meses depois pedindo mais um modulo.

    REPARE NO QUE **NAO** ESTA AQUI: o codigo do projeto.

    Mesma licao do "Codigo da arte" da serigrafia: codigo de projeto nao existe
    ate alguem inventar, e campo obrigatorio que o atendente nao tem como
    preencher vira lixo. Ele e GERADO do numero da OS (ver `identificador`) e
    sai impresso -- e util para etiquetar as pecas cortadas na fabrica, que e
    o mesmo papel da etiqueta na tela de serigrafia guardada na prateleira.

    Sobra um campo obrigatorio: o nome, que o atendente sabe. O rotulo muda
    por tipo ("Nome do projeto" em Planejados, "Movel" em Reforma) mas a coluna
    e a mesma (`modelo`), como "nome_arte" grava em `modelo` na serigrafia.
    """
    return [
        campo("nome_projeto", label_nome, "texto", obrigatorio=True,
              escopo="objeto", grupo=GRUPO_PROJETO, origem="coluna", coluna="modelo",
              largura="inteira"),
    ]


_PLANEJADOS = tipo_de_trabalho("planejados", "Móveis planejados", [
    *_campos_do_projeto("Nome do projeto"),  # ex: "Cozinha apto 302"

    # Onde o movel vai ser MONTADO -- nao e o endereco do cliente. Quem compra
    # para o apartamento novo mora no antigo; quem e revendedor manda para o
    # cliente final. Texto livre nesta versao; estruturar (CEP, rota para o
    # montador) e Fase 5.4, so se alguma loja pedir.
    campo("endereco_obra", "Endereço da obra", "texto",
          escopo="objeto", grupo=GRUPO_PROJETO, largura="inteira"),

    campo("ambiente", "Ambiente", "opcao", opcoes=AMBIENTES,
          escopo="os", grupo=GRUPO_ESPECIFICACAO),
    # Um por linha, com a medida ESCRITA ("Aereo 180x70x35"). E `lista` de
    # texto, nao numero: o sistema nao calcula nada com isso nesta versao --
    # serve para abrir a OS, para o corte ler e para a via impressa. Medida
    # estruturada (LxAxP por modulo) e Fase 5.3, se a fabrica quiser orcar por
    # m2 dentro do sistema.
    campo("modulos", "Módulos (um por linha, com medida)", "lista",
          escopo="os", grupo=GRUPO_ESPECIFICACAO, largura="inteira"),
    # Texto livre de proposito, como a cor na serigrafia: "MDF 15mm branco TX",
    # "MDF 18mm carvalho + fundo 6mm". Enum aqui viraria campo que o atendente
    # contorna escrevendo no lugar errado.
    campo("material", "Material / chapa", "texto",
          escopo="os", grupo=GRUPO_ESPECIFICACAO),
    campo("acabamento", "Acabamento / cor", "texto",
          escopo="os", grupo=GRUPO_ESPECIFICACAO),
    campo("ferragens", "Ferragens e puxadores", "texto",
          escopo="os", grupo=GRUPO_ESPECIFICACAO, largura="inteira"),

    # Algumas lojas incluem a montagem no preco, outras cobram a parte. O campo
    # nao muda preco (isso e item do catalogo); ele diz a via impressa e ao
    # montador se a montagem externa faz parte deste pedido.
    campo("montagem_incluida", "Montagem incluída", "booleano",
          escopo="os", grupo=GRUPO_PRODUCAO),
    campo("etapa", "Etapa atual", "opcao", opcoes=ETAPAS_PLANEJADOS,
          escopo="os", grupo=GRUPO_PRODUCAO),
])


_REFORMA = tipo_de_trabalho("reforma_moveis", "Reforma de móveis", [
    *_campos_do_projeto("Móvel"),  # ex: "Guarda-roupa 3 portas"

    campo("servico_reforma", "O que fazer", "opcao",
          opcoes=["Restauração", "Troca de peça", "Pintura / verniz", "Ajuste", "Outro"],
          escopo="os", grupo=GRUPO_ESPECIFICACAO),
    campo("material", "Material", "texto",
          escopo="os", grupo=GRUPO_ESPECIFICACAO),
    campo("acabamento", "Acabamento / cor", "texto",
          escopo="os", grupo=GRUPO_ESPECIFICACAO),
    # Trazido pelo cliente e o padrao no bairro; desmarcado significa que a
    # loja vai buscar -- e a via de entrada precisa dizer isso, porque e
    # quando o movel entra sob responsabilidade da loja.
    campo("movel_trazido", "Móvel trazido pelo cliente", "booleano",
          escopo="os", grupo=GRUPO_PRODUCAO),
    campo("etapa", "Etapa atual", "opcao", opcoes=ETAPAS_REFORMA,
          escopo="os", grupo=GRUPO_PRODUCAO),
])


MARCENARIA = {
    "segmento": SEGMENTO_MARCENARIA,
    "rotulo_objeto_singular": "Projeto",
    "rotulo_objeto_plural": "Projetos",

    # `defeito_relatado` e o "o que ele pediu", em texto livre, e sai impresso
    # na via -- em Planejados e encomenda, em Reforma e conserto. O rotulo
    # neutro serve aos dois; o placeholder mostra o caso mais comum.
    "rotulo_defeito": "Descrição do pedido",
    "rotulo_responsavel": "Responsável",
    "placeholder_defeito": "Ex: cozinha planejada, MDF branco, 4 módulos + bancada",

    # O desfecho e o MESMO enum de sempre (REPARADO/SEM_REPARO/CONDENADO); so
    # os rotulos mudam. SEM_REPARO e CONDENADO dispensam o pagamento integral
    # (services/ordem_servico.py) -- numa marcenaria e o cliente que desiste
    # depois do adiantamento, ou a peca que se perde na producao.
    #
    # "Projeto" e masculino, entao 'Situacao do ' + rotulo daria certo; o
    # titulo inteiro e declarado mesmo assim para nao depender da concatenacao.
    "rotulo_situacao": "Situação do Projeto",
    "rotulos_situacao": {
        "REPARADO": "Entregue",
        "SEM_REPARO": "Não produzido",
        "CONDENADO": "Perda na produção",
    },

    # Gerado do numero da OS ("PRJ-2026-000042"), nunca pedido ao atendente.
    # Vale impresso: e o que vai na etiqueta das pecas cortadas para a montagem
    # saber de que pedido e cada peca.
    "identificador": {
        "nome": "codigo_projeto",
        "label": "Código do projeto",
        "regex": None,
        "gerado": True,
        "prefixo": "PRJ",
    },

    # aprovacao_itens: o orcamento e aprovado item a item ("aprovou a cozinha,
    #   deixou o closet para depois"). Mecanismo da oficina, sem mudanca.
    # imagem_na_entrada: em Planejados a foto e o PEDIDO (o ambiente, o
    #   projeto); em Reforma e o estado do movel -- e ir para a via de entrada
    #   e bom, o cliente assina vendo a foto. Capacidade e por segmento, nao
    #   por tipo, entao liga para os dois (§7.5 do plano).
    # garantia_prazo: marcenaria da garantia (90 dias e comum; planejados as
    #   vezes 1 ano). Desligada, a via de saida sairia sem Termo de Garantia
    #   (§7.2 do plano -- recomendacao: ligar).
    #
    # Sem vistoria nesta versao: a medicao do ambiente (vaos, pe-direito,
    # prumo, pontos de agua/luz/gas) e o "vistoria" da fabrica e o mecanismo
    # ja existe na oficina -- falta so o checklist declarado. E Fase 5.6, se a
    # fabrica pedir. Sem revisoes: movel nao volta para manutencao por data.
    "capacidades": [
        CAP_APROVACAO_ITENS,
        CAP_IMAGEM_NA_ENTRADA,
        CAP_GARANTIA_PRAZO,
    ],

    # Vazios porque este segmento declara por tipo de trabalho. O guard
    # (test/core/test_registry_segmentos.py) proibe usar os dois caminhos.
    "veiculo": [],
    "checkin": [],
    "acessorios": [],
    "vistoria": [],

    "tipos": [_PLANEJADOS, _REFORMA],
}
