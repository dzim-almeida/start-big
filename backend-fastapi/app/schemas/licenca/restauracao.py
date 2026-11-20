# ---------------------------------------------------------------------------
# ARQUIVO: schemas/licenca/restauracao.py
# DESCRICAO: Contratos da restauração pelo titular (LIC-03 §4.1, §5) e do
#            "reenviar link" (LIC-03, decisão do usuário).
#
# Um "schema" Pydantic é a descrição do formato de um JSON: o FastAPI usa a
# classe para conferir o corpo que chega e para montar a resposta que sai.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, EmailStr, Field  # EmailStr confere o formato do e-mail


class RestaurarBackupPayload(BaseModel):
    """Corpo de POST /licenca/restaurar-backup."""
    email: EmailStr = Field(..., description="E-mail da conta StartBig")
    senha: str = Field(..., description="Senha da conta, usada só para conferir na nuvem (D-07)")
    ciclo: str | None = Field(None, description="Ciclo do backup; None = o mais recente com full")


class RestaurarBackupResposta(BaseModel):
    """Resposta de POST /licenca/restaurar-backup quando a restauração ficou preparada."""
    status: str = Field(..., description='Sempre "pendente_reinicio" nesta versão')
    ciclo: str = Field(..., description="Ciclo que será restaurado")
    mensagem: str = Field(..., description="Texto para mostrar ao dono")


class BackupEncontrado(BaseModel):
    """Resumo do backup da nuvem mostrado na tela 'Sua licença foi encontrada' (§6.2)."""
    ciclo: str = Field(..., description="Ciclo (semana) do full mais recente, data ISO")
    ultimo_envio: str | None = Field(None, description="Data e hora do último envio desse ciclo, se a nuvem informar")


class ReenviarLinkPayload(BaseModel):
    """Corpo de POST /licenca/reenviar-link."""
    email: EmailStr = Field(..., description="E-mail da conta StartBig")
