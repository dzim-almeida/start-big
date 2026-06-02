from sqlalchemy.orm import Session
from app.db.models.configuracao_clientes import ConfiguracaoClientes


def get_configuracao_clientes(db: Session, empresa_id: int) -> ConfiguracaoClientes | None:
    return db.query(ConfiguracaoClientes).filter(
        ConfiguracaoClientes.empresa_id == empresa_id
    ).first()


def create_configuracao_clientes(db: Session, empresa_id: int) -> ConfiguracaoClientes:
    config = ConfiguracaoClientes(empresa_id=empresa_id)
    db.add(config)
    db.flush()
    return config


def update_configuracao_clientes(
    db: Session,
    config: ConfiguracaoClientes,
) -> ConfiguracaoClientes:
    db.flush()
    return config
