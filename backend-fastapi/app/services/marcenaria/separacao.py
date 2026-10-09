# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/separacao.py
# DESCRICAO: Separacao de material da OS da marcenaria (Spec 10A): ler,
#            retirar, devolver, concluir, reabrir, leitor, faltas da OS e o
#            disponivel por produto para a busca de insumo do orcamento.
# ---------------------------------------------------------------------------
"""
O que se separa: as PECAS EMBUTIDAS que a aprovacao do orcamento criou na OS
(Spec 08A): um item de PRODUTO por produto, com `origem = ORCAMENTO_MARCENARIA`.
Nenhuma tabela nova (E3b): a separacao usa colunas do item que a finalizacao
e o Compras ja entendem.

- `quantidade`           o que a OS vai consumir (nasce = sugerido);
- `quantidade_separada`  o que ja saiu do estoque (retiradas - devolucoes);
- `status_aprovacao`     REPROVADO = "nao usado" (a tela nunca diz "reprovado").

Por que isso basta (sem mexer em nenhum modulo compartilhado):
- a FINALIZACAO baixa so `quantidade - separada` (services/ordem_servico.py);
- a RESERVA do Compras conta `quantidade - separada` (compras/demanda_os.py);
- item REPROVADO fica fora da baixa, da reserva e do CMV.

Quantidades na API: MILESIMOS (int, PR4). O item e o estoque guardam Float com
3 casas; a conversao fica nas funcoes `_mil` (Float -> milesimos) e `/ 1000`.

A separacao NUNCA devolve preco, custo nem valor (D22), qualquer que seja a
permissao: e a tela de quem trabalha no deposito.
"""

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Optional

from sqlalchemy import func, update
from sqlalchemy.orm import Session

from app.core import segmentos as reg
from app.core.enum import (
    MovimentacaoOrigem,
    MovimentacaoTipo,
    OrdemServicoItemAprovacao,
    OrdemServicoItemTipo,
)
from app.core.tempo import fuso_local
from app.db.crud import ordem_servico as os_crud
from app.db.crud.marcenaria import orcamento as crud
from app.db.models.marcenaria.orcamento import MarcenariaOrcamento, StatusOrcamento
from app.db.models.ordem_servico import OrdemServico
from app.db.models.ordem_servico_item import OrdemServicoItem
from app.db.models.produto import Produto
from app.schemas.marcenaria.separacao import ConferenciaEntrada, MovimentoEntrada
from app.services import movimentacao_estoque
from app.services.compras import demanda_os
from app.services.marcenaria import erros, leitor
from app.services.marcenaria.aprovacao import ORIGEM
from app.services.marcenaria.insumos_os import InsumoDaOS, insumos_da_os, insumos_sem_produto
from app.services.marcenaria.orcamento_comum import (
    exigir_orcamento_tecnico,
    registrar_evento,
    usuario_id,
    usuario_nome,
)
from app.services.marcenaria.orcamento_detalhe import nome_do_cliente
from app.services.segmentos import get_segmento_atual

# --- Frases e codigos de erro (secao 6.4) --------------------------------------
MSG_SEM_SEPARACAO = "Esta OS não tem separação de material."
MSG_FORA_DA_OS = "Este produto não faz parte desta OS."
MSG_OS_FECHADA = "A OS está finalizada ou cancelada; a separação não pode mais ser alterada."
MSG_CONCORRENCIA = "Outra pessoa alterou este item. A lista foi atualizada."
MSG_QUANTIDADE = "A quantidade deve ser maior que zero."
MSG_NAO_USADO = "Este material foi marcado como não usado. Reabra a linha para retirar."
MSG_SEM_CODIGO = "Leia ou digite o código do material."
OS_FECHADA = "OS_FECHADA"
ITEM_NAO_USADO = "ITEM_NAO_USADO"

# Status em que a OS ja nao muda (D14): a separacao vira so leitura.
STATUS_FECHADOS = ("FINALIZADA", "CANCELADA")

