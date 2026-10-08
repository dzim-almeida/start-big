# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/emissao_nfe_os.py
# DESCRIÇÃO: Emissão de NF-e (modelo 55) de uma Ordem de Serviço.
#
# Saiu do emissao.py na F5 (07/10/2026), sem mudar comportamento: o código foi
# movido, não reescrito. Quem importa de `emissao` continua funcionando.
# ---------------------------------------------------------------------------

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.crud import fiscal as crud
from .helpers import obter_crt, regime_apuracao, usa_csosn
from .http import get_fiscal_client
from .payload_builder import montar_payload_nfe
from .tax_engine import calcular_impostos
from .tax_engine.resolver import resolver_aliquotas_venda
from .snapshot import gravar_snapshot
from .emissao_nucleo import _fiscais_efetivos, _aplicar_resultado, _obter_fiscal_settings, _avisos

logger = logging.getLogger(__name__)


# ===========================================================================
# NF-e A PARTIR DE ORDEM DE SERVIÇO
#
# Só os itens de PRODUTO entram. Mão de obra é serviço e pede NFS-e municipal,
# que este sistema ainda não emite -- então a NF-e de uma OS cobre as peças, e
# quem precisa de documento da mão de obra continua dependendo da prefeitura.
#
# Todo o miolo (alíquotas, rateio, montagem, fechamento de pagamentos) é o
# MESMO da venda: a OS é apresentada com a forma de uma venda em
# `adaptador_os.py`. Ver lá o porquê de adaptar em vez de duplicar.
# ===========================================================================

def _preparar_dados_emissao_os(db: Session, numero_os: str, empresa_id: int):
    """Espelho de `_preparar_dados_emissao`, para OS.

    Returns:
        (empresa, endereco, os_obj, os_como_venda, simples, resultado_calculo)
    """
    from .adaptador_os import adaptar, itens_de_produto
    from .core import verificar_completude_os

    verificacao = verificar_completude_os(db, numero_os, empresa_id, tipo_documento="nfe")
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
    os_obj = crud.get_os_completa(db, numero_os)
    if not os_obj:
        raise HTTPException(status_code=404, detail="Ordem de Serviço não encontrada.")

    if not itens_de_produto(os_obj):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Esta OS não tem peça aprovada para faturar. A NF-e cobre os "
                "produtos; a mão de obra é nota de serviço (NFS-e)."
            ),
        )

    os_como_venda = adaptar(os_obj)

    uf_emitente = endereco.estado.value if hasattr(endereco.estado, "value") else str(endereco.estado)
    simples = usa_csosn(obter_crt(empresa))

    try:
        itens_entrada, dados_nota = resolver_aliquotas_venda(
            db, os_como_venda, uf_emitente, simples,
            regime_apuracao=regime_apuracao(empresa),
        )
        resultado_calculo = calcular_impostos(itens_entrada, dados_nota)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[FISCAL] Erro no cálculo tributário da OS %s: %s", numero_os, e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erro no cálculo tributário: {str(e)}",
        )

    return empresa, endereco, os_obj, os_como_venda, simples, resultado_calculo


def preview_nfe_os(db: Session, numero_os: str, empresa_id: int) -> dict:
    """Pré-visualização da NF-e de uma OS. Não emite e NÃO reserva número."""
    empresa, endereco, os_obj, os_como_venda, _simples, resultado_calculo = (
        _preparar_dados_emissao_os(db, numero_os, empresa_id)
    )
    fiscal_settings = _obter_fiscal_settings(db, empresa_id)

    payload = montar_payload_nfe(
        empresa, endereco, fiscal_settings, os_como_venda, os_obj.nota_fiscal,
        resultado_calculo=resultado_calculo,
        fiscais=_fiscais_efetivos(db, os_como_venda),
    )

    return {
        "numero_os": numero_os,
        "itens": payload.get("items", []),
        "totais": payload.get("totais", {}),
        "formas_pagamento": payload.get("formas_pagamento", []),
        "destinatario": payload.get("destinatario", {}),
        "avisos": _avisos(empresa, getattr(os_como_venda, "cliente", None)),
    }


