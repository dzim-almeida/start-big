# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/devolucao.py
# DESCRIÇÃO: NF-e de devolução (modelo 55, entrada, finalidade 4) a partir de
#            uma NF-e/NFC-e autorizada.
#
# É uma EMISSÃO nova -- consome número da NF-e, tem itens, passa pela SEFAZ --
# que aponta para a nota original pela chave de 44 dígitos (refNFe). Serve
# quando o prazo de cancelamento passou (24 h / 30 min) ou quando a mercadoria
# volta fisicamente ao balcão.
#
# Os itens vêm do SNAPSHOT da nota original (`DocumentoFiscalItem`), nunca do
# cadastro atual: o que se devolve é o que a SEFAZ viu. Os tributos são
# recalculados pelo tax_engine sobre a quantidade devolvida, com o CST/CSOSN
# e a alíquota de ICMS congelados no snapshot (ADR-002).
#
# Saldo e estoque só mudam com AUTORIZAÇÃO confirmada: rejeição e
# INDETERMINADA não devolvem nada -- ver `aplicar_efeitos_autorizacao`.
# ---------------------------------------------------------------------------

import logging
import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enum import MovimentacaoOrigem, MovimentacaoTipo
from app.db.crud import fiscal as crud
from app.db.crud import produto as produto_crud
from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.models.documento_fiscal_item import DocumentoFiscalItem
from app.schemas.emissao_fiscal import EmissaoDevolucaoRequest
from app.services import movimentacao_estoque as mov_service
from app.services.fiscal.derivacao.cfop import cfop_devolucao
from app.services.fiscal.helpers import obter_crt, regime_apuracao, usa_csosn
from app.services.fiscal.http import get_fiscal_client
from app.services.fiscal.payload_builder import (
    _montar_destinatario,
    _montar_destinatario_avulso,
    montar_payload_devolucao,
)
from app.services.fiscal.snapshot import gravar_snapshot
from app.services.fiscal.tax_engine import calcular_impostos
from app.services.fiscal.tax_engine.constants import (
    COFINS_CUMULATIVO,
    COFINS_NAO_CUMULATIVO,
    CST_PIS_COFINS_SIMPLES,
    PIS_CUMULATIVO,
    PIS_NAO_CUMULATIVO,
)
from app.services.fiscal.tax_engine.types import DadosNota, ItemEntrada
from app.services.fiscal.tributacao import fiscal_efetivo

logger = logging.getLogger(__name__)

_RE_CHAVE = re.compile(r"^\d{44}$")
FINALIDADE_DEVOLUCAO = 4

# (item do snapshot, quantidade a devolver em milésimos, CFOP de entrada)
ItemDevolucao = tuple[DocumentoFiscalItem, int, str]


# ===========================================================================
# 1. Pré-requisitos e saldos
# ===========================================================================

def _obter_origem_devolvivel(db: Session, documento_id: int) -> DocumentoFiscal:
    doc = crud.get_documento_fiscal(db, documento_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento fiscal não encontrado.")
    if doc.status != "AUTORIZADA":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Só uma nota AUTORIZADA pode ser devolvida.",
        )
    # Sem chave válida a SEFAZ recusa com 267/321: melhor recusar aqui, antes
    # de reservar número.
    if not doc.chave_acesso or not _RE_CHAVE.match(doc.chave_acesso):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A nota de origem não tem chave de acesso válida (44 dígitos).",
        )
    if not doc.itens:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A nota de origem não tem itens registrados; não há o que devolver.",
        )
    return doc


def saldo_devolvivel(item: DocumentoFiscalItem) -> int:
    return max(0, item.quantidade_milesimos - (item.quantidade_devolvida_acumulada or 0))


