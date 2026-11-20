# ---------------------------------------------------------------------------
# ARQUIVO: schemas/licenca/titular.py
# DESCRICAO: Dados do titular da conta na nuvem (LIC-03 §5, D-22, conflito 16).
#
# Os nomes dos campos seguem a API StartBig (camelCase), porque estes objetos
# vão e voltam da nuvem exatamente assim.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict


class EnderecoTitular(BaseModel):
    """Endereço principal do titular, como a nuvem guarda."""
    cep: str
    logradouro: str
    numero: str
    bairro: str
    cidade: str
    estado: str


class TitularNuvem(BaseModel):
    """O que o GET /erp/usuario/titular devolve."""
    tipoPessoa: str                         # "PF" ou "PJ"
    nomeOuRazao: str
    documento: str                          # CPF ou CNPJ: só LEITURA, nunca enviado de volta
    nomeFantasia: str | None = None
    telefone: str | None = None
    celular: str | None = None
    endereco: EnderecoTitular | None = None


class AtualizarTitularCorpo(BaseModel):
    """Lista FECHADA de campos que podem ir à nuvem no PUT.

    O documento NÃO existe aqui de propósito: ele nunca sai do app (conflito 16).
    `extra="forbid"` faz o Pydantic recusar qualquer campo a mais, então nem por
    engano alguém consegue mandar o documento por esta classe.
    """
    model_config = ConfigDict(extra="forbid")

    nomeOuRazao: str
    nomeFantasia: str | None = None
    telefone: str | None = None
    celular: str | None = None
    endereco: EnderecoTitular | None = None
