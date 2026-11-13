# ---------------------------------------------------------------------------
# ARQUIVO: app/services/lava_rapido/portes.py
# DESCRICAO: Portes da loja e preco/duracao de cada servico por porte
#            (docs/lava-rapido/ SPEC-00 P1, P2a, P5 e Spec 02A).
#
# So existe para segmento que declara a capacidade `preco_por_porte` (hoje, o
# lava-rapido). A regra le a CAPACIDADE no registry, nunca o nome do
# segmento: para os outros, as rotas respondem 404, como se nao existissem.
# ---------------------------------------------------------------------------

from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core import segmentos as reg
from app.db.crud.lava_rapido import porte as crud
from app.db.models.lava_rapido import PorteVeiculo, ServicoPrecoPorte
from app.db.models.servico import Servico
from app.schemas.lava_rapido.porte import (
    PorteCreate,
    PorteUpdate,
    PrecosServicoUpdate,
    ServicoDoPorte,
)
from app.services.sistema.segmentos import get_segmento_atual


# =========================
# Guardas
# =========================

def _exigir_preco_por_porte(db: Session) -> str:
    """404 fora de segmento com preco por porte; devolve o segmento."""
    segmento = get_segmento_atual(db)
    if not reg.segmento_tem_capacidade(segmento, reg.CAP_PRECO_POR_PORTE):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preço por porte não disponível para este segmento.",
        )
    return segmento


def _tipos_do_segmento(segmento: str) -> Dict[str, List[str]]:
    """{id do tipo: portes iniciais}, lidos do campo `porte` de cada tipo.

    A lista inicial mora no registry, junto do campo, para nao haver duas
    fontes da mesma lista (P2a).
    """
    tipos: Dict[str, List[str]] = {}
    for tipo in (reg.get_definicao_segmento(segmento) or {}).get("tipos", []):
        porte = next((c for c in tipo.get("campos", []) if c.get("nome") == "porte"), None)
        tipos[tipo["id"]] = list((porte or {}).get("opcoes") or [])
    return tipos


def _exigir_tipo(segmento: str, tipo_veiculo: str) -> None:
    if tipo_veiculo not in _tipos_do_segmento(segmento):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Tipo de veículo desconhecido.",
        )


def _porte_ou_404(db: Session, porte_id: int) -> PorteVeiculo:
    porte = crud.get_porte(db, porte_id)
    if porte is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Porte não encontrado.")
    return porte


def _servico_ou_404(db: Session, servico_id: int) -> Servico:
    servico = db.get(Servico, servico_id)
    if servico is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Serviço não encontrado.")
    return servico


def _recusar_nome_repetido(db: Session, tipo_veiculo: str, nome: str,
                           ignorar_id: Optional[int] = None) -> None:
    existente = crud.get_porte_por_nome(db, tipo_veiculo, nome)
    if existente is not None and existente.id != ignorar_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Já existe o porte "{existente.nome}" neste tipo de veículo.',
        )


# =========================
# Portes
# =========================

def _garantir_portes_iniciais(db: Session, segmento: str) -> None:
    """Grava a lista inicial do registry na primeira leitura (P2a).

    Uma vez so: tabela com qualquer linha (mesmo desativada) e da loja, e
    nada aqui a reescreve -- o dono pode ter renomeado ou desativado tudo.
    """
    if crud.contar_portes(db) > 0:
        return
    for tipo_veiculo, nomes in _tipos_do_segmento(segmento).items():
        for ordem, nome in enumerate(nomes):
            db.add(PorteVeiculo(tipo_veiculo=tipo_veiculo, nome=nome, ordem=ordem, ativo=True))
    db.flush()


def listar_portes(db: Session, tipo_veiculo: Optional[str] = None,
                  incluir_inativos: bool = False) -> List[PorteVeiculo]:
    segmento = _exigir_preco_por_porte(db)
    _garantir_portes_iniciais(db, segmento)
    return list(crud.listar_portes(db, tipo_veiculo, incluir_inativos))


def criar_porte(db: Session, dados: PorteCreate) -> PorteVeiculo:
    segmento = _exigir_preco_por_porte(db)
    _garantir_portes_iniciais(db, segmento)              # a lista inicial vem antes do novo
    _exigir_tipo(segmento, dados.tipo_veiculo)
    _recusar_nome_repetido(db, dados.tipo_veiculo, dados.nome)
    porte = PorteVeiculo(
        tipo_veiculo=dados.tipo_veiculo,
        nome=dados.nome,
        ordem=crud.proxima_ordem(db, dados.tipo_veiculo),   # entra no fim da fila
        ativo=True,
    )
    return crud.adicionar_porte(db, porte)


def atualizar_porte(db: Session, porte_id: int, dados: PorteUpdate) -> PorteVeiculo:
    _exigir_preco_por_porte(db)
    porte = _porte_ou_404(db, porte_id)
    if dados.nome is not None:
        _recusar_nome_repetido(db, porte.tipo_veiculo, dados.nome, ignorar_id=porte.id)
    for campo, valor in dados.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(porte, campo, valor)
    db.flush()
    return porte


# =========================
# Preco do servico por porte
# =========================

def listar_precos_do_servico(db: Session, servico_id: int) -> List[ServicoPrecoPorte]:
    _exigir_preco_por_porte(db)
    _servico_ou_404(db, servico_id)
    return list(crud.listar_precos_do_servico(db, servico_id))


def salvar_precos_do_servico(db: Session, servico_id: int,
                             dados: PrecosServicoUpdate) -> List[ServicoPrecoPorte]:
    """Grava a grade inteira. Porte fora da lista volta ao preco padrao."""
    _exigir_preco_por_porte(db)
    _servico_ou_404(db, servico_id)

    ids = [item.porte_id for item in dados.precos]
    if len(ids) != len(set(ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="O mesmo porte aparece duas vezes na tabela de preços.",
        )
    for porte_id in ids:
        _porte_ou_404(db, porte_id)

    crud.substituir_precos_do_servico(db, servico_id, [
        ServicoPrecoPorte(
            servico_id=servico_id,
            porte_id=item.porte_id,
            valor=item.valor,
            duracao_minutos=item.duracao_minutos,
        )
        for item in dados.precos
    ])
    return list(crud.listar_precos_do_servico(db, servico_id))


def servicos_do_porte(db: Session, porte_id: int) -> List[ServicoDoPorte]:
    """Todo servico ativo, com o preco que vale para o porte.

    E o que a comanda mostra nos botoes (SPEC-00 U2). Sem linha para o porte,
    o servico aparece com o preco padrao (`preco_do_porte=False`) -- some do
    balcao so o que o dono desativou.
    """
    _exigir_preco_por_porte(db)
    _porte_ou_404(db, porte_id)
    precos = crud.precos_do_porte(db, porte_id)
    resultado: List[ServicoDoPorte] = []
    for servico in crud.listar_servicos_ativos(db):
        linha = precos.get(servico.id)
        resultado.append(ServicoDoPorte(
            servico_id=servico.id,
            descricao=servico.descricao,
            valor=linha.valor if linha else servico.valor,
            # A duracao do cadastro do servico vale quando o porte nao tem a sua.
            duracao_minutos=(linha.duracao_minutos if linha else None) or servico.duracao_minutos,
            preco_do_porte=linha is not None,
        ))
    return resultado
