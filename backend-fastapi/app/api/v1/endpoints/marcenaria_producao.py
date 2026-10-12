# ---------------------------------------------------------------------------
# ARQUIVO: app/api/v1/endpoints/marcenaria_producao.py
# DESCRICAO: API da producao da OS da marcenaria (Spec 12A, secao 6).
#            Prefixo: /api/v1/marcenaria
#
# Esta camada so le o token e os parametros e aplica a permissao. A regra
# fica em app/services/marcenaria/producao.py. Tudo responde 404 fora da
# marcenaria e em OS sem orcamento aprovado. Toda escrita devolve a producao
# atualizada com `sugestao_status` (o backend nunca muda o status da OS).
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.endpoints.marcenaria_orcamento import executar
from app.core.depends import check_permission
from app.db.session import get_db
from app.schemas.marcenaria.producao import ConcluirEmTodosEntrada, EtapasDoMovelEntrada, LoteEntrada
from app.services.marcenaria import producao

router = APIRouter()

# D19: a producao e uma ABA DA OS, entao vale a permissao de OS ("servico").
OS = Depends(check_permission(["servico"]))


@router.get("/os/{numero_os}/producao", summary="Produção da OS: etapas por móvel e progresso")
def ler(numero_os: str, usuario_token: dict = OS, db: Session = Depends(get_db)):
    return executar(db, producao.ler, numero_os)


@router.post("/os/{numero_os}/producao/etapas/iniciar", summary="Iniciar etapas (em lote)")
def iniciar(numero_os: str, dados: LoteEntrada, usuario_token: dict = OS, db: Session = Depends(get_db)):
    return executar(db, producao.iniciar, numero_os, dados, usuario_token)


@router.post("/os/{numero_os}/producao/etapas/concluir", summary="Concluir etapas (em lote)")
def concluir(numero_os: str, dados: LoteEntrada, usuario_token: dict = OS, db: Session = Depends(get_db)):
    return executar(db, producao.concluir, numero_os, dados, usuario_token)


@router.post("/os/{numero_os}/producao/etapas/concluir-em-todos", summary="Concluir uma etapa em todos os móveis")
def concluir_em_todos(numero_os: str, dados: ConcluirEmTodosEntrada, usuario_token: dict = OS,
                      db: Session = Depends(get_db)):
    return executar(db, producao.concluir_em_todos, numero_os, dados.nome, usuario_token)


@router.post("/os/{numero_os}/producao/etapas/{etapa_id}/reabrir", summary="Reabrir uma etapa")
def reabrir(numero_os: str, etapa_id: int, usuario_token: dict = OS, db: Session = Depends(get_db)):
    return executar(db, producao.reabrir, numero_os, etapa_id, usuario_token)


@router.put("/os/{numero_os}/producao/moveis/{movel_id}/etapas", summary="Editar a lista de etapas do móvel")
def editar_etapas(numero_os: str, movel_id: int, dados: EtapasDoMovelEntrada, usuario_token: dict = OS,
                  db: Session = Depends(get_db)):
    return executar(db, producao.editar_etapas, numero_os, movel_id, dados, usuario_token)


@router.post("/os/{numero_os}/producao/moveis/{movel_id}/aplicar-padrao", summary="Dar ao móvel as etapas padrão")
def aplicar_padrao(numero_os: str, movel_id: int, usuario_token: dict = OS, db: Session = Depends(get_db)):
    return executar(db, producao.aplicar_padrao, numero_os, movel_id, usuario_token)


@router.get("/producao", summary="Quadro da fábrica: as OS abertas em produção")
def quadro(usuario_token: dict = OS, db: Session = Depends(get_db)):
    return executar(db, producao.quadro)
