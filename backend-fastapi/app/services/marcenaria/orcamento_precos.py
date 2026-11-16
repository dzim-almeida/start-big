# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/orcamento_precos.py
# DESCRICAO: Custo do produto (O3a), copia no insumo (D2/D3) e atualizacao de
#            precos com aviso (O3, secao 6.5). Spec 06A.
# ---------------------------------------------------------------------------
"""
O orcamento NUNCA le o preco do produto ao calcular: usa a COPIA gravada no
insumo. Mudar o preco (ou o `sofre_perda`) do produto nao muda um orcamento
em silencio; a tela "precos desatualizados" mostra a diferenca, e o usuario
escolhe o que atualizar.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.db.crud.marcenaria.orcamento import buscar_por_ids
from app.db.models.marcenaria.ambiente import MarcenariaMovelInsumo
from app.db.models.marcenaria.orcamento import MarcenariaOrcamento
from app.db.models.produto import Produto
from app.services.marcenaria import erros

# De onde veio o custo do insumo (coluna `custo_origem`).
ORIGEM_ULTIMA_COMPRA = "ULTIMA_COMPRA"
ORIGEM_CUSTO_MEDIO = "CUSTO_MEDIO"
ORIGEM_SEM_CUSTO = "SEM_CUSTO"
ORIGEM_MANUAL = "MANUAL"            # digitado no orcamento por quem ve custos


def custo_do_produto(produto: Produto) -> tuple[int, str]:
    """(centavos, origem) pela regra O3a: ultima compra, senao custo medio, senao zero.

    `valor_entrada = 0` conta como "sem custo" (secao 7.3): um produto
    cadastrado com zero na compra nao tem custo conhecido, e o motor avisa
    INSUMO_SEM_CUSTO.
    """
    estoque = produto.estoque
    if estoque and estoque.valor_entrada:                 # ultimo preco de compra
        return estoque.valor_entrada, ORIGEM_ULTIMA_COMPRA
    if estoque and estoque.custo_medio:                   # reserva: custo medio
        return estoque.custo_medio, ORIGEM_CUSTO_MEDIO
    return 0, ORIGEM_SEM_CUSTO


def carregar_produtos(db: Session, ids: list[int]) -> dict[int, Produto]:
    """{id: produto} dos ids pedidos; produto inexistente responde 422."""
    unicos = sorted(set(ids))
    produtos = buscar_por_ids(db, Produto, unicos)
    if len(produtos) != len(unicos):
        erros.invalido("Produto do insumo não encontrado.")
    return produtos


def _cortar(texto: Optional[str], tamanho: int) -> Optional[str]:
    """Texto cortado no tamanho da coluna; vazio vira None."""
    if not texto:
        return None
    return texto[:tamanho]


def copiar_do_produto(produto: Produto, custo_manual: Optional[int]) -> dict:
    """Os campos que o insumo NOVO copia do produto (D2, D3).

    Com `custo_manual` (quem ve custos digitou), o custo e esse e a origem e
    MANUAL; o resto vem do produto do mesmo jeito.
    """
    if custo_manual is not None:
        custo, origem = custo_manual, ORIGEM_MANUAL
    else:
        custo, origem = custo_do_produto(produto)
    return {
        "produto_id": produto.id,
        "descricao": produto.nome[:255],                   # cortes = tamanho das colunas
        "codigo": _cortar(produto.codigo_produto, 100),
        "unidade": _cortar(produto.unidade_medida, 10),
        "custo_unit_centavos": custo,
        "custo_origem": origem,
        "sofre_perda": bool(produto.sofre_perda),
    }


# ===========================================================================
# PRECOS DESATUALIZADOS (secao 6.5)
# ===========================================================================

def _insumos_com_produto(orc: MarcenariaOrcamento) -> list[tuple[MarcenariaMovelInsumo, str]]:
    """(insumo, nome do movel) de todos os insumos ligados a um produto."""
    return [
        (insumo, movel.nome)
        for ambiente in orc.ambientes
        for movel in ambiente.moveis
        for insumo in movel.insumos
        if insumo.produto_id is not None
    ]


def itens_desatualizados(db: Session, orc: MarcenariaOrcamento) -> list[dict]:
    """Os insumos cujo custo pelo O3a OU `sofre_perda` mudou desde a copia.

    Insumos com custo MANUAL tambem entram (o usuario decide se troca).
    """
    pares = _insumos_com_produto(orc)
    produtos = buscar_por_ids(db, Produto, sorted({i.produto_id for i, _ in pares}))
    itens = []
    for insumo, nome_movel in pares:
        produto = produtos.get(insumo.produto_id)
        if produto is None:                               # produto apagado no meio: nada a comparar
            continue
        custo_hoje, origem_hoje = custo_do_produto(produto)
        perda_hoje = bool(produto.sofre_perda)
        mudou = (
            custo_hoje != insumo.custo_unit_centavos
            or perda_hoje != insumo.sofre_perda
            or insumo.custo_origem == ORIGEM_MANUAL
        )
        if mudou:
            itens.append({
                "insumo_id": insumo.id,
                "movel": nome_movel,
                "descricao": insumo.descricao,
                "custo_atual_orcamento": insumo.custo_unit_centavos,
                "custo_produto_hoje": custo_hoje,
                "origem_hoje": origem_hoje,
                "sofre_perda_orcamento": insumo.sofre_perda,
                "sofre_perda_hoje": perda_hoje,
            })
    return itens


def substituicoes_para(itens: list[dict], insumo_ids: Optional[set[int]]) -> dict[int, tuple[int, str, bool]]:
    """{insumo_id: (custo_hoje, origem_hoje, sofre_perda_hoje)} dos escolhidos.

    `insumo_ids=None` = todos os desatualizados.
    """
    return {
        item["insumo_id"]: (item["custo_produto_hoje"], item["origem_hoje"], item["sofre_perda_hoje"])
        for item in itens
        if insumo_ids is None or item["insumo_id"] in insumo_ids
    }


def aplicar_substituicoes(orc: MarcenariaOrcamento, trocas: dict[int, tuple[int, str, bool]]) -> int:
    """Grava os custos novos nos insumos escolhidos. Devolve quantos mudaram."""
    alterados = 0
    for ambiente in orc.ambientes:
        for movel in ambiente.moveis:
            for insumo in movel.insumos:
                troca = trocas.get(insumo.id)
                if troca is None:
                    continue
                insumo.custo_unit_centavos, insumo.custo_origem, insumo.sofre_perda = troca
                alterados += 1
    return alterados

