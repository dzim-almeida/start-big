from sqlalchemy.orm import Session

from app.db.crud.configuracao_vendas import (
    get_configuracao_vendas,
    create_configuracao_vendas,
)
from app.db.models.configuracao_vendas import ConfiguracaoVendas
from app.schemas.configuracao_vendas import ConfiguracaoVendasUpdate


def get_or_create_configuracao_vendas(
    db: Session,
    empresa_id: int,
) -> ConfiguracaoVendas:
    config = get_configuracao_vendas(db, empresa_id)
    if not config:
        config = create_configuracao_vendas(db, empresa_id)
    return config


def update_configuracao_vendas(
    db: Session,
    empresa_id: int,
    data: ConfiguracaoVendasUpdate,
) -> ConfiguracaoVendas:
    config = get_configuracao_vendas(db, empresa_id)
    if not config:
        config = create_configuracao_vendas(db, empresa_id)

    campos = data.model_dump(exclude_unset=True)
    for campo, valor in campos.items():
        setattr(config, campo, valor)

    return config
