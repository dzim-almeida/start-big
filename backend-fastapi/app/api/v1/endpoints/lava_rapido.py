# ---------------------------------------------------------------------------
# ARQUIVO: app/api/v1/endpoints/lava_rapido.py
# DESCRICAO: API do segmento lava-rapido (docs/lava-rapido/). Prefixo:
#            /api/v1/lava-rapido
#
# Esta camada so le o token e os parametros e aplica as permissoes. A regra
# fica em app/services/lava_rapido/. Tudo responde 404 fora do segmento com a
# capacidade correspondente (`preco_por_porte`, `executores_os`,
# `operacao_patio`).
# ---------------------------------------------------------------------------

from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.core.depends import _handle_db_transaction, check_permission
from app.db.session import get_db
from app.schemas.lava_rapido.porte import (
    PorteCreate,
    PorteRead,
    PorteUpdate,
    PrecoPorteRead,
    PrecosServicoUpdate,
    ServicoDoPorte,
)
from app.core.tempo import hoje_local
from app.schemas.lava_rapido.lavador import LavadoresUpdate, LavadorRead
from app.schemas.lava_rapido.patio import CartaoPatio, PatioRead
from app.services.lava_rapido import lavadores, patio, portes

router = APIRouter()

# Portes e precos sao parte do cadastro de servico; lavadores, da OS. As duas
# telas usam a permissao "servico".
SERVICO = Depends(check_permission(required_permission="servico"))


# ===========================================================================
# PORTES (Spec 02A)
# ===========================================================================

@router.get("/portes", response_model=List[PorteRead], summary="Portes da loja")
def listar_portes(
    tipo_veiculo: Optional[str] = Query(None, max_length=30, description="carro, moto, pesado..."),
    incluir_inativos: bool = Query(False),
    usuario_token: dict = SERVICO,
    db: Session = Depends(get_db),
):
    # Transacao: a primeira leitura grava a lista inicial (P2a).
    return _handle_db_transaction(db, portes.listar_portes, tipo_veiculo, incluir_inativos)


@router.post("/portes", response_model=PorteRead, status_code=status.HTTP_201_CREATED,
             summary="Novo porte")
def criar_porte(dados: PorteCreate, usuario_token: dict = SERVICO, db: Session = Depends(get_db)):
    return _handle_db_transaction(db, portes.criar_porte, dados)


@router.put("/portes/{porte_id}", response_model=PorteRead,
            summary="Renomear, reordenar ou desativar um porte")
def atualizar_porte(dados: PorteUpdate, porte_id: int = Path(..., gt=0),
                    usuario_token: dict = SERVICO, db: Session = Depends(get_db)):
    return _handle_db_transaction(db, portes.atualizar_porte, porte_id, dados)


@router.get("/portes/{porte_id}/servicos", response_model=List[ServicoDoPorte],
            summary="Serviços ativos com o preço deste porte (comanda)")
def servicos_do_porte(porte_id: int = Path(..., gt=0), usuario_token: dict = SERVICO,
                      db: Session = Depends(get_db)):
    return portes.servicos_do_porte(db, porte_id)


# ===========================================================================
# PRECO DO SERVICO POR PORTE (Spec 02A)
# ===========================================================================

@router.get("/servicos/{servico_id}/precos", response_model=List[PrecoPorteRead],
            summary="Tabela de preços por porte de um serviço")
def listar_precos(servico_id: int = Path(..., gt=0), usuario_token: dict = SERVICO,
                  db: Session = Depends(get_db)):
    return portes.listar_precos_do_servico(db, servico_id)


@router.put("/servicos/{servico_id}/precos", response_model=List[PrecoPorteRead],
            summary="Gravar a tabela de preços por porte de um serviço (inteira)")
def salvar_precos(dados: PrecosServicoUpdate, servico_id: int = Path(..., gt=0),
                  usuario_token: dict = SERVICO, db: Session = Depends(get_db)):
    return _handle_db_transaction(db, portes.salvar_precos_do_servico, servico_id, dados)


# ===========================================================================
# LAVADORES DA OS (Spec 10A)
# ===========================================================================

@router.get("/os/{numero_os}/lavadores", response_model=List[LavadorRead],
            summary="Lavadores da OS")
def listar_lavadores(numero_os: str, usuario_token: dict = SERVICO, db: Session = Depends(get_db)):
    return lavadores.listar(db, numero_os)


@router.put("/os/{numero_os}/lavadores", response_model=List[LavadorRead],
            summary="Trocar os lavadores da OS (lista inteira)")
def definir_lavadores(numero_os: str, dados: LavadoresUpdate, usuario_token: dict = SERVICO,
                      db: Session = Depends(get_db)):
    return _handle_db_transaction(db, lavadores.definir, numero_os, dados.funcionario_ids)


# ===========================================================================
# PATIO (Spec 04A)
# ===========================================================================

@router.get("/patio", response_model=PatioRead, summary="Veículos do pátio por coluna")
def ler_patio(usuario_token: dict = SERVICO, db: Session = Depends(get_db)):
    return patio.ler_patio(db, hoje_local())


@router.post("/os/{numero_os}/avancar", response_model=CartaoPatio,
             summary="Levar o veículo para a próxima coluna do pátio")
def avancar(numero_os: str, usuario_token: dict = SERVICO, db: Session = Depends(get_db)):
    return _handle_db_transaction(db, patio.mover, numero_os, 1)


@router.post("/os/{numero_os}/voltar", response_model=CartaoPatio,
             summary="Devolver o veículo para a coluna anterior (engano)")
def voltar(numero_os: str, usuario_token: dict = SERVICO, db: Session = Depends(get_db)):
    return _handle_db_transaction(db, patio.mover, numero_os, -1)
