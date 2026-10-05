# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fabrica/trilho.py
# DESCRIÇÃO: As 10 etapas da OS da fábrica (docs/marcenaria-fabrica-plano.md, §6; F3).
# ---------------------------------------------------------------------------
"""
A tabela da §6 do plano, como DADO: rótulo, status de sempre e o que trava a
saída de cada etapa. Tudo que muda a fase passa por `mudar_fase`, que deriva
o status da OS e grava o log — é o que mantém a lista de OS, o dashboard e os
relatórios funcionando sem saber das etapas.

TRAVA × AVISO (D0b): com `fabrica_travar_etapas` ligado, etapa com pendência
não avança (409). Desligado (o padrão), a pendência vira aviso: avança se
quem avança escrever o motivo, e o log guarda AVISO_IGNORADO.

Três passagens só acontecem por uma ação própria, nunca pelo "Avançar":
enviar a proposta, registrar a resposta do cliente e finalizar a OS — é nelas
que o dinheiro e os itens mudam.

Só ENTREGUE não deriva status aqui: quem põe FINALIZADA é o finalizar de
sempre (pagamento, baixa, livro). Este módulo só acompanha.
"""

from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enum import OrdemServicoStatus
from app.core.tempo import agora_utc
from app.db.crud import empresa as empresa_crud
from app.db.crud.configuracao_os import get_configuracao_os
from app.db.models.fabrica_orcamento import (
    EventoFase,
    FabricaFaseLog,
    FabricaOrcamento,
    SituacaoOrcamento,
)
from app.db.models.ordem_servico import OrdemServico
from app.services.fabrica.modo import Fase

ROTULOS = {
    Fase.MEDICAO: "Medição",
    Fase.ELABORACAO: "Em elaboração",
    Fase.AGUARDANDO_APROVACAO: "Aguardando aprovação",
    Fase.AGUARDANDO_SINAL: "Aguardando sinal",
    Fase.SEPARACAO_COMPRA: "Separação e compra",
    Fase.EM_PRODUCAO: "Em produção",
    Fase.PRONTO_EXPEDICAO: "Pronto para expedição",
    Fase.EM_INSTALACAO: "Em instalação",
    Fase.VISTORIA_FINAL: "Vistoria final",
    Fase.ENTREGUE: "Entregue",
}

STATUS_DA_FASE = {
    Fase.MEDICAO: OrdemServicoStatus.ABERTA,
    Fase.ELABORACAO: OrdemServicoStatus.ABERTA,
    Fase.AGUARDANDO_APROVACAO: OrdemServicoStatus.AGUARDANDO_APROVACAO,
    Fase.AGUARDANDO_SINAL: OrdemServicoStatus.AGUARDANDO_APROVACAO,
    Fase.SEPARACAO_COMPRA: OrdemServicoStatus.AGUARDANDO_PECAS,
    Fase.EM_PRODUCAO: OrdemServicoStatus.EM_ANDAMENTO,
    Fase.PRONTO_EXPEDICAO: OrdemServicoStatus.EM_ANDAMENTO,
    Fase.EM_INSTALACAO: OrdemServicoStatus.EM_ANDAMENTO,
    Fase.VISTORIA_FINAL: OrdemServicoStatus.AGUARDANDO_RETIRADA,
    Fase.ENTREGUE: OrdemServicoStatus.FINALIZADA,
}

# Sair destas etapas é uma ação própria, não o "Avançar".
AVANCO_POR_ACAO = {
    Fase.ELABORACAO: "Envie a proposta ao cliente na aba Orçamento.",
    Fase.AGUARDANDO_APROVACAO: "Registre a resposta do cliente na aba Orçamento.",
    Fase.VISTORIA_FINAL: "Finalize a OS para registrar a entrega.",
}

# Até aqui a OS não compra (RC04): o material está reservado, mas só vira
# necessidade de compra com o sinal pago ou a liberação do gestor.
FASES_SEM_COMPRA = (Fase.MEDICAO, Fase.ELABORACAO, Fase.AGUARDANDO_APROVACAO, Fase.AGUARDANDO_SINAL)


@dataclass(frozen=True)
class Trava:
    codigo: str
    texto: str
    ok: bool


