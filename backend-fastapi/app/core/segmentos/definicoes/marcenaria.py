# ---------------------------------------------------------------------------
# ARQUIVO: app/core/segmentos/definicoes/marcenaria.py
# DESCRICAO: Definicao do segmento MARCENARIA (dado, nao motor).
#
# Specs e decisoes: backend-fastapi/docs/marcenaria/ (SPEC-00 e Spec 03A).
#
# FASE 1 = SO MOVEIS PLANEJADOS. A loja fabrica o movel para um ambiente do
# cliente e instala na obra. O fluxo nasce no ORCAMENTO TECNICO (moveis,
# insumos, mao de obra, instalacao): a OS so existe depois que o cliente
# aprova o orcamento (Spec 08A). Por isso o tipo declara `criacao_manual=False`
# e o servico da OS recusa a criacao pelo caminho comum (Spec 03A).
#
# Ambiente, modulos, material, acabamento, ferragens, montagem e etapa NAO
# estao aqui: vivem no orcamento e na producao por movel. Este arquivo guarda
# so o que e do PROJETO (o nome e o endereco da obra), que o cliente
# reutiliza quando volta.
#
# A Reforma de moveis saiu da fase 1. A referencia para a volta dela esta na
# SPEC-00, secao 7.1.
#
# Status. Desde a Spec 01A o segmento pode RENOMEAR o texto de um status sem
# mudar o status gravado: veja `rotulos_status` abaixo ("Aguardando Pecas"
# aparece como "Aguardando Material"). Os outros segmentos nao declaram a
# chave e continuam com os textos de sempre.
# ---------------------------------------------------------------------------

from typing import Any, Dict, List

from ..campos import campo, tipo_de_trabalho
from ..capacidades import (
    CAP_GARANTIA_PRAZO,
    CAP_IMAGEM_NA_ENTRADA,
    CAP_ORCAMENTO_TECNICO,
)

SEGMENTO_MARCENARIA = "marcenaria"

GRUPO_PROJETO = "Dados do Projeto"


def _campos_do_projeto() -> List[Dict[str, Any]]:
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

    Sobra um campo obrigatorio: o nome, que o atendente sabe. Ele grava na
    coluna `modelo` do objeto, como "nome_arte" grava em `modelo` na serigrafia.
    """
    return [
        campo("nome_projeto", "Nome do projeto", "texto", obrigatorio=True,
              escopo="objeto", grupo=GRUPO_PROJETO, origem="coluna", coluna="modelo",
              largura="inteira"),
    ]


# Unico tipo da fase 1 (SPEC-00, E0). A OS nasce da aprovacao de um orcamento
# (Spec 03A): ambiente, modulos, materiais, montagem e etapa vivem no orcamento
# e na producao por movel. Aqui ficam so os dados do PROJETO, que o cliente
# reutiliza quando volta.
_PLANEJADOS = tipo_de_trabalho(
    "planejados",
    "Móveis planejados",
    [
        *_campos_do_projeto(),  # ex: "Cozinha apto 302"
        # Onde o movel vai ser INSTALADO -- nao e o endereco do cliente. Quem
        # compra para o apartamento novo mora no antigo; quem e revendedor manda
        # para o cliente final. Texto livre nesta versao.
        campo("endereco_obra", "Endereço da obra", "texto",
              escopo="objeto", grupo=GRUPO_PROJETO, largura="inteira"),
    ],
    criacao_manual=False,  # so pela aprovacao do orcamento (Spec 08A)
)


MARCENARIA = {
    "segmento": SEGMENTO_MARCENARIA,
    "rotulo_objeto_singular": "Projeto",
    "rotulo_objeto_plural": "Projetos",

    # `defeito_relatado` e o "o que ele pediu", em texto livre, e sai impresso
    # na via. Em Planejados e a encomenda; o placeholder mostra o caso comum.
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
    # A aba dinamica montava '<objeto> ja cadastrada' (escrito para "Arte"):
    # com "Projeto" saia "Projeto ja cadastrada". Declarado inteiro, como o
    # titulo da situacao.
    "rotulo_objeto_anterior": "Projeto já cadastrado",
    "rotulos_situacao": {
        "REPARADO": "Entregue",
        "SEM_REPARO": "Não produzido",
        "CONDENADO": "Perda na produção",
    },

    # Rotulos de STATUS da OS (nao confundir com rotulos_situacao, que e o
    # desfecho). O status gravado continua o mesmo enum de todos os segmentos;
    # so o texto mostrado muda. Spec 01A, decisoes D1-D8.
    # "rotulo" = texto completo (telas e impressao, cada palavra com maiuscula);
    # "curto" = texto do widget do dashboard (so a primeira com maiuscula).
    "rotulos_status": {
        # Quando a OS sai de "aberta", o movel esta sendo fabricado.
        "EM_ANDAMENTO": {"rotulo": "Em Produção", "curto": "Em produção"},
        # Na marcenaria, o que se espera e chapa, fita e ferragem.
        "AGUARDANDO_PECAS": {"rotulo": "Aguardando Material", "curto": "Aguard. material"},
        # Pronto: em Planejados vai ser instalado; em Reforma, o cliente retira.
        # "Entrega" serve aos dois tipos (ver secao 8 da Spec 01A).
        "AGUARDANDO_RETIRADA": {"rotulo": "Aguardando Entrega", "curto": "Aguard. entrega"},
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

    # imagem_na_entrada: em Planejados a foto e o PEDIDO (o ambiente, o
    #   projeto) -- e ir para a via de entrada e bom, o cliente assina vendo a
    #   foto.
    # garantia_prazo: marcenaria da garantia (90 dias e comum; planejados as
    #   vezes 1 ano). Desligada, a via de saida sairia sem Termo de Garantia.
    #
    # Sem aprovacao_itens (Spec 03A, D10): os moveis sao aprovados no
    # ORCAMENTO, antes de a OS existir. A capacidade so ficava por causa da
    # Reforma, que saiu da fase 1.
    # orcamento_tecnico: o orcamento por ambiente, movel e insumo, com perda,
    #   markup e margem (Spec 04A). Liga os parametros da marcenaria e a flag
    #   "sofre perda" no produto.
    # Sem vistoria e sem revisoes: a medicao do ambiente nao e checklist nesta
    # versao, e movel nao volta para manutencao por data.
    "capacidades": [
        CAP_IMAGEM_NA_ENTRADA,
        CAP_GARANTIA_PRAZO,
        CAP_ORCAMENTO_TECNICO,
    ],

    # Vazios porque este segmento declara por tipo de trabalho. O guard
    # (test/core/test_registry_segmentos.py) proibe usar os dois caminhos.
    "veiculo": [],
    "checkin": [],
    "acessorios": [],
    "vistoria": [],

    "tipos": [_PLANEJADOS],
}
