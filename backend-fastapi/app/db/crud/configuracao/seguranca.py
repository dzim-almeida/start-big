from sqlalchemy.orm import Session
from app.db.models.configuracao_seguranca import ConfiguracaoSeguranca


def get_configuracao_seguranca(db: Session, empresa_id: int) -> ConfiguracaoSeguranca | None:
    return db.query(ConfiguracaoSeguranca).filter(
        ConfiguracaoSeguranca.empresa_id == empresa_id
    ).first()


def create_configuracao_seguranca(db: Session, empresa_id: int) -> ConfiguracaoSeguranca:
    config = ConfiguracaoSeguranca(empresa_id=empresa_id)
    db.add(config)
    db.flush()
    return config


def update_configuracao_seguranca(
    db: Session,
    config: ConfiguracaoSeguranca,
) -> ConfiguracaoSeguranca:
    db.flush()
    return config
