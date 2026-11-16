# ---------------------------------------------------------------------------
# PACOTE: app/services/marcenaria/faturamento
# DESCRICAO: Faturamento dos moveis (docs/marcenaria-faturamento-plano.md):
#            o movel pronto vira produto acabado no estoque e sai na NF-e.
#
#            Tudo aqui so age com `faturamento_modo != DESLIGADO` (R1).
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session

from app.core import segmentos as reg
from app.db.crud.configuracao.marcenaria import get_configuracao_marcenaria
from app.db.models.configuracao_marcenaria import ConfiguracaoMarcenaria
from app.services.sistema.segmentos import get_segmento_atual

DESLIGADO = "DESLIGADO"


def empresa_atual_id(db: Session) -> int | None:
    """A empresa do banco (o sistema e de uma empresa por banco; a OS nao a guarda)."""
    from app.db.crud import empresa as empresa_crud

    empresa = empresa_crud.get_empresa_atual(db)
    return empresa.id if empresa is not None else None


def configuracao_ligada(db: Session, empresa_id: int | None) -> ConfiguracaoMarcenaria | None:
    """A configuracao da marcenaria SE o faturamento dos moveis esta ligado.

    None fora da marcenaria, sem configuracao gravada ou desligado: quem chama
    segue o caminho de sempre. Nunca CRIA a configuracao (e so leitura).
    """
    if empresa_id is None:
        return None
    if not reg.segmento_tem_capacidade(get_segmento_atual(db), reg.CAP_ORCAMENTO_TECNICO):
        return None
    config = get_configuracao_marcenaria(db, int(empresa_id))
    if config is None or config.faturamento_modo == DESLIGADO:
        return None
    return config


def ids_produtos_acabados(db: Session, empresa_id: int | None) -> set[int]:
    """Os produtos acabados da configuracao (D10: nao aparecem no PDV).

    Vale com o faturamento ligado ou nao: o produto foi criado para isso e nao
    tem preco, entao nao ha por que oferece-lo no balcao.
    """
    if empresa_id is None:
        return set()
    if not reg.segmento_tem_capacidade(get_segmento_atual(db), reg.CAP_ORCAMENTO_TECNICO):
        return set()
    config = get_configuracao_marcenaria(db, int(empresa_id))
    if config is None:
        return set()
    return {pid for pid in (config.produto_acabado_padrao_id, config.produto_acabado_revenda_id) if pid}