# Alertas de cada linha (secao 6.2): a tela traduz cada codigo numa frase.
ALERTA_SEM_COBERTURA = "SEM_COBERTURA"          # nem estoque nem pedido cobrem
ALERTA_ESTOQUE_NEGATIVO = "ESTOQUE_NEGATIVO"    # D8: retirou sem saldo
ALERTA_ACIMA_DO_SUGERIDO = "ACIMA_DO_SUGERIDO"  # D7: retirou mais que o sugerido


# ===========================================================================
# AJUDANTES
# ===========================================================================

def _valor(status) -> str:
    """O texto do enum ("ABERTA"), venha o enum ou o texto."""
    return getattr(status, "value", status)


def _mil(quantidade: Optional[float]) -> int:
    """Float com 3 casas (item, estoque) -> milesimos inteiros. Nulo = 0."""
    return int(round((quantidade or 0) * 1000))


def _texto(milesimos: int) -> str:
    """Milesimos -> texto pt-BR para o historico: 3000 -> "3"; 26350 -> "26,35"."""
    texto = f"{milesimos / 1000:.3f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def _aberta(os_: OrdemServico) -> bool:
    """D14: a separacao so muda com a OS fora de FINALIZADA e CANCELADA."""
    return _valor(os_.status) not in STATUS_FECHADOS


def _os_e_orcamento(db: Session, numero_os: str) -> tuple[OrdemServico, MarcenariaOrcamento]:
    """A OS e o orcamento APROVADO que a gerou, ou 404 (secao 6.4).

    Tambem 404 fora da marcenaria (capacidade `orcamento_tecnico`, lida no
    registry): para os outros segmentos, a separacao nao existe.
    """
    if not reg.segmento_tem_capacidade(get_segmento_atual(db), reg.CAP_ORCAMENTO_TECNICO):
        erros.nao_encontrado(MSG_SEM_SEPARACAO)
    os_ = os_crud.get_ordem_servico_by_numero_os(db, numero_os)
    orc = crud.get_orcamento_por_os(db, os_.id) if os_ is not None and os_.ativo else None
    if orc is None or orc.status != StatusOrcamento.APROVADO:
        erros.nao_encontrado(MSG_SEM_SEPARACAO)
    return os_, orc


def _itens(os_: OrdemServico) -> list[OrdemServicoItem]:
    """As linhas da separacao (D1): pecas embutidas do orcamento, com produto.

    Inclui as marcadas "nao usado" (REPROVADO): elas continuam na tela, com o
    botao de reabrir. Os moveis (SERVICO) e a instalacao nao se separam.
    """
    return sorted(
        (i for i in os_.itens
         if i.origem == ORIGEM and i.tipo == OrdemServicoItemTipo.PRODUTO and i.produto_id is not None),
        key=lambda i: i.id,
    )


def _nao_usado(item: OrdemServicoItem) -> bool:
    """D11: concluido sem retirar nada (ou devolvido por inteiro)."""
    return item.status_aprovacao == OrdemServicoItemAprovacao.REPROVADO


def _planejados(db: Session, orc: MarcenariaOrcamento, itens: list[OrdemServicoItem]) -> tuple[dict, dict]:
    """({produto_id: Produto}, {produto_id: InsumoDaOS}) numa consulta so (D2).

    O planejado e o sugerido saem do orcamento APROVADO (que nao muda, F3): a
    mesma conta que criou a OS, entao o "reabrir" sabe para onde voltar.
    """
    produtos = crud.buscar_por_ids(db, Produto, [i.produto_id for i in itens])
    unidades = {pid: p.unidade_medida or "UN" for pid, p in produtos.items()}
    return produtos, {p.produto_id: p for p in insumos_da_os(orc, unidades)}


def _unidade(produto: Optional[Produto], planejado: Optional[InsumoDaOS]) -> str:
    """A unidade do cadastro do produto; sem ela, a do planejado; senao "UN"."""
    unidade = (produto.unidade_medida if produto else None) or (planejado.unidade if planejado else None) or "UN"
    return unidade.upper()


