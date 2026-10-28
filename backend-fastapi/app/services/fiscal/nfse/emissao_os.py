# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/nfse/emissao_os.py
# DESCRIÇÃO: NFS-e (Nacional) da mão de obra de uma OS. docs/nfse-plano.md, F3.
# ---------------------------------------------------------------------------
"""
Segue o `emitir_nfe_os` passo a passo — primeiro tudo que pode recusar, depois
o documento —, com as diferenças da NFS-e:
- não há número a reservar: a Focus numera a DPS (D3), então nada se queima;
- o documento convive com a NF-e das peças da mesma OS: cada um tem a sua trava
  (`get_nfse_ativa_por_os`) e a sua contagem de tentativas na `ref`;
- consulta, polling, reconciliação e cancelamento são os da NF-e, que já
  escolhem o caminho pelo `tipo_documento` do documento.
"""

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.crud import fiscal as crud
from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.models.documento_fiscal_item import DocumentoFiscalItem
from app.services.fiscal.emissoes.nucleo import CODIGO_NOTA_REPETIDA, _aplicar_resultado, _obter_fiscal_settings
from app.services.fiscal.http import get_fiscal_client
from app.services.fiscal.nfse.completude import verificar_nfse_os
from app.services.fiscal.nfse.espelho import espelhar_nfse_na_os
from app.services.fiscal.nfse.payload import desconto_dos_servicos, montar_dps_os, servicos_da_os

logger = logging.getLogger(__name__)

# Mesmo valor de `nfe_os.ORIGEM_MARCENARIA`.
ORIGEM_MARCENARIA = "ORCAMENTO_MARCENARIA"


def _preparar(db: Session, numero_os: str, empresa_id: int):
    os_obj = crud.get_os_completa(db, numero_os)
    if not os_obj:
        raise HTTPException(status_code=404, detail="Ordem de Serviço não encontrada.")

    # Na marcenaria o MÓVEL é item de serviço: por aqui ele sairia como
    # prestação de serviço. A instalação em NFS-e é o terceiro modo do
    # faturamento dos móveis (plano, D8) e ainda não existe.
    if any(getattr(i, "origem", None) == ORIGEM_MARCENARIA for i in os_obj.itens):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "codigo": "OS_DA_MARCENARIA",
                "mensagem": "A nota de serviço da marcenaria ainda não está disponível. Os móveis saem pela aba Entrega da OS.",
            },
        )

    empresa = crud.get_empresa(db, empresa_id)
    endereco = crud.get_endereco_empresa(db, empresa_id)
    pendencias, fiscal_servico = verificar_nfse_os(db, os_obj, empresa, endereco)
    if pendencias:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "codigo": "PENDENCIAS_FISCAIS",
                "mensagem": "Dados incompletos para a nota de serviço (NFS-e).",
                "pendencias": [p.model_dump() for p in pendencias],
            },
        )
    return os_obj, empresa, endereco, fiscal_servico


def _gravar_snapshot(doc: DocumentoFiscal, dps: dict, itens: list) -> None:
    """O que saiu, congelado antes de transmitir (como `emissoes/snapshot.py`).

    O snapshot genérico lê `items`, que a DPS não tem: aqui é um item por serviço
    da OS (a tela de detalhes e o ZIP do contador leem daí) e o tomador enviado.
    Nunca levanta.
    """
    try:
        doc.itens = [
            DocumentoFiscalItem(
                numero_item=n,
                descricao=(i.nome or "Serviço")[:255],
                codigo_produto=dps.get("codigo_tributacao_nacional_iss"),
                quantidade_milesimos=int(round((i.quantidade or 1) * 1000)),
                valor_unitario=i.valor_unitario or 0,
                valor_bruto=i.valor_total or 0,
            )
            for n, i in enumerate(itens, start=1)
        ]
        doc.destinatario_documento_enviado = (dps.get("cnpj_tomador") or dps.get("cpf_tomador") or None)
        doc.destinatario_nome_enviado = (dps.get("razao_social_tomador") or "")[:120] or None
    except Exception as exc:  # pragma: no cover - rede de segurança
        logger.error("[NFS-e] Falha ao montar o snapshot: %s", exc)


