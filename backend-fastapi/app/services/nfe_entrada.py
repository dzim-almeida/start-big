# ---------------------------------------------------------------------------
# ARQUIVO: app/services/nfe_entrada.py
# MÓDULO: Service — Entrada de mercadoria pela XML da NF-e do fornecedor
# ---------------------------------------------------------------------------
"""
Duas operações (docs/entrada-xml-nfe-plano.md, D1/D2):

- `ler`: lê o XML e devolve a prévia com a sugestão de cada item. NÃO grava.
- `importar`: relê o MESMO XML e grava tudo numa transação — fornecedor,
  produtos novos, entradas no livro de estoque (com o custo real), o De-Para
  do fornecedor, a nota (chave única) e as parcelas a pagar.

Quantidade e custo vêm SEMPRE do XML relido aqui, nunca da tela: a tela só
decide QUAL produto, embalagem e fator. Assim uma tela velha ou adulterada não
consegue dar entrada em mais do que a nota diz.
"""

from typing import Any, Optional

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import nfe_xml
from app.core.enum import ContaPagarStatus, EntityType, MovimentacaoOrigem, MovimentacaoTipo, State
from app.core.segregacao_receita import CRT_QUE_USAM_CSOSN
from app.db.models.conta_pagar import ContaPagar
from app.db.models.empresa import Empresa
from app.db.models.endereco import Endereco
from app.db.models.fornecedor import Fornecedor
from app.db.models.nota_entrada import NotaEntrada
from app.db.models.produto import Produto
from app.db.models.produto_codigo_fornecedor import ProdutoCodigoFornecedor
from app.db.models.produto_embalagem import ProdutoEmbalagem
from app.schemas.estoque import EstoqueCreate
from app.schemas.nfe_entrada import (
    DecisaoItem,
    DuplicataPrevia,
    EntradaLancada,
    FiscalSugerido,
    FornecedorPrevia,
    ImportarNota,
    ItemPrevia,
    NotaPrevia,
    PedidoAbertoPrevia,
    ProdutoPrevia,
    ResultadoImportacao,
)
from app.schemas.produto import ProdutoCreateComFiscal
from app.schemas.produto_fiscal import ProdutoFiscalUpdate
from app.services.compras import fornecedores_produto as compras_fornecedores

# Teto do arquivo: uma NF-e com 990 itens (o máximo) fica bem abaixo disto.
TAMANHO_MAXIMO = 5 * 1024 * 1024


def _ler(conteudo: bytes | str) -> nfe_xml.NotaLida:
    if len(conteudo) > TAMANHO_MAXIMO:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "O arquivo é grande demais para uma NF-e.")
    try:
        return nfe_xml.ler_nfe(conteudo)
    except nfe_xml.NotaInvalida as erro:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(erro))


# ---------------------------------------------------------------------------
# Quem é quem
# ---------------------------------------------------------------------------

def _fornecedor_por_documento(db: Session, documento: Optional[str]) -> Optional[Fornecedor]:
    if not documento:
        return None
    campo = Fornecedor.cnpj if len(documento) == 14 else Fornecedor.cpf
    return db.scalars(select(Fornecedor).where(campo == documento)).first()


