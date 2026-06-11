from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.crud.configuracao_seguranca import (
    get_configuracao_seguranca,
    create_configuracao_seguranca,
)
from app.db.models.configuracao_seguranca import ConfiguracaoSeguranca
from app.core.security import hash_password, verify_password
from app.schemas.configuracao_seguranca import ConfiguracaoSegurancaUpdate


def get_or_create_configuracao_seguranca(
    db: Session,
    empresa_id: int,
) -> ConfiguracaoSeguranca:
    config = get_configuracao_seguranca(db, empresa_id)
    if not config:
        config = create_configuracao_seguranca(db, empresa_id)
    return config


def update_configuracao_seguranca(
    db: Session,
    empresa_id: int,
    data: ConfiguracaoSegurancaUpdate,
) -> ConfiguracaoSeguranca:
    config = get_configuracao_seguranca(db, empresa_id)
    if not config:
        config = create_configuracao_seguranca(db, empresa_id)

    campos = data.model_dump(exclude_unset=True)
    if "pin_gerente" in campos and campos["pin_gerente"]:
        campos["pin_gerente"] = hash_password(campos["pin_gerente"])
    for campo, valor in campos.items():
        setattr(config, campo, valor)

    return config


def verificar_pin_gerente(db: Session, empresa_id: int, pin: str) -> None:
    config = get_configuracao_seguranca(db, empresa_id)
    if not config or not config.pin_gerente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN_GERENTE_INVALIDO",
        )
    if not verify_password(pin, config.pin_gerente):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN_GERENTE_INVALIDO",
        )