def _diferenca_bp(separada: int, planejado: Optional[int]) -> Optional[int]:
    """D15: orcado x real em basis points (+1200 = 12% acima do orcado).

    Nulo antes da primeira retirada (ainda nao ha "real") e sem planejado.
    """
    if separada <= 0 or not planejado:
        return None
    bp = Decimal(separada - planejado) * 10000 / Decimal(planejado)
    return int(bp.quantize(Decimal(1), rounding=ROUND_HALF_UP))


# ===========================================================================
# LEITURA (D1-D5, D15, D17; secao 6.2)
# ===========================================================================

def _montar_linha(item: OrdemServicoItem, produto: Optional[Produto],
                  planejado: Optional[InsumoDaOS], cobertura) -> dict[str, Any]:
    """Uma linha da separacao (secao 6.2). Nenhum campo de preco (D22)."""
    nao_usado = _nao_usado(item)
    quantidade = _mil(item.quantidade)
    separada = _mil(item.quantidade_separada)
    falta = 0 if nao_usado else max(quantidade - separada, 0)      # o que ainda sai do estoque
    saldo = produto.estoque.quantidade if produto is not None and produto.estoque is not None else 0
    sugerido = planejado.sugerido_milesimos if planejado else None
    # D17: a cobertura e a do Compras ("Compras desta OS"); linha concluida ou
    # nao usada nao esta na conta dele e fica com zeros, o que e o certo.
    no_estoque = _mil(cobertura.no_estoque) if cobertura else 0
    em_pedido = _mil(cobertura.em_pedido) if cobertura else 0
    sem_cobertura = _mil(cobertura.falta) if cobertura else 0

    alertas = []
    if sem_cobertura > 0:
        alertas.append(ALERTA_SEM_COBERTURA)
    if (saldo or 0) < 0:
        alertas.append(ALERTA_ESTOQUE_NEGATIVO)
    if sugerido is not None and separada > sugerido:
        alertas.append(ALERTA_ACIMA_DO_SUGERIDO)

    return {
        "item_id": item.id,
        "produto_id": item.produto_id,
        "descricao": item.nome,
        "codigo": produto.codigo_produto if produto else None,
        "unidade": _unidade(produto, planejado),
        "localizacao": (produto.localizacao_estoque or None) if produto else None,
        "planejado_milesimos": planejado.planejado_milesimos if planejado else None,
        "sugerido_milesimos": sugerido,
        "quantidade_milesimos": quantidade,
        "separada_milesimos": separada,
        "falta_milesimos": falta,
        "concluida": nao_usado or falta == 0,
        "nao_usado": nao_usado,
        "no_estoque_milesimos": no_estoque,
        "em_pedido_milesimos": em_pedido,
        "sem_cobertura_milesimos": sem_cobertura,
        "estoque_milesimos": _mil(saldo),
        "diferenca_bp": _diferenca_bp(separada, planejado.planejado_milesimos if planejado else None),
        # D5: quais moveis usam o produto e quanto cada um planejou.
        "moveis": [
            {"nome": movel, "ambiente": ambiente, "planejado_milesimos": qtd}
            for movel, ambiente, qtd in (planejado.moveis if planejado else ())
        ],
        "alertas": alertas,
    }


def _ordem_do_deposito(linha: dict) -> tuple:
    """D4: pela localizacao (quem separa anda pelo deposito uma vez), depois o nome.

    Sem localizacao vai para o FIM (o `True` ordena depois do `False`).
    """
    local = linha["localizacao"] or ""
    return (not local, local.casefold(), linha["descricao"].casefold(), linha["item_id"])


