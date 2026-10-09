# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/orcamento_comum.py
# DESCRICAO: Pecas usadas por todos os servicos do orcamento de marcenaria
#            (Spec 06A): capacidade, carregar, trava de revisao, status,
#            historico, vencimento preguicoso e o fecho de toda escrita.
# ---------------------------------------------------------------------------
"""
Toda ESCRITA no orcamento segue o mesmo roteiro (secao 7.2):

    carregar -> conferir revisao (D20) -> conferir status (D11) -> mudar ->
    rodar o motor -> atualizar o resumo (D5) -> revisao + 1 -> commit

Se o motor recusar (ex.: desconto maior que o novo total), sai um 422 e o
endpoint desfaz tudo (rollback): nada fica gravado pela metade.
"""

from typing import Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.core import segmentos as reg
from app.core.tempo import hoje_local
from app.db.crud.marcenaria import evento as crud_evento
from app.db.crud.marcenaria import orcamento as crud
from app.db.models.marcenaria.orcamento import MarcenariaOrcamento, StatusOrcamento
from app.services.marcenaria import erros
from app.services.marcenaria.calculo import OrcamentoResultado
from app.services.marcenaria.orcamento_calculo import atualizar_resumo, calcular_orcamento_do_banco
from app.services.marcenaria.permissoes import pode_ver_custos_marcenaria
from app.services.segmentos import get_segmento_atual

USUARIO_SISTEMA = "Sistema"     # quem assina o vencimento automatico (D14)


# ===========================================================================
# CAPACIDADE E USUARIO
# ===========================================================================

def exigir_orcamento_tecnico(db: Session) -> None:
    """404 fora de segmento com `orcamento_tecnico` (D26): para os outros, nada existe.

    Le a CAPACIDADE no registry, nunca o nome do segmento.
    """
    if not reg.segmento_tem_capacidade(get_segmento_atual(db), reg.CAP_ORCAMENTO_TECNICO):
        erros.nao_encontrado()


def usuario_id(usuario_token: dict) -> Optional[int]:
    """O id do usuario logado (o `sub` do token), ou None."""
    sub = usuario_token.get("sub")
    return int(sub) if sub is not None and str(sub).isdigit() else None


def usuario_nome(usuario_token: dict) -> str:
    """O nome do usuario logado, copiado no historico."""
    return usuario_token.get("nome") or "Usuário"


# ===========================================================================
# HISTORICO (D25)
# ===========================================================================

def registrar_evento(
    db: Session,
    orc: Optional[MarcenariaOrcamento],
    tipo: str,
    descricao: str,
    usuario_token: Optional[dict],
    dados: Optional[dict[str, Any]] = None,
    os_id: Optional[int] = None,
) -> None:
    """Inclui um evento no historico (sem commit: vai junto com a acao).

    `usuario_token=None` = acao do sistema (vencimento). `os_id` liga o evento
    a OS (aprovacao e desfazer, Spec 08A D23): a OS conta a mesma historia.
    """
    crud_evento.inserir_evento(
        db,
        orcamento_id=orc.id if orc is not None else None,
        os_id=os_id,
        tipo=tipo,
        descricao=descricao,
        dados=dados,
        usuario_id=usuario_id(usuario_token) if usuario_token else None,
        usuario_nome=usuario_nome(usuario_token) if usuario_token else USUARIO_SISTEMA,
    )


# ===========================================================================
# VENCIMENTO PREGUICOSO (D14, secao 7.4)
# ===========================================================================

def marcar_vencidos(db: Session) -> None:
    """ENVIADO com validade no passado vira VENCIDO, com evento do "Sistema".

    Chamado antes de toda leitura e escrita: ninguem ve um orcamento vencido
    marcado como enviado. NAO soma na `revisao` (nao e edicao de quem esta
    com a tela aberta).
    """
    vencidos = crud.listar_enviados_vencidos(db, hoje_local())    # data no fuso da loja
    for orc in vencidos:
        orc.status = StatusOrcamento.VENCIDO
        registrar_evento(
            db, orc, "ORCAMENTO_VENCIDO",
            f"Validade terminou em {orc.data_validade:%d/%m/%Y}.",
            None,
            {"data_validade": orc.data_validade.isoformat()},
        )
    if vencidos:
        try:
            db.commit()
        except StaleDataError:                      # outro computador gravou no meio: a proxima leitura vence
            db.rollback()


# ===========================================================================
# CARREGAR E CONFERIR
# ===========================================================================

def carregar(db: Session, orcamento_id: int) -> MarcenariaOrcamento:
    """Capacidade (D26) + vencimento (D14) + o orcamento com a arvore, ou 404."""
    exigir_orcamento_tecnico(db)
    marcar_vencidos(db)
    orc = crud.get_orcamento(db, orcamento_id)
    if orc is None:
        erros.nao_encontrado()
    return orc


def conferir_revisao(orc: MarcenariaOrcamento, revisao: int) -> None:
    """Trava otimista (D20): a revisao da tela tem de ser a gravada."""
    if revisao != orc.revisao:
        erros.conflito(erros.REVISAO_DESATUALIZADA, erros.MSG_REVISAO)


def exigir_rascunho(orc: MarcenariaOrcamento) -> None:
    """So RASCUNHO e editavel (D11)."""
    if orc.status != StatusOrcamento.RASCUNHO:
        erros.conflito(erros.STATUS_NAO_EDITAVEL, erros.MSG_NAO_EDITAVEL)


def carregar_para_editar(db: Session, orcamento_id: int, revisao: int) -> MarcenariaOrcamento:
    """Carrega e confere revisao (primeiro) e status (depois). Para edicoes."""
    orc = carregar(db, orcamento_id)
    conferir_revisao(orc, revisao)
    exigir_rascunho(orc)
    return orc


def exigir_custos(usuario_token: dict) -> None:
    """403 para escrita de campo de custo sem `view_custos_marcenaria` (D24)."""
    if not pode_ver_custos_marcenaria(usuario_token):
        erros.sem_permissao("view_custos_marcenaria")


# ===========================================================================
# FECHO DE TODA ESCRITA
# ===========================================================================

def fechar_escrita(db: Session, orc: MarcenariaOrcamento, somar_revisao: bool = True) -> OrcamentoResultado:
    """Motor -> resumo (D5) -> revisao + 1 (D20) -> commit.

    O `flush` manda as mudancas para o banco antes de recalcular, para o
    motor ver a arvore como ficou (moveis novos, removidos, trocados de
    ambiente). Se o motor recusar, sai 422 ANTES do commit.

    Trava (D20), em duas camadas: a coluna de versao do model pega quem
    gravou o CABECALHO no meio; a conferencia depois da releitura pega quem
    gravou enquanto esta escrita so mexia nos ambientes e moveis. Depois do
    primeiro flush, o SQLite nao deixa outra conexao gravar ate o commit.
    """
    revisao_lida = orc.revisao                      # a que foi conferida no comeco
    db.flush()                                      # daqui ate o commit, so este computador grava
    db.expire_all()                                 # esquece o que esta em memoria: rele do banco
    if orc.revisao != revisao_lida:                 # outro computador gravou entre a leitura e o flush
        erros.conflito(erros.REVISAO_DESATUALIZADA, erros.MSG_REVISAO)
    resultado = calcular_orcamento_do_banco(orc)    # 422 CALCULO_INVALIDO se nao fechar
    atualizar_resumo(orc, resultado)
    if somar_revisao:
        orc.revisao += 1
    db.commit()
    return resultado
