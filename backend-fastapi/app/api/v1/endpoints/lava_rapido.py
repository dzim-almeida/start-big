# ---------------------------------------------------------------------------
# ARQUIVO: app/api/v1/endpoints/lava_rapido.py
# DESCRICAO: API do segmento lava-rapido (docs/lava-rapido/). Prefixo:
#            /api/v1/lava-rapido
#
# Esta camada so le o token e os parametros e aplica as permissoes. A regra
# fica em app/services/lava_rapido/. Tudo responde 404 fora do segmento com a
# capacidade correspondente (hoje, `preco_por_porte`).
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
from app.services.lava_rapido import portes

router = APIRouter()

# Portes e precos sao parte do cadastro de servico: mesma permissao dele.
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
