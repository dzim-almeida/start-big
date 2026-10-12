# ---------------------------------------------------------------------------
# ARQUIVO: app/api/v1/endpoints/marcenaria_separacao.py
# DESCRICAO: API da separacao de material da OS da marcenaria (Spec 10A,
#            secao 6.1). Prefixo: /api/v1/marcenaria
#
# Esta camada so le o token e os parametros e aplica a permissao. A regra
# fica em app/services/marcenaria/separacao.py. Tudo responde 404 fora da
# marcenaria (capacidade `orcamento_tecnico`) e em OS sem orcamento aprovado.
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.endpoints.marcenaria_orcamento import VER, executar
from app.core.depends import check_permission
from app.db.session import get_db
from app.schemas.marcenaria.separacao import ConferenciaEntrada, MovimentoEntrada
from app.services.marcenaria import erros, separacao

router = APIRouter()

# D21: a separacao e uma ABA DA OS, entao vale a permissao de OS de sempre
# ("servico"). Nenhuma chave nova. Master e `all` passam em tudo.
OS = Depends(check_permission(["servico"]))

# Teto de produtos por consulta do disponivel (a busca de insumo pede poucos).
MAXIMO_PRODUTOS = 200


# ===========================================================================
# LEITURA
# ===========================================================================

@router.get("/os/{numero_os}/separacao", summary="Separação de material da OS")
def ler(numero_os: str, usuario_token: dict = OS, db: Session = Depends(get_db)):
    return executar(db, separacao.ler, numero_os)


@router.get("/os/{numero_os}/separacao/ler", summary="Leitor: a linha do código lido (e o fator da embalagem)")
def ler_codigo(
    numero_os: str,
    codigo: str = Query("", max_length=100, description="Código de barras, código do produto ou da embalagem"),
    usuario_token: dict = OS,
    db: Session = Depends(get_db),
):
    return executar(db, separacao.ler_codigo, numero_os, codigo)


@router.get("/os/{numero_os}/separacao/faltas", summary="O que falta comprar para esta OS")
def faltas(numero_os: str, usuario_token: dict = OS, db: Session = Depends(get_db)):
    return executar(db, separacao.faltas, numero_os)


# ===========================================================================
# ACOES (cada uma responde a separacao inteira atualizada)
# ===========================================================================

@router.post("/os/{numero_os}/separacao/{item_id}/retirar", summary="Retirar do estoque para a OS")
def retirar(numero_os: str, item_id: int, dados: MovimentoEntrada,
            usuario_token: dict = OS, db: Session = Depends(get_db)):
    return executar(db, separacao.retirar, numero_os, item_id, dados, usuario_token)


@router.post("/os/{numero_os}/separacao/{item_id}/devolver", summary="Devolver ao estoque (sobra)")
def devolver(numero_os: str, item_id: int, dados: MovimentoEntrada,
             usuario_token: dict = OS, db: Session = Depends(get_db)):
    return executar(db, separacao.devolver, numero_os, item_id, dados, usuario_token)


@router.post("/os/{numero_os}/separacao/{item_id}/concluir", summary="Concluir a linha (usou menos, ou não usou)")
def concluir(numero_os: str, item_id: int, dados: ConferenciaEntrada,
             usuario_token: dict = OS, db: Session = Depends(get_db)):
    return executar(db, separacao.concluir, numero_os, item_id, dados, usuario_token)


@router.post("/os/{numero_os}/separacao/{item_id}/reabrir", summary="Reabrir a linha concluída")
def reabrir(numero_os: str, item_id: int, dados: ConferenciaEntrada,
            usuario_token: dict = OS, db: Session = Depends(get_db)):
    return executar(db, separacao.reabrir, numero_os, item_id, dados, usuario_token)


# ===========================================================================
# DISPONIVEL PARA A BUSCA DE INSUMO DO ORCAMENTO (D19)
# ===========================================================================

def _ids(texto: str) -> list[int]:
    """'1,2,3' -> [1, 2, 3]. Qualquer coisa que nao seja numero vira 422."""
    pedacos = [p.strip() for p in (texto or "").split(",") if p.strip()]
    if not pedacos or not all(p.isdigit() for p in pedacos):
        erros.invalido("Informe os produtos pelos ids, separados por vírgula.")
    if len(pedacos) > MAXIMO_PRODUTOS:
        erros.invalido(f"Consulte no máximo {MAXIMO_PRODUTOS} produtos por vez.")
    return [int(p) for p in pedacos]


@router.get("/estoque/disponivel", summary="Estoque, reservado pelas OS abertas e disponível, por produto")
def disponivel(
    produto_ids: str = Query(..., description="Ids dos produtos separados por vírgula (ex.: 1,2,3)"),
    usuario_token: dict = VER,                     # quem monta o orcamento (D21)
    db: Session = Depends(get_db),
):
    return executar(db, separacao.disponivel, _ids(produto_ids))
