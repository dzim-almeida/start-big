# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/lava_rapido/__init__.py
# DESCRICAO: Tabelas do segmento lava-rapido (docs/lava-rapido/).
# ---------------------------------------------------------------------------

from app.db.models.lava_rapido.agendamento import Agendamento
from app.db.models.lava_rapido.porte import PorteVeiculo, ServicoPrecoPorte

__all__ = ["Agendamento", "PorteVeiculo", "ServicoPrecoPorte"]
