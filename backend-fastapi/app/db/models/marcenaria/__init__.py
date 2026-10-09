# ---------------------------------------------------------------------------
# PACOTE: app/db/models/marcenaria
# DESCRICAO: Tabelas do orcamento tecnico da marcenaria (Spec 06A).
#            Todas comecam com `marcenaria_` para nao se misturar com as da
#            fabrica aposentada (`fabrica_*`), que ficam no banco sem uso.
# ---------------------------------------------------------------------------

from app.db.models.marcenaria.ambiente import MarcenariaAmbiente, MarcenariaMovel, MarcenariaMovelInsumo
from app.db.models.marcenaria.etapa import MarcenariaEtapa
from app.db.models.marcenaria.evento import MarcenariaEvento
from app.db.models.marcenaria.orcamento import (
    MarcenariaOrcamento,
    MarcenariaOrcamentoAnexo,
    MarcenariaOrcamentoRT,
)

__all__ = [
    "MarcenariaOrcamento",
    "MarcenariaOrcamentoRT",
    "MarcenariaOrcamentoAnexo",
    "MarcenariaAmbiente",
    "MarcenariaMovel",
    "MarcenariaMovelInsumo",
    "MarcenariaEvento",
    "MarcenariaEtapa",          # Spec 12A
]
