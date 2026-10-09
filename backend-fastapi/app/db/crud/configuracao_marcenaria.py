# ---------------------------------------------------------------------------
# ARQUIVO: app/db/crud/configuracao_marcenaria.py
# DESCRICAO: Leitura e gravacao dos parametros da marcenaria (Spec 04A).
#            So SQL; a regra fica no servico. Mesmo padrao de configuracao_os.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session

from app.db.models.configuracao_marcenaria import ConfiguracaoMarcenaria


def get_configuracao_marcenaria(db: Session, empresa_id: int) -> ConfiguracaoMarcenaria | None:
    """A configuracao da empresa, ou None se ainda nao foi criada."""
    return (
        db.query(ConfiguracaoMarcenaria)
        .filter(ConfiguracaoMarcenaria.empresa_id == empresa_id)
        .first()
    )


def create_configuracao_marcenaria(db: Session, empresa_id: int) -> ConfiguracaoMarcenaria:
    """Cria a configuracao com os valores padrao do model."""
    config = ConfiguracaoMarcenaria(empresa_id=empresa_id)
    db.add(config)
    db.commit()            # mesmo padrao das outras configuracoes (get-or-create grava na hora)
    db.refresh(config)
    return config


def update_configuracao_marcenaria(db: Session, config: ConfiguracaoMarcenaria) -> ConfiguracaoMarcenaria:
    """Grava o que o servico alterou no objeto."""
    db.commit()
    db.refresh(config)
    return config
