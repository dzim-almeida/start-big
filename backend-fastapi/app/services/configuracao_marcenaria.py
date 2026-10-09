# ---------------------------------------------------------------------------
# ARQUIVO: app/services/configuracao_marcenaria.py
# DESCRICAO: Parametros padrao do orcamento de marcenaria (Spec 04A).
#
#            So existe para segmento que declara a capacidade
#            `orcamento_tecnico` (hoje, a marcenaria). A regra le a CAPACIDADE
#            no registry, nunca o nome do segmento (D1).
# ---------------------------------------------------------------------------

from enum import Enum

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core import segmentos as reg
from app.db.crud.configuracao_marcenaria import (
    create_configuracao_marcenaria,
    get_configuracao_marcenaria,
    update_configuracao_marcenaria,
)
from app.db.models.configuracao_marcenaria import ConfiguracaoMarcenaria
from app.schemas.configuracao_marcenaria import ConfiguracaoMarcenariaUpdate
from app.services.segmentos import get_segmento_atual


def _exigir_orcamento_tecnico(db: Session) -> None:
    """404 fora de segmento com orcamento tecnico (D1): para os outros, a rota nao existe."""
    if not reg.segmento_tem_capacidade(get_segmento_atual(db), reg.CAP_ORCAMENTO_TECNICO):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parâmetros de marcenaria não disponíveis para este segmento.",
        )


def obter_configuracao(db: Session, empresa_id: int) -> ConfiguracaoMarcenaria:
    """A configuracao da empresa; criada com os padroes na primeira chamada.

    E tambem o ponto que o orcamento (Spec 06A) usa para COPIAR os padroes.
    """
    _exigir_orcamento_tecnico(db)
    config = get_configuracao_marcenaria(db, empresa_id)       # ja existe?
    if config is None:
        config = create_configuracao_marcenaria(db, empresa_id)  # get-or-create
    return config


def atualizar_configuracao(
    db: Session,
    empresa_id: int,
    dados: ConfiguracaoMarcenariaUpdate,
) -> ConfiguracaoMarcenaria:
    """PUT parcial: so os campos enviados mudam."""
    config = obter_configuracao(db, empresa_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():   # so o que veio
        # O enum do RT vira o texto gravado no banco ("MARGEM"/"PRECO").
        setattr(config, campo, valor.value if isinstance(valor, Enum) else valor)
    return update_configuracao_marcenaria(db, config)
