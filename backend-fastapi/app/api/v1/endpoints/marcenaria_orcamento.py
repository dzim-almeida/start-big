# ---------------------------------------------------------------------------
# ARQUIVO: app/api/v1/endpoints/marcenaria_orcamento.py
# DESCRICAO: API do orcamento de marcenaria -- lista, cabecalho, transicoes,
#            versoes, precos e historico (Spec 06A, secao 6.1).
#            Prefixo: /api/v1/marcenaria/orcamentos
#
# Ambientes, moveis, simulacao, arquitetos e anexos ficam em
# marcenaria_orcamento_itens.py (mesmo prefixo; arquivos menores por causa do
# teto de bytecode do PyArmor).
#
# Esta camada so le o token e os parametros e aplica a permissao. A regra fica
# nos servicos (app/services/marcenaria/). As respostas com custo sao
# dicionarios montados la, ja recortados (D23) -- por isso `response_model`
# nao e usado nelas: ele escreveria `null` nas chaves que devem SUMIR.
# ---------------------------------------------------------------------------

from typing import Callable, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.core.depends import check_permission
from app.db.session import get_db
from app.schemas.marcenaria.orcamento import (
    AtualizarPrecosEntrada,
    OrcamentoAtualizar,
    OrcamentoCriar,
    RecusarEntrada,
)
from app.schemas.marcenaria.aprovacao import AprovacaoEntrada, DesfazerEntrada
from app.services.marcenaria import aprovacao, erros, rt
from app.services.marcenaria import orcamento as servico
from app.services.marcenaria.orcamento_comum import exigir_custos
from app.services.marcenaria.permissoes import (
    PERMISSOES_EXCLUIR_ORCAMENTOS,
    PERMISSOES_GERIR_ORCAMENTOS,
    PERMISSOES_VER_ORCAMENTOS,
)

router = APIRouter()

# Dependencias de permissao (D22). Master e `all` passam em tudo.
VER = Depends(check_permission(PERMISSOES_VER_ORCAMENTOS))
GERIR = Depends(check_permission(PERMISSOES_GERIR_ORCAMENTOS))
EXCLUIR = Depends(check_permission(PERMISSOES_EXCLUIR_ORCAMENTOS))

# Toda escrita manda a revisao que a tela tem (trava otimista, D20).
REVISAO = Query(..., ge=1, description="Revisão que a tela tem (D20). Diferente da gravada = 409.")


def executar(db: Session, funcao: Callable, *args, **kwargs):
    """Roda o servico; qualquer erro desfaz o que nao foi gravado (rollback).

    O servico faz o proprio commit no fim da escrita. Se algo falhar antes (o
    motor recusou, revisao antiga, status errado), o rollback aqui garante que
    nada fica pela metade.
    """
    try:
        return funcao(db, *args, **kwargs)
    except StaleDataError:               # outro computador gravou no meio (coluna de versao, D20)
        db.rollback()
        erros.conflito(erros.REVISAO_DESATUALIZADA, erros.MSG_REVISAO)
    except Exception:                    # HTTPException (404, 409, 422...) e erro inesperado
        db.rollback()
        raise                            # o erro segue para o handler de sempre


# ===========================================================================
# ROTAS ESTATICAS (antes de /{orcamento_id})
# ===========================================================================

@router.get("/", summary="Lista de orçamentos de marcenaria")
def listar_orcamentos(
    status_: Optional[str] = Query(None, alias="status"),
    cliente: Optional[int] = Query(None, description="id do cliente"),
    vendedor_id: Optional[int] = None,
    vence_em_dias: Optional[int] = Query(None, ge=0, le=365),
    busca: Optional[str] = None,
    incluir_versoes_antigas: bool = False,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    usuario_token: dict = VER,
    db: Session = Depends(get_db),
):
    """Por padrao, so a versao mais recente de cada codigo (sem SUBSTITUIDO)."""
    filtros = {
        "status": status_,
        "cliente_id": cliente,
        "vendedor_id": vendedor_id,
        "vence_em_dias": vence_em_dias,
        "busca": busca,
        "incluir_versoes_antigas": incluir_versoes_antigas,
    }
    return executar(db, servico.listar, filtros, page, limit, usuario_token)


