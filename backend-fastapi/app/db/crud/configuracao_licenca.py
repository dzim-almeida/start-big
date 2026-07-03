# ---------------------------------------------------------------------------
# ARQUIVO: crud/configuracao_licenca.py
# DESCRIÇÃO: Queries SQL para a entidade ConfiguracaoLicenca.
# ---------------------------------------------------------------------------

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.configuracao_licenca import ConfiguracaoLicenca


def get_licenca(db: Session) -> Optional[ConfiguracaoLicenca]:
    """Retorna a licença do sistema (espera-se no máximo uma)."""
    stmt = select(ConfiguracaoLicenca).limit(1)
    return db.scalars(stmt).first()


def get_licenca_by_hwid(db: Session, hwid: str) -> Optional[ConfiguracaoLicenca]:
    """Busca licença pelo HWID."""
    stmt = select(ConfiguracaoLicenca).where(ConfiguracaoLicenca.hwid == hwid)
    return db.scalars(stmt).first()


def create_licenca(db: Session, licenca: ConfiguracaoLicenca) -> ConfiguracaoLicenca:
    """Persiste a licença no banco de dados."""
    db.add(licenca)
    db.flush()
    db.refresh(licenca)
    return licenca


def update_licenca(db: Session, licenca: ConfiguracaoLicenca) -> ConfiguracaoLicenca:
    """Atualiza a licença existente."""
    db.flush()
    db.refresh(licenca)
    return licenca