def _reconhecer(
    db: Session, fornecedor: Optional[Fornecedor], item: nfe_xml.ItemNota
) -> tuple[Optional[Produto], Optional[ProdutoEmbalagem], int, Optional[str]]:
    """(produto, embalagem, fator, como reconheceu) — a ordem da D4."""
    if fornecedor is not None and item.codigo:
        vinculo = db.scalars(
            select(ProdutoCodigoFornecedor).where(
                ProdutoCodigoFornecedor.fornecedor_id == fornecedor.id,
                ProdutoCodigoFornecedor.codigo_fornecedor == item.codigo,
            )
        ).first()
        if vinculo is not None:
            produto = db.get(Produto, vinculo.produto_id)
            if produto is not None and produto.ativo:
                embalagem = db.get(ProdutoEmbalagem, vinculo.embalagem_id) if vinculo.embalagem_id else None
                if embalagem is not None and not embalagem.ativo:
                    embalagem = None
                return produto, embalagem, vinculo.fator or 1, "vinculo"

    for codigo in (item.ean, item.ean_tributavel):
        if not codigo:
            continue
        embalagem = db.scalars(
            select(ProdutoEmbalagem).where(
                ProdutoEmbalagem.codigo_barras == codigo, ProdutoEmbalagem.ativo.is_(True)
            )
        ).first()
        if embalagem is not None and embalagem.produto.ativo:
            # O código do FARDO na nota: cada item da nota é uma embalagem.
            # Pelo cEANTrib (código da unidade) não acontece na prática.
            return embalagem.produto, embalagem, embalagem.fator, "embalagem"
        produto = db.scalars(
            select(Produto).where(Produto.codigo_barras == codigo, Produto.ativo.is_(True))
        ).first()
        if produto is not None:
            return produto, None, item.fator_sugerido(), "codigo_barras"

    return None, None, item.fator_sugerido(), None


def _fiscal_sugerido(crt: Optional[int], item: nfe_xml.ItemNota) -> FiscalSugerido:
    """D7: a nota do fornecedor é a melhor pista; quem confirma é o contador."""
    simples = crt in CRT_QUE_USAM_CSOSN or crt is None
    pis = "04" if item.monofasico else ("49" if simples else "01")
    return FiscalSugerido(
        ncm=item.ncm,
        cest=item.cest,
        csosn=("500" if item.tinha_st else "102") if simples else None,
        cst_icms=None if simples else ("60" if item.tinha_st else "00"),
        cfop_padrao="5405" if item.tinha_st else "5102",
        cst_pis=pis,
        cst_cofins=pis,
        icms_st=item.tinha_st,
        monofasico=item.monofasico,
    )


def _fator_suspeito(
    item: nfe_xml.ItemNota, fator: int, embalagem: Optional[ProdutoEmbalagem], por: Optional[str]
) -> bool:
    """"2 CX" entrando como 2 unidades: a unidade é de embalagem e ninguém disse o fator.

    Embalagem cadastrada e vínculo já confirmado contam como "alguém disse".
    """
    return item.unidade_de_embalagem and fator == 1 and embalagem is None and por != "vinculo"


def _custo_atual(produto: Produto) -> Optional[int]:
    estoque = produto.estoque
    if estoque is None:
        return None
    return estoque.custo_medio if estoque.custo_medio is not None else estoque.valor_entrada


def _empresa(db: Session, empresa_id: int) -> Optional[Empresa]:
    return db.get(Empresa, empresa_id)


def _financeiro_disponivel(db: Session) -> bool:
    """Mesma regra do `requer_modulo`: não saber (None ou []) libera."""
    from app.services import licenca as licenca_service

    modulos = licenca_service.modulos_da_licenca(db)
    return not modulos or "FINANCEIRO" in modulos


def _ja_importada(db: Session, chave: str) -> Optional[NotaEntrada]:
    return db.scalars(select(NotaEntrada).where(NotaEntrada.chave == chave)).first()


# ---------------------------------------------------------------------------
# Prévia
# ---------------------------------------------------------------------------

