# ---------------------------------------------------------------------------
# ARQUIVO: services/sessao_caixa/consultas.py
# DESCRICAO: Caixa - sessao atual, resumo, historico e saldo esperado em especie.
# ---------------------------------------------------------------------------

from datetime import date
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.core.enum import (
    MovimentacaoFinanceiraOrigem,
    SessaoCaixaStatus,
)
from app.core.depends import is_visao_gerencial
from app.core.tempo import fim_do_dia_utc, inicio_do_dia_utc
from app.helpers.exceptions import BadRequestException, NotFoundException
from app.db.crud import sessao_caixa as caixa_crud
from app.db.models.sessao_caixa import SessaoCaixa
from app.schemas.sessao_caixa import (
    SessaoCaixaHistoricoItem,
    MovimentoCaixaRead,
    SessaoCaixaResumo,
    TotalPorForma,
)
from app.services.sessao_caixa.regras import _config, _ids_das_formas_em_especie, caixa_esta_ligado


# ===========================================================================
# CONSULTA
# ===========================================================================

def get_sessao_atual(
    db: Session,
    usuario_token: Dict[str, Any],
) -> Optional[SessaoCaixaResumo]:
    """O turno aberto deste operador, ou None. Não explode se não houver."""
    empresa_id = usuario_token["empresa_id"]
    if not caixa_esta_ligado(db, empresa_id):
        return None
    funcionario_id = usuario_token.get("funcionario_id")
    if not funcionario_id:
        return None
    sessao = caixa_crud.get_sessao_aberta_do_funcionario(db, funcionario_id)
    if not sessao:
        return None

    config = _config(db, empresa_id)
    ocultar = bool(config and config.fechamento_cego)
    return montar_resumo(db, sessao, usuario_token, ocultar_esperado=ocultar)


def get_resumo_de_sessao(
    db: Session,
    sessao_id: int,
    usuario_token: Dict[str, Any],
) -> SessaoCaixaResumo:
    sessao = caixa_crud.get_sessao_by_id(db, sessao_id)
    if not sessao:
        raise NotFoundException(detail="Sessão de caixa não encontrada")
    # Turno já fechado não tem o que esconder: a conferência acabou.
    ocultar = False
    if sessao.status == SessaoCaixaStatus.ABERTO:
        config = _config(db, usuario_token["empresa_id"])
        ocultar = bool(config and config.fechamento_cego)
    return montar_resumo(db, sessao, usuario_token, ocultar_esperado=ocultar)


def listar_historico(
    db: Session,
    usuario_token: Dict[str, Any],
    inicio: Optional[date] = None,
    fim: Optional[date] = None,
    limit: int = 50,
) -> List[SessaoCaixaHistoricoItem]:
    """O histórico de turnos como o DONO precisa ver.

    Responde as duas perguntas dele: quem fechou faltando dinheiro e quem fechou
    sobrando. As duas saem de `diferenca` — negativa é falta, positiva é sobra —
    e as duas merecem atenção: sobra costuma ser troco não registrado ou venda
    não lançada.

    VISÃO GERENCIAL APENAS. O operador vê o próprio turno pelo PDV; o histórico
    de quem fechou com quanto é do dono. Sem isso, um operador veria a diferença
    dos colegas.
    """
    if not is_visao_gerencial(usuario_token):
        raise BadRequestException(
            detail="Apenas o responsável pela loja pode ver o histórico de caixas"
        )

    dt_inicio = inicio_do_dia_utc(inicio) if inicio else None
    dt_fim = fim_do_dia_utc(fim) if fim else None

    sessoes = caixa_crud.listar_sessoes(
        db,
        empresa_id=usuario_token["empresa_id"],
        inicio=dt_inicio,
        fim=dt_fim,
        limit=limit,
    )

    # Nome do terminal resolvido de uma vez: uma consulta por linha viraria N+1
    # numa lista que o dono abre todo dia.
    #
    # Lido do CADASTRO (`terminais`), não da tabela de presença: o relatório
    # olha para trás, e a máquina que fechou o turno de ontem pode estar
    # desligada agora. Enquanto o nome vinha da presença, a coluna Terminal
    # ficava vazia justamente nos turnos antigos — que são os que o dono abre o
    # relatório para ver.
    from app.db.crud.terminal import estacoes as terminal_crud

    hwids = {s.terminal_hwid for s in sessoes if s.terminal_hwid}
    nomes_terminal: Dict[str, Optional[str]] = terminal_crud.nomes_por_hwid(
        db, sorted(hwids)
    )

    itens: List[SessaoCaixaHistoricoItem] = []
    for sessao in sessoes:
        esperado = sessao.saldo_final_esperado
        contado = sessao.saldo_final_informado
        # Só há diferença depois do fechamento: turno aberto ainda não foi
        # conferido, e mostrar um número ali sugeriria uma quebra que não existe.
        diferenca = None if (esperado is None or contado is None) else int(contado - esperado)

        itens.append(
            SessaoCaixaHistoricoItem(
                sessao_id=sessao.id,
                status=sessao.status,
                funcionario_id=sessao.funcionario_id,
                funcionario_nome=getattr(sessao.funcionario, "nome", None),
                terminal_hwid=sessao.terminal_hwid,
                terminal_nome=nomes_terminal.get(sessao.terminal_hwid or ""),
                data_abertura=sessao.data_abertura,
                data_fechamento=sessao.data_fechamento,
                saldo_inicial=sessao.saldo_inicial,
                saldo_esperado=esperado,
                saldo_contado=contado,
                diferenca=diferenca,
            )
        )
    return itens


