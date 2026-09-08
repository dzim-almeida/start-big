# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/derivacao/bases/municipios_ce.py
# DESCRIÇÃO: Códigos IBGE dos municípios do Ceará (cMun da NF-e).
#
# GERADO a partir da API oficial do IBGE:
#   https://servicodados.ibge.gov.br/api/v1/localidades/estados/CE/municipios
#
# Vigência: 2026-09-08 · 184 municípios.
#
# Embarcado de propósito: o app roda em loja, e a emissão não pode depender de
# internet para descobrir o código de um município. Mesmo padrão do
# `aliquota_uf`, que também é dado de referência semeado localmente.
#
# Só o CEARÁ. A tabela nacional tem 5.570 linhas e não há por que carregar as
# outras 5.386 enquanto a emissão é estadual. Quando outra UF entrar, gere o
# arquivo dela do mesmo jeito.
# ---------------------------------------------------------------------------
"""
Município → código IBGE, no Ceará.

Por que isto importa: o `cMun` é obrigatório no XML, e o payload não o enviava
— quem adivinhava era a integradora, pelo NOME do município. É onde ela erra
com homônimos, e o Ceará tem os seus.

As chaves são normalizadas (minúsculas, sem acento) para que "Juazeiro do
Norte", "JUAZEIRO DO NORTE" e "juazeiro do norte" cheguem ao mesmo lugar.
"""
import unicodedata
from typing import Optional

UF = "CE"
VIGENCIA = "2026-09-08"