def ler(db: Session, conteudo: bytes, usuario_token: dict[str, Any]) -> NotaPrevia:
    nota = _ler(conteudo)
    empresa = _empresa(db, usuario_token["empresa_id"])
    crt = empresa.crt if empresa else None
    fornecedor = _fornecedor_por_documento(db, nota.emitente.documento)

    avisos: list[str] = []
    if empresa and empresa.documento and nota.destinatario_documento and (
        nota.destinatario_documento != empresa.documento
    ):
        avisos.append(
            "A nota foi emitida para outro CNPJ/CPF, não o desta loja. Confira se é mesmo daqui."
        )
    anterior = _ja_importada(db, nota.chave)
    if anterior is not None:
        avisos.append("Esta nota já foi importada. Importar de novo não é permitido.")

    itens = []
    for item in nota.itens:
        produto, embalagem, fator, por = _reconhecer(db, fornecedor, item)
        itens.append(ItemPrevia(
            indice=item.indice,
            codigo=item.codigo,
            descricao=item.descricao,
            ean=item.ean,
            ean_tributavel=item.ean_tributavel,
            unidade=item.unidade,
            quantidade=float(item.quantidade),
            custo_total=item.custo_total,
            reconhecido_por=por,
            produto=ProdutoPrevia(
                id=produto.id,
                nome=produto.nome,
                codigo_produto=produto.codigo_produto,
                custo_atual=_custo_atual(produto),
                valor_varejo=produto.estoque.valor_varejo if produto.estoque else None,
            ) if produto else None,
            embalagem_id=embalagem.id if embalagem else None,
            embalagem_sigla=embalagem.sigla if embalagem else None,
            fator=fator,
            fator_da_nota=item.fator_sugerido(),
            unidade_de_embalagem=item.unidade_de_embalagem,
            fator_a_confirmar=_fator_suspeito(item, fator, embalagem, por),
            fiscal_sugerido=_fiscal_sugerido(crt, item),
        ))

    pedidos_abertos, pedido_sugerido_id, pedido_avisos = _conferir_com_pedido(
        db, usuario_token, fornecedor, nota, itens
    )

    return NotaPrevia(
        chave=nota.chave,
        numero=nota.numero,
        serie=nota.serie,
        emissao=nota.emissao,
        natureza=nota.natureza,
        valor_total=nota.valor_total,
        fornecedor=FornecedorPrevia(
            id=fornecedor.id if fornecedor else None,
            documento=nota.emitente.documento,
            nome=nota.emitente.nome,
            fantasia=nota.emitente.fantasia,
        ),
        itens=itens,
        duplicatas=[DuplicataPrevia(numero=d.numero, vencimento=d.vencimento, valor=d.valor) for d in nota.duplicatas],
        financeiro_disponivel=_financeiro_disponivel(db),
        ja_importada_em=anterior.importada_em if anterior else None,
        avisos=avisos,
        pedidos_abertos=pedidos_abertos,
        pedido_sugerido_id=pedido_sugerido_id,
        pedido_avisos=pedido_avisos,
    )


def _conferir_com_pedido(
    db: Session,
    usuario_token: dict[str, Any],
    fornecedor: Optional[Fornecedor],
    nota: nfe_xml.NotaLida,
    itens: list[ItemPrevia],
) -> tuple[list[PedidoAbertoPrevia], Optional[int], list[str]]:
    """Módulo Compras (fase 4): os pedidos abertos do fornecedor e a conferência
    contra o mais recente. SEM o módulo, ou sem pedido aberto, devolve vazio —
    e a prévia fica exatamente como era antes do módulo existir.

    Os avisos de cada item vão para `ItemPrevia.pedido_avisos` (mexe na lista
    recebida); os do pedido inteiro (o que não veio) voltam no retorno.
    """
    from app.services.compras import nota_pedido

    if fornecedor is None or not nota_pedido.modulo_compras_ativo(db):
        return [], None, []
    abertos = nota_pedido.pedidos_abertos(db, usuario_token["empresa_id"], fornecedor.id)
    if not abertos:
        return [], None, []

    sugerido = abertos[0]
    por_indice = {i.indice: i for i in nota.itens}
    entradas = [
        nota_pedido.EntradaDaNota(
            produto_id=previa.produto.id,
            unidades=por_indice[previa.indice].quantidade * max(previa.fator, 1),
            custo_total=previa.custo_total,
        )
        for previa in itens
        if previa.produto is not None
    ]
    casamento = nota_pedido.casar(sugerido, entradas)
    avisos_por_produto = {l.item.produto_id: l.avisos for l in casamento.linhas}
    do_pedido = {i.produto_id for i in sugerido.itens}
    for previa in itens:
        if previa.produto is None:
            continue
        if previa.produto.id not in do_pedido:
            previa.pedido_avisos = [f"Não está no pedido {sugerido.codigo} (entra no estoque assim mesmo)."]
        else:
            previa.pedido_avisos = list(avisos_por_produto.get(previa.produto.id, []))

    gerais = [
        f"'{i.descricao}': o pedido espera {i.pendente} {i.unidade_compra} e não veio na nota."
        for i in casamento.nao_vieram
    ]
    lista = [
        PedidoAbertoPrevia(
            id=p.id, codigo=p.codigo, situacao=p.situacao,
            previsao_entrega=p.previsao_entrega, quantidade_itens=len(p.itens),
        )
        for p in abertos
    ]
    return lista, sugerido.id, gerais


