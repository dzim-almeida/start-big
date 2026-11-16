# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/nfse/tabelas.py
# DESCRIÇÃO: Busca do código de tributação nacional e do NBS, com a sugestão
#            de NBS pela correlação oficial (Anexo VIII).
# ---------------------------------------------------------------------------
"""
As tabelas são pequenas (338 códigos nacionais, 917 NBS), então uma passada
só pelo motor de `core/busca.py` basta — diferente do NCM, que tem 10 mil
linhas e precisou de duas (ver `buscar_ncm` em endpoints/fiscal_produto.py).
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.core import busca as motor_busca
from app.db.models.nfse_tabelas import Nbs, NfseCorrelacaoNbs, NfseServicoNacional


def _como_item(registro) -> dict:
    return {
        "codigo": registro.codigo,
        "descricao": registro.descricao,
        "descricao_completa": registro.descricao_completa,
    }


def _buscar(db: Session, modelo, termo: str, limite: int) -> list[dict]:
    termo = (termo or "").strip()
    if not termo:
        return []

    # Código digitado com pontos ("01.07.01", "1.1501.30.00") casa com o
    # gravado sem eles.
    digitos = "".join(c for c in termo if c.isdigit())
    if digitos and digitos == "".join(c for c in termo if c not in ". "):
        achados = (
            db.query(modelo).filter(modelo.codigo.startswith(digitos))
            .order_by(modelo.codigo).limit(limite).all()
        )
        return [_como_item(r) for r in achados]

    filtro = motor_busca.filtro_busca(termo, (modelo.codigo, modelo.descricao_completa))
    if filtro is None:
        return []
    consulta = db.query(modelo).filter(filtro)
    ordem = motor_busca.ordenacao_relevancia(termo, modelo.descricao, (modelo.codigo,))
    if ordem is not None:
        consulta = consulta.order_by(ordem, modelo.codigo)
    return [_como_item(r) for r in consulta.limit(limite).all()]


def buscar_servicos_nacionais(db: Session, termo: str, limite: int = 20) -> list[dict]:
    return _buscar(db, NfseServicoNacional, termo, limite)


def buscar_nbs(db: Session, termo: str, limite: int = 20) -> list[dict]:
    return _buscar(db, Nbs, termo, limite)


def nbs_sugeridos(db: Session, codigo_tributacao_nacional: Optional[str]) -> list[dict]:
    """
    Os NBS que a Receita correlaciona com o código nacional escolhido.

    A correlação é por subitem da LC 116 (os 4 primeiros dígitos do código
    nacional): "010701" → subitem "0107" → suporte em TI, manutenção de
    programas... Lista vazia quando o código não tem correlação publicada — o
    campo continua aceitando busca livre.
    """
    digitos = "".join(c for c in (codigo_tributacao_nacional or "") if c.isdigit())
    if len(digitos) < 4:
        return []
    registros = (
        db.query(Nbs)
        .join(NfseCorrelacaoNbs, NfseCorrelacaoNbs.nbs == Nbs.codigo)
        .filter(NfseCorrelacaoNbs.item_lc116 == digitos[:4])
        .order_by(Nbs.codigo)
        .all()
    )
    return [_como_item(r) for r in registros]