def _reais(centavos: int) -> str:
    """R$ 1.234,56 — o texto da trava vai direto para a tela."""
    texto = f"{centavos / 100:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {texto}"


def _erro(codigo: int, detalhe) -> HTTPException:
    return HTTPException(status_code=codigo, detail=detalhe)


# --- Leitura de estado -------------------------------------------------------------

def travar_etapas(db: Session) -> bool:
    empresa = empresa_crud.get_empresa_atual(db)
    config = get_configuracao_os(db, empresa.id) if empresa else None
    return bool(config and config.fabrica_travar_etapas)


def orcamento_aprovado(db: Session, os_id: int) -> Optional[FabricaOrcamento]:
    return db.scalar(select(FabricaOrcamento).where(
        FabricaOrcamento.os_id == os_id, FabricaOrcamento.situacao == SituacaoOrcamento.APROVADO,
    ))


def sinal_exigido(db: Session, os_: OrdemServico) -> int:
    orc = orcamento_aprovado(db, os_.id)
    if orc is None:
        return 0
    return -(-orc.total * orc.sinal_bp // 10000)


def recebido(os_: OrdemServico) -> int:
    """O dinheiro que a OS já recebeu — a MESMA soma da finalização."""
    return (
        sum(p.valor for p in os_.pagamentos)
        + (os_.adiantamentos_anteriores or 0)
        + (os_.valor_entrada or 0)
    )


def pode_comprar(fase: Optional[str], compra_liberada_em) -> bool:
    """A OS já gera necessidade de compra? (RC04). OS comum: sempre."""
    return fase is None or fase not in FASES_SEM_COMPRA or compra_liberada_em is not None


def _material_no_estoque(db: Session, os_: OrdemServico) -> Trava:
    # A F4 troca isto por "tudo SEPARADO" (bipado). Até lá, a trava é o
    # material existir na prateleira para esta OS, na fila de Compras.
    from app.services.compras.demanda_os import compras_da_os

    painel = compras_da_os(db, os_.id)
    faltando = [i.descricao for i in painel.itens if i.situacao != "NO_ESTOQUE"]
    if not faltando:
        return Trava("MATERIAL", "Todo o material está no estoque", True)
    return Trava("MATERIAL", "Material que ainda não chegou: " + ", ".join(faltando), False)


def travas(db: Session, os_: OrdemServico) -> list[Trava]:
    """O que precisa ser verdade para SAIR da etapa atual."""
    fase = os_.fase_fabrica
    if fase == Fase.MEDICAO:
        return [Trava("FOTO", "Medição registrada com ao menos uma foto", len(os_.fotos) > 0)]
    if fase == Fase.AGUARDANDO_SINAL:
        exigido, pago = sinal_exigido(db, os_), recebido(os_)
        if os_.compra_liberada_em is not None:
            return [Trava("SINAL", "Compra liberada pelo gestor antes do sinal", True)]
        return [Trava("SINAL", f"Sinal recebido: {_reais(pago)} de {_reais(exigido)}", pago >= exigido)]
    if fase == Fase.SEPARACAO_COMPRA:
        return [_material_no_estoque(db, os_)]
    if fase == Fase.PRONTO_EXPEDICAO:
        return [Trava("INSTALACAO", "Data de instalação marcada", os_.data_instalacao is not None)]
    return []


def _proxima(fase: str) -> Optional[str]:
    i = Fase.ORDEM.index(fase)
    return Fase.ORDEM[i + 1] if i + 1 < len(Fase.ORDEM) else None


# --- Escrita --------------------------------------------------------------------------

def registrar(db: Session, os_: OrdemServico, evento: str, usuario: str,
              motivo: Optional[str] = None, anterior: Optional[str] = None, nova: Optional[str] = None) -> None:
    db.add(FabricaFaseLog(
        os_id=os_.id, fase_anterior=anterior if anterior is not None else os_.fase_fabrica,
        fase_nova=nova if nova is not None else os_.fase_fabrica,
        evento=evento, motivo=motivo, usuario=usuario, ocorrido_em=agora_utc(),
    ))


def mudar_fase(db: Session, os_: OrdemServico, nova: str, evento: str, usuario: str,
               motivo: Optional[str] = None) -> None:
    """A ÚNICA porta da mudança de fase: deriva o status e grava o log."""
    anterior = os_.fase_fabrica
    os_.fase_fabrica = nova
    if nova != Fase.ENTREGUE:
        os_.status = STATUS_DA_FASE[nova]
    registrar(db, os_, evento, usuario, motivo, anterior=anterior, nova=nova)
    db.flush()


def _os(db: Session, numero_os: str) -> OrdemServico:
    os_ = db.scalar(select(OrdemServico).where(OrdemServico.numero_os == numero_os))
    if os_ is None:
        raise _erro(status.HTTP_404_NOT_FOUND, "Ordem de Serviço não encontrada")
    if os_.fase_fabrica is None:
        raise _erro(status.HTTP_409_CONFLICT, "Esta OS não está no trilho da fábrica.")
    return os_


def _os_aberta(db: Session, numero_os: str) -> OrdemServico:
    os_ = _os(db, numero_os)
    if os_.status in (OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA):
        raise _erro(status.HTTP_409_CONFLICT, "A OS está finalizada ou cancelada. Reabra para mexer nas etapas.")
    return os_


def avancar(db: Session, numero_os: str, usuario: str, motivo: Optional[str]) -> OrdemServico:
    os_ = _os_aberta(db, numero_os)
    fase = os_.fase_fabrica
    if fase in AVANCO_POR_ACAO:
        raise _erro(status.HTTP_409_CONFLICT, AVANCO_POR_ACAO[fase])
    proxima = _proxima(fase)
    if proxima is None:
        raise _erro(status.HTTP_409_CONFLICT, "Esta é a última etapa.")

    pendentes = [t.texto for t in travas(db, os_) if not t.ok]
    motivo = (motivo or "").strip() or None
    if pendentes:
        if travar_etapas(db):
            raise _erro(status.HTTP_409_CONFLICT, {
                "codigo": "TRAVA_PENDENTE",
                "mensagem": f"Não dá para sair de \"{ROTULOS[fase]}\" ainda.",
                "travas": pendentes,
            })
        if not motivo:
            raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, {
                "codigo": "MOTIVO_OBRIGATORIO",
                "mensagem": "Há pendências nesta etapa. Para avançar mesmo assim, escreva o motivo.",
                "travas": pendentes,
            })
        registrar(db, os_, EventoFase.AVISO_IGNORADO, usuario, motivo + " | " + "; ".join(pendentes))
    mudar_fase(db, os_, proxima, EventoFase.AVANCO, usuario, motivo)
    return os_


