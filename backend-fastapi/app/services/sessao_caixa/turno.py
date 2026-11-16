# ---------------------------------------------------------------------------
# ARQUIVO: services/sessao_caixa/turno.py
# DESCRICAO: Caixa - abrir, suprimento, sangria e fechar o turno.
# ---------------------------------------------------------------------------

from typing import Any, Dict
from sqlalchemy.orm import Session
from app.core.enum import (
    MovimentacaoFinanceiraOrigem,
    MovimentacaoFinanceiraTipo,
    SessaoCaixaStatus,
)
from app.helpers.exceptions import BadRequestException
from app.db.crud import sessao_caixa as caixa_crud
from app.schemas.sessao_caixa import (
    MovimentoCaixaCreate,
    SessaoCaixaAbrir,
    SessaoCaixaFechar,
    SessaoCaixaResumo,
)
from app.services.sessao_caixa.autorizacao import _validar_autorizacao_abertura, _validar_autorizacao_sangria
from app.services.sessao_caixa.consultas import calcular_saldo_esperado_em_especie, montar_resumo
from app.services.sessao_caixa.regras import _exigir_caixa_ligado, _funcionario_do_token, _ids_das_formas_em_especie, _sessao_aberta_obrigatoria


# ===========================================================================
# ABRIR
# ===========================================================================

def abrir_caixa(
    db: Session,
    dados: SessaoCaixaAbrir,
    usuario_token: Dict[str, Any],
) -> SessaoCaixaResumo:
    empresa_id = usuario_token["empresa_id"]
    _exigir_caixa_ligado(db, empresa_id)
    # ANTES de qualquer checagem de ocupacao: recusar por falta de PIN e recusar
    # por terminal ocupado sao respostas diferentes, e a primeira nao pode
    # depender da segunda para acontecer.
    _validar_autorizacao_abertura(db, empresa_id, usuario_token, dados.codigo_gerente)
    funcionario_id = _funcionario_do_token(usuario_token)

    # Um operador, um caixa. É o que permite a finalização da venda descobrir o
    # turno sem receber o HWID no checkout — ninguém está em dois caixas de uma
    # vez.
    if caixa_crud.get_sessao_aberta_do_funcionario(db, funcionario_id):
        raise BadRequestException(
            detail="Você já tem um caixa aberto. Feche-o antes de abrir outro."
        )

    # Uma máquina, um caixa. O banco também garante isso (índice único parcial);
    # a checagem aqui existe para devolver uma mensagem que o operador entenda,
    # em vez do erro cru de constraint.
    if dados.terminal_hwid:
        ocupada = caixa_crud.get_sessao_aberta_do_terminal(db, dados.terminal_hwid)
        if ocupada:
            raise BadRequestException(
                detail="Este terminal já tem um caixa aberto por outro operador. "
                       "Ele precisa ser fechado antes."
            )

    sessao = caixa_crud.criar_sessao(
        db,
        funcionario_id=funcionario_id,
        saldo_inicial=dados.saldo_inicial,
        terminal_hwid=dados.terminal_hwid,
    )

    # O troco inicial é dinheiro que entra na gaveta sem venda por trás — logo,
    # é movimento. Sem registrá-lo, o fechamento acusaria sobra todo dia.
    if dados.saldo_inicial > 0:
        formas_especie = _ids_das_formas_em_especie(db)
        caixa_crud.registrar_movimento(
            db,
            tipo=MovimentacaoFinanceiraTipo.ENTRADA,
            origem=MovimentacaoFinanceiraOrigem.ABERTURA,
            valor=dados.saldo_inicial,
            sessao_caixa_id=sessao.id,
            forma_pagamento_id=formas_especie[0] if formas_especie else None,
            funcionario_id=funcionario_id,
            funcionario_nome=usuario_token.get("nome"),
            motivo="Troco de abertura",
        )

    return montar_resumo(db, sessao, usuario_token)


def registrar_suprimento(
    db: Session,
    dados: MovimentoCaixaCreate,
    usuario_token: Dict[str, Any],
) -> SessaoCaixaResumo:
    empresa_id = usuario_token["empresa_id"]
    _exigir_caixa_ligado(db, empresa_id)
    funcionario_id = _funcionario_do_token(usuario_token)
    sessao = _sessao_aberta_obrigatoria(db, funcionario_id)

    formas_especie = _ids_das_formas_em_especie(db)
    caixa_crud.registrar_movimento(
        db,
        tipo=MovimentacaoFinanceiraTipo.ENTRADA,
        origem=MovimentacaoFinanceiraOrigem.SUPRIMENTO,
        valor=dados.valor,
        sessao_caixa_id=sessao.id,
        forma_pagamento_id=formas_especie[0] if formas_especie else None,
        funcionario_id=funcionario_id,
        funcionario_nome=usuario_token.get("nome"),
        motivo=dados.motivo,
    )
    return montar_resumo(db, sessao, usuario_token)


def registrar_sangria(
    db: Session,
    dados: MovimentoCaixaCreate,
    usuario_token: Dict[str, Any],
) -> SessaoCaixaResumo:
    empresa_id = usuario_token["empresa_id"]
    _exigir_caixa_ligado(db, empresa_id)
    funcionario_id = _funcionario_do_token(usuario_token)
    sessao = _sessao_aberta_obrigatoria(db, funcionario_id)

    _validar_autorizacao_sangria(db, empresa_id, usuario_token, dados.codigo_gerente)

    formas_especie = _ids_das_formas_em_especie(db)
    caixa_crud.registrar_movimento(
        db,
        tipo=MovimentacaoFinanceiraTipo.SAIDA,
        origem=MovimentacaoFinanceiraOrigem.SANGRIA,
        valor=dados.valor,
        sessao_caixa_id=sessao.id,
        forma_pagamento_id=formas_especie[0] if formas_especie else None,
        funcionario_id=funcionario_id,
        funcionario_nome=usuario_token.get("nome"),
        motivo=dados.motivo,
    )
    return montar_resumo(db, sessao, usuario_token)


# ===========================================================================
# FECHAR
# ===========================================================================

def fechar_caixa(
    db: Session,
    dados: SessaoCaixaFechar,
    usuario_token: Dict[str, Any],
) -> SessaoCaixaResumo:
    empresa_id = usuario_token["empresa_id"]
    _exigir_caixa_ligado(db, empresa_id)
    funcionario_id = _funcionario_do_token(usuario_token)
    sessao = _sessao_aberta_obrigatoria(db, funcionario_id)

    esperado = calcular_saldo_esperado_em_especie(db, sessao)

    sessao.saldo_final_esperado = esperado
    sessao.saldo_final_informado = dados.saldo_contado
    sessao.status = SessaoCaixaStatus.FECHADO
    from app.core.tempo import agora_utc
    sessao.data_fechamento = agora_utc()
    db.flush()

    # No fechamento o esperado SEMPRE volta, mesmo no modo cego: cego é não ver
    # ANTES de contar. Esconder depois só impediria o operador de assinar o que
    # ele mesmo conferiu.
    return montar_resumo(db, sessao, usuario_token, ocultar_esperado=False)