# Chave normalizada → código IBGE de 7 dígitos.
MUNICIPIOS_CE: dict[str, str] = {
    "abaiara": "2300101",  # Abaiara
    "acarape": "2300150",  # Acarape
    "acarau": "2300200",  # Acaraú
    "acopiara": "2300309",  # Acopiara
    "aiuaba": "2300408",  # Aiuaba
    "alcantaras": "2300507",  # Alcântaras
    "altaneira": "2300606",  # Altaneira
    "alto santo": "2300705",  # Alto Santo
    "amontada": "2300754",  # Amontada
    "antonina do norte": "2300804",  # Antonina do Norte
    "apuiares": "2300903",  # Apuiarés
    "aquiraz": "2301000",  # Aquiraz
    "aracati": "2301109",  # Aracati
    "aracoiaba": "2301208",  # Aracoiaba
    "ararenda": "2301257",  # Ararendá
    "araripe": "2301307",  # Araripe
    "aratuba": "2301406",  # Aratuba
    "arneiroz": "2301505",  # Arneiroz
    "assare": "2301604",  # Assaré
    "aurora": "2301703",  # Aurora
    "baixio": "2301802",  # Baixio
    "banabuiu": "2301851",  # Banabuiú
    "barbalha": "2301901",  # Barbalha
    "barreira": "2301950",  # Barreira
    "barro": "2302008",  # Barro
    "barroquinha": "2302057",  # Barroquinha
    "baturite": "2302107",  # Baturité
    "beberibe": "2302206",  # Beberibe
    "bela cruz": "2302305",  # Bela Cruz
    "boa viagem": "2302404",  # Boa Viagem
    "brejo santo": "2302503",  # Brejo Santo
    "camocim": "2302602",  # Camocim
    "campos sales": "2302701",  # Campos Sales
    "caninde": "2302800",  # Canindé
    "capistrano": "2302909",  # Capistrano
    "caridade": "2303006",  # Caridade
    "carire": "2303105",  # Cariré
    "caririacu": "2303204",  # Caririaçu
    "carius": "2303303",  # Cariús
    "carnaubal": "2303402",  # Carnaubal
    "cascavel": "2303501",  # Cascavel
    "catarina": "2303600",  # Catarina
    "catunda": "2303659",  # Catunda
    "caucaia": "2303709",  # Caucaia
    "cedro": "2303808",  # Cedro
    "chaval": "2303907",  # Chaval
    "choro": "2303931",  # Choró
    "chorozinho": "2303956",  # Chorozinho
    "coreau": "2304004",  # Coreaú
    "crateus": "2304103",  # Crateús
    "crato": "2304202",  # Crato
    "croata": "2304236",  # Croatá
    "cruz": "2304251",  # Cruz
    "deputado irapuan pinheiro": "2304269",  # Deputado Irapuan Pinheiro
    "erere": "2304277",  # Ereré
    "eusebio": "2304285",  # Eusébio
    "farias brito": "2304301",  # Farias Brito
    "forquilha": "2304350",  # Forquilha
    "fortaleza": "2304400",  # Fortaleza
    "fortim": "2304459",  # Fortim
    "frecheirinha": "2304509",  # Frecheirinha
    "general sampaio": "2304608",  # General Sampaio
    "graca": "2304657",  # Graça
    "granja": "2304707",  # Granja
    "granjeiro": "2304806",  # Granjeiro
    "groairas": "2304905",  # Groaíras
    "guaiuba": "2304954",  # Guaiúba
    "guaraciaba do norte": "2305001",  # Guaraciaba do Norte
    "guaramiranga": "2305100",  # Guaramiranga
    "hidrolandia": "2305209",  # Hidrolândia
    "horizonte": "2305233",  # Horizonte
    "ibaretama": "2305266",  # Ibaretama
    "ibiapina": "2305308",  # Ibiapina
    "ibicuitinga": "2305332",  # Ibicuitinga
    "icapui": "2305357",  # Icapuí
    "ico": "2305407",  # Icó
    "iguatu": "2305506",  # Iguatu
    "independencia": "2305605",  # Independência
    "ipaporanga": "2305654",  # Ipaporanga
    "ipaumirim": "2305704",  # Ipaumirim
    "ipu": "2305803",  # Ipu
    "ipueiras": "2305902",  # Ipueiras
    "iracema": "2306009",  # Iracema
    "iraucuba": "2306108",  # Irauçuba
    "itaicaba": "2306207",  # Itaiçaba
    "itaitinga": "2306256",  # Itaitinga
    "itapaje": "2306306",  # Itapajé
    "itapipoca": "2306405",  # Itapipoca
    "itapiuna": "2306504",  # Itapiúna
    "itarema": "2306553",  # Itarema
    "itatira": "2306603",  # Itatira
    "jaguaretama": "2306702",  # Jaguaretama
    "jaguaribara": "2306801",  # Jaguaribara
    "jaguaribe": "2306900",  # Jaguaribe
    "jaguaruana": "2307007",  # Jaguaruana
    "jardim": "2307106",  # Jardim
    "jati": "2307205",  # Jati
    "jijoca de jericoacoara": "2307254",  # Jijoca de Jericoacoara
    "juazeiro do norte": "2307304",  # Juazeiro do Norte
    "jucas": "2307403",  # Jucás
    "lavras da mangabeira": "2307502",  # Lavras da Mangabeira
    "limoeiro do norte": "2307601",  # Limoeiro do Norte
    "madalena": "2307635",  # Madalena
    "maracanau": "2307650",  # Maracanaú
    "maranguape": "2307700",  # Maranguape
    "marco": "2307809",  # Marco
    "martinopole": "2307908",  # Martinópole
    "massape": "2308005",  # Massapê
    "mauriti": "2308104",  # Mauriti
    "meruoca": "2308203",  # Meruoca
    "milagres": "2308302",  # Milagres
    "milha": "2308351",  # Milhã
    "miraima": "2308377",  # Miraíma
    "missao velha": "2308401",  # Missão Velha
    "mombaca": "2308500",  # Mombaça
    "monsenhor tabosa": "2308609",  # Monsenhor Tabosa
    "morada nova": "2308708",  # Morada Nova
    "moraujo": "2308807",  # Moraújo
    "morrinhos": "2308906",  # Morrinhos
    "mucambo": "2309003",  # Mucambo
    "mulungu": "2309102",  # Mulungu
    "nova olinda": "2309201",  # Nova Olinda
    "nova russas": "2309300",  # Nova Russas
    "novo oriente": "2309409",  # Novo Oriente
    "ocara": "2309458",  # Ocara
    "oros": "2309508",  # Orós
    "pacajus": "2309607",  # Pacajus
    "pacatuba": "2309706",  # Pacatuba
    "pacoti": "2309805",  # Pacoti
    "pacuja": "2309904",  # Pacujá
    "palhano": "2310001",  # Palhano
    "palmacia": "2310100",  # Palmácia
    "paracuru": "2310209",  # Paracuru
    "paraipaba": "2310258",  # Paraipaba
    "parambu": "2310308",  # Parambu
    "paramoti": "2310407",  # Paramoti
    "pedra branca": "2310506",  # Pedra Branca
    "penaforte": "2310605",  # Penaforte
    "pentecoste": "2310704",  # Pentecoste
    "pereiro": "2310803",  # Pereiro
    "pindoretama": "2310852",  # Pindoretama
    "piquet carneiro": "2310902",  # Piquet Carneiro
    "pires ferreira": "2310951",  # Pires Ferreira
    "poranga": "2311009",  # Poranga
    "porteiras": "2311108",  # Porteiras
    "potengi": "2311207",  # Potengi
    "potiretama": "2311231",  # Potiretama
    "quiterianopolis": "2311264",  # Quiterianópolis
    "quixada": "2311306",  # Quixadá
    "quixelo": "2311355",  # Quixelô
    "quixeramobim": "2311405",  # Quixeramobim
    "quixere": "2311504",  # Quixeré
    "redencao": "2311603",  # Redenção
    "reriutaba": "2311702",  # Reriutaba
    "russas": "2311801",  # Russas
    "saboeiro": "2311900",  # Saboeiro
    "salitre": "2311959",  # Salitre
    "santa quiteria": "2312205",  # Santa Quitéria
    "santana do acarau": "2312007",  # Santana do Acaraú
    "santana do cariri": "2312106",  # Santana do Cariri
    "sao benedito": "2312304",  # São Benedito
    "sao goncalo do amarante": "2312403",  # São Gonçalo do Amarante
    "sao joao do jaguaribe": "2312502",  # São João do Jaguaribe
    "sao luis do curu": "2312601",  # São Luís do Curu
    "senador pompeu": "2312700",  # Senador Pompeu
    "senador sa": "2312809",  # Senador Sá
    "sobral": "2312908",  # Sobral
    "solonopole": "2313005",  # Solonópole
    "tabuleiro do norte": "2313104",  # Tabuleiro do Norte
    "tamboril": "2313203",  # Tamboril
    "tarrafas": "2313252",  # Tarrafas
    "taua": "2313302",  # Tauá
    "tejucuoca": "2313351",  # Tejuçuoca
    "tiangua": "2313401",  # Tianguá
    "trairi": "2313500",  # Trairi
    "tururu": "2313559",  # Tururu
    "ubajara": "2313609",  # Ubajara
    "umari": "2313708",  # Umari
    "umirim": "2313757",  # Umirim
    "uruburetama": "2313807",  # Uruburetama
    "uruoca": "2313906",  # Uruoca
    "varjota": "2313955",  # Varjota
    "varzea alegre": "2314003",  # Várzea Alegre
    "vicosa do ceara": "2314102",  # Viçosa do Ceará
}


def _normalizar(nome: str) -> str:
    """Minúsculas, sem acento, espaços colapsados — a mesma chave da tabela."""
    sem_acento = unicodedata.normalize("NFKD", nome or "")
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return " ".join(sem_acento.lower().split())


def codigo_ibge(cidade: str, uf: str = UF) -> Optional[str]:
    """
    Código IBGE do município, ou None.

    Devolve None fora do Ceará em vez de tentar adivinhar: uma tabela estadual
    respondendo sobre outro estado é pior que não responder — o município
    homônimo em UF diferente tem código diferente, e é exatamente esse o erro
    que este arquivo existe para evitar.
    """
    if (uf or "").strip().upper() != UF:
        return None
    return MUNICIPIOS_CE.get(_normalizar(cidade))