def voltar(db: Session, numero_os: str, destino: str, usuario: str, motivo: str) -> OrdemServico:
    os_ = _os_aberta(db, numero_os)
    if destino not in Fase.ORDEM:
        raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, "Etapa desconhecida.")
    if Fase.ORDEM.index(destino) >= Fase.ORDEM.index(os_.fase_fabrica):
        raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, "Para ir adiante, use Avançar.")
    if orcamento_aprovado(db, os_.id) and Fase.ORDEM.index(destino) < Fase.ORDEM.index(Fase.AGUARDANDO_SINAL):
        raise _erro(
            status.HTTP_409_CONFLICT,
            "Com o orçamento aprovado, a OS não volta para antes do sinal. "
            "Para mudar o que o cliente aprovou, faça uma nova versão na aba Orçamento e aprove.",
        )
    mudar_fase(db, os_, destino, EventoFase.RETROCESSO, usuario, motivo.strip())
    return os_


def liberar_compra(db: Session, numero_os: str, usuario: str, motivo: str) -> OrdemServico:
    os_ = _os_aberta(db, numero_os)
    if os_.compra_liberada_em is not None:
        raise _erro(status.HTTP_409_CONFLICT, "A compra desta OS já foi liberada.")
    os_.compra_liberada_em = agora_utc()
    os_.compra_liberada_por = usuario[:100]
    os_.compra_liberada_motivo = motivo.strip()
    registrar(db, os_, EventoFase.LIBERACAO_COMPRA, usuario, motivo.strip())
    db.flush()
    return os_


