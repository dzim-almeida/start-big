# ---------------------------------------------------------------------------
# ARQUIVO: app/services/lava_rapido/patio.py
# DESCRICAO: Patio do lava-rapido: os veiculos do dia por status e o avanco
#            com um clique (docs/lava-rapido/ SPEC-00 U3 e Spec 04A).
#
# So existe para segmento com a capacidade `operacao_patio`. Nada aqui e
# documento novo: cada cartao e uma OS de sempre, e avancar o status passa
# pela MESMA atualizacao da OS (com as travas de sempre: status do segmento,
# trilho da fabrica, OS fechada).
# ---------------------------------------------------------------------------

from datetime import date
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core import segmentos as reg
from app.core.enum import OrdemServicoItemAprovacao, OrdemServicoItemTipo, OrdemServicoStatus
from app.core.tempo import intervalo_utc
from app.db.models.cliente import ClientePF, ClientePJ
from app.db.models.objeto_servico import ObjetoServico
from app.db.models.ordem_servico import OrdemServico
from app.schemas.lava_rapido.patio import CartaoPatio, PatioRead
from app.schemas.ordem_servico import OrdemServicoUpdate
from app.services.lava_rapido.lavadores import lavadores_da_os
from app.services.ordem_servico.atualizacao import update_ordem_servico
from app.services.sistema.segmentos import get_segmento_atual

# A fila do patio: cada clique leva o veiculo uma casa adiante (ou volta uma).
# Finalizar NAO e um passo daqui: e o recebimento, pela tela de pagamento de
# sempre (o botao "Receber" do cartao Pronto).
FLUXO = [
    OrdemServicoStatus.ABERTA,
    OrdemServicoStatus.EM_ANDAMENTO,
    OrdemServicoStatus.AGUARDANDO_RETIRADA,
]
EM_ABERTO = FLUXO


def _exigir_patio(db: Session) -> None:
    if not reg.segmento_tem_capacidade(get_segmento_atual(db), reg.CAP_OPERACAO_PATIO):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Pátio não disponível para este segmento.")


def _nome_do_cliente(cliente) -> Optional[str]:
    if isinstance(cliente, ClientePF):
        return cliente.nome
    if isinstance(cliente, ClientePJ):
        return cliente.razao_social
    return getattr(cliente, "nome", None) or getattr(cliente, "razao_social", None)


def _cartao(db: Session, os_db: OrdemServico) -> CartaoPatio:
    objeto = os_db.objeto
    cliente = objeto.cliente if objeto is not None else None
    dados_os = os_db.dados_adicionais or {}
    dados_objeto = (objeto.dados_adicionais if objeto is not None else None) or {}
    servicos = [
        item.nome for item in os_db.itens
        if item.tipo == OrdemServicoItemTipo.SERVICO
        and item.status_aprovacao != OrdemServicoItemAprovacao.REPROVADO
    ]
    return CartaoPatio(
        numero_os=os_db.numero_os,
        status=getattr(os_db.status, "value", os_db.status),
        tipo_veiculo=dados_os.get("tipo_trabalho"),
        placa=objeto.numero_serie if objeto is not None else None,
        modelo=objeto.modelo if objeto is not None else None,
        marca=(objeto.marca or None) if objeto is not None else None,
        cor=objeto.cor if objeto is not None else None,
        porte=dados_objeto.get("porte"),
        cliente_nome=_nome_do_cliente(cliente) if cliente is not None else None,
        cliente_contato=(cliente.celular or cliente.telefone) if cliente is not None else None,
        servicos=servicos,
        valor_total=os_db.valor_total or 0,
        lavadores=lavadores_da_os(db, os_db.id),
        responsavel=os_db.funcionario.nome if os_db.funcionario is not None else None,
        avarias=list(dados_os.get("avarias") or []),
        entrada=os_db.data_criacao,
        previsao=os_db.data_previsao,
        finalizada_em=os_db.data_finalizacao,
    )


def ler_patio(db: Session, hoje: date) -> PatioRead:
    """Os veiculos do patio: TODAS as OS em aberto (as de hoje e as que ficaram
    de ontem) e as entregues hoje. Ordem de chegada: quem entrou primeiro sai
    primeiro."""
    _exigir_patio(db)
    inicio, fim = intervalo_utc(hoje, hoje)
    consulta = (
        select(OrdemServico)
        .options(
            selectinload(OrdemServico.itens),
            selectinload(OrdemServico.funcionario),
            selectinload(OrdemServico.objeto).selectinload(ObjetoServico.cliente),
        )
        .where(
            OrdemServico.ativo.is_(True),
            or_(
                OrdemServico.status.in_(EM_ABERTO),
                and_(
                    OrdemServico.status == OrdemServicoStatus.FINALIZADA,
                    OrdemServico.data_finalizacao >= inicio,
                    OrdemServico.data_finalizacao <= fim,
                ),
            ),
        )
        .order_by(OrdemServico.data_criacao, OrdemServico.id)
    )
    colunas: Dict[OrdemServicoStatus, List[CartaoPatio]] = {s: [] for s in [*FLUXO, OrdemServicoStatus.FINALIZADA]}
    for os_db in db.scalars(consulta).all():
        colunas[os_db.status].append(_cartao(db, os_db))
    # Entregues: a mais recente primeiro (e o que o atendente procura).
    entregues = sorted(colunas[OrdemServicoStatus.FINALIZADA],
                       key=lambda c: c.finalizada_em or c.entrada, reverse=True)
    return PatioRead(
        aguardando=colunas[OrdemServicoStatus.ABERTA],
        lavando=colunas[OrdemServicoStatus.EM_ANDAMENTO],
        pronto=colunas[OrdemServicoStatus.AGUARDANDO_RETIRADA],
        entregues_hoje=entregues,
    )


def mover(db: Session, numero_os: str, passo: int) -> CartaoPatio:
    """Leva o veiculo uma casa adiante (+1) ou de volta (-1) no fluxo."""
    _exigir_patio(db)
    from app.db.crud.ordem_servico.consultas import get_ordem_servico_by_numero_os

    os_db = get_ordem_servico_by_numero_os(db, numero_os)
    if os_db is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OS não encontrada.")
    if os_db.status not in FLUXO:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail="Esta OS não está no pátio.")
    posicao = FLUXO.index(os_db.status) + passo
    if not 0 <= posicao < len(FLUXO):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Não há próxima etapa: use Receber." if passo > 0 else "Esta OS já está no início.",
        )
    # A atualizacao de sempre: ela confere o status do segmento e as travas.
    os_db = update_ordem_servico(db, numero_os, OrdemServicoUpdate(status=FLUXO[posicao]))
    db.flush()
    return _cartao(db, os_db)