def _separacao(db: Session, os_: OrdemServico, orc: MarcenariaOrcamento) -> dict[str, Any]:
    """A separacao inteira (secao 6.2). Toda escrita devolve isto (secao 6.1)."""
    itens = _itens(os_)
    produtos, planejados = _planejados(db, orc, itens)
    # D17: UMA chamada ao Compras por leitura (e servico, nao rota: nao exige o modulo).
    cobertura = {c.produto_id: c for c in demanda_os.compras_da_os(db, os_.id).itens} if itens else {}
    linhas = [
        _montar_linha(i, produtos.get(i.produto_id), planejados.get(i.produto_id), cobertura.get(i.produto_id))
        for i in itens
    ]
    linhas.sort(key=_ordem_do_deposito)
    return {
        "os": {"numero_os": os_.numero_os, "status": _valor(os_.status), "editavel": _aberta(os_)},
        "linhas": linhas,
        # D3: insumo cujo produto foi excluido: so informa, nao baixa estoque.
        "sem_cadastro": [
            {"descricao": descricao, "planejado_milesimos": planejado}
            for descricao, planejado in insumos_sem_produto(orc)
        ],
        "resumo": {
            "linhas": len(linhas),
            "concluidas": sum(1 for linha in linhas if linha["concluida"]),
            # "Com falta" = o que nem o estoque nem pedido cobrem (as faltas da OS, D18).
            "com_falta": sum(1 for linha in linhas if linha["sem_cobertura_milesimos"] > 0),
        },
    }


def ler(db: Session, numero_os: str) -> dict[str, Any]:
    """GET /os/{numero_os}/separacao."""
    os_, orc = _os_e_orcamento(db, numero_os)
    return _separacao(db, os_, orc)


# ===========================================================================
# ESCRITAS: retirar, devolver, concluir, reabrir (D6-D14, D16)
# ===========================================================================

def _preparar_escrita(db: Session, numero_os: str, item_id: int) -> tuple:
    """OS aberta (D14) e o item, que tem de ser uma linha da separacao desta OS."""
    os_, orc = _os_e_orcamento(db, numero_os)
    if not _aberta(os_):
        erros.conflito(OS_FECHADA, MSG_OS_FECHADA)
    item = next((i for i in _itens(os_) if i.id == item_id), None)
    if item is None:
        erros.nao_encontrado(MSG_FORA_DA_OS)
    return os_, orc, item


def _gravar_separada(db: Session, item: OrdemServicoItem, esperada_milesimos: int,
                     nova: Optional[float]) -> None:
    """Trava de concorrencia (D16): grava a nova `quantidade_separada` SO se a
    do banco ainda for a que a tela tinha.

    E um UPDATE condicional (compara e grava num comando so): dois marceneiros
    clicando "Retirar" ao mesmo tempo nao tiram a mesma chapa duas vezes; o
    segundo recebe 409 e nada muda (o endpoint desfaz a transacao).
    """
    resultado = db.execute(
        update(OrdemServicoItem)
        .where(
            OrdemServicoItem.id == item.id,
            func.round(func.coalesce(OrdemServicoItem.quantidade_separada, 0) * 1000) == esperada_milesimos,
        )
        .values(quantidade_separada=nova)
        .execution_options(synchronize_session=False)
    )
    if resultado.rowcount != 1:
        erros.conflito(erros.REVISAO_DESATUALIZADA, MSG_CONCORRENCIA)
    item.quantidade_separada = nova                    # o objeto da sessao acompanha o banco


def _movimentar(db: Session, os_: OrdemServico, orc: MarcenariaOrcamento, produto: Optional[Produto],
                tipo: MovimentacaoTipo, quantidade: float, usuario: dict) -> None:
    """O livro de estoque de sempre, ligado a OS (E2): o CMV da OS enxerga (F2a)."""
    movimentacao_estoque.registrar_movimentacao(
        db, produto=produto, tipo=tipo, quantidade=quantidade,
        origem=MovimentacaoOrigem.ORDEM_SERVICO, ordem_servico_id=os_.id,
        usuario_id=usuario_id(usuario), usuario_nome=usuario_nome(usuario),
        observacao=f"Separação marcenaria {orc.codigo} (OS {os_.numero_os})",
        # D8: a chapa ja esta na mao; saldo negativo e contagem a acertar, nao trava.
        permitir_negativo=True,
    )


