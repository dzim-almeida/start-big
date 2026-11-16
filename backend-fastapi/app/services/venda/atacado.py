# ---------------------------------------------------------------------------
# ARQUIVO: services/venda/atacado.py (era services/venda_atacado.py ate 13/10/2026)
# MÓDULO: Service — Venda no preço de atacado
# ---------------------------------------------------------------------------
"""
A chave "Atacado" do PDV passa a venda INTEIRA para o `estoque.valor_atacado`.

Regras (decididas com a loja em 10/10/2026):
- Só a linha de UNIDADE de produto cadastrado muda (fator 1). Fardo já tem o
  preço dele; avulso não tem atacado; preço trocado pelo gerente (`MANUAL`)
  fica como o gerente deixou.
- Produto SEM preço de atacado fica no varejo — a tela marca a linha.
- A linha em atacado usa as colunas das regras de preço: `regra_preco =
  'ATACADO'` e o varejo em `valor_unitario_tabela`, que é como a tela já
  mostra preço riscado. Os relatórios de regra de preço filtram R1/R2/R3, então
  o atacado não entra neles.
- Com o atacado ligado as regras por quantidade (R1/R2/R3) NÃO se aplicam: o
  atacado já é o preço de quantidade, e as duas juntas dariam um preço que
  ninguém consegue prever no balcão (ver `regras_preco.aplicar_na_venda`).
- Pedido mínimo (`atacado_pedido_minimo`) sobre a soma dos itens: abaixo dele a
  venda NÃO finaliza (`exigir_pedido_minimo`, chamado no `finish_sale`).
"""

from app.core.enum import TipoProdutoVenda
from app.helpers.exceptions import BadRequestException
from app.services.precificacao.quantidade import subtotal_da_linha

ATACADO = "ATACADO"
DESCRICAO = "Preço de atacado"
MANUAL = "MANUAL"


def _preco_atacado(linha) -> int | None:
    estoque = linha.produto.estoque if linha.produto is not None else None
    preco = estoque.valor_atacado if estoque is not None else None
    return preco if preco and preco > 0 else None


def _participa(linha) -> bool:
    return (
        linha.tipo_produto == TipoProdutoVenda.CADASTRADO
        and linha.produto_id is not None
        and linha.produto is not None
        and (linha.fator_embalagem or 1) == 1
        and linha.regra_preco != MANUAL
    )


def _recalcular_subtotal(linha) -> None:
    linha.subtotal = subtotal_da_linha(linha.quantidade or 0, linha.valor_unitario or 0)
    # O desconto do operador nunca passa do novo valor da linha.
    if (linha.desconto or 0) > linha.subtotal:
        linha.desconto = linha.subtotal


def _voltar_ao_varejo(linha) -> None:
    if linha.valor_unitario_tabela is not None:
        linha.valor_unitario = linha.valor_unitario_tabela
    linha.regra_preco = None
    linha.regra_descricao = None
    linha.valor_unitario_tabela = None
    _recalcular_subtotal(linha)


def aplicar(venda) -> set[int]:
    """Põe (ou tira) o preço de atacado nas linhas. Devolve os ids que mudaram.

    Sem `modo_atacado` e sem linha marcada, não toca em nada: a venda de sempre.
    """
    alteradas: set[int] = set()
    ligado = bool(getattr(venda, "modo_atacado", False))

    for linha in venda.itens:
        if linha.regra_preco == ATACADO:
            preco = _preco_atacado(linha) if ligado else None
            if preco is None:
                _voltar_ao_varejo(linha)
                alteradas.add(linha.id)
            continue
        if not ligado or not _participa(linha):
            continue
        preco = _preco_atacado(linha)
        if preco is None:
            continue  # sem preço de atacado: fica no varejo
        linha.valor_unitario_tabela = linha.valor_unitario
        linha.valor_unitario = preco
        linha.regra_preco = ATACADO
        linha.regra_descricao = DESCRICAO
        linha.desconto_regra = 0
        _recalcular_subtotal(linha)
        alteradas.add(linha.id)

    return alteradas


def valor_dos_itens(venda) -> int:
    """O que o pedido mínimo mede: a soma dos itens, sem entrega nem desconto."""
    return sum(item.subtotal or 0 for item in venda.itens)


def _reais(centavos: int) -> str:
    return f"R$ {centavos / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def exigir_habilitado(config_vendas) -> None:
    if not (config_vendas and config_vendas.atacado_habilitado):
        raise BadRequestException(
            detail="A venda no atacado está desligada (Configurações › Regras de Vendas)"
        )


def exigir_pedido_minimo(venda, config_vendas) -> None:
    """Venda em atacado abaixo do pedido mínimo não finaliza."""
    if not getattr(venda, "modo_atacado", False):
        return
    minimo = (config_vendas.atacado_pedido_minimo if config_vendas else 0) or 0
    valor = valor_dos_itens(venda)
    if valor < minimo:
        raise BadRequestException(
            detail=(
                f"Pedido mínimo do atacado é {_reais(minimo)}: faltam {_reais(minimo - valor)}. "
                f"Complete o pedido ou volte a venda para o varejo."
            )
        )
