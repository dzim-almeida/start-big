# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/emissao_nfe_venda.py
# DESCRIÇÃO: Emissão de NF-e (modelo 55) de uma venda, e o lote.
#
# Saiu do emissao.py na F5 (07/10/2026), sem mudar comportamento: o código foi
# movido, não reescrito. Quem importa de `emissao` continua funcionando.
# ---------------------------------------------------------------------------

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.crud import fiscal as crud
from .core import verificar_completude_venda
from .helpers import obter_crt, regime_apuracao, usa_csosn
from .http import get_fiscal_client
from .payload_builder import montar_payload_nfe
from .tax_engine import calcular_impostos
from .tax_engine.resolver import resolver_aliquotas_venda
from .snapshot import gravar_snapshot
from .espelho_nota import espelhar_na_nota_da_venda
from .emissao_nucleo import _fiscais_efetivos, _aplicar_resultado, _obter_fiscal_settings, _avisos

logger = logging.getLogger(__name__)


def _preparar_dados_emissao(
    db: Session, venda_id: int, empresa_id: int, tipo_documento: str = "nfe",
):
    """
    Setup compartilhado entre preview e emissão.
    Verifica completude, carrega dados e calcula tributos.

    `tipo_documento` decide se o endereço do destinatário é exigido: a NF-e não
    sai sem ele, a NFC-e não o quer. Quem chama daqui de dentro precisa dizer
    qual está emitindo — o padrão "nfe" é o caminho mais restritivo, então
    esquecer de passar reprova em vez de deixar passar.

    Returns:
        Tupla (empresa, endereco, venda, simples, resultado_calculo).

    Raises:
        HTTPException 422 se dados incompletos ou cálculo falhar.
        HTTPException 404 se venda não encontrada.
    """
    verificacao = verificar_completude_venda(db, venda_id, empresa_id, tipo_documento)
    if not verificacao.completo:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "mensagem": "Dados fiscais incompletos para emissão.",
                "pendencias": [p.model_dump() for p in verificacao.pendencias],
            },
        )

    empresa = crud.get_empresa(db, empresa_id)
    endereco = crud.get_endereco_empresa(db, empresa_id)
    venda = crud.get_venda_completa(db, venda_id)
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada.")

    uf_emitente = endereco.estado.value if hasattr(endereco.estado, "value") else str(endereco.estado)
    simples = usa_csosn(obter_crt(empresa))

    try:
        itens_entrada, dados_nota = resolver_aliquotas_venda(
            db, venda, uf_emitente, simples,
            regime_apuracao=regime_apuracao(empresa),
            modelo_documento=65 if tipo_documento == "nfce" else 55,
        )
        resultado_calculo = calcular_impostos(itens_entrada, dados_nota)
    except Exception as e:
        logger.error("[FISCAL] Erro no cálculo tributário: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erro no cálculo tributário: {str(e)}",
        )

    return empresa, endereco, venda, simples, resultado_calculo