def definir_instalacao(db: Session, numero_os: str, data) -> OrdemServico:
    os_ = _os_aberta(db, numero_os)
    os_.data_instalacao = data
    db.flush()
    return os_


# --- Ganchos da OS de sempre (services/ordem_servico.py) ----------------------------------

def assert_status_manual(os_: OrdemServico) -> None:
    """Na OS da fábrica o status vem da etapa: trocar à mão desalinharia os dois."""
    if os_.fase_fabrica is not None:
        raise _erro(
            status.HTTP_409_CONFLICT,
            "Nesta OS o status acompanha a etapa da fábrica. Use Avançar/Voltar no trilho.",
        )


def assert_pode_finalizar(db: Session, os_: OrdemServico) -> None:
    if os_.fase_fabrica is None or os_.fase_fabrica == Fase.VISTORIA_FINAL:
        return
    if travar_etapas(db):
        raise _erro(
            status.HTTP_409_CONFLICT,
            f"A OS está em \"{ROTULOS[os_.fase_fabrica]}\". Ela só é entregue depois da vistoria final.",
        )


def ao_finalizar(db: Session, os_: OrdemServico, usuario: str) -> None:
    if os_.fase_fabrica is None:
        return
    motivo = None if os_.fase_fabrica == Fase.VISTORIA_FINAL else "Finalizada antes da vistoria final"
    mudar_fase(db, os_, Fase.ENTREGUE, EventoFase.AVANCO, usuario, motivo)


def ao_cancelar(db: Session, os_: OrdemServico, usuario: str, motivo: Optional[str]) -> None:
    if os_.fase_fabrica is not None:
        registrar(db, os_, EventoFase.CANCELAMENTO, usuario, motivo)


def ao_reabrir(db: Session, os_: OrdemServico, usuario: str) -> None:
    """Reaberta, a OS volta para a etapa em que estava (ENTREGUE volta à vistoria)."""
    if os_.fase_fabrica is None:
        return
    destino = Fase.VISTORIA_FINAL if os_.fase_fabrica == Fase.ENTREGUE else os_.fase_fabrica
    mudar_fase(db, os_, destino, EventoFase.REABERTURA, usuario)


# --- O retrato para a tela -----------------------------------------------------------------

def estado(db: Session, numero_os: str):
    from app.schemas.fabrica import EtapaRead, LogFaseRead, TravaRead, TrilhoRead

    os_ = _os(db, numero_os)
    fase = os_.fase_fabrica
    atual = Fase.ORDEM.index(fase)
    aberta = os_.status not in (OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA)
    proxima = _proxima(fase)
    log = db.scalars(
        select(FabricaFaseLog).where(FabricaFaseLog.os_id == os_.id)
        .order_by(FabricaFaseLog.ocorrido_em.desc(), FabricaFaseLog.id.desc())
    ).all()
    return TrilhoRead(
        numero_os=os_.numero_os,
        fase=fase,
        rotulo=ROTULOS[fase],
        status_os=os_.status.value,
        aberta=aberta,
        travar_etapas=travar_etapas(db),
        etapas=[
            EtapaRead(
                fase=f, rotulo=ROTULOS[f],
                situacao="FEITA" if i < atual else ("ATUAL" if i == atual else "A_FAZER"),
            )
            for i, f in enumerate(Fase.ORDEM)
        ],
        proxima=proxima,
        proxima_rotulo=ROTULOS[proxima] if proxima else None,
        avanco_por_acao=AVANCO_POR_ACAO.get(fase),
        travas=[TravaRead(codigo=t.codigo, texto=t.texto, ok=t.ok) for t in travas(db, os_)] if aberta else [],
        sinal_exigido=sinal_exigido(db, os_),
        recebido=recebido(os_),
        pode_comprar=pode_comprar(fase, os_.compra_liberada_em),
        compra_liberada_em=os_.compra_liberada_em,
        compra_liberada_por=os_.compra_liberada_por,
        compra_liberada_motivo=os_.compra_liberada_motivo,
        data_instalacao=os_.data_instalacao,
        log=[LogFaseRead.model_validate(linha) for linha in log],
    )
