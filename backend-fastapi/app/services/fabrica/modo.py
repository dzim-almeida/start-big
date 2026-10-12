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

APOSENTADA (08/10/2026): a marcenaria passou a seguir as specs de
backend-fastapi/docs/marcenaria/ (orçamento técnico). `modo_fabrica_ligado`
responde sempre False, então nenhuma OS nova entra no trilho; o resto da
fábrica fica inerte e sai numa limpeza depois do piloto (SPEC-00 FB1,
Spec 03A D13-D16).
"""

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.segmentos.definicoes.marcenaria import MARCENARIA

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
    """Sempre False: a fábrica foi APOSENTADA (SPEC-00 da marcenaria, Revisão 15, FB1).

    A marcenaria segue as specs de docs/marcenaria/ (orçamento técnico). A chave
    `configuracoes_os.modo_fabrica` continua no banco e no contrato, mas não liga
    mais nada: nenhuma OS nova entra no trilho. O código da fábrica fica inerte
    (tudo pergunta pela `fase_fabrica` da OS, que nenhuma OS nova recebe) e sai
    numa limpeza depois do piloto.
    """
    return False  # `db` fica na assinatura: quem chama não muda


def fase_inicial(db: Session, dados_adicionais: Optional[dict[str, Any]]) -> Optional[str]:
    """MEDICAO para OS nova de Planejados no modo fábrica; None para todo o resto."""
    tipo = (dados_adicionais or {}).get("tipo_trabalho") or TIPO_PADRAO
    if tipo != TIPO_PLANEJADOS:
        return None
    return Fase.MEDICAO if modo_fabrica_ligado(db) else None
