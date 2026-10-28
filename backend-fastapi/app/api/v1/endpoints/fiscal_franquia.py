# ---------------------------------------------------------------------------
# ARQUIVO: api/v1/endpoints/fiscal_franquia.py
# DESCRIÇÃO: A franquia fiscal do mês, para a tela avisar antes de emitir
#            (docs/nfse-fase2-plano.md, G1).
#
# Sem trava de módulo, como a rota da plataforma: a franquia soma NF-e, NFC-e
# e NFS-e, e a loja com qualquer um dos três precisa ver o saldo. Arquivo à
# parte para não engordar `fiscal.py` (teto do PyArmor).
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.depends import get_current_active_user, get_db

router = APIRouter()


@router.get(
    "/franquia",
    summary="Franquia fiscal do mês",
    description=(
        "O que a plataforma informa da franquia (70 notas somando NF-e, NFC-e e NFS-e "
        "de produção). `consultou=false` quando não deu para saber: a tela esconde o "
        "cartão, e nada trava -- quem barra a emissão é a plataforma."
    ),
)
def franquia_fiscal(
    user_token: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    from app.db.crud import fiscal as fiscal_crud
    from app.services.fiscal.http import get_fiscal_client

    fs = fiscal_crud.get_fiscal_settings(db, user_token["empresa_id"])
    ambiente = fs.ambiente_emissao if fs else 2
    dados = get_fiscal_client(ambiente, fiscal_crud.get_licenca_token(db)).consultar_franquia()
    return {"consultou": bool(dados), **dados}
