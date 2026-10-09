# ---------------------------------------------------------------------------
# ARQUIVO: app/api/v1/endpoints/marcenaria_orcamento_itens.py
# DESCRICAO: API do orcamento de marcenaria -- arquitetos, ambientes, moveis,
#            simulacao e anexos (Spec 06A, secao 6.1).
#            Prefixo: /api/v1/marcenaria/orcamentos (o mesmo do arquivo irmao,
#            marcenaria_orcamento.py; separados so pelo tamanho).
# ---------------------------------------------------------------------------

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.marcenaria_orcamento import GERIR, REVISAO, VER, executar
from app.db.session import get_db
from app.schemas.marcenaria.orcamento import (
    AmbienteEntrada,
    ArquitetosEntrada,
    LegendaEntrada,
    MovelEntrada,
    OrdemEntrada,
    SimularEntrada,
)
from app.services.marcenaria import orcamento as servico
from app.services.marcenaria import orcamento_anexos as anexos
from app.services.marcenaria import orcamento_arvore as arvore

router = APIRouter()


# ===========================================================================
# ARQUITETOS (RT) -- Revisao 3
# ===========================================================================

@router.put("/{orcamento_id}/rt", summary="Substituir a lista de arquitetos")
def substituir_arquitetos(
    orcamento_id: int,
    dados: ArquitetosEntrada,
    revisao: int = REVISAO,
    usuario_token: dict = GERIR,
    db: Session = Depends(get_db),
):
    """`manage` troca QUEM e o arquiteto; enviar `rt_bp` exige view_custos (403)."""
    executar(db, servico.substituir_arquitetos, orcamento_id, revisao, dados, usuario_token)
    return executar(db, servico.detalhe, orcamento_id, usuario_token)


# ===========================================================================
# AMBIENTES
# ===========================================================================

@router.post("/{orcamento_id}/ambientes", status_code=status.HTTP_201_CREATED, summary="Incluir ambiente")
def criar_ambiente(
    orcamento_id: int, dados: AmbienteEntrada, revisao: int = REVISAO,
    usuario_token: dict = GERIR, db: Session = Depends(get_db),
):
    executar(db, arvore.criar_ambiente, orcamento_id, revisao, dados)
    return executar(db, servico.detalhe, orcamento_id, usuario_token)


# `ordem` antes de `{ambiente_id}`: rota fixa primeiro.
@router.put("/{orcamento_id}/ambientes/ordem", summary="Reordenar ambientes")
def ordenar_ambientes(
    orcamento_id: int, dados: OrdemEntrada, revisao: int = REVISAO,
    usuario_token: dict = GERIR, db: Session = Depends(get_db),
):
    executar(db, arvore.ordenar_ambientes, orcamento_id, revisao, dados)
    return executar(db, servico.detalhe, orcamento_id, usuario_token)


@router.patch("/{orcamento_id}/ambientes/{ambiente_id}", summary="Renomear ambiente")
def renomear_ambiente(
    orcamento_id: int, ambiente_id: int, dados: AmbienteEntrada, revisao: int = REVISAO,
    usuario_token: dict = GERIR, db: Session = Depends(get_db),
):
    executar(db, arvore.renomear_ambiente, orcamento_id, ambiente_id, revisao, dados)
    return executar(db, servico.detalhe, orcamento_id, usuario_token)


@router.delete("/{orcamento_id}/ambientes/{ambiente_id}", summary="Remover ambiente (com os móveis)")
def remover_ambiente(
    orcamento_id: int, ambiente_id: int, revisao: int = REVISAO,
    usuario_token: dict = GERIR, db: Session = Depends(get_db),
):
    executar(db, arvore.remover_ambiente, orcamento_id, ambiente_id, revisao)
    return executar(db, servico.detalhe, orcamento_id, usuario_token)


@router.put("/{orcamento_id}/ambientes/{ambiente_id}/moveis/ordem", summary="Reordenar móveis do ambiente")
def ordenar_moveis(
    orcamento_id: int, ambiente_id: int, dados: OrdemEntrada, revisao: int = REVISAO,
    usuario_token: dict = GERIR, db: Session = Depends(get_db),
):
    executar(db, arvore.ordenar_moveis, orcamento_id, ambiente_id, revisao, dados)
    return executar(db, servico.detalhe, orcamento_id, usuario_token)