# ---------------------------------------------------------------------------
# Importação
# ---------------------------------------------------------------------------

def _so_digitos(valor: Optional[str], tamanho: int) -> Optional[str]:
    if not valor:
        return None
    digitos = "".join(c for c in valor if c.isdigit())
    return digitos[:tamanho] or None


def _criar_fornecedor(db: Session, parte: nfe_xml.Parte) -> Fornecedor:
    """D9: o emitente vira fornecedor com o que a nota traz."""
    documento = parte.documento or ""
    ie = _so_digitos(parte.ie, 14)
    # IE é única no cadastro: se outro fornecedor já usa, não trava a nota por isso.
    if ie and db.scalars(select(Fornecedor).where(Fornecedor.ie == ie)).first():
        ie = None
    telefone = _so_digitos(parte.telefone, 11)
    fornecedor = Fornecedor(
        tipo="produto",
        nome=(parte.nome or "Fornecedor da NF-e")[:255],
        nome_fantasia=(parte.fantasia or None),
        cnpj=documento if len(documento) == 14 else None,
        cpf=documento if len(documento) == 11 else None,
        ie=ie,
        telefone=telefone if telefone and len(telefone) <= 10 else None,
        celular=telefone if telefone and len(telefone) == 11 else None,
        ativo=True,
    )
    db.add(fornecedor)
    db.flush()
    try:
        uf = State(parte.uf) if parte.uf else None
    except ValueError:
        uf = None
    if parte.logradouro and parte.cidade and uf:
        cep = _so_digitos(parte.cep, 8) or ""
        db.add(Endereco(
            id_entidade=fornecedor.id,
            tipo_entidade=EntityType.FORNECEDOR,
            logradouro=parte.logradouro[:255],
            numero=(parte.numero or "S/N")[:20],
            bairro=(parte.bairro or "-")[:100],
            cidade=parte.cidade[:100],
            estado=uf,
            cep=f"{cep[:5]}-{cep[5:]}" if len(cep) == 8 else cep,
        ))
        db.flush()
    return fornecedor


def _criar_produto(
    db: Session, decisao: DecisaoItem, item: nfe_xml.ItemNota, custo: int, crt: Optional[int],
    fornecedor: Fornecedor, usuario_token: dict[str, Any],
) -> Produto:
    from app.services import produto as produto_service

    novo = decisao.novo
    assert novo is not None
    fiscal = None
    if novo.usar_fiscal_sugerido:
        sugerido = _fiscal_sugerido(crt, item).model_dump(exclude={"icms_st", "monofasico"})
        try:
            fiscal = ProdutoFiscalUpdate(**sugerido)
        except ValidationError:
            # NCM/CEST fora do padrão na nota do fornecedor: o produto nasce
            # sem fiscal (como no cadastro manual) em vez de travar a entrada.
            fiscal = None
    try:
        dados = ProdutoCreateComFiscal(
            nome=novo.nome.strip(),
            codigo_produto=novo.codigo_produto.strip(),
            codigo_barras=(novo.codigo_barras or "").strip() or None,
            unidade_medida=novo.unidade_medida or "UN",
            fornecedor_id=fornecedor.id,
            # Nasce zerado: quem dá a entrada é a nota, logo em seguida, pelo livro.
            estoque=EstoqueCreate(valor_varejo=novo.valor_varejo, quantidade=0, valor_entrada=custo),
            fiscal=fiscal,
        )
    except ValidationError as erro:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Item {item.indice} ({item.descricao}): dados do produto novo inválidos — {erro.errors()[0]['msg']}",
        )
    return produto_service.create_produto(db, dados, usuario_token)


