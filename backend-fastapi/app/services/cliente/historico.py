# ---------------------------------------------------------------------------
# ARQUIVO: services/cliente/historico.py
# DESCRICAO: Historico de equipamentos (objetos de OS) do cliente.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session

from app.db.crud import cliente as cliente_crud
from app.services.cliente.cadastro import _get_cliente_or_raise


# ===========================================================================
# EQUIPAMENTOS DO CLIENTE (HISTÓRICO)
# ===========================================================================

EQUIPMENT_HISTORY_LIMIT = 20


def get_equipamentos_historico_by_cliente_id(
    db: Session, cliente_id: int
) -> list:
    """
    Retorna equipamentos únicos (ativos) de um cliente, deduplicados
    por (tipo_equipamento, marca, modelo, numero_serie) e limitados
    aos mais recentes.
    """
    _get_cliente_or_raise(db, cliente_id)

    equipamentos = cliente_crud.get_objetos_by_cliente_id(db, cliente_id)

    seen: set[tuple] = set()
    resultado: list = []

    for equip in equipamentos:
        key = (equip.tipo_equipamento, equip.marca, equip.modelo, equip.numero_serie)
        if key not in seen:
            seen.add(key)
            resultado.append(equip)
        if len(resultado) >= EQUIPMENT_HISTORY_LIMIT:
            break

    return resultado
