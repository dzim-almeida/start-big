from sqlalchemy.orm import Session

from app.db.crud.configuracao_vendas import (
    get_configuracao_vendas,
    create_configuracao_vendas,
)
from app.db.models.configuracao_vendas import ConfiguracaoVendas
from app.db.models.venda import Venda
from app.db.models.funcionario import Funcionario
from app.core.enum import VendaStatus
from app.schemas.configuracao_vendas import ConfiguracaoVendasUpdate


def get_or_create_configuracao_vendas(
    db: Session,
    empresa_id: int,
) -> ConfiguracaoVendas:
    config = get_configuracao_vendas(db, empresa_id)
    if not config:
        config = create_configuracao_vendas(db, empresa_id)
    return config


def _zerar_descontos_excessivos(db: Session, empresa_id: int, desconto_maximo_percent: int) -> None:
    vendas_ativas = (
        db.query(Venda)
        .join(Funcionario, Venda.funcionario_id == Funcionario.id)
        .filter(Funcionario.empresa_id == empresa_id, Venda.status == VendaStatus.ATIVA)
        .all()
    )
    for venda in vendas_ativas:
        if venda.total_bruto <= 0 or venda.descontos <= 0:
            continue
        percentual = (venda.descontos * 100) // venda.total_bruto
        if percentual > desconto_maximo_percent:
            for item in venda.itens:
                item.desconto = 0
            venda.total = venda.total_bruto


def update_configuracao_vendas(
    db: Session,
    empresa_id: int,
    data: ConfiguracaoVendasUpdate,
) -> ConfiguracaoVendas:
    config = get_configuracao_vendas(db, empresa_id)
    if not config:
        config = create_configuracao_vendas(db, empresa_id)

    campos = data.model_dump(exclude_unset=True)
    for campo, valor in campos.items():
        setattr(config, campo, valor)

    if config.permitir_desconto and config.desconto_maximo_percent > 0:
        _zerar_descontos_excessivos(db, empresa_id, config.desconto_maximo_percent)

    return config