def _resolver_itens(doc: DocumentoFiscal, dados: EmissaoDevolucaoRequest, interestadual: bool) -> list[ItemDevolucao]:
    """Quais itens e quantidades saem nesta devolução, já com o CFOP de entrada.

    Total (sem `itens`): tudo o que ainda tem saldo. Parcial: cada item precisa
    pertencer à nota e caber no saldo -- excedente é 422, nunca "o que der".
    """
    por_id = {item.id: item for item in doc.itens}

    if not dados.itens:
        selecionados = [(item, saldo_devolvivel(item)) for item in doc.itens if saldo_devolvivel(item) > 0]
        if not selecionados:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Esta nota já foi totalmente devolvida.",
            )
    else:
        selecionados = []
        for pedido in dados.itens:
            item = por_id.get(pedido.documento_item_id)
            if item is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Item {pedido.documento_item_id} não pertence a esta nota.",
                )
            saldo = saldo_devolvivel(item)
            if pedido.quantidade > saldo:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Item '{item.descricao}': quantidade a devolver "
                        f"({pedido.quantidade / 1000:g}) excede o saldo ({saldo / 1000:g})."
                    ),
                )
            selecionados.append((item, pedido.quantidade))

    return [(item, qtd, cfop_devolucao(item.cfop, interestadual)) for item, qtd in selecionados]


# ===========================================================================
# 2. Destinatário e tributos
# ===========================================================================

def _resolver_destinatario(db: Session, doc: DocumentoFiscal, dados: EmissaoDevolucaoRequest) -> dict:
    """Quem devolve. Cliente cadastrado na venda de origem; senão, o avulso."""
    cliente = _cliente_da_origem(db, doc)
    if cliente is not None and getattr(cliente, "endereco", None):
        return _montar_destinatario(cliente)
    if dados.destinatario_avulso is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "codigo": "DESTINATARIO_OBRIGATORIO",
                "mensagem": (
                    "A nota de origem não identificou o comprador com endereço. "
                    "Informe os dados de quem está devolvendo (destinatário avulso)."
                ),
            },
        )
    return _montar_destinatario_avulso(dados.destinatario_avulso)


def _cliente_da_origem(db: Session, doc: DocumentoFiscal):
    if doc.origem_tipo != "VENDA" or doc.origem_id is None:
        return None
    venda_id = crud.get_venda_id_por_numero(db, doc.origem_id)
    venda = crud.get_venda_completa(db, venda_id) if venda_id else None
    return getattr(venda, "cliente", None)


def _itens_para_o_motor(
    db: Session, itens: list[ItemDevolucao], simples: bool, regime: str,
) -> list[ItemEntrada]:
    """ItemEntrada a partir do snapshot: CST/CSOSN e alíquota de ICMS congelados.

    PIS/COFINS não estão no snapshot; vêm do regime (Simples = CST 49 zerado)
    ou do cadastro fiscal efetivo do produto, como na emissão original.
    """
    nao_cumulativo = regime == "NAO_CUMULATIVO"
    pis_padrao = PIS_NAO_CUMULATIVO if nao_cumulativo else PIS_CUMULATIVO
    cofins_padrao = COFINS_NAO_CUMULATIVO if nao_cumulativo else COFINS_CUMULATIVO

    entradas = []
    for idx, (snap, qtd_mil, cfop_entrada) in enumerate(itens, start=1):
        produto = produto_crud.get_produto_by_id(db, produto_id=snap.produto_id) if snap.produto_id else None
        fiscal = fiscal_efetivo(db, produto) if produto else None

        if simples:
            aliq_pis = aliq_cofins = Decimal("0")
            cst_pis = cst_cofins = CST_PIS_COFINS_SIMPLES
        else:
            aliq_pis = Decimal(fiscal.aliquota_pis) / 100 if fiscal and fiscal.aliquota_pis is not None else pis_padrao
            aliq_cofins = Decimal(fiscal.aliquota_cofins) / 100 if fiscal and fiscal.aliquota_cofins is not None else cofins_padrao
            cst_pis = fiscal.cst_pis if fiscal and fiscal.cst_pis else "01"
            cst_cofins = fiscal.cst_cofins if fiscal and fiscal.cst_cofins else "01"

        quantidade = Decimal(qtd_mil) / 1000
        unitario = Decimal(snap.valor_unitario) / 100
        entradas.append(ItemEntrada(
            numero_item=idx,
            produto_id=snap.produto_id,
            descricao=snap.descricao,
            quantidade=quantidade,
            valor_unitario=unitario,
            valor_bruto=(quantidade * unitario).quantize(Decimal("0.01")),
            desconto_item=Decimal("0"),
            ncm=snap.ncm,
            cfop=cfop_entrada,
            origem_mercadoria=int(snap.origem_mercadoria or 0),
            cst_icms=None if simples else snap.situacao_tributaria,
            csosn=snap.situacao_tributaria if simples else None,
            aliquota_icms=Decimal(snap.aliquota_icms_centesimos or 0) / 100,
            aliquota_pis=aliq_pis,
            aliquota_cofins=aliq_cofins,
            cst_pis=cst_pis,
            cst_cofins=cst_cofins,
        ))
    return entradas


