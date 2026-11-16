# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/configuracao/licenca.py (era db/crud/configuracao_licenca.py ate 13/10/2026)
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


def remover_licencas_de_outras_maquinas(db: Session, hwid: str) -> int:
    """Apaga as licenças cifradas com o HWID de OUTRA máquina; devolve quantas.

    Só o reconectar chama isto, e só depois que a nuvem aprovou: é a linha que
    veio junto com um banco copiado de outro computador. Ela não decifra aqui
    e ocupa o `licenca_id` (unique) que a licença nova precisa.
    """
    antigas = db.scalars(
        select(ConfiguracaoLicenca).where(ConfiguracaoLicenca.hwid != hwid)
    ).all()
    for antiga in antigas:
        db.delete(antiga)
    db.flush()
    return len(antigas)


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
