# ---------------------------------------------------------------------------
# ARQUIVO: services/financeiro/extrato.py
# DESCRICAO: Financeiro - extrato (o livro do dinheiro linha a linha) e o
#            detalhe de custo.
# ---------------------------------------------------------------------------

from datetime import date
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.core.tempo import fim_do_dia_utc, inicio_do_dia_utc
from app.db.crud import financeiro as financeiro_crud
from app.db.crud.relatorio import custo as custo_crud
from app.schemas.financeiro import (
    Extrato,
    ExtratoLinha,
)


# ===========================================================================
# EXTRATO (Onda 5)
# ===========================================================================

def listar_extrato(
    db: Session,
    empresa_id: int,
    *,
    inicio: Optional[date] = None,
    fim: Optional[date] = None,
    tipo: Optional[str] = None,
    origem: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
) -> Extrato:
    """O livro do dinheiro linha a linha — o que JÁ aconteceu.

    O Fluxo de Caixa olha para frente e só enxerga documento em aberto; conta
    paga SAI da régua dele. Este é o outro lado: aqui nada sai nunca, porque
    `movimentacoes_financeiras` só recebe INSERT. Estorno não apaga o
    lançamento original, cria o contrário -- e as duas linhas ficam.

    O período filtra por `criado_em` (o instante em que o dinheiro andou), e
    não por vencimento: no extrato não existe futuro.
    """
    dt_inicio = inicio_do_dia_utc(inicio) if inicio else None
    dt_fim = fim_do_dia_utc(fim) if fim else None

    itens, total = financeiro_crud.listar_extrato(
        db, empresa_id, inicio=dt_inicio, fim=dt_fim, tipo=tipo, origem=origem,
        limit=limit, offset=offset,
    )
    entradas, saidas = financeiro_crud.totais_extrato(
        db, empresa_id, inicio=dt_inicio, fim=dt_fim, tipo=tipo, origem=origem
    )

    por_venda, por_os = financeiro_crud.documentos_de_origem(
        db,
        venda_pagamento_ids=[m.venda_pagamento_id for m in itens if m.venda_pagamento_id],
        os_pagamento_ids=[
            m.ordem_servico_pagamento_id for m in itens if m.ordem_servico_pagamento_id
        ],
    )

    def _documento(mov) -> Optional[str]:
        if mov.venda_pagamento_id:
            numero = por_venda.get(mov.venda_pagamento_id)
            return f"Venda {numero}" if numero else "Venda"
        if mov.ordem_servico_pagamento_id:
            return por_os.get(mov.ordem_servico_pagamento_id)
        return None

    # A conta bancária é lida do relacionamento por linha e não por join com
    # `joinedload`: nem toda linha tem conta, e o extrato de um mês cabe numa
    # página. Se um dia a tela paginar milhares, isto vira joinedload.
    contas = {
        c.id: c.nome for c in financeiro_crud.listar_contas_bancarias(db, empresa_id)
    }

    return Extrato(
        total_itens=total,
        total_entradas=entradas,
        total_saidas=saidas,
        saldo=entradas - saidas,
        itens=[
            ExtratoLinha(
                id=m.id,
                criado_em=m.criado_em,
                tipo=m.tipo,
                origem=m.origem,
                valor=int(m.valor or 0),
                motivo=m.motivo,
                funcionario_nome=m.funcionario_nome,
                conta_bancaria_nome=contas.get(m.conta_bancaria_id),
                forma_pagamento_nome=(
                    m.forma_pagamento.nome if m.forma_pagamento else None
                ),
                sessao_caixa_id=m.sessao_caixa_id,
                documento=_documento(m),
            )
            for m in itens
        ],
    )


def get_detalhe_custo(
    db: Session, empresa_id: int, inicio: date, fim: date
) -> Dict[str, Any]:
    """Abre o card "Custo do que vendeu": cada linha que formou o CMV.

    Só leitura, e de propósito no mesmo arquivo das outras três leituras.

    O TOTAL DAQUI TEM QUE BATER com `custo_mercadorias` do resumo. As duas somas
    saem das mesmas quatro parcelas com os mesmos filtros (ver o cabeçalho de
    `crud/relatorio/custo.get_detalhe_cmv`), e há teste amarrando os dois números --
    um detalhe que não fecha com o total piora a desconfiança em vez de
    resolvê-la, que é exatamente o problema que ele veio consertar.
    """
    dt_inicio, dt_fim = inicio_do_dia_utc(inicio), fim_do_dia_utc(fim)
    linhas = custo_crud.get_detalhe_cmv(db, dt_inicio, dt_fim, empresa_id)
    return {
        "periodo_inicio": inicio,
        "periodo_fim": fim,
        "total": sum(l["custo"] for l in linhas),
        "linhas": linhas,
    }