def preview_nfe_venda(db: Session, venda_id: int, empresa_id: int) -> dict:
    """Retorna os dados de pré-visualização da NF-e sem emiti-la."""
    empresa, endereco, venda, simples, resultado_calculo = _preparar_dados_emissao(
        db, venda_id, empresa_id,
    )

    # Montar resposta de preview
    # Tax engine retorna Decimal em reais — converter para centavos (int)
    # para manter consistência com os demais valores monetários da resposta.
    total_tributos_centavos = int(sum(
        (i.icms_valor + i.pis_valor + i.cofins_valor)
        for i in resultado_calculo.itens
    ) * 100) if resultado_calculo else 0

    impostos_por_item = {imp.numero_item: imp for imp in resultado_calculo.itens} if resultado_calculo else {}
    itens_preview = []
    for num, item_venda in enumerate(venda.itens, start=1):
        if not item_venda.produto:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Item #{num} é avulso (sem produto cadastrado). "
                       f"Emissão de NF-e requer todos os itens vinculados a produtos.",
            )
        fiscal_prod = item_venda.produto.fiscal
        itens_preview.append({
            "numero_item": num,
            "produto_id": item_venda.produto.id,
            "nome": item_venda.produto.nome,
            "quantidade": float(item_venda.quantidade),
            # "2 FD" em vez de "2": a conferência mostra o que vai no uCom/qCom.
            "sigla_embalagem": item_venda.sigla_embalagem,
            "fator_embalagem": item_venda.fator_embalagem or 1,
            "valor_unitario": float(item_venda.valor_unitario),
            "valor_total": float(item_venda.total),
            # CFOP da operação (6xxx se interestadual), como vai na nota
            "cfop": (impostos_por_item[num].cfop if num in impostos_por_item and impostos_por_item[num].cfop
                     else (fiscal_prod.cfop_padrao if fiscal_prod else "")),
            "ncm": fiscal_prod.ncm if fiscal_prod else "",
            "cst_csosn": (
                fiscal_prod.csosn if simples else fiscal_prod.cst_icms
            ) if fiscal_prod else "",
        })

    # Resolver nome/documento do destinatário (herança polimórfica)
    dest_nome = "NÃO INFORMADO"
    dest_documento = ""
    if venda.cliente:
        from app.db.models.cliente import ClientePF, ClientePJ
        if isinstance(venda.cliente, ClientePF):
            dest_nome = venda.cliente.nome or "NÃO INFORMADO"
            dest_documento = venda.cliente.cpf or ""
        elif isinstance(venda.cliente, ClientePJ):
            dest_nome = venda.cliente.razao_social or "NÃO INFORMADO"
            dest_documento = venda.cliente.cnpj or ""

    # Formas de pagamento
    formas_preview = []
    if hasattr(venda, "pagamentos") and venda.pagamentos:
        for pag in venda.pagamentos:
            forma = pag.forma_pagamento if hasattr(pag, "forma_pagamento") else None
            formas_preview.append({
                "nome": forma.nome if forma else "Outros",
                "codigo_sefaz": forma.codigo_sefaz if forma and forma.codigo_sefaz else "99",
                "valor": int(pag.valor),
            })

    return {
        "destinatario": {
            "nome": dest_nome,
            "documento": dest_documento,
        },
        "totais": {
            "valor_produtos": float(sum(i.total for i in venda.itens)),
            "descontos": float((venda.descontos or 0) + (venda.descontos_regra or 0)),
            "frete": float(venda.entrega or 0),
            "valor_nota": float(venda.total),
            "total_tributos": total_tributos_centavos
        },
        "itens": itens_preview,
        "formas_pagamento": formas_preview,
        "avisos": _avisos(empresa, venda.cliente),
    }