@router.get("/contagens", summary="Quantos orçamentos por status (chips da lista)")
def contagens(usuario_token: dict = VER, db: Session = Depends(get_db)):
    return executar(db, servico.contagens)


@router.get("/projetos", summary="Projetos (objetos) ativos do cliente")
def projetos(cliente_id: int = Query(...), usuario_token: dict = VER, db: Session = Depends(get_db)):
    return executar(db, servico.projetos_do_cliente, cliente_id)


@router.get("/arquitetos", summary="Arquitetos ativos para o select do orçamento (Spec 09B)")
def arquitetos(usuario_token: dict = VER, db: Session = Depends(get_db)):
    # So id, nome e escritorio: quem monta o orcamento escolhe sem ver PIX e banco.
    return executar(db, rt.arquitetos_para_escolher)


@router.get("/por-os/{numero_os}", summary="O orçamento que gerou a OS (aba Orçamento da OS)")
def por_os(
    numero_os: str,
    # Quem trabalha na OS precisa saber o que foi vendido: vale a permissao de
    # orcamento OU a de OS ("servico"). A resposta nunca traz custo (08A, Revisao 1).
    usuario_token: dict = Depends(check_permission(PERMISSOES_VER_ORCAMENTOS + ["servico"])),
    db: Session = Depends(get_db),
):
    return executar(db, aprovacao.resumo_por_os, numero_os)


# ===========================================================================
# CRIAR, LER, EDITAR O CABECALHO, EXCLUIR
# ===========================================================================

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Criar orçamento (RASCUNHO)")
def criar(
    dados: Optional[OrcamentoCriar] = None,
    usuario_token: dict = GERIR,
    db: Session = Depends(get_db),
):
    """Corpo opcional. Os parametros sao copiados da configuracao (D4)."""
    novo_id = executar(db, servico.criar_orcamento, dados or OrcamentoCriar(), usuario_token)
    return executar(db, servico.detalhe, novo_id, usuario_token)


@router.get("/{orcamento_id}", summary="Detalhe com o cálculo")
def detalhe(orcamento_id: int, usuario_token: dict = VER, db: Session = Depends(get_db)):
    return executar(db, servico.detalhe, orcamento_id, usuario_token)


@router.patch("/{orcamento_id}", summary="Editar o cabeçalho")
def atualizar(
    orcamento_id: int,
    dados: OrcamentoAtualizar,
    revisao: int = REVISAO,
    usuario_token: dict = GERIR,
    db: Session = Depends(get_db),
):
    executar(db, servico.atualizar_cabecalho, orcamento_id, revisao, dados, usuario_token)
    return executar(db, servico.detalhe, orcamento_id, usuario_token)