# ===========================================================================
# MOVEIS
# ===========================================================================

@router.post("/{orcamento_id}/ambientes/{ambiente_id}/moveis", status_code=status.HTTP_201_CREATED,
             summary="Incluir móvel (com insumos)")
def criar_movel(
    orcamento_id: int, ambiente_id: int, dados: MovelEntrada, revisao: int = REVISAO,
    usuario_token: dict = GERIR, db: Session = Depends(get_db),
):
    executar(db, arvore.criar_movel, orcamento_id, ambiente_id, revisao, dados, usuario_token)
    return executar(db, servico.detalhe, orcamento_id, usuario_token)


# `simular` antes de `{movel_id}`: rota fixa primeiro. Nao grava: sem revisao.
@router.post("/{orcamento_id}/moveis/simular", summary="Calcular um móvel sem gravar")
def simular_movel(
    orcamento_id: int, dados: SimularEntrada, usuario_token: dict = GERIR, db: Session = Depends(get_db),
):
    return executar(db, arvore.simular_movel, orcamento_id, dados, usuario_token)


@router.put("/{orcamento_id}/moveis/{movel_id}", summary="Salvar móvel completo")
def atualizar_movel(
    orcamento_id: int, movel_id: int, dados: MovelEntrada, revisao: int = REVISAO,
    usuario_token: dict = GERIR, db: Session = Depends(get_db),
):
    executar(db, arvore.atualizar_movel, orcamento_id, movel_id, revisao, dados, usuario_token)
    return executar(db, servico.detalhe, orcamento_id, usuario_token)


@router.delete("/{orcamento_id}/moveis/{movel_id}", summary="Remover móvel")
def remover_movel(
    orcamento_id: int, movel_id: int, revisao: int = REVISAO,
    usuario_token: dict = GERIR, db: Session = Depends(get_db),
):
    executar(db, arvore.remover_movel, orcamento_id, movel_id, revisao)
    return executar(db, servico.detalhe, orcamento_id, usuario_token)


@router.post("/{orcamento_id}/moveis/{movel_id}/duplicar", status_code=status.HTTP_201_CREATED,
             summary="Duplicar móvel (cópia logo abaixo)")
def duplicar_movel(
    orcamento_id: int, movel_id: int, revisao: int = REVISAO,
    usuario_token: dict = GERIR, db: Session = Depends(get_db),
):
    executar(db, arvore.duplicar_movel, orcamento_id, movel_id, revisao)
    return executar(db, servico.detalhe, orcamento_id, usuario_token)


# ===========================================================================
# ANEXOS (D27-D31): sem revisao (nao somam nela)
# ===========================================================================

@router.get("/{orcamento_id}/anexos", summary="Anexos da medição (todas as versões)")
def listar_anexos(orcamento_id: int, usuario_token: dict = VER, db: Session = Depends(get_db)):
    return executar(db, anexos.listar, orcamento_id)


@router.post("/{orcamento_id}/anexos", status_code=status.HTTP_201_CREATED, summary="Incluir foto ou PDF")
def incluir_anexo(
    orcamento_id: int,
    arquivo: UploadFile = File(...),
    legenda: Optional[str] = Form(None),
    usuario_token: dict = GERIR,
    db: Session = Depends(get_db),
):
    return executar(db, anexos.incluir, orcamento_id, arquivo, legenda, usuario_token)


@router.patch("/{orcamento_id}/anexos/{anexo_id}", summary="Mudar a legenda do anexo")
def alterar_legenda(
    orcamento_id: int, anexo_id: int, dados: LegendaEntrada,
    usuario_token: dict = GERIR, db: Session = Depends(get_db),
):
    return executar(db, anexos.alterar_legenda, orcamento_id, anexo_id, dados.legenda)


@router.delete("/{orcamento_id}/anexos/{anexo_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Remover anexo (de todas as versões)")
def remover_anexo(
    orcamento_id: int, anexo_id: int, usuario_token: dict = GERIR, db: Session = Depends(get_db),
):
    executar(db, anexos.remover, orcamento_id, anexo_id, usuario_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