# ===========================================================================
# 3. Efeitos da autorização: saldo dos itens e estoque
# ===========================================================================

def aplicar_efeitos_autorizacao(db: Session, doc: DocumentoFiscal, usuario_id: Optional[int] = None) -> None:
    """Incrementa o devolvido nos itens de origem e dá entrada no estoque.

    Chamado UMA vez, na transição para AUTORIZADA -- síncrona (aqui) ou pelo
    polling (`consultar_documento`). Rejeição e INDETERMINADA não passam por
    aqui: sem autorização confirmada, nada volta.
    """
    if doc.finalidade_emissao != FINALIDADE_DEVOLUCAO or not doc.documento_referenciado_id:
        return
    origem = crud.get_documento_fiscal(db, doc.documento_referenciado_id)
    if not origem:
        return

    # `origem_id` guarda o NÚMERO da venda; a movimentação referencia a PK.
    venda_id = (
        crud.get_venda_id_por_numero(db, origem.origem_id)
        if origem.origem_tipo == "VENDA" and origem.origem_id is not None else None
    )

    for item_origem, item_dev in _parear_itens(origem, doc):
        item_origem.quantidade_devolvida_acumulada = (
            (item_origem.quantidade_devolvida_acumulada or 0) + item_dev.quantidade_milesimos
        )
        if doc.devolver_estoque and item_dev.produto_id:
            mov_service.registrar_movimentacao(
                db,
                produto=produto_crud.get_produto_by_id(db, produto_id=item_dev.produto_id),
                tipo=MovimentacaoTipo.ENTRADA,
                quantidade=item_dev.quantidade_milesimos / 1000,
                origem=MovimentacaoOrigem.DEVOLUCAO,
                usuario_id=usuario_id,
                usuario_nome="Sistema",
                venda_id=venda_id,
                observacao=f"Entrada por NF-e de devolução nº {doc.numero_documento}",
            )
    db.flush()


def _parear_itens(origem: DocumentoFiscal, devolucao: DocumentoFiscal):
    """Casa cada item da devolução com o item de origem pelo `codigo_produto`.

    O snapshot da devolução carrega, em `codigo_produto`, o mesmo código do
    item original (ver `_montar_itens_devolucao`), e uma nota não repete
    código de produto entre itens.
    """
    por_codigo = {i.codigo_produto: i for i in origem.itens}
    for item_dev in devolucao.itens:
        item_origem = por_codigo.get(item_dev.codigo_produto)
        if item_origem is not None:
            yield item_origem, item_dev


# ===========================================================================
# 4. Orquestração
# ===========================================================================