def _embalagem_do_produto(produto: Produto, embalagem_id: Optional[int]) -> Optional[ProdutoEmbalagem]:
    if embalagem_id is None:
        return None
    embalagem = next((e for e in produto.embalagens if e.id == embalagem_id), None)
    if embalagem is None or not embalagem.ativo:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"A embalagem escolhida não é do produto '{produto.nome}' ou está inativa.",
        )
    return embalagem


def _vinculo_com_fator_1(db: Session, fornecedor: Fornecedor, codigo: str, produto_id: int) -> bool:
    """O lojista já confirmou, numa nota anterior, que este item entra 1 por 1."""
    return db.scalars(
        select(ProdutoCodigoFornecedor).where(
            ProdutoCodigoFornecedor.fornecedor_id == fornecedor.id,
            ProdutoCodigoFornecedor.codigo_fornecedor == (codigo or "")[:60],
            ProdutoCodigoFornecedor.produto_id == produto_id,
            ProdutoCodigoFornecedor.fator == 1,
        )
    ).first() is not None


def _lembrar_vinculo(
    db: Session, fornecedor: Fornecedor, codigo: str, produto: Produto,
    embalagem: Optional[ProdutoEmbalagem], fator: int,
) -> None:
    if not codigo:
        return
    vinculo = db.scalars(
        select(ProdutoCodigoFornecedor).where(
            ProdutoCodigoFornecedor.fornecedor_id == fornecedor.id,
            ProdutoCodigoFornecedor.codigo_fornecedor == codigo[:60],
        )
    ).first()
    if vinculo is None:
        vinculo = ProdutoCodigoFornecedor(fornecedor_id=fornecedor.id, codigo_fornecedor=codigo[:60])
        db.add(vinculo)
    vinculo.produto_id = produto.id
    vinculo.embalagem_id = embalagem.id if embalagem else None
    vinculo.fator = fator