def _evento(db: Session, orc, os_, item, tipo: str, frase: str, usuario: dict, **dados) -> None:
    """D13: o historico da marcenaria conta quem fez o que, e quanto."""
    registrar_evento(db, orc, tipo, frase, usuario,
                     {"item_id": item.id, "produto_id": item.produto_id, **dados}, os_id=os_.id)


def retirar(db: Session, numero_os: str, item_id: int, dados: MovimentoEntrada, usuario: dict) -> dict:
    """D6-D8: tira do estoque (SAIDA ligada a OS) e soma em `quantidade_separada`."""
    os_, orc, item = _preparar_escrita(db, numero_os, item_id)
    if _nao_usado(item):
        erros.conflito(ITEM_NAO_USADO, MSG_NAO_USADO)
    if dados.quantidade_milesimos <= 0:
        erros.invalido(MSG_QUANTIDADE)

    q = dados.quantidade_milesimos / 1000              # o livro e o item sao Float
    antes = item.quantidade_separada or 0
    depois = round(antes + q, 3)                       # 3 casas, como o estoque
    _gravar_separada(db, item, dados.separada_esperada_milesimos, depois)     # D16

    produto = db.get(Produto, item.produto_id)
    # D6: custo medio do estoque NO INSTANTE, ponderado pelas retiradas. Fica
    # gravado para um relatorio de margem real futuro; nenhuma tela mostra (P4).
    custo_agora = (movimentacao_estoque.custo_atual(produto.estoque) if produto else None) or 0
    _movimentar(db, os_, orc, produto, MovimentacaoTipo.SAIDA, q, usuario)
    item.custo_real = round(((item.custo_real or 0) * antes + custo_agora * q) / depois)
    if depois > (item.quantidade or 0):
        # D7: retirou mais que o sugerido: a OS consome o que saiu (a tela avisa).
        item.quantidade = depois

    unidade = _unidade(produto, None)
    _evento(db, orc, os_, item, "MATERIAL_RETIRADO",
            f"Retirado do estoque: {_texto(dados.quantidade_milesimos)} {unidade} de {item.nome}.",
            usuario, quantidade_milesimos=dados.quantidade_milesimos)
    db.commit()
    return _separacao(db, os_, orc)


def devolver(db: Session, numero_os: str, item_id: int, dados: MovimentoEntrada, usuario: dict) -> dict:
    """D9: volta ao estoque (ENTRADA ligada a OS) e a OS deixa de precisar disso.

    "Devolver" quer dizer "isto nao vai ser usado": a `quantidade` cai junto,
    para a finalizacao nao baixar de novo o que voltou. Se cairia a zero, a
    linha vira "nao usado" (D11) e a quantidade fica (a coluna exige > 0).
    """
    os_, orc, item = _preparar_escrita(db, numero_os, item_id)
    if dados.quantidade_milesimos <= 0:
        erros.invalido(MSG_QUANTIDADE)
    retirado = _mil(item.quantidade_separada)
    if dados.quantidade_milesimos > retirado:
        erros.invalido(f"Não é possível devolver mais do que foi retirado ({_texto(retirado)}).")

    q = dados.quantidade_milesimos / 1000
    restante = round((item.quantidade_separada or 0) - q, 3)
    _gravar_separada(db, item, dados.separada_esperada_milesimos, restante if restante > 0 else None)
    if item.quantidade_separada is None:
        item.custo_real = None                         # nada retirado: nada a custear

    produto = db.get(Produto, item.produto_id)
    _movimentar(db, os_, orc, produto, MovimentacaoTipo.ENTRADA, q, usuario)
    nova_quantidade = round((item.quantidade or 0) - q, 3)
    if nova_quantidade > 0:
        item.quantidade = nova_quantidade
    else:
        item.status_aprovacao = OrdemServicoItemAprovacao.REPROVADO     # "nao usado" (D11)

    unidade = _unidade(produto, None)
    _evento(db, orc, os_, item, "MATERIAL_DEVOLVIDO",
            f"Devolvido ao estoque: {_texto(dados.quantidade_milesimos)} {unidade} de {item.nome}.",
            usuario, quantidade_milesimos=dados.quantidade_milesimos)
    db.commit()
    return _separacao(db, os_, orc)