# ===========================================================================
# A CONTA DA GAVETA
# ===========================================================================

def calcular_saldo_esperado_em_especie(db: Session, sessao: SessaoCaixa) -> int:
    """Entradas em espécie MENOS saídas em espécie, no turno.

    A abertura e o suprimento já entram como movimento em espécie, então somar
    `saldo_inicial` de novo contaria o troco duas vezes: o que se soma aqui são
    os movimentos, e o saldo inicial já está entre eles.

    Subtrai por TIPO e não pela origem SANGRIA, como fazia antes. O resultado é
    idêntico para os dados de sempre — a sangria é lançada com forma em espécie
    e continua sendo descontada. O que muda é o que ANTES ESCAPAVA: o estorno de
    uma OS reaberta sem pagamento real tira da gaveta dinheiro que nunca entrou,
    e pela regra antiga não era descontado, porque a origem não era SANGRIA.
    Contar por tipo faz qualquer saída futura já nascer na conta certa.
    """
    formas_especie = _ids_das_formas_em_especie(db)
    entradas = caixa_crud.somar_dinheiro_em_especie(db, sessao.id, formas_especie)
    saidas = caixa_crud.somar_saidas_em_especie(db, sessao.id, formas_especie)
    return int(entradas - saidas)


def montar_resumo(
    db: Session,
    sessao: SessaoCaixa,
    usuario_token: Dict[str, Any],
    ocultar_esperado: bool = False,
) -> SessaoCaixaResumo:
    totais = caixa_crud.somar_por_origem(db, sessao.id)
    vendas = totais.get(MovimentacaoFinanceiraOrigem.VENDA.value, 0)
    vendas += totais.get(MovimentacaoFinanceiraOrigem.ORDEM_SERVICO.value, 0)
    vendas += totais.get(MovimentacaoFinanceiraOrigem.RECEBIMENTO.value, 0)
    suprimentos = totais.get(MovimentacaoFinanceiraOrigem.SUPRIMENTO.value, 0)
    sangrias = totais.get(MovimentacaoFinanceiraOrigem.SANGRIA.value, 0)

    esperado = calcular_saldo_esperado_em_especie(db, sessao)
    contado = sessao.saldo_final_informado
    diferenca = None if contado is None else int(contado - esperado)

    por_forma = [
        TotalPorForma(
            forma_pagamento_id=forma_id,
            forma_pagamento_nome=nome,
            total=int(total),
        )
        for forma_id, nome, total in caixa_crud.somar_por_forma_pagamento(db, sessao.id)
    ]

    movimentos = [
        MovimentoCaixaRead.model_validate(m)
        for m in caixa_crud.listar_movimentos_da_sessao(db, sessao.id)
    ]

    # Do cadastro durável, não da presença: o resumo de um turno FECHADO é lido
    # depois, com a máquina possivelmente desligada.
    terminal_nome = None
    if sessao.terminal_hwid:
        from app.db.crud.terminal import estacoes as terminal_crud

        terminal = terminal_crud.get_por_hwid(db, sessao.terminal_hwid)
        terminal_nome = getattr(terminal, "nome", None)

    return SessaoCaixaResumo(
        sessao_id=sessao.id,
        status=sessao.status,
        funcionario_id=sessao.funcionario_id,
        funcionario_nome=getattr(sessao.funcionario, "nome", None),
        terminal_hwid=sessao.terminal_hwid,
        terminal_nome=terminal_nome,
        data_abertura=sessao.data_abertura,
        data_fechamento=sessao.data_fechamento,
        saldo_inicial=sessao.saldo_inicial,
        total_vendas=int(vendas),
        total_suprimentos=int(suprimentos),
        total_sangrias=int(sangrias),
        # No modo cego o operador não vê o esperado ANTES de contar — é o que
        # torna a conferência uma conferência de verdade. `None` diz "oculto";
        # devolver `0` dizia "a gaveta está vazia", que é outra coisa e é falso.
        saldo_esperado_dinheiro=None if ocultar_esperado else esperado,
        saldo_contado=contado,
        diferenca=diferenca,
        por_forma=por_forma,
        movimentos=movimentos,
    )
