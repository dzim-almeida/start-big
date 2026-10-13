# ---------------------------------------------------------------------------
# ARQUIVO: services/sessao_caixa/regras.py
# DESCRICAO: Caixa - a chave do caixa, formas em especie, sessao aberta
#            obrigatoria e a trava de vender com o caixa fechado.
# ---------------------------------------------------------------------------

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.helpers.exceptions import BadRequestException
from app.db.crud.configuracao import vendas as config_vendas_crud
from app.db.crud import sessao_caixa as caixa_crud
from app.db.models.forma_pagamento import FormaPagamento
from app.db.models.sessao_caixa import SessaoCaixa


# Formas que ficam FISICAMENTE na gaveta. Só elas entram na conta do que o
# operador conta na mão — cartão e PIX faturam, mas não estão lá.
# Casadas por nome porque a tabela é catálogo livre: a loja pode renomear ou
# criar as suas, e "Dinheiro" é o nome semeado no startup.
NOMES_DE_ESPECIE = ("dinheiro",)


# ===========================================================================
# HELPERS
# ===========================================================================

def _config(db: Session, empresa_id: int):
    return config_vendas_crud.get_configuracao_vendas(db, empresa_id=empresa_id)


def caixa_esta_ligado(db: Session, empresa_id: int) -> bool:
    """Porta de entrada de tudo. Sem isso, o caixa não existe para a loja."""
    config = _config(db, empresa_id)
    return bool(config and config.controlar_caixa)


def _exigir_caixa_ligado(db: Session, empresa_id: int) -> None:
    if not caixa_esta_ligado(db, empresa_id):
        raise BadRequestException(
            detail="O controle de caixa está desligado nas configurações de vendas"
        )


def _funcionario_do_token(usuario_token: Dict[str, Any]) -> int:
    funcionario_id = usuario_token.get("funcionario_id")
    if not funcionario_id:
        raise BadRequestException(
            detail="Apenas funcionários podem operar o caixa"
        )
    return funcionario_id


def _ids_das_formas_em_especie(db: Session) -> List[int]:
    formas = db.query(FormaPagamento).all()
    return [f.id for f in formas if (f.nome or "").strip().lower() in NOMES_DE_ESPECIE]


# ===========================================================================
# SANGRIA E SUPRIMENTO
# ===========================================================================

def _sessao_aberta_obrigatoria(db: Session, funcionario_id: int) -> SessaoCaixa:
    sessao = caixa_crud.get_sessao_aberta_do_funcionario(db, funcionario_id)
    if not sessao:
        raise BadRequestException(detail="Nenhum caixa aberto para este operador")
    return sessao


def exigir_caixa_aberto_para_vender(
    db: Session,
    funcionario,
    operador_funcionario_id: Optional[int] = None,
) -> None:
    """Bloqueia a finalização quando a loja exige turno aberto.

    As duas chaves são separadas de propósito: `controlar_caixa` registra,
    `exigir_caixa_aberto` obriga. A loja pode querer o registro sem a trava
    enquanto a equipe se acostuma.

    A cobrança é sobre o turno de QUEM RECEBE (mesma razão de
    `registrar_pagamentos_de_venda`): não faz sentido exigir caixa aberto do
    vendedor que só atendeu.
    """
    empresa_id = getattr(funcionario, "empresa_id", None)
    if not empresa_id:
        return
    config = _config(db, empresa_id)
    if not (config and config.controlar_caixa and config.exigir_caixa_aberto):
        return

    candidatos = [operador_funcionario_id, getattr(funcionario, "id", None)]
    if any(
        caixa_crud.get_sessao_aberta_do_funcionario(db, fid)
        for fid in candidatos
        if fid
    ):
        return

    raise BadRequestException(detail="Abra o caixa antes de finalizar vendas")