def preview_nfse_os(db: Session, numero_os: str, empresa_id: int) -> dict:
    """A DPS que sairia, sem enviar nada."""
    os_obj, empresa, endereco, fiscal_servico = _preparar(db, numero_os, empresa_id)
    fiscal_settings = _obter_fiscal_settings(db, empresa_id)
    return {"numero_os": numero_os, "dps": montar_dps_os(empresa, endereco, fiscal_settings, os_obj, fiscal_servico)}


def emitir_nfse_os(
    db: Session, numero_os: str, empresa_id: int,
    tentativa_anterior_id: Optional[int] = None,
    confirmar_duplicidade: bool = False,
) -> DocumentoFiscal:
    from app.core.enum import OrdemServicoStatus

    os_obj, empresa, endereco, fiscal_servico = _preparar(db, numero_os, empresa_id)
    fiscal_settings = _obter_fiscal_settings(db, empresa_id)

    if os_obj.status != OrdemServicoStatus.FINALIZADA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Apenas ordens de serviço finalizadas podem gerar NFS-e.",
        )

    doc_ativo = crud.get_nfse_ativa_por_os(db, numero_os)
    if doc_ativo:
        codigo, mensagem = {
            "AUTORIZADA": ("NFSE_JA_AUTORIZADA", f"Esta OS já tem NFS-e autorizada (Nº {doc_ativo.numero_documento})."),
            "INDETERMINADA": (
                "NFSE_INDETERMINADA",
                "A NFS-e anterior desta OS ficou sem resposta confirmada e pode estar autorizada. "
                "Consulte o documento antes de emitir de novo.",
            ),
        }.get(doc_ativo.status, ("NFSE_EM_PROCESSAMENTO", "A NFS-e desta OS ainda está em processamento."))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"codigo": codigo, "mensagem": mensagem, "documento_id": doc_ativo.id},
        )

    dps = montar_dps_os(empresa, endereco, fiscal_settings, os_obj, fiscal_servico)

    tentativas = crud.contar_documentos_por_os(db, numero_os, tipo_documento="NFSE")
    ref_bruta = f"os-{numero_os}-nfse" if tentativas == 0 else f"os-{numero_os}-nfse-{tentativas + 1}"
    ref = re.sub(r"[^A-Za-z0-9._-]", "-", ref_bruta)[:50]

    base = sum(i.valor_total for i in servicos_da_os(os_obj))
    doc = DocumentoFiscal(
        tipo_documento="NFSE",
        origem_tipo="OS",
        origem_id=os_obj.id,
        origem_numero_os=numero_os,
        status="PROCESSANDO",
        ref_api=ref,
        idempotency_key=str(uuid.uuid4()),
        ambiente_emissao=fiscal_settings.ambiente_emissao,
        # O valor do DOCUMENTO é o dos serviços, não o da OS.
        valor_total=base - desconto_dos_servicos(os_obj, base),
        data_emissao=datetime.now(timezone.utc),
        tentativa_anterior_id=tentativa_anterior_id,
    )
    _gravar_snapshot(doc, dps, servicos_da_os(os_obj))
    crud.salvar_documento(db, doc)

    client = get_fiscal_client(fiscal_settings.ambiente_emissao, crud.get_licenca_token(db))
    resultado = None
    try:
        resultado = client.emitir_nfse(
            ref, dps, idempotency_key=doc.idempotency_key, confirmar_duplicidade=confirmar_duplicidade,
        )
    except Exception as e:
        # Falha de comunicação NÃO é rejeição (mesma regra da NF-e): a nota pode
        # ter saído, e a reconciliação de boot / o polling resolvem.
        logger.error("[NFS-e] Falha de comunicação ao emitir a NFS-e da OS ref=%s: %s", ref, e)
        doc.status = "INDETERMINADA"
        doc.mensagem_sefaz = (
            f"Não foi possível confirmar o resultado da NFS-e: {str(e)[:300]}. "
            "O documento será reconsultado automaticamente."
        )
    else:
        # Nota repetida (docs/integracao-erp-local.md da plataforma, 13.4.2): a
        # plataforma não emitiu e quer a confirmação do operador. Vira 409 para
        # a tela perguntar — e o documento não fica gravado (o
        # `_handle_db_transaction` desfaz), porque nada saiu daqui.
        if resultado.get("codigo") == CODIGO_NOTA_REPETIDA:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"codigo": CODIGO_NOTA_REPETIDA, "mensagem": resultado.get("mensagem_sefaz")},
            )
        _aplicar_resultado(doc, resultado, client)

    espelhar_nfse_na_os(db, doc, resultado)
    return doc
