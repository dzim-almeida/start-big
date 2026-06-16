from sqlalchemy.orm import Session
from app.db.models.configuracao_vendas import ConfiguracaoVendas


def get_configuracao_vendas(db: Session, empresa_id: int) -> ConfiguracaoVendas | None:
    return db.query(ConfiguracaoVendas).filter(
        ConfiguracaoVendas.empresa_id == empresa_id
    ).first()


def create_configuracao_vendas(db: Session, empresa_id: int) -> ConfiguracaoVendas:
    config = ConfiguracaoVendas(empresa_id=empresa_id)
    db.add(config)
    db.flush()
    return config


def update_configuracao_vendas(
    db: Session,
    config: ConfiguracaoVendas,
) -> ConfiguracaoVendas:
    db.flush()
    return config