def importar(db: Session, dados: ImportarNota, usuario_token: dict[str, Any]) -> ResultadoImportacao:
    from app.services import movimentacao_estoque as mov_service

    nota = _ler(dados.xml)
    anterior = _ja_importada(db, nota.chave)
    if anterior is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Esta nota já foi importada em {anterior.importada_em:%d/%m/%Y %H:%M}"
            + (f" por {anterior.usuario_nome}" if anterior.usuario_nome else "") + ".",
        )

    por_indice = {i.indice: i for i in nota.itens}
    decisoes = {d.indice: d for d in dados.itens}
    faltando = sorted(set(por_indice) - set(decisoes))
    if faltando:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Falta decidir o que fazer com o(s) item(ns) {', '.join(map(str, faltando))}.",
        )
    estranhos = sorted(set(decisoes) - set(por_indice))
    if estranhos:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"A nota não tem o(s) item(ns) {estranhos}.")

    empresa_id = usuario_token["empresa_id"]
    empresa = _empresa(db, empresa_id)
    crt = empresa.crt if empresa else None
    usuario_nome = usuario_token.get("nome", "Desconhecido")

    fornecedor = _fornecedor_por_documento(db, nota.emitente.documento)
    fornecedor_criado = fornecedor is None
    if fornecedor is None:
        fornecedor = _criar_fornecedor(db, nota.emitente)
    elif not fornecedor.ativo:
        fornecedor.ativo = True  # comprou dele de novo

    # Módulo Compras (fase 4): o lojista ligou a nota a um pedido. Valida ANTES
    # de lançar qualquer item (módulo, situação, mesmo fornecedor).
    pedido = None
    if dados.pedido_id is not None:
        from app.services.compras import nota_pedido

        pedido = nota_pedido.validar_pedido_da_nota(db, usuario_token, dados.pedido_id, fornecedor.id)
    para_o_pedido: list = []
    movimentos_por_produto: dict[int, list] = {}

    registro = NotaEntrada(
        empresa_id=empresa_id,
        chave=nota.chave,
        numero=nota.numero[:9],
        serie=nota.serie[:3],
        emissao=nota.emissao,
        valor_total=nota.valor_total,
        fornecedor_id=fornecedor.id,
        fornecedor_nome=(nota.emitente.nome or "")[:255] or None,
        usuario_nome=usuario_nome,
    )
    db.add(registro)
    db.flush()

    observacao = f"NF-e {nota.numero}/{nota.serie} — {nota.emitente.fantasia or nota.emitente.nome or ''}".strip()[:500]
    movimentos: list[int] = []
    entradas: list[EntradaLancada] = []
    criados = ignorados = 0

    for indice in sorted(por_indice):
        item, decisao = por_indice[indice], decisoes[indice]
        if decisao.acao == "ignorar":
            ignorados += 1
            continue

        custo = nfe_xml.custo_por_unidade(item, decisao.fator)
        if decisao.acao == "criar":
            produto = _criar_produto(db, decisao, item, custo, crt, fornecedor, usuario_token)
            criados += 1
            embalagem = None
        else:
            produto = db.get(Produto, decisao.produto_id)
            if produto is None or not produto.ativo:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Item {indice}: produto não encontrado.")
            embalagem = _embalagem_do_produto(produto, decisao.embalagem_id)
        if produto.estoque is None:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Item {indice}: o produto '{produto.nome}' não controla estoque.",
            )
        # A embalagem manda no fator: é o cadastro dizendo quantas unidades ela tem.
        fator = embalagem.fator if embalagem else decisao.fator
        if (
            fator == 1
            and embalagem is None
            and item.unidade_de_embalagem
            and not decisao.fator_confirmado
            and not _vinculo_com_fator_1(db, fornecedor, item.codigo, produto.id)
        ):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Item {indice} ({item.descricao}): a nota diz {item.unidade}, mas não quantas unidades "
                f"vêm em cada {item.unidade}. Informe ou confirme que é 1.",
            )
        custo = nfe_xml.custo_por_unidade(item, fator)
        unidades = float(item.quantidade * fator)
        if unidades == int(unidades):
            unidades = int(unidades)

        movimento = mov_service.registrar_movimentacao(
            db,
            produto=produto,
            tipo=MovimentacaoTipo.ENTRADA,
            quantidade=unidades,
            origem=MovimentacaoOrigem.NFE_ENTRADA,
            usuario_id=int(usuario_token["sub"]) if usuario_token.get("sub") else None,
            usuario_nome=usuario_nome,
            observacao=observacao,
            custo_unitario=custo,
        )
        if movimento is None:
            ignorados += 1
            continue
        movimento.nota_entrada_id = registro.id
        if embalagem is not None:
            movimento.embalagem_id = embalagem.id
            movimento.embalagem_sigla = embalagem.sigla
            movimento.embalagem_fator = embalagem.fator
            if item.quantidade == item.quantidade.to_integral_value():
                movimento.quantidade_embalagem = int(item.quantidade)
        movimentos.append(movimento.id)
        entradas.append(EntradaLancada(produto_id=produto.id, unidades=unidades))
        _lembrar_vinculo(db, fornecedor, item.codigo, produto, embalagem, fator)
        # Último preço pago a este fornecedor (módulo Compras, docs/compras-plano.md
        # D13/D18). Grava com ou sem o módulo: quem contratar depois já encontra
        # o histórico. Sem o módulo, nenhuma tela lê isto.
        compras_fornecedores.registrar_compra(
            db,
            produto_id=produto.id,
            fornecedor_id=fornecedor.id,
            custo_total=item.custo_total,
            unidades=item.quantidade * fator,
            fator=fator,
            embalagem_id=embalagem.id if embalagem else None,
            codigo_fornecedor=item.codigo,
            data=nota.emissao,
        )
        if pedido is not None:
            from app.services.compras.nota_pedido import EntradaDaNota

            para_o_pedido.append(EntradaDaNota(produto.id, item.quantidade * fator, item.custo_total))
            movimentos_por_produto.setdefault(produto.id, []).append(movimento)

    contas = 0
    if dados.lancar_contas_pagar and nota.duplicatas and _financeiro_disponivel(db):
        contas = _lancar_duplicatas(db, empresa_id, nota, fornecedor)

    pedido_avisos: list[str] = []
    if pedido is not None:
        # Com duplicatas, as contas são as da nota (acima) e as parcelas do
        # pedido NÃO nascem — nunca em dobro (plano de compras, D8).
        pedido_avisos, contas_do_pedido = nota_pedido.receber_pela_nota(
            db, usuario_token, pedido,
            nota_entrada_id=registro.id,
            numero_nota=nota.numero,
            entradas=para_o_pedido,
            movimentos_por_produto=movimentos_por_produto,
            gerar_contas=dados.lancar_contas_pagar and not nota.duplicatas,
        )
        contas += contas_do_pedido

    registro.itens_lancados = len(movimentos)
    registro.contas_pagar_lancadas = contas
    db.flush()

    return ResultadoImportacao(
        nota_entrada_id=registro.id,
        fornecedor_id=fornecedor.id,
        fornecedor_criado=fornecedor_criado,
        itens_lancados=len(movimentos),
        itens_ignorados=ignorados,
        produtos_criados=criados,
        contas_pagar_lancadas=contas,
        movimentacao_ids=movimentos,
        entradas=entradas,
        pedido_codigo=pedido.codigo if pedido is not None else None,
        pedido_situacao=pedido.situacao if pedido is not None else None,
        pedido_avisos=pedido_avisos,
    )


