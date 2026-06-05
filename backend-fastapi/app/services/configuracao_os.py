from sqlalchemy.orm import Session

from app.db.crud.configuracao_os import (
    get_configuracao_os,
    create_configuracao_os,
    update_configuracao_os,
)
from app.db.models.configuracao_os import ConfiguracaoOS
from app.schemas.configuracao_os import ConfiguracaoOSUpdate


def get_or_create_configuracao_os(db: Session, empresa_id: int) -> ConfiguracaoOS:
    config = get_configuracao_os(db, empresa_id)
    if not config:
        config = create_configuracao_os(db, empresa_id)
    return config


def update_configuracao_os_service(
    db: Session,
    empresa_id: int,
    data: ConfiguracaoOSUpdate,
) -> ConfiguracaoOS:
    config = get_or_create_configuracao_os(db, empresa_id)
    campos = data.model_dump(exclude_unset=True)
    for campo, valor in campos.items():
        setattr(config, campo, valor)
    return update_configuracao_os(db, config)
