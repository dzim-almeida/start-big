# ---------------------------------------------------------------------------
# ARQUIVO: schemas/etiqueta_envio.py
# MÓDULO: Schemas Pydantic — Etiquetas de envio (Central de Etiquetas, fase 5)
# ---------------------------------------------------------------------------
"""
Tudo o que uma etiqueta de volume ou um DANFE Simplificado – Etiqueta
imprime, já resolvido: o frontend não precisa saber que o cliente PJ tem
razão social e o PF tem nome, nem onde mora a chave da NF-e de uma OS.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

TipoOrigemEnvio = Literal["os", "venda"]


class OrigemEnvioItem(BaseModel):
    """Uma OS ou Venda na busca de "de onde vem a etiqueta"."""

    tipo: TipoOrigemEnvio
    id: int
    numero: str
    cliente_nome: Optional[str] = None
    data: datetime
    tem_nfe: bool = False


class EnderecoEnvio(BaseModel):
    logradouro: str = ""
    numero: str = ""
    complemento: Optional[str] = None
    bairro: str = ""
    cidade: str = ""
    uf: str = ""
    cep: str = ""


class ParteEnvio(BaseModel):
    """Remetente ou destinatário."""

    nome: str = ""
    documento: Optional[str] = None
    inscricao_estadual: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[EnderecoEnvio] = None


class NfeEnvio(BaseModel):
    """A NF-e AUTORIZADA da origem — o que o DANFE Simplificado precisa."""

    numero: int
    serie: int
    chave_acesso: str
    protocolo: Optional[str] = None
    data_autorizacao: Optional[datetime] = None
    data_emissao: Optional[datetime] = None
    valor_total: Optional[int] = None
    # 1 = produção, 2 = homologação (o DANFE de homologação avisa "SEM VALOR FISCAL").
    ambiente: Optional[int] = None
    # O destinatário COMO FOI PARA A NOTA. O DANFE mostra este, e não o cadastro
    # atual do cliente, que pode ter mudado depois da emissão.
    destinatario_nome: Optional[str] = None
    destinatario_documento: Optional[str] = None


class DadosEnvio(BaseModel):
    tipo: TipoOrigemEnvio
    id: int
    numero: str
    # Placa, nº de série, código do projeto (PRJ)... — o que o segmento usa.
    identificador: Optional[str] = None
    remetente: ParteEnvio
    destinatario: Optional[ParteEnvio] = None
    nfe: Optional[NfeEnvio] = None