@router.delete("/{orcamento_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir rascunho nunca enviado")
def excluir(
    orcamento_id: int,
    revisao: int = REVISAO,
    usuario_token: dict = EXCLUIR,
    db: Session = Depends(get_db),
):
    executar(db, servico.excluir, orcamento_id, revisao, usuario_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ===========================================================================
# TRANSICOES (D12-D17) E NOVA VERSAO (D16)
# ===========================================================================

@router.post("/{orcamento_id}/enviar", summary="RASCUNHO → ENVIADO")
def enviar(orcamento_id: int, revisao: int = REVISAO, usuario_token: dict = GERIR, db: Session = Depends(get_db)):
    executar(db, servico.enviar, orcamento_id, revisao, usuario_token)
    return executar(db, servico.detalhe, orcamento_id, usuario_token)


@router.post("/{orcamento_id}/voltar-a-editar", summary="ENVIADO → RASCUNHO")
def voltar_a_editar(
    orcamento_id: int, revisao: int = REVISAO, usuario_token: dict = GERIR, db: Session = Depends(get_db),
):
    executar(db, servico.voltar_a_editar, orcamento_id, revisao, usuario_token)
    return executar(db, servico.detalhe, orcamento_id, usuario_token)


@router.post("/{orcamento_id}/recusar", summary="ENVIADO/VENCIDO → RECUSADO")
def recusar(
    orcamento_id: int,
    dados: RecusarEntrada,
    revisao: int = REVISAO,
    usuario_token: dict = GERIR,
    db: Session = Depends(get_db),
):
    executar(db, servico.recusar, orcamento_id, revisao, dados.motivo, usuario_token)
    return executar(db, servico.detalhe, orcamento_id, usuario_token)


@router.post("/{orcamento_id}/renovar", summary="VENCIDO → RASCUNHO")
def renovar(orcamento_id: int, revisao: int = REVISAO, usuario_token: dict = GERIR, db: Session = Depends(get_db)):
    executar(db, servico.renovar, orcamento_id, revisao, usuario_token)
    return executar(db, servico.detalhe, orcamento_id, usuario_token)


@router.post("/{orcamento_id}/nova-versao", status_code=status.HTTP_201_CREATED, summary="Nova versão")
def nova_versao(
    orcamento_id: int, revisao: int = REVISAO, usuario_token: dict = GERIR, db: Session = Depends(get_db),
):
    """Responde o detalhe da versao NOVA."""
    novo_id = executar(db, servico.nova_versao, orcamento_id, revisao, usuario_token)
    return executar(db, servico.detalhe, novo_id, usuario_token)


@router.get("/{orcamento_id}/versoes", summary="Todas as versões do mesmo código")
def versoes(orcamento_id: int, usuario_token: dict = VER, db: Session = Depends(get_db)):
    return executar(db, servico.versoes, orcamento_id)


# ===========================================================================
# APROVACAO (Spec 08A): cria a OS; desfazer cancela a OS
# ===========================================================================

@router.post("/{orcamento_id}/aprovacao/simular", summary="Números do que seria aprovado (não grava)")
def simular_aprovacao(
    orcamento_id: int, dados: AprovacaoEntrada, usuario_token: dict = GERIR, db: Session = Depends(get_db),
):
    return executar(db, aprovacao.simular, orcamento_id, dados, usuario_token)


@router.post("/{orcamento_id}/aprovar", summary="Aprovar (todo ou em parte) e criar a OS")
def aprovar(
    orcamento_id: int,
    dados: AprovacaoEntrada,
    revisao: int = REVISAO,
    usuario_token: dict = GERIR,
    db: Session = Depends(get_db),
):
    executar(db, aprovacao.aprovar, orcamento_id, revisao, dados, usuario_token)
    return executar(db, servico.detalhe, orcamento_id, usuario_token)


@router.post("/{orcamento_id}/desfazer-aprovacao", summary="Desfazer a aprovação (cancela a OS)")
def desfazer_aprovacao(
    orcamento_id: int,
    dados: DesfazerEntrada,
    revisao: int = REVISAO,
    usuario_token: dict = GERIR,
    db: Session = Depends(get_db),
):
    executar(db, aprovacao.desfazer_aprovacao, orcamento_id, revisao, dados, usuario_token)
    return executar(db, servico.detalhe, orcamento_id, usuario_token)


# ===========================================================================
# PRECOS (secao 6.5) -- custos: exigem tambem view_custos_marcenaria
# ===========================================================================

@router.get("/{orcamento_id}/precos-desatualizados", summary="Insumos com preço diferente do produto hoje")
def precos_desatualizados(orcamento_id: int, usuario_token: dict = VER, db: Session = Depends(get_db)):
    exigir_custos(usuario_token)
    return executar(db, servico.precos_desatualizados, orcamento_id)


@router.post("/{orcamento_id}/atualizar-precos", summary="Aplicar os preços de hoje")
def atualizar_precos(
    orcamento_id: int,
    dados: AtualizarPrecosEntrada,
    revisao: int = REVISAO,
    usuario_token: dict = GERIR,
    db: Session = Depends(get_db),
):
    exigir_custos(usuario_token)
    executar(db, servico.atualizar_precos, orcamento_id, revisao, dados, usuario_token)
    return executar(db, servico.detalhe, orcamento_id, usuario_token)


# ===========================================================================
# HISTORICO (D25)
# ===========================================================================

@router.get("/{orcamento_id}/historico", summary="Histórico de todas as versões do código")
def historico(orcamento_id: int, usuario_token: dict = VER, db: Session = Depends(get_db)):
    return executar(db, servico.historico, orcamento_id)