def emitir_nfe_os(
    db: Session, numero_os: str, empresa_id: int,
    tentativa_anterior_id: Optional[int] = None,
) -> DocumentoFiscal:
    """
    Emite NF-e para as peças de uma Ordem de Serviço.

    Segue passo a passo o `emitir_nfe_venda` -- inclusive na ordem: primeiro
    tudo que pode recusar, e só depois a reserva do número. Descobrir problema
    com o número já reservado queima numeração à toa, e buraco na sequência
    obriga inutilização junto à SEFAZ.
    """
    from app.core.enum import OrdemServicoStatus

    empresa, endereco, os_obj, os_como_venda, _simples, resultado_calculo = (
        _preparar_dados_emissao_os(db, numero_os, empresa_id)
    )
    fiscal_settings = _obter_fiscal_settings(db, empresa_id)

    if os_obj.status != OrdemServicoStatus.FINALIZADA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Apenas ordens de serviço finalizadas podem gerar NF-e.",
        )

    doc_ativo = crud.get_documento_ativo_por_os(db, numero_os)
    if doc_ativo:
        if doc_ativo.status == "AUTORIZADA":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "codigo": "NF_JA_AUTORIZADA",
                    "mensagem": (
                        f"Esta OS já possui NF-e autorizada "
                        f"(Nº {doc_ativo.numero_documento}, Série {doc_ativo.serie})."
                    ),
                    "documento_id": doc_ativo.id,
                    "chave_acesso": doc_ativo.chave_acesso,
                },
            )
        if doc_ativo.status == "INDETERMINADA":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "codigo": "NF_INDETERMINADA",
                    "mensagem": (
                        "A emissão anterior desta OS não teve retorno confirmado da "
                        "SEFAZ. A nota pode estar autorizada. Consulte o documento "
                        "antes de emitir novamente para não gerar nota duplicada."
                    ),
                    "documento_id": doc_ativo.id,
                },
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "codigo": "NF_EM_PROCESSAMENTO",
                "mensagem": (
                    "Esta OS já possui uma emissão em andamento. "
                    "Aguarde o retorno da SEFAZ."
                ),
                "documento_id": doc_ativo.id,
            },
        )

    numero = crud.reservar_proximo_numero_nfe(db, empresa_id)

    payload = montar_payload_nfe(
        empresa, endereco, fiscal_settings, os_como_venda, os_obj.nota_fiscal,
        resultado_calculo=resultado_calculo,
        numero=numero,
        fiscais=_fiscais_efetivos(db, os_como_venda),
    )

    tentativas = crud.contar_documentos_por_os(db, numero_os)
    ref_bruta = f"os-{numero_os}" if tentativas == 0 else f"os-{numero_os}-{tentativas + 1}"
    # A `ref` é a proteção contra duplicidade na plataforma, e o contrato aceita
    # só `A-Za-z0-9._-`. O número da OS vem formatado ("OS-2026-000001"), então
    # qualquer outro caractere é normalizado aqui em vez de virar 4xx lá.
    ref = re.sub(r"[^A-Za-z0-9._-]", "-", ref_bruta)[:50]

    doc = DocumentoFiscal(
        tipo_documento="NFE",
        origem_tipo="OS",
        origem_id=os_obj.id,
        origem_numero_os=numero_os,
        status="PROCESSANDO",
        numero_documento=numero,
        serie=fiscal_settings.serie_nfe,
        ref_api=ref,
        idempotency_key=str(uuid.uuid4()),
        ambiente_emissao=fiscal_settings.ambiente_emissao,
        # O valor do DOCUMENTO é o das peças, não o da OS: é ele que a SEFAZ
        # autoriza e o que o relatório fiscal soma.
        valor_total=os_como_venda.total,
        data_emissao=datetime.now(timezone.utc),
        tentativa_anterior_id=tentativa_anterior_id,
    )
    gravar_snapshot(doc, payload, venda=os_como_venda)
    crud.salvar_documento(db, doc)

    client = get_fiscal_client(
        fiscal_settings.ambiente_emissao, crud.get_licenca_token(db),
    )

    try:
        resultado = client.emitir_nfe(ref, payload, idempotency_key=doc.idempotency_key)
        _aplicar_resultado(doc, resultado, client)
    except NotImplementedError as e:
        doc.status = "REJEITADA"
        doc.mensagem_sefaz = str(e)
    except Exception as e:
        # Falha de comunicação NÃO é rejeição -- ver o mesmo trecho em
        # `emitir_nfe_venda`. REJEITADA seria reemitível e geraria duplicata.
        logger.error(
            "[FISCAL] Falha de comunicação ao emitir NF-e da OS ref=%s: %s", ref, e,
        )
        doc.status = "INDETERMINADA"
        doc.mensagem_sefaz = (
            f"Não foi possível confirmar o resultado junto à SEFAZ: {str(e)[:300]}. "
            f"O documento será reconsultado automaticamente."
        )

    return doc
