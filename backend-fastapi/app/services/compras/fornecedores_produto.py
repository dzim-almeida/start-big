# ---------------------------------------------------------------------------
# ARQUIVO: app/services/compras/fornecedores_produto.py
# MÓDULO: Service — De quem a loja compra cada produto (Compras, fase 1)
# ---------------------------------------------------------------------------
"""
Três entradas para a mesma tabela (`produto_fornecedores`):

1. `listar` / `salvar` — a aba Fornecedores do produto (só com o módulo
   COMPRAS; a trava fica no router).
2. `registrar_compra` — chamada pela entrada por XML a cada item lançado,
   COM OU SEM o módulo. É de propósito: quando a loja contratar Compras, o
   histórico de preço de cada fornecedor já está lá, e o aviso de "mais barato"
   (D18) funciona no primeiro dia. Para quem não tem o módulo, nada aparece.

O fornecedor PRINCIPAL é o `produtos.fornecedor_id` (ver o model). Marcar uma
linha como principal muda esse campo; tirar a marca não o apaga — o cadastro
do produto continua dono dele.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional, Union

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models.estoque import Estoque
from app.db.models.fornecedor import Fornecedor
from app.db.models.produto import Produto
from app.db.models.produto_embalagem import ProdutoEmbalagem
from app.db.models.produto_fornecedor import ProdutoFornecedor
from app.schemas.compras import (
    EmbalagemResumo,
    FornecedorDoProdutoRead,
    FornecedoresDoProdutoSalvar,
    FornecedorResumo,
    ProdutoParaPedido,
)
from app.services.compras.necessidade import (
    OfertaFornecedor,
    economia_percentual,
    mais_barato,
    preco_por_unidade,
)

# Fornecedor de produto: o cadastro também guarda transportadora e entregador
# (`fornecedores.tipo`), que não vendem mercadoria. Nulo = cadastro antigo.
TIPOS_QUE_VENDEM = (None, "produto")


def _erro(codigo: int, detalhe: str) -> HTTPException:
    return HTTPException(status_code=codigo, detail=detalhe)


def _produto(db: Session, produto_id: int) -> Produto:
    produto = db.get(Produto, produto_id)
    if produto is None:
        raise _erro(status.HTTP_404_NOT_FOUND, "Produto não encontrado.")
    return produto


def _nome(fornecedor: Fornecedor) -> str:
    return fornecedor.nome_fantasia or fornecedor.nome


def listar_fornecedores_que_vendem(db: Session) -> list[FornecedorResumo]:
    """Fornecedores ativos que vendem mercadoria, para o seletor da aba."""
    fornecedores = db.scalars(
        select(Fornecedor)
        .where(Fornecedor.ativo.is_(True))
        .where((Fornecedor.tipo.is_(None)) | (Fornecedor.tipo == "produto"))
        .order_by(Fornecedor.nome)
    ).all()
    return [FornecedorResumo(id=f.id, nome=f.nome, nome_fantasia=f.nome_fantasia) for f in fornecedores]


def listar(db: Session, produto_id: int, ver_custos: bool) -> list[FornecedorDoProdutoRead]:
    produto = _produto(db, produto_id)
    linhas = db.scalars(
        select(ProdutoFornecedor).where(ProdutoFornecedor.produto_id == produto.id).order_by(ProdutoFornecedor.id)
    ).unique().all()

    ofertas = [OfertaFornecedor(l.fornecedor_id, l.ultimo_preco, l.fator) for l in linhas]
    vencedor = mais_barato(ofertas)
    menor = next(
        (preco_por_unidade(l.ultimo_preco, l.fator) for l in linhas if l.fornecedor_id == vencedor), None
    )

    saida: list[FornecedorDoProdutoRead] = []
    for l in linhas:
        unidade = preco_por_unidade(l.ultimo_preco, l.fator) if l.ultimo_preco is not None else None
        saida.append(FornecedorDoProdutoRead(
            id=l.id,
            fornecedor_id=l.fornecedor_id,
            fornecedor_nome=_nome(l.fornecedor),
            codigo_fornecedor=l.codigo_fornecedor,
            embalagem_id=l.embalagem_id,
            embalagem_sigla=l.embalagem.sigla if l.embalagem else None,
            fator=l.fator,
            ultimo_preco=l.ultimo_preco if ver_custos else None,
            preco_unidade=float(unidade) if ver_custos and unidade is not None else None,
            ultima_compra_em=l.ultima_compra_em,
            prazo_dias=l.prazo_dias,
            padrao=l.fornecedor_id == produto.fornecedor_id,
            # O ranking também revela preço: some junto com ele (D14).
            mais_barato=ver_custos and l.fornecedor_id == vencedor,
            acima_do_menor_bp=(
                economia_percentual(unidade, menor) if ver_custos and unidade is not None and menor is not None else 0
            ),
        ))

    # O principal do cadastro aparece mesmo sem linha aqui: é o primeiro que o
    # lojista espera ver, e completar o código/preço dele é o caso mais comum.
    ja_listados = {l.fornecedor_id for l in linhas}
    if produto.fornecedor_id and produto.fornecedor_id not in ja_listados and produto.fornecedor is not None:
        saida.insert(0, FornecedorDoProdutoRead(
            fornecedor_id=produto.fornecedor_id,
            fornecedor_nome=_nome(produto.fornecedor),
            padrao=True,
        ))
    return saida


def _validar_fornecedor(db: Session, fornecedor_id: int) -> Fornecedor:
    fornecedor = db.get(Fornecedor, fornecedor_id)
    if fornecedor is None:
        raise _erro(status.HTTP_404_NOT_FOUND, f"Fornecedor {fornecedor_id} não encontrado.")
    if fornecedor.tipo not in TIPOS_QUE_VENDEM:
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"'{_nome(fornecedor)}' está cadastrado como {fornecedor.tipo}, não como fornecedor de produto.",
        )
    return fornecedor


def _embalagem(produto: Produto, embalagem_id: Optional[int]) -> Optional[ProdutoEmbalagem]:
    if embalagem_id is None:
        return None
    embalagem = next((e for e in produto.embalagens if e.id == embalagem_id), None)
    if embalagem is None or not embalagem.ativo:
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"A embalagem escolhida não é do produto '{produto.nome}' ou está inativa.",
        )
    return embalagem


def salvar(
    db: Session, produto_id: int, dados: FornecedoresDoProdutoSalvar, ver_custos: bool
) -> list[FornecedorDoProdutoRead]:
    """Replace-all pela chave `fornecedor_id`: atualiza, cria e apaga o que não veio.

    Sem permissão de custo, o preço que vier é IGNORADO e o salvo é mantido —
    senão quem não vê o preço o apagaria ao salvar a lista.
    """
    produto = _produto(db, produto_id)
    existentes = {
        l.fornecedor_id: l
        for l in db.scalars(select(ProdutoFornecedor).where(ProdutoFornecedor.produto_id == produto.id)).unique()
    }

    # Valida tudo antes de mexer em qualquer linha.
    embalagens: dict[int, Optional[ProdutoEmbalagem]] = {}
    for item in dados.fornecedores:
        _validar_fornecedor(db, item.fornecedor_id)
        embalagens[item.fornecedor_id] = _embalagem(produto, item.embalagem_id)

    manter = {item.fornecedor_id for item in dados.fornecedores}
    for fornecedor_id, linha in existentes.items():
        if fornecedor_id not in manter:
            db.delete(linha)
    db.flush()

    for item in dados.fornecedores:
        linha = existentes.get(item.fornecedor_id)
        if linha is None:
            linha = ProdutoFornecedor(produto_id=produto.id, fornecedor_id=item.fornecedor_id)
            db.add(linha)
        embalagem = embalagens[item.fornecedor_id]
        linha.codigo_fornecedor = item.codigo_fornecedor
        linha.embalagem_id = embalagem.id if embalagem else None
        # A embalagem manda no fator: é o cadastro dizendo quantas unidades ela tem.
        linha.fator = embalagem.fator if embalagem else item.fator
        linha.prazo_dias = item.prazo_dias
        if ver_custos:
            linha.ultimo_preco = item.ultimo_preco
        if item.padrao:
            produto.fornecedor_id = item.fornecedor_id
    db.flush()
    db.expire_all()
    return listar(db, produto.id, ver_custos)


def registrar_compra(
    db: Session,
    *,
    produto_id: int,
    fornecedor_id: int,
    custo_total: int,
    unidades: Union[int, float, Decimal],
    fator: int,
    embalagem_id: Optional[int],
    codigo_fornecedor: Optional[str],
    data: Optional[date],
) -> None:
    """Guarda o preço pago a este fornecedor (chamada pela entrada por XML).

    - custo_total: o que o item custou, em centavos (com impostos e frete, D6
      da XML), para `unidades` unidades do produto;
    - a linha existente MANTÉM a embalagem que o lojista configurou: o preço é
      convertido para ela (custo por unidade × fator da linha);
    - linha nova nasce com a embalagem e o código da própria nota.
    """
    unidades = Decimal(str(unidades))
    if unidades <= 0 or custo_total < 0:
        return

    linha = db.scalars(
        select(ProdutoFornecedor).where(
            ProdutoFornecedor.produto_id == produto_id,
            ProdutoFornecedor.fornecedor_id == fornecedor_id,
        )
    ).first()
    if linha is None:
        linha = ProdutoFornecedor(
            produto_id=produto_id,
            fornecedor_id=fornecedor_id,
            embalagem_id=embalagem_id,
            fator=max(fator, 1),
        )
        db.add(linha)
        # Já no banco: o mesmo produto pode vir em dois itens da mesma nota, e a
        # sessão não faz autoflush — sem o flush, a segunda busca não veria esta
        # linha, criaria outra e o UNIQUE derrubaria a importação. Hoje a XML
        # está protegida por tabela (o livro de estoque dá flush a cada item),
        # mas o recebimento da fase 3 vai chamar daqui por outro caminho.
        db.flush()
    if not linha.codigo_fornecedor and codigo_fornecedor:
        linha.codigo_fornecedor = codigo_fornecedor[:60]

    por_unidade = Decimal(custo_total) / unidades
    linha.ultimo_preco = int((por_unidade * (linha.fator or 1)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    linha.ultima_compra_em = data or date.today()


def buscar_produtos(db: Session, busca: str, limite: int = 20) -> list[ProdutoParaPedido]:
    """Produtos ativos com estoque, por nome, código ou código de barras (inclui o da embalagem).

    Rota do próprio módulo: o comprador pode não ter a permissão de Produtos,
    e montar um pedido não exige ver o cadastro inteiro.
    """
    termo = (busca or "").strip()
    if not termo:
        return []
    por_embalagem = select(ProdutoEmbalagem.produto_id).where(ProdutoEmbalagem.codigo_barras == termo)
    produtos = db.scalars(
        select(Produto)
        .join(Estoque, Estoque.id == Produto.id)
        .where(
            Produto.ativo.is_(True),
            or_(
                Produto.nome.ilike(f"%{termo}%"),
                Produto.codigo_produto.ilike(f"%{termo}%"),
                Produto.codigo_barras == termo,
                Produto.id.in_(por_embalagem),
            ),
        )
        .order_by(Produto.nome)
        .limit(limite)
    ).all()
    return [
        ProdutoParaPedido(
            id=p.id,
            nome=p.nome,
            codigo_produto=p.codigo_produto,
            codigo_barras=p.codigo_barras,
            unidade_medida=p.unidade_medida or "UN",
            saldo=p.estoque.quantidade or 0,
            embalagens=[EmbalagemResumo(id=e.id, sigla=e.sigla, fator=e.fator) for e in p.embalagens if e.ativo],
        )
        for p in produtos
    ]
