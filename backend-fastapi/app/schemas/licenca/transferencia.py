# ---------------------------------------------------------------------------
# ARQUIVO: schemas/licenca/transferencia.py
# DESCRICAO: Schemas da licenca - transferir para este computador, situacao
#            da licenca nesta maquina e desativacao (troca de servidor).
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TransferirLicencaPayload(BaseModel):
    """Login da conta StartBig: é o que prova que o dono autorizou a troca."""
    email: str = Field(..., max_length=255, description="E-mail da conta StartBig")
    senha: str = Field(..., min_length=1, max_length=255, description="Senha da conta StartBig")


class TransferenciaResultado(BaseModel):
    """Resposta da transferência."""
    transferida: bool = Field(True, description="A licença agora pertence a este computador")
    inicializado: bool = Field(
        ...,
        description=(
            "O banco já tem empresa e usuário master. True no caso normal de troca "
            "de servidor (banco copiado); False manda para o assistente de primeiro acesso."
        ),
    )


class DesativarMaquinaPayload(BaseModel):
    """Quem pede a desativação precisa ser o próprio servidor.

    O HWID vem do Tauri da janela que clicou. Se não bater com o do backend, o
    pedido saiu de um caixa -- e um caixa não pode desligar a licença do servidor.
    """
    hwid: str = Field(..., min_length=1, max_length=255, description="HWID da máquina que pediu")


class LicencaEstaMaquinaRead(BaseModel):
    """O que a tela de Configurações › Licença mostra sobre este computador."""
    ativada_nesta_maquina: bool = Field(
        ..., description="False quando o banco veio de outro computador e ainda não foi transferido"
    )
    licenca_id: str = Field(..., description="ID da licença na StartBig (parcial, para suporte)")
    computador: str = Field(..., description="Identificador deste computador (parcial, para suporte)")
    limite_computadores: int = Field(..., description="Quantos computadores o plano permite ao mesmo tempo")
    computadores_conectados: int = Field(..., description="Computadores com sessão aberta agora")
    data_vencimento: datetime
    ultima_sincronizacao: Optional[datetime] = None