def concluir(db: Session, numero_os: str, item_id: int, dados: ConferenciaEntrada, usuario: dict) -> dict:
    """D10-D11: encerra a linha com o que saiu de verdade.

    - usou MENOS que a quantidade: `quantidade := separada` (a reserva do
      Compras solta a diferenca e a finalizacao nao a baixa);
    - nao retirou NADA: a linha vira "nao usado" (REPROVADO), quantidade intacta.
    Linha ja concluida: nada muda (nem historico).
    """
    os_, orc, item = _preparar_escrita(db, numero_os, item_id)
    _gravar_separada(db, item, dados.separada_esperada_milesimos, item.quantidade_separada)   # D16
    separada = item.quantidade_separada or 0
    if _nao_usado(item) or (separada > 0 and separada >= (item.quantidade or 0)):
        return _separacao(db, os_, orc)                # ja estava concluida

    produto = db.get(Produto, item.produto_id)
    unidade = _unidade(produto, None)
    if separada > 0:
        eram = _mil(item.quantidade)                   # o que a OS ia consumir antes
        item.quantidade = separada
        frase = (f"Separação de {item.nome} concluída com {_texto(_mil(separada))} {unidade} "
                 f"(eram {_texto(eram)}).")
    else:
        item.status_aprovacao = OrdemServicoItemAprovacao.REPROVADO
        frase = f"{item.nome}: marcado como não usado nesta OS."
    _evento(db, orc, os_, item, "SEPARACAO_CONCLUIDA", frase, usuario)
    db.commit()
    return _separacao(db, os_, orc)


def reabrir(db: Session, numero_os: str, item_id: int, dados: ConferenciaEntrada, usuario: dict) -> dict:
    """D12: desfaz um "concluir" por engano: volta ao sugerido (ou ao retirado, se maior)."""
    os_, orc, item = _preparar_escrita(db, numero_os, item_id)
    _gravar_separada(db, item, dados.separada_esperada_milesimos, item.quantidade_separada)   # D16
    _produtos, planejados = _planejados(db, orc, [item])
    planejado = planejados.get(item.produto_id)
    sugerido = planejado.sugerido_milesimos / 1000 if planejado else (item.quantidade or 0)
    item.status_aprovacao = OrdemServicoItemAprovacao.APROVADO
    item.quantidade = max(sugerido, item.quantidade_separada or 0)
    _evento(db, orc, os_, item, "SEPARACAO_REABERTA", f"Separação de {item.nome} reaberta.", usuario)
    db.commit()
    return _separacao(db, os_, orc)


# ===========================================================================
# LEITOR (D20), FALTAS DA OS (D18) E DISPONIVEL (D19)
# ===========================================================================

def ler_codigo(db: Session, numero_os: str, codigo: str) -> dict[str, Any]:
    """GET /separacao/ler?codigo=: a linha do que foi lido e o FATOR da embalagem.

    So procura entre as linhas desta OS. Linha concluida tambem volta (com
    `concluida: true`): a tela avisa em vez de dizer que nao achou.
    """
    os_, orc = _os_e_orcamento(db, numero_os)
    if not (codigo or "").strip():
        erros.invalido(MSG_SEM_CODIGO)
    achado = leitor.achar(db, _itens(os_), codigo)
    if achado is None:
        erros.nao_encontrado(MSG_FORA_DA_OS)
    item, fator = achado
    linha = next(linha for linha in _separacao(db, os_, orc)["linhas"] if linha["item_id"] == item.id)
    return {"fator": fator, "linha": linha}


