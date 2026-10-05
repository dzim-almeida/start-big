# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fabrica/modo.py
# DESCRIÇÃO: Quando uma OS é da fábrica (docs/marcenaria-fabrica-plano.md, D0/D5).
# ---------------------------------------------------------------------------
"""
A porta de entrada da fábrica na OS é UMA: `ordens_servico.fase_fabrica`.
Ela só nasce preenchida quando as três coisas são verdade ao abrir a OS:

1. o segmento da loja é Marcenaria;
2. a chave `modo_fabrica` da configuração de OS está ligada;
3. o tipo de trabalho da OS é Planejados (Reforma continua de balcão).

Desligar a chave depois não tira ninguém do trilho (D0c): a OS que já tem
fase continua até fechar. Por isso todo o resto pergunta pela FASE da OS, não
pela chave.
"""

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.segmentos.definicoes.marcenaria import MARCENARIA, SEGMENTO_MARCENARIA
from app.db.crud import empresa as empresa_crud
from app.db.crud.configuracao_os import get_configuracao_os

TIPO_PLANEJADOS = "planejados"
# A tela mostra o PRIMEIRO tipo do segmento como escolhido e só grava
# `tipo_trabalho` quando o atendente mexe no seletor
# (OSObjetoDinamicoTab.vue). Ausente = o padrão da tela, senão a OS que todo
# mundo vê como "Planejados" ficaria fora do trilho.
TIPO_PADRAO = MARCENARIA["tipos"][0]["id"]


class Fase:
    """As 10 etapas guardadas (plano, §6). "Aprovado" é evento, não etapa."""

    MEDICAO = "MEDICAO"
    ELABORACAO = "ELABORACAO"
    AGUARDANDO_APROVACAO = "AGUARDANDO_APROVACAO"
    AGUARDANDO_SINAL = "AGUARDANDO_SINAL"
    SEPARACAO_COMPRA = "SEPARACAO_COMPRA"
    EM_PRODUCAO = "EM_PRODUCAO"
    PRONTO_EXPEDICAO = "PRONTO_EXPEDICAO"
    EM_INSTALACAO = "EM_INSTALACAO"
    VISTORIA_FINAL = "VISTORIA_FINAL"
    ENTREGUE = "ENTREGUE"

    ORDEM = (
        MEDICAO, ELABORACAO, AGUARDANDO_APROVACAO, AGUARDANDO_SINAL, SEPARACAO_COMPRA,
        EM_PRODUCAO, PRONTO_EXPEDICAO, EM_INSTALACAO, VISTORIA_FINAL, ENTREGUE,
    )
    # Antes da aprovação o orçamento ainda pode mudar livremente.
    ANTES_DA_APROVACAO = (MEDICAO, ELABORACAO, AGUARDANDO_APROVACAO)


def modo_fabrica_ligado(db: Session) -> bool:
    empresa = empresa_crud.get_empresa_atual(db)
    if not empresa or empresa.segmento != SEGMENTO_MARCENARIA:
        return False
    # Só lê: abrir uma OS não pode criar a linha de configuração como efeito
    # colateral (get_or_create comita).
    config = get_configuracao_os(db, empresa.id)
    return bool(config and config.modo_fabrica)


def fase_inicial(db: Session, dados_adicionais: Optional[dict[str, Any]]) -> Optional[str]:
    """MEDICAO para OS nova de Planejados no modo fábrica; None para todo o resto."""
    tipo = (dados_adicionais or {}).get("tipo_trabalho") or TIPO_PADRAO
    if tipo != TIPO_PLANEJADOS:
        return None
    return Fase.MEDICAO if modo_fabrica_ligado(db) else None
