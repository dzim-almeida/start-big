# ---------------------------------------------------------------------------
# ARQUIVO: enum.py
# DESCRIÇÃO: Centraliza todas as classes Enum da aplicação para garantir
#            consistência e reutilização de tipos de dados fixos.
# ---------------------------------------------------------------------------

import enum

class Gender(enum.Enum):
    """Define os gêneros possíveis para usuários ou clientes."""
    MASCULINO = "MASCULINO"
    FEMININO = "FEMININO"
    OUTRO = "OUTRO"

class ClientType(str, enum.Enum):
    """Define os tipos de cliente (Pessoa Física ou Jurídica)."""
    PF = "PF"
    PJ = "PJ"

class State(str, enum.Enum):
    """Define as siglas dos estados brasileiros."""
    ACRE = "AC"
    ALAGOAS = "AL"
    AMAPA = "AP"
    AMAZONAS = "AM"
    BAHIA = "BA"
    CEARA = "CE"
    DISTRITO_FEDERAL = "DF"
    ESPIRITO_SANTO = "ES"
    GOIAS = "GO"
    MARANHAO = "MA"
    MATO_GROSSO = "MT"
    MATO_GROSSO_DO_SUL = "MS"
    MINAS_GERAIS = "MG"
    PARA = "PA"
    PARAIBA = "PB"
    PARANA = "PR"
    PERNAMBUCO = "PE"
    PIAUI = "PI"
    RIO_DE_JANEIRO = "RJ"
    RIO_GRANDE_DO_NORTE = "RN"
    RIO_GRANDE_DO_SUL = "RS"
    RONDONIA = "RO"
    RORAIMA = "RR"
    SANTA_CATARINA = "SC"
    SAO_PAULO = "SP"
    SERGIPE = "SE"
    TOCANTINS = "TO"

class UserType(str, enum.Enum):
    """Define os níveis de permissão ou tipos de usuário no sistema."""
    ADMIN = "ADMIN"
    USER = "USER"