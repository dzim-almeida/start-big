# ---------------------------------------------------------------------------
# ARQUIVO: services/movimentacao_estoque.py
# DESCRIÇÃO: Lógica de negócio para movimentações de estoque.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Sequence, Optional, Dict, Any

from app.schemas.movimentacao_estoque import MovimentacaoCreate
from app.db.models.movimentacao_estoque import MovimentacaoEstoque
from app.db.crud import movimentacao_estoque as mov_crud
from app.db.crud import produto as produto_crud
from app.core.enum import MovimentacaoTipo, MovimentacaoOrigem


not_found_produto = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Produto não encontrado"
)

estoque_insuficiente = HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    detail="Estoque insuficiente para realizar a saída"
)

quantidade_invalida = HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    detail="Entrada e saída exigem quantidade maior que zero"
)

produto_sem_estoque = HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    detail="Produto não possui controle de estoque vinculado"
)


# ===========================================================================
# CUSTO — média ponderada
#
# O custo de uma peça precisa ficar CONGELADO no momento em que ela sai, senão
# o lucro do passado muda toda vez que o fornecedor reajusta o preço. Quem
# guarda esse congelamento é `movimentacoes_estoque.custo_unitario`; o que está
# aqui é só a política que decide QUAL número congelar.
#
# A política é média ponderada, e não PEPS/FIFO, por um motivo concreto deste
# sistema: a OS pode deixar o estoque NEGATIVO de propósito (a peça já foi
# instalada; travar a OS não a traz de volta). PEPS não tem o que consumir
# quando não há camada, e cairia em lote fantasma com custo inventado. A média
# absorve o negativo sem inventar nada.
#
# Nada disso fecha a porta para PEPS depois: como toda ENTRADA guarda o valor
# realmente pago, o histórico bruto continua no livro e dá para reprocessar.
# ===========================================================================

def custo_atual(estoque) -> Optional[int]:
    """Custo unitário corrente do produto, em centavos.

    Cai para `valor_entrada` quando `custo_medio` ainda é NULL — o caso dos
    produtos cadastrados antes de existir média. É o melhor palpite disponível,
    e vira média de verdade na primeira compra registrada com valor pago.
    """
    if estoque is None:
        return None
    if estoque.custo_medio is not None:
        return estoque.custo_medio
    return estoque.valor_entrada


def calcular_custo_medio(
    quantidade_anterior: int,
    custo_anterior: Optional[int],
    quantidade_entrada: int,
    custo_entrada: int,
) -> int:
    """Média ponderada após uma compra: ((q₀ × c₀) + (qₑ × cₑ)) ÷ (q₀ + qₑ).

    `quantidade_anterior` negativa entra como zero: saldo negativo é dívida de
    contagem, não estoque avaliável, e ponderar por ele produziria um custo
    maior que o preço pago (ex.: −2 a 40 + 3 a 60 daria 100).

    Sem custo anterior conhecido, a compra define o custo sozinha.
    """
    base = max(0, quantidade_anterior)
    if custo_anterior is None or base == 0:
        return custo_entrada
    total = (base * custo_anterior) + (quantidade_entrada * custo_entrada)
    return round(total / (base + quantidade_entrada))


# ===========================================================================
# REGISTRO CENTRAL DE MOVIMENTAÇÃO
#
# Este é o ÚNICO lugar que altera `estoque.quantidade`. Venda, OS, cadastro de
# produto, edição de produto e ajuste manual passam todos por aqui — antes cada
# um mexia na quantidade por conta própria, e um deles (a edição de produto)
# trocava a quantidade sem deixar rastro nenhum no livro. Concentrando, a
# quantidade e o histórico não têm como divergir: ou as duas coisas acontecem,
# ou nenhuma.
# ===========================================================================

def registrar_movimentacao(
    db: Session,
    *,
    produto,
    tipo: MovimentacaoTipo,
    quantidade: int,
    origem: MovimentacaoOrigem,
    usuario_id: Optional[int] = None,
    usuario_nome: str = "Sistema",
    venda_id: Optional[int] = None,
    ordem_servico_id: Optional[int] = None,
    observacao: Optional[str] = None,
    permitir_negativo: bool = False,
    custo_unitario: Optional[int] = None,
) -> Optional[MovimentacaoEstoque]:
    """Altera o estoque do produto e registra a movimentação, numa operação só.

    O que `quantidade` significa depende do tipo:
      - ENTRADA / SAIDA: quantas unidades entraram ou saíram.
      - AJUSTE: a quantidade FINAL desejada (é uma contagem de inventário, não
        um delta). O movimento grava a diferença absoluta.
      - EDICAO_DADOS: ignorada — não mexe em quantidade, só deixa o rastro da
        edição de cadastro.

    `permitir_negativo` existe porque as duas frentes têm regras diferentes e
    ambas são deliberadas:
      - Venda (False): recusa a saída sem estoque. O produto ainda está na
        prateleira e dá para não vender.
      - OS (True): a peça já foi instalada no equipamento; travar a finalização
        não a devolve, só prende a OS. O saldo negativo é o sinal de que a
        contagem precisa ser acertada.

    `custo_unitario` só deve ser informado numa ENTRADA de COMPRA — é o valor
    efetivamente pago por unidade, e é ele que recalcula a média ponderada. Nos
    demais casos o custo é derivado (ver `_resolver_custo`).

    Retorna None quando não há o que movimentar (produto sem estoque vinculado
    ou quantidade zero numa entrada/saída), para o chamador não precisar repetir
    essa checagem.
    """
    if produto is None or produto.estoque is None:
        return None
    if tipo in (MovimentacaoTipo.ENTRADA, MovimentacaoTipo.SAIDA) and quantidade <= 0:
        return None

    estoque = produto.estoque
    anterior = estoque.quantidade or 0

    # 3 casas, como a quantidade da venda (app/schemas/quantidade.py): 1,5 − 0,1
    # em ponto flutuante dá 1,4000000000000001, e esse resto ficaria no saldo
    # para sempre. Inteiro passa intacto (round(97, 3) == 97).
    quantidade = round(quantidade, 3) if quantidade is not None else quantidade

    if tipo == MovimentacaoTipo.ENTRADA:
        posterior = anterior + quantidade
        movimentada = quantidade
    elif tipo == MovimentacaoTipo.SAIDA:
        if not permitir_negativo and anterior < quantidade:
            raise estoque_insuficiente
        posterior = anterior - quantidade
        movimentada = quantidade
    elif tipo == MovimentacaoTipo.AJUSTE:
        posterior = quantidade
        movimentada = abs(posterior - anterior)
    elif tipo == MovimentacaoTipo.EDICAO_DADOS:
        posterior = anterior
        movimentada = 0
    else:
        raise ValueError(f"registrar_movimentacao não trata o tipo {tipo}")
    posterior = round(posterior, 3)
    movimentada = round(movimentada, 3)

    custo_movimento = _resolver_custo(
        estoque=estoque,
        tipo=tipo,
        quantidade=movimentada,
        quantidade_anterior=anterior,
        custo_unitario=custo_unitario,
    )

    if tipo != MovimentacaoTipo.EDICAO_DADOS:
        estoque.quantidade = posterior

    movimentacao = MovimentacaoEstoque(
        produto_id=produto.id,
        produto_nome=produto.nome,
        usuario_id=usuario_id,
        usuario_nome=usuario_nome,
        tipo=tipo,
        quantidade=movimentada,
        quantidade_anterior=anterior,
        quantidade_posterior=posterior,
        origem=origem.value,
        venda_id=venda_id,
        ordem_servico_id=ordem_servico_id,
        observacao=observacao,
        custo_unitario=custo_movimento,
    )
    return mov_crud.create_movimentacao(db, movimentacao)


def _resolver_custo(
    *,
    estoque,
    tipo: MovimentacaoTipo,
    quantidade: int,
    quantidade_anterior: int,
    custo_unitario: Optional[int],
) -> Optional[int]:
    """Decide o custo que fica congelado no movimento e atualiza a média.

    Uma regra por situação, cada uma por um motivo:

    - ENTRADA com valor pago (compra): recalcula a média e congela o que foi
      pago. É o único caso em que a média muda — comprar é o único evento que
      altera quanto o estoque custou.

    - ENTRADA sem valor pago (estorno de venda, reabertura de OS): a média fica
      intacta. Devolução não é compra; a peça volta pelo custo com que saiu.
      Congelar a média corrente aqui faz o CMV do período se anular sozinho
      contra a saída original, sem ninguém precisar caçar estorno na mão.

    - SAIDA: congela a média corrente. Este número É o CMV daquela venda ou OS,
      e é o que nunca mais pode mudar.

    - AJUSTE: média intacta. Contagem não é compra nem venda. O custo vai junto
      só para dar preço à sobra ou à perda — e perda é DESPESA, não CMV, por
      isso o relatório separa por tipo em vez de somar tudo que sai.

    - EDICAO_DADOS: não movimenta nada, não tem custo.
    """
    if tipo == MovimentacaoTipo.EDICAO_DADOS:
        return None

    if tipo == MovimentacaoTipo.ENTRADA and custo_unitario is not None:
        estoque.custo_medio = calcular_custo_medio(
            quantidade_anterior=quantidade_anterior,
            custo_anterior=custo_atual(estoque),
            quantidade_entrada=quantidade,
            custo_entrada=custo_unitario,
        )
        return custo_unitario

    return custo_atual(estoque)


# ===========================================================================
# MOVIMENTAÇÃO MANUAL (endpoint)
# ===========================================================================

def create_movimentacao(
    db: Session,
    produto_id: int,
    data: MovimentacaoCreate,
    usuario_token: Dict[str, Any],
) -> MovimentacaoEstoque:
    """Movimentação manual de estoque, disparada pela tela de produto.

    É só um adaptador do endpoint para o registro central — a lógica de
    quantidade e de custo mora lá, e não pode existir em dois lugares: com duas
    cópias, a entrada manual deixaria de recalcular a média e o custo iria
    drenando sem nenhum erro aparecer.
    """
    produto = produto_crud.get_produto_by_id(db, produto_id)
    if not produto:
        raise not_found_produto
    if produto.estoque is None:
        raise produto_sem_estoque
    if data.tipo in (MovimentacaoTipo.ENTRADA, MovimentacaoTipo.SAIDA) and data.quantidade <= 0:
        raise quantidade_invalida

    # Entrada por embalagem: converte para a unidade ANTES do registro central,
    # que continua recebendo unidade e custo por unidade (é o que o custo médio
    # e os relatórios de CMV esperam). Plano de embalagens, D10 / G6.
    embalagem = _embalagem_da_entrada(produto, data) if data.embalagem_id is not None else None
    quantidade = data.quantidade
    custo_unitario = data.custo_unitario
    if embalagem is not None:
        quantidade = data.quantidade * embalagem.fator
        if custo_unitario is not None:
            custo_unitario = round(custo_unitario / embalagem.fator)

    movimentacao = registrar_movimentacao(
        db,
        produto=produto,
        tipo=data.tipo,
        quantidade=quantidade,
        origem=MovimentacaoOrigem.MANUAL,
        usuario_id=int(usuario_token["sub"]),
        usuario_nome=usuario_token.get("nome", "Desconhecido"),
        observacao=data.observacao,
        custo_unitario=custo_unitario,
    )
    assert movimentacao is not None  # as guardas acima já cobrem os casos de None
    if embalagem is not None:
        movimentacao.embalagem_id = embalagem.id
        movimentacao.embalagem_sigla = embalagem.sigla
        movimentacao.embalagem_fator = embalagem.fator
        movimentacao.quantidade_embalagem = int(data.quantidade)
        db.flush()
    return movimentacao


def _embalagem_da_entrada(produto, data: MovimentacaoCreate):
    """A embalagem da entrada, conferida: do produto, ativa, marcada para entrada."""
    if data.tipo != MovimentacaoTipo.ENTRADA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Embalagem só vale na entrada. Saída e ajuste são em unidade.",
        )
    if data.quantidade != int(data.quantidade):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Entrada por embalagem é em número inteiro de embalagens.",
        )
    embalagem = next((e for e in produto.embalagens if e.id == data.embalagem_id), None)
    if embalagem is None or not embalagem.ativo or not embalagem.usa_na_entrada:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Essa embalagem não é deste produto, está inativa ou não é usada na entrada.",
        )
    return embalagem


def get_movimentacoes(
    db: Session,
    produto_id: Optional[int] = None,
    limit: int = 100,
) -> Sequence[MovimentacaoEstoque]:
    """Lista movimentações de estoque, opcionalmente por produto."""
    return mov_crud.get_movimentacoes(db, produto_id=produto_id, limit=limit)
