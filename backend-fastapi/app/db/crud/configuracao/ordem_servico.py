from sqlalchemy.orm import Session
from app.db.models.configuracao_os import ConfiguracaoOS


def get_configuracao_os(db: Session, empresa_id: int) -> ConfiguracaoOS | None:
    return db.query(ConfiguracaoOS).filter(ConfiguracaoOS.empresa_id == empresa_id).first()


def create_configuracao_os(db: Session, empresa_id: int) -> ConfiguracaoOS:
    config = ConfiguracaoOS(empresa_id=empresa_id)
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def update_configuracao_os(db: Session, config: ConfiguracaoOS) -> ConfiguracaoOS:
    db.commit()
    db.refresh(config)
    return config
