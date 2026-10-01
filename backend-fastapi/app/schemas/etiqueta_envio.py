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

# Só venda: o que se embala e despacha é produto (OS ficou de fora — serviço não se envia).
TipoOrigemEnvio = Literal["venda"]


class OrigemEnvioItem(BaseModel):
    """Uma venda na busca de "de onde vem a etiqueta"."""

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
    remetente: ParteEnvio
    destinatario: Optional[ParteEnvio] = None
    nfe: Optional[NfeEnvio] = None
    # A5 (plano de embalagens): o que dá para tirar dos fardos/caixas vendidos.
    # Volumes = quantas embalagens fechadas; peso = Σ quantidade × peso delas.
    # `peso_completo` só é verdade quando TODA linha da venda é embalagem com
    # peso — aí a tela preenche sozinha. Senão ela só mostra o parcial como
    # dica: uma soma que esquece as latas avulsas é peso errado na etiqueta.
    volumes_embalagens: int = 0
    peso_embalagens_gramas: int = 0
    peso_completo: bool = False
