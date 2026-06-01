from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.crud.configuracao_clientes import (
    get_configuracao_clientes,
    create_configuracao_clientes,
)
from app.db.models.configuracao_clientes import ConfiguracaoClientes
from app.schemas.configuracao_clientes import ConfiguracaoClientesUpdate


def get_or_create_configuracao_clientes(
    db: Session,
    empresa_id: int,
) -> ConfiguracaoClientes:
    config = get_configuracao_clientes(db, empresa_id)
    if not config:
        config = create_configuracao_clientes(db, empresa_id)
    return config


def update_configuracao_clientes(
    db: Session,
    empresa_id: int,
    data: ConfiguracaoClientesUpdate,
) -> ConfiguracaoClientes:
    config = get_configuracao_clientes(db, empresa_id)
    if not config:
        config = create_configuracao_clientes(db, empresa_id)

    campos = data.model_dump(exclude_unset=True)
    for campo, valor in campos.items():
        setattr(config, campo, valor)

    return config