def emitir_nfe_venda(
    db: Session, venda_id: int, empresa_id: int,
    tentativa_anterior_id: Optional[int] = None,
) -> DocumentoFiscal:
    """
    Emite NF-e para uma venda.

    1. Verifica completude fiscal + calcula tributos (via _preparar_dados_emissao)
    2. Valida status da venda e bloqueio de duplicata
    3. Monta payload e cria DocumentoFiscal
    4. Chama client fiscal e atualiza resultado

    `tentativa_anterior_id` é o elo da reemissão (ver `reemissao.py`): o
    documento novo aponta para o rejeitado e o histórico mostra a cadeia. Fora
    isso a reemissão é IGUAL a uma emissão -- mesmo gate, número novo, mesma
    transmissão.
    """
    empresa, endereco, venda, simples, resultado_calculo = _preparar_dados_emissao(
        db, venda_id, empresa_id,
    )

    fiscal_settings = _obter_fiscal_settings(db, empresa_id)

    from app.core.enum import VendaStatus
    if venda.status != VendaStatus.FINALIZADA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Apenas vendas finalizadas podem gerar NF-e.",
        )

    nota_fiscal = venda.nota_fiscal

    # Verificar emissão ativa existente (bloqueio de duplicata)
    doc_ativo = crud.get_documento_ativo_por_venda(db, venda.numero_venda)
    if doc_ativo:
        if doc_ativo.status == "AUTORIZADA":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "codigo": "NF_JA_AUTORIZADA",
                    "mensagem": f"Esta venda já possui NF-e autorizada (Nº {doc_ativo.numero_documento}, Série {doc_ativo.serie}).",
                    "documento_id": doc_ativo.id,
                    "chave_acesso": doc_ativo.chave_acesso,
                },
            )
        elif doc_ativo.status == "INDETERMINADA":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "codigo": "NF_INDETERMINADA",
                    "mensagem": (
                        "A emissão anterior desta venda não teve retorno confirmado da "
                        "SEFAZ. A nota pode estar autorizada. Consulte o documento antes "
                        "de emitir novamente para não gerar nota duplicada."
                    ),
                    "documento_id": doc_ativo.id,
                },
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "codigo": "NF_EM_PROCESSAMENTO",
                    "mensagem": "Esta venda já possui uma emissão em andamento. Aguarde o retorno da SEFAZ.",
                    "documento_id": doc_ativo.id,
                },
            )

    # 3. Reservar o número de forma atômica.
    #    Feito só agora, depois de todas as validações que podem recusar a
    #    emissão, para não queimar número à toa. A partir daqui o número é
    #    definitivo — ver passo 7.
    numero_venda = venda.numero_venda
    numero = crud.reservar_proximo_numero_nfe(db, empresa_id)

    # 4. Montar payload (com tributos calculados e o número já reservado)
    payload = montar_payload_nfe(
        empresa, endereco, fiscal_settings, venda, nota_fiscal,
        resultado_calculo=resultado_calculo,
        numero=numero,
        fiscais=_fiscais_efetivos(db, venda),
    )

    # 5. Criar documento fiscal (ref e chave de idempotência únicas por tentativa)
    tentativas_existentes = crud.contar_documentos_por_venda(db, numero_venda)
    ref = f"venda-{numero_venda}" if tentativas_existentes == 0 else f"venda-{numero_venda}-{tentativas_existentes + 1}"

    doc = DocumentoFiscal(
        tipo_documento="NFE",
        origem_tipo="VENDA",
        origem_id=numero_venda,
        status="PROCESSANDO",
        numero_documento=numero,
        serie=fiscal_settings.serie_nfe,
        ref_api=ref,
        idempotency_key=str(uuid.uuid4()),
        ambiente_emissao=fiscal_settings.ambiente_emissao,
        valor_total=venda.total,
        data_emissao=datetime.now(timezone.utc),
        tentativa_anterior_id=tentativa_anterior_id,
    )
    # Congela o que vai ser transmitido, ANTES de transmitir: assim existe
    # registro mesmo se a resposta da SEFAZ se perder no caminho.
    gravar_snapshot(doc, payload, venda=venda)
    crud.salvar_documento(db, doc)

    # 6. Chamar client fiscal
    token = crud.get_licenca_token(db)
    client = get_fiscal_client(fiscal_settings.ambiente_emissao, token)

    try:
        resultado = client.emitir_nfe(ref, payload, idempotency_key=doc.idempotency_key)
        _aplicar_resultado(doc, resultado, client)
    except NotImplementedError as e:
        # Client sem implementação: nada foi transmitido, é recusa local.
        doc.status = "REJEITADA"
        doc.mensagem_sefaz = str(e)
    except Exception as e:
        # Falha de comunicação NÃO é rejeição: a nota pode estar autorizada na
        # SEFAZ. Marcar REJEITADA aqui libera a venda para nova emissão e gera
        # nota duplicada. O documento fica INDETERMINADA até ser reconciliado.
        logger.error("[FISCAL] Falha de comunicação ao emitir NF-e ref=%s: %s", ref, e)
        doc.status = "INDETERMINADA"
        doc.mensagem_sefaz = (
            f"Não foi possível confirmar o resultado junto à SEFAZ: {str(e)[:300]}. "
            f"O documento será reconsultado automaticamente."
        )

    # 7. O contador NÃO é revertido.
    #    Reverter parecia evitar buracos na sequência, mas depois que o payload
    #    já foi transmitido o número pode estar consumido na SEFAZ — reusá-lo
    #    causa Rejeição 204 e trava a sequência de vez. Buraco se resolve com
    #    inutilização; duplicidade, não.

    espelhar_na_nota_da_venda(db, doc)
    return doc


def emitir_nfe_batch(
    db: Session, venda_ids: list[int], empresa_id: int
) -> list[dict]:
    """
    Emite NF-e para múltiplas vendas sequencialmente.
    Cada venda é atômica — falhas individuais não interrompem o lote.
    Commit-per-sale para preservar numeração fiscal.
    """
    resultados = []
    for venda_id in venda_ids:
        try:
            doc = emitir_nfe_venda(db, venda_id, empresa_id)
            db.commit()
            resultados.append({
                "venda_id": venda_id,
                "documento_id": doc.id,
                "status": doc.status,
                "mensagem": doc.mensagem_sefaz or f"NF-e {doc.status.lower()}.",
            })
        except HTTPException as e:
            db.rollback()
            mensagem = e.detail if isinstance(e.detail, str) else (
                e.detail.get("mensagem", str(e.detail))
                if isinstance(e.detail, dict) else str(e.detail)
            )
            resultados.append({
                "venda_id": venda_id,
                "documento_id": None,
                "status": "ERRO",
                "mensagem": mensagem,
            })
        except Exception as e:
            db.rollback()
            logger.error("[FISCAL] Erro batch venda_id=%d: %s", venda_id, e)
            resultados.append({
                "venda_id": venda_id,
                "documento_id": None,
                "status": "ERRO",
                "mensagem": f"Erro inesperado: {str(e)[:200]}",
            })
    return resultados
