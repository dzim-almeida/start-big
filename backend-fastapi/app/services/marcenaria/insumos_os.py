# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/insumos_os.py
# DESCRICAO: Insumos dos moveis aprovados -> pecas embutidas da OS
#            (Spec 08A, Revisao 2, D1a-D1e). Funcao pura: recebe o orcamento
#            ja carregado e devolve numeros; nao le nem grava o banco.
# ---------------------------------------------------------------------------
"""
Por que pecas embutidas: o Compras (reserva, Necessidades, "Compras desta OS")
e a finalizacao da OS enxergam material pelos itens de PRODUTO da OS. Um item
de produto com `valor_unitario = 0` e `visivel_cliente = false` e o que a OS ja
chama de "peca embutida": sai do estoque e entra no custo, mas o cliente nao
ve nem paga (o dinheiro esta na linha do movel).

Regras (D1a-D1d):
- um item por PRODUTO, so dos moveis APROVADOS de producao INTERNA (o material
  do terceirizado e da central);
- planejado = soma de (quantidade do insumo x quantidade do movel x perda, so
  onde o insumo `sofre_perda`), arredondado UMA vez por produto;
- sugerido = planejado arredondado PARA CIMA ate a unidade inteira, menos nas
  unidades fracionaveis (KG, M, M2...), em que fica o proprio planejado:
  1,4 + 1,2 + 0,6 chapa = 3,2 -> 4 chapas (e nao 2 + 2 + 1 = 5);
- insumo sem produto (produto excluido depois da copia) nao vira item.

Unidades: milesimos (1,4 chapa = 1400), centavos e basis points, como o resto
da marcenaria (PR4). Contas em Decimal; nenhum float.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from app.db.models.marcenaria.orcamento import MarcenariaOrcamento
from app.services.quantidade_venda import UNIDADES_FRACIONAVEIS

_BP = Decimal(10000)          # 100% em basis points
_MILESIMOS = 1000             # uma unidade inteira em milesimos


@dataclass(frozen=True)
class InsumoDaOS:
    """Uma peca embutida da OS (um produto)."""
    produto_id: int
    nome: str                     # descricao copiada do primeiro insumo do produto
    unidade: str                  # unidade do produto, como texto (UN, CH, M, M2...)
    planejado_milesimos: int      # D1b, ja com a perda
    sugerido_milesimos: int       # D1b, arredondado para cima nas unidades inteiras
    custo_unitario_centavos: int  # media dos custos copiados, ponderada pelo planejado
    moveis: tuple[tuple[str, str, int], ...]   # (movel, ambiente, planejado em milesimos) -- para a 10A


def _arredondar(valor: Decimal) -> int:
    """Meio para cima (ROUND_HALF_UP), como o motor da Spec 05."""
    return int(valor.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def sugerido(planejado_milesimos: int, unidade: str) -> int:
    """O que a OS reserva/baixa: inteiro para cima, salvo unidade fracionavel."""
    if (unidade or "").upper() in UNIDADES_FRACIONAVEIS:
        return planejado_milesimos                         # fita de borda: 26,35 m e 26,35 m
    inteiras = -(-planejado_milesimos // _MILESIMOS)       # divisao para cima (3200 -> 4)
    return inteiras * _MILESIMOS


def insumos_da_os(
    orc: MarcenariaOrcamento,
    unidades: dict[int, str],
) -> list[InsumoDaOS]:
    """Um por produto: so moveis APROVADOS e INTERNA; perda so onde `sofre_perda`.

    `unidades` = {produto_id: unidade_medida} lido do cadastro (uma consulta so).
    A ordem devolvida e a de aparicao (ambiente, movel, insumo); quem monta a OS
    decide a ordem final (D1e).
    """
    # Acumuladores por produto, na ordem em que o produto aparece.
    total: dict[int, Decimal] = {}             # planejado sem arredondar
    custo_x_qtd: dict[int, Decimal] = {}       # soma de custo x planejado (para a media)
    nome: dict[int, str] = {}
    por_movel: dict[int, list[tuple[str, str, Decimal]]] = {}

    for ambiente in sorted(orc.ambientes, key=lambda a: (a.ordem, a.id)):
        for movel in sorted(ambiente.moveis, key=lambda m: (m.ordem, m.id)):
            if not movel.aprovado or movel.tipo_producao != "INTERNA":
                continue                                    # D1a, D1d
            for insumo in sorted(movel.insumos, key=lambda i: (i.ordem, i.id)):
                if insumo.produto_id is None:
                    continue                                # D1c: nada a baixar
                fator = (_BP + orc.perda_bp) / _BP if insumo.sofre_perda else Decimal(1)
                planejado = Decimal(insumo.quantidade_milesimos) * movel.quantidade * fator
                pid = insumo.produto_id
                total[pid] = total.get(pid, Decimal(0)) + planejado
                custo_x_qtd[pid] = custo_x_qtd.get(pid, Decimal(0)) + planejado * insumo.custo_unit_centavos
                nome.setdefault(pid, insumo.descricao)       # o primeiro insumo da o nome
                por_movel.setdefault(pid, []).append((movel.nome, ambiente.nome, planejado))

    resultado = []
    for pid, planejado_bruto in total.items():
        planejado = _arredondar(planejado_bruto)            # uma vez por produto (E3a)
        unidade = (unidades.get(pid) or "UN").upper()
        media = _arredondar(custo_x_qtd[pid] / planejado_bruto) if planejado_bruto else 0
        resultado.append(InsumoDaOS(
            produto_id=pid,
            nome=nome[pid],
            unidade=unidade,
            planejado_milesimos=planejado,
            sugerido_milesimos=sugerido(planejado, unidade),
            custo_unitario_centavos=media,
            moveis=tuple((m, a, _arredondar(q)) for m, a, q in por_movel[pid]),
        ))
    return resultado


def ordenar_para_a_os(insumos: list[InsumoDaOS], localizacoes: Optional[dict[int, str]] = None) -> list[InsumoDaOS]:
    """D1e: pela localizacao do produto no estoque e depois pelo nome (a ordem da separacao)."""
    localizacoes = localizacoes or {}
    return sorted(insumos, key=lambda i: ((localizacoes.get(i.produto_id) or "").casefold(), i.nome.casefold()))
