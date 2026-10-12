# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/financeiro/alertas.py
# DESCRICAO: Financeiro (banco) - alertas: atraso mais antigo, alertas
#            dispensados e prazo medio de recebimento.
# ---------------------------------------------------------------------------

from datetime import date
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.enum import (
    ContaPagarStatus,
    ContaReceberStatus,
)
from app.db.models.alerta_dispensado import AlertaDispensado
from app.db.models.conta_pagar import ContaPagar
from app.db.models.conta_receber import ContaReceber


# ===========================================================================
# ALERTAS — o atraso mais antigo e o silenciamento
# ===========================================================================

def vencimento_mais_antigo_pendente(
    db: Session, empresa_id: int, *, hoje: date, receber: bool = False
) -> Optional[date]:
    """A conta vencida há mais tempo. É o que gradua a gravidade.

    Business Central deixa o admin digitar o limiar do indicador; aqui a
    pergunta "isto é grave?" se responde com o próprio dado -- e o tempo de
    atraso é metade da resposta (a outra metade é o valor).
    """
    if receber:
        q = db.query(func.min(ContaReceber.vencimento)).filter(
            ContaReceber.empresa_id == empresa_id,
            ContaReceber.status == ContaReceberStatus.PENDENTE.value,
            ContaReceber.vencimento < hoje,
        )
    else:
        q = db.query(func.min(ContaPagar.vencimento)).filter(
            ContaPagar.empresa_id == empresa_id,
            ContaPagar.status == ContaPagarStatus.PENDENTE.value,
            ContaPagar.vencimento < hoje,
        )
    return q.scalar()


def codigos_dispensados(db: Session, empresa_id: int, hoje: date) -> set:
    """Alertas silenciados que ainda não venceram o prazo."""
    linhas = (
        db.query(AlertaDispensado.codigo)
        .filter(
            AlertaDispensado.empresa_id == empresa_id,
            AlertaDispensado.dispensado_ate >= hoje,
        )
        .all()
    )
    return {linha[0] for linha in linhas}


def dispensar_alerta(
    db: Session,
    empresa_id: int,
    *,
    codigo: str,
    ate: date,
    funcionario_id: Optional[int] = None,
    funcionario_nome: Optional[str] = None,
) -> AlertaDispensado:
    """Silencia (ou re-silencia) um alerta até a data.

    Uma linha por empresa/código: adiar de novo ESTENDE o prazo em vez de
    empilhar linhas. Histórico de quem calou o quê é assunto da trilha de
    auditoria, não desta tabela, que existe só para responder "mostrar ou não".
    """
    existente = (
        db.query(AlertaDispensado)
        .filter(
            AlertaDispensado.empresa_id == empresa_id,
            AlertaDispensado.codigo == codigo,
        )
        .first()
    )
    if existente:
        existente.dispensado_ate = ate
        existente.funcionario_id = funcionario_id
        existente.funcionario_nome = funcionario_nome
        db.flush()
        return existente

    registro = AlertaDispensado(
        empresa_id=empresa_id, codigo=codigo, dispensado_ate=ate,
        funcionario_id=funcionario_id, funcionario_nome=funcionario_nome,
    )
    db.add(registro)
    db.flush()
    return registro


def prazo_medio_recebimento(db: Session, empresa_id: int, inicio, fim):
    """Quantos dias, em média, o cliente demorou para pagar.

    Média de (recebido_em - criado_em) das cobranças RECEBIDAS no período.

    Escolhi este cálculo, e não o DSO clássico (recebíveis ÷ receita × dias),
    por uma razão só: o dono precisa poder conferir. "Seus clientes demoram 23
    dias para pagar" se prova abrindo três cobranças e contando no calendário;
    o DSO clássico exige acreditar numa fórmula.

    Feito em Python e não em SQL porque diferença de datas muda de dialeto
    (SQLite não tem DATEDIFF), e o volume de um mês cabe na memória sem
    esforço. Se um dia não couber, vira SQL -- não antes.
    """
    linhas = (
        db.query(ContaReceber.criado_em, ContaReceber.recebido_em)
        .filter(
            ContaReceber.empresa_id == empresa_id,
            ContaReceber.status == ContaReceberStatus.RECEBIDA.value,
            ContaReceber.recebido_em.isnot(None),
            ContaReceber.recebido_em >= inicio,
            ContaReceber.recebido_em <= fim,
        )
        .all()
    )
    dias = [
        (recebido - criado).days
        for criado, recebido in linhas
        if criado is not None and recebido is not None
    ]
    if not dias:
        return None
    # Negativo não existe aqui: recebimento lançado com data anterior à criação
    # da cobrança é digitação, e contá-lo puxaria a média para baixo mentindo
    # que a loja recebe rápido.
    dias = [d for d in dias if d >= 0]
    if not dias:
        return None
    return round(sum(dias) / len(dias))