def _lancar_duplicatas(db: Session, empresa_id: int, nota: nfe_xml.NotaLida, fornecedor: Fornecedor) -> int:
    """D8: uma conta por duplicata, com o vencimento e o valor dela."""
    from app.db.crud import financeiro as financeiro_crud

    total = len(nota.duplicatas)
    nome = nota.emitente.fantasia or nota.emitente.nome or "fornecedor"
    primeira: Optional[ContaPagar] = None
    for numero, dup in enumerate(nota.duplicatas, start=1):
        conta = financeiro_crud.criar_conta_pagar(db, ContaPagar(
            empresa_id=empresa_id,
            descricao=(f"NF-e {nota.numero} — {nome}" + (f" (dup. {dup.numero})" if dup.numero else ""))[:255],
            valor=dup.valor,
            vencimento=dup.vencimento,
            fornecedor_id=fornecedor.id,
            recorrente=False,
            status=ContaPagarStatus.PENDENTE.value,
            parcela_numero=numero if total > 1 else None,
            parcela_total=total if total > 1 else None,
            parcelamento_id=(primeira.id if primeira else None) if total > 1 else None,
            observacao=f"Chave {nota.chave}",
        ))
        if primeira is None:
            primeira = conta
            if total > 1:
                conta.parcelamento_id = conta.id
                db.flush()
    return total


def listar(db: Session, usuario_token: dict[str, Any], limite: int = 50) -> list[NotaEntrada]:
    return list(db.scalars(
        select(NotaEntrada)
        .where(NotaEntrada.empresa_id == usuario_token["empresa_id"])
        .order_by(NotaEntrada.importada_em.desc(), NotaEntrada.id.desc())
        .limit(limite)
    ))