def emitir_devolucao(
    db: Session,
    documento_id: int,
    empresa_id: int,
    dados: EmissaoDevolucaoRequest,
    usuario_id: Optional[int],
) -> DocumentoFiscal:
    """Emite a NF-e de devolução. Mesma esteira da emissão normal.

    Tudo o que pode recusar vem ANTES de reservar o número; depois de
    transmitido, o número nunca volta (Rejeição 204 -- ver `emitir_nfe_venda`).
    """
    origem = _obter_origem_devolvivel(db, documento_id)
    empresa = crud.get_empresa(db, empresa_id)
    endereco = crud.get_endereco_empresa(db, empresa_id)
    fs = crud.get_fiscal_settings(db, empresa_id)
    if not empresa or not endereco or not fs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cadastro fiscal da empresa incompleto (empresa, endereço ou configurações).",
        )

    # O motor só cobre operação interna (idDest 1); a devolução segue a nota
    # de origem, que também era interna. Fica o gancho para o interestadual.
    interestadual = False
    itens = _resolver_itens(origem, dados, interestadual)
    destinatario = _resolver_destinatario(db, origem, dados)

    simples = usa_csosn(obter_crt(empresa))
    uf_emitente = endereco.estado.value if hasattr(endereco.estado, "value") else str(endereco.estado)
    try:
        resultado_calculo = calcular_impostos(
            _itens_para_o_motor(db, itens, simples, regime_apuracao(empresa)),
            DadosNota(uf_emitente=uf_emitente.upper(), simples_nacional=simples),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erro no cálculo tributário da devolução: {e}",
        )

    numero = crud.reservar_proximo_numero_nfe(db, empresa_id)
    payload = montar_payload_devolucao(
        empresa, endereco, fs, origem.chave_acesso, destinatario, itens,
        resultado_calculo, numero, dados.motivo,
    )

    doc = DocumentoFiscal(
        tipo_documento="NFE",
        origem_tipo=origem.origem_tipo,
        origem_id=origem.origem_id,
        origem_numero_os=origem.origem_numero_os,
        status="PROCESSANDO",
        numero_documento=numero,
        serie=fs.serie_nfe,
        ref_api=f"devolucao-{origem.id}-{uuid.uuid4().hex[:8]}",
        idempotency_key=str(uuid.uuid4()),
        ambiente_emissao=fs.ambiente_emissao,
        valor_total=int(round(resultado_calculo.totais.valor_total_nota * 100)),
        data_emissao=datetime.now(timezone.utc),
        finalidade_emissao=FINALIDADE_DEVOLUCAO,
        documento_referenciado_id=origem.id,
        chave_documento_referenciado=origem.chave_acesso,
        devolver_estoque=dados.devolver_estoque,
    )
    gravar_snapshot(doc, payload)
    # O snapshot tira o `produto_id` da venda, que a devolução não tem: ele vem
    # do item de origem, na mesma ordem em que o payload foi montado. É por ele
    # que a entrada no estoque acha o produto.
    for item_dev, (snap, _, _) in zip(doc.itens, itens):
        item_dev.produto_id = snap.produto_id
    crud.salvar_documento(db, doc)

    client = get_fiscal_client(fs.ambiente_emissao, crud.get_licenca_token(db))
    from app.services.fiscal.emissao import _aplicar_resultado  # evita import circular no topo

    try:
        resultado = client.emitir_nfe(doc.ref_api, payload, idempotency_key=doc.idempotency_key)
        _aplicar_resultado(doc, resultado, client)
    except NotImplementedError as e:
        doc.status = "REJEITADA"
        doc.mensagem_sefaz = str(e)
    except Exception as e:
        # Falha de comunicação NÃO é rejeição: a nota pode estar autorizada.
        logger.error("[FISCAL] Falha de comunicação na devolução ref=%s: %s", doc.ref_api, e)
        doc.status = "INDETERMINADA"
        doc.mensagem_sefaz = (
            f"Não foi possível confirmar o resultado junto à SEFAZ: {str(e)[:300]}. "
            f"O documento será reconsultado automaticamente."
        )

    if doc.status == "AUTORIZADA":
        aplicar_efeitos_autorizacao(db, doc, usuario_id)

    return doc
