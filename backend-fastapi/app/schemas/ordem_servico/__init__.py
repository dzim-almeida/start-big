# ---------------------------------------------------------------------------
# ARQUIVO: schemas/ordem_servico/__init__.py
# DESCRICAO: Schemas Pydantic para Ordens de Serviço (OS).
#
# Hierarquia de schemas:
#   OSItemCreate/Read/Update    → itens de peças e serviços dentro de uma OS
#   OSEquipamentoCreate/Read    → equipamento registrado no ato de abertura
#   OSEquipamentoUpdate         → atualização parcial do equipamento/cliente
#   OSPagamentoCreate/Read      → pagamentos criados apenas ao finalizar
#   OSFotoRead                  → fotos de diagnóstico
#   OrdemServicoBase            → campos comuns a criação e leitura
#   OrdemServicoCreate          → payload de abertura de OS
#   OrdemServicoUpdate          → atualização parcial da OS
#   OrdemServicoRead            → resposta completa com relacionamentos
#   OrdemServicoFinalizar       → payload de finalização com pagamentos
#   OrdemServicoCancelar        → payload de cancelamento
#   OrdemServicoFilterParams    → query params de listagem
#   OrdemServicoQuery           → resposta paginada
#   OrdemServicoStats           → estatísticas agregadas
#
# Era um arquivo so (ordem_servico.py) ate 13/10/2026; virou pacote:
#   item.py        - itens da OS
#   objeto.py      - objeto/equipamento e identificador
#   pagamento.py   - pagamentos
#   foto.py        - fotos
#   ordem.py       - a OS (base, criar, editar, ler)
#   acoes.py       - finalizar, cancelar, reabrir
#   consulta.py    - filtros, pagina e estatisticas
#   nota_fiscal.py - dados fiscais da OS (era schemas/ordem_servico_nota_fiscal.py)
#
# Este __init__ reexporta tudo: `from app.schemas.ordem_servico import ...`
# continua valendo como antes.
# ---------------------------------------------------------------------------

from app.schemas.ordem_servico.item import (
    OSItemBase,
    OSItemCreate,
    OSItemRead,
    OSItemUpdate,
)

from app.schemas.ordem_servico.objeto import (
    OSIdentificadorConflito,
    OSIdentificadorCheck,
    OSObjetoBuscaItem,
    OSObjetoCreate,
    OSObjetoRead,
    OSObjetoUpdate,
    OSEquipamentoCreate,
    OSEquipamentoRead,
    OSEquipamentoUpdate,
)

from app.schemas.ordem_servico.pagamento import (
    OSPagamentoCreate,
    OSPagamentoRead,
)

from app.schemas.ordem_servico.foto import (
    OSFotoRead,
)

from app.schemas.ordem_servico.ordem import (
    OrdemServicoBase,
    OrdemServicoCreate,
    OrdemServicoUpdate,
    OrdemServicoRead,
)

from app.schemas.ordem_servico.acoes import (
    OrdemServicoFinalizar,
    OrdemServicoCancelar,
    OrdemServicoReabrir,
)

from app.schemas.ordem_servico.consulta import (
    OrdemServicoFilterParams,
    OrdemServicoQuery,
    OrdemServicoStats,
)

from app.schemas.ordem_servico.nota_fiscal import (
    OrdemServicoNotaFiscalUpdate,
    OrdemServicoNotaFiscalRead,
)

__all__ = [
    "OSItemBase",
    "OSItemCreate",
    "OSItemRead",
    "OSItemUpdate",
    "OSIdentificadorConflito",
    "OSIdentificadorCheck",
    "OSObjetoBuscaItem",
    "OSObjetoCreate",
    "OSObjetoRead",
    "OSObjetoUpdate",
    "OSEquipamentoCreate",
    "OSEquipamentoRead",
    "OSEquipamentoUpdate",
    "OSPagamentoCreate",
    "OSPagamentoRead",
    "OSFotoRead",
    "OrdemServicoBase",
    "OrdemServicoCreate",
    "OrdemServicoUpdate",
    "OrdemServicoRead",
    "OrdemServicoFinalizar",
    "OrdemServicoCancelar",
    "OrdemServicoReabrir",
    "OrdemServicoFilterParams",
    "OrdemServicoQuery",
    "OrdemServicoStats",
    "OrdemServicoNotaFiscalUpdate",
    "OrdemServicoNotaFiscalRead",
]
