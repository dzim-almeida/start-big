# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/certificado.py
# DESCRIÇÃO: Reconferir na plataforma o certificado que ficou VALIDADO_LOCAL.
#
# O caso que motivou (06/10/2026): o certificado do primeiro cliente em
# produção foi enviado antes de a ficha fiscal existir na plataforma e ficou
# "Validado, não enviado". Depois alguém o cadastrou na emissora — pelo
# painel da Focus ou reenviando —, e o ERP continuou dizendo "a emissão não vai
# funcionar" com a nota saindo normalmente. O status local não tinha caminho
# de volta a não ser reenviar o .pfx.
#
# A regra é conservadora: só promove a CONECTADO_NUVEM quando a plataforma
# afirma as duas coisas — certificado ATIVO e token de emissão presente. "Não
# sei" (plataforma fora do ar) nunca muda nada.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session

from app.db.crud import fiscal as fiscal_crud


def reconferir_certificado(db: Session, empresa_id: int) -> dict:
    from app.services.fiscal.http import get_fiscal_client

    fs = fiscal_crud.get_fiscal_settings(db, empresa_id)
    if fs is None:
        return {"certificado_status": None, "alterado": False,
                "mensagem": "Configurações fiscais ainda não cadastradas."}

    config = get_fiscal_client(
        fs.ambiente_emissao or 2, fiscal_crud.get_licenca_token(db),
    ).consultar_config()

    if not config:
        return {"certificado_status": fs.certificado_status, "alterado": False,
                "mensagem": "Não foi possível falar com a plataforma de emissão agora. Tente de novo em instantes."}

    if not config.get("configurado"):
        return {"certificado_status": fs.certificado_status, "alterado": False,
                "mensagem": "A plataforma ainda não tem a configuração fiscal desta empresa. Peça ao suporte StartBig para liberar a emissão."}

    na_emissora = config.get("certificadoStatus") == "ATIVO" and bool(config.get("tokenConfigurado"))
    if not na_emissora:
        pendencias = [str(p) for p in (config.get("pendencias") or [])]
        detalhe = f" A plataforma informa: {' '.join(pendencias)}" if pendencias else ""
        return {"certificado_status": fs.certificado_status, "alterado": False,
                "mensagem": f"O certificado ainda não consta na emissora. Envie o certificado de novo.{detalhe}"}

    alterado = fs.certificado_status != "CONECTADO_NUVEM"
    fs.certificado_status = "CONECTADO_NUVEM"
    db.flush()
    return {"certificado_status": "CONECTADO_NUVEM", "alterado": alterado,
            "mensagem": "O certificado está na emissora. Tudo certo para emitir."}