def faltas(db: Session, numero_os: str) -> dict[str, Any]:
    """D18: o que nem o estoque nem pedido cobrem, para imprimir e comprar.

    Responde igual com ou sem o modulo Compras (a lista ENTRE OS e o pedido sao
    dele, E5a). Cada item leva o fornecedor principal do produto.
    """
    os_, orc = _os_e_orcamento(db, numero_os)
    separacao = _separacao(db, os_, orc)
    com_falta = [linha for linha in separacao["linhas"] if linha["sem_cobertura_milesimos"] > 0]
    produtos = crud.buscar_por_ids(db, Produto, [linha["produto_id"] for linha in com_falta])
    itens = []
    for linha in com_falta:
        fornecedor = getattr(produtos.get(linha["produto_id"]), "fornecedor", None)
        itens.append({
            "produto_id": linha["produto_id"],
            "descricao": linha["descricao"],
            "unidade": linha["unidade"],
            "faltam_milesimos": linha["sem_cobertura_milesimos"],
            "localizacao": linha["localizacao"],
            "fornecedor": None if fornecedor is None else {
                "id": fornecedor.id,
                "nome": fornecedor.nome,
                "telefone": fornecedor.celular or fornecedor.telefone,
            },
        })
    return {
        "numero_os": os_.numero_os,
        "cliente": nome_do_cliente(os_.cliente) or nome_do_cliente(orc.cliente) or None,
        "itens": itens,
        # Hora local da loja (vai impressa na folha), sem fuso e sem microssegundos.
        "gerado_em": datetime.now(fuso_local()).replace(tzinfo=None, microsecond=0).isoformat(),
    }


def disponivel(db: Session, produto_ids: list[int]) -> dict[int, dict[str, int]]:
    """D19: para a busca de insumo do orcamento: estoque, reservado e disponivel.

    `reservado` e a conta do Compras sobre TODAS as OS abertas (E1b): a
    marcenaria so da a forma da resposta. Produto inexistente fica de fora.
    """
    exigir_orcamento_tecnico(db)
    produtos = crud.buscar_por_ids(db, Produto, produto_ids)
    demandas = demanda_os.demandas_por_produto(db, list(produtos))
    saida = {}
    for produto_id in dict.fromkeys(produto_ids):                  # sem repetir, na ordem pedida
        produto = produtos.get(produto_id)
        if produto is None:
            continue
        estoque = _mil(produto.estoque.quantidade if produto.estoque is not None else 0)
        reservado = _mil(demanda_os.reservado(demandas.get(produto_id, [])))
        saida[produto_id] = {
            "estoque_milesimos": estoque,
            "reservado_milesimos": reservado,
            "disponivel_milesimos": estoque - reservado,
        }
    return saida


# ===========================================================================
# GANCHO DO CANCELAMENTO DA OS (D24)
# ===========================================================================

def avisar_material_no_cancelamento(db: Session, os_, usuario: Optional[dict], contexto: Optional[dict] = None) -> None:
    """Cancelar a OS NAO devolve o material (03A D15, E2a: chapa cortada nao volta
    a prateleira); aqui so fica escrito no historico o que continua fora.

    Roda dentro da transacao do cancelamento (sem commit). OS de outro
    segmento (ou sem orcamento) sai na hora.
    """
    orc = crud.get_orcamento_por_os(db, os_.id)
    if orc is None:
        return
    retirados = [i for i in _itens(os_) if (i.quantidade_separada or 0) > 0]
    if not retirados:
        return
    produtos = crud.buscar_por_ids(db, Produto, [i.produto_id for i in retirados])
    lista = ", ".join(
        f"{_texto(_mil(i.quantidade_separada))} {_unidade(produtos.get(i.produto_id), None)} {i.nome}"
        for i in retirados
    )
    registrar_evento(
        db, orc, "MATERIAL_FORA_DO_ESTOQUE",
        f"Material retirado para esta OS continua fora do estoque: {lista}.",
        usuario,
        {"itens": [{"item_id": i.id, "separada_milesimos": _mil(i.quantidade_separada)} for i in retirados]},
        os_id=os_.id,
    )
