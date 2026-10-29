# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/nfse/avulsa.py
# DESCRIÇÃO: NFS-e de um serviço que não passou por OS (docs/nfse-fase2-plano.md,
#            G4): consultoria, aula, o MEI que hoje emite pelo portal.
# ---------------------------------------------------------------------------
"""
Mesmo caminho da NFS-e da OS (`emissao_os.py`) sem a OS:
- sem trava por origem (não há origem). Quem segura o clique duplo é a
  plataforma: a mesma nota em menos de 1 h volta 409 de nota repetida;
- `origem_tipo = "AVULSA"`, `ref nfse-av-<8 hex>`;
- consulta, cancelamento, polling e reconciliação são os de sempre (o
  `tipo_documento` NFSE escolhe a rota da plataforma).
"""

import logging
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.crud import fiscal as crud
from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.models.documento_fiscal_item import DocumentoFiscalItem
from app.schemas.fiscal.verificacao import PendenciaFiscal
from app.services.fiscal.emissoes.nucleo import _aplicar_resultado, _obter_fiscal_settings, recusar_se_nota_repetida
from app.services.fiscal.http import get_fiscal_client
from app.services.fiscal.nfse.municipio import codigo_ibge
from app.services.fiscal.nfse.payload import montar_dps_avulsa, tomador_digitado
from app.services.fiscal.nfse.rota import exige_nbs, pendencia_da_rota, pendencias_do_servico, rota_da_empresa

logger = logging.getLogger(__name__)


def _servico_fiscal(db: Session, dados) -> object:
    """O 'ServicoFiscal' da nota: o do serviço do catálogo, com o que foi
    digitado por cima (a tela pode trocar código e NBS só para esta nota)."""
    base = crud.get_servico_fiscal(db, dados.servico_id) if dados.servico_id else None
    return SimpleNamespace(
        codigo_tributacao_nacional=dados.codigo_tributacao_nacional or getattr(base, "codigo_tributacao_nacional", None),
        codigo_nbs=dados.codigo_nbs or getattr(base, "codigo_nbs", None),
        codigo_tributacao_municipio=getattr(base, "codigo_tributacao_municipio", None),
        cnae=getattr(base, "cnae", None),
        codigo_servico_lc116=getattr(base, "codigo_servico_lc116", None),
        aliquota_iss=getattr(base, "aliquota_iss", None),
        cst_ibs_cbs=getattr(base, "cst_ibs_cbs", None),
        c_class_trib=getattr(base, "c_class_trib", None),
    )


def _pendencias(empresa, endereco, fiscal, dados, rota=None) -> list[PendenciaFiscal]:
    falta = []
    da_rota = pendencia_da_rota(rota)
    if da_rota:
        falta.append(da_rota)
    def p(categoria, campo, mensagem):
        falta.append(PendenciaFiscal(categoria=categoria, campo=campo, mensagem=mensagem))

    if len("".join(c for c in (getattr(empresa, "documento", None) or "") if c.isdigit())) != 14:
        p("emitente", "cnpj", "Informe o CNPJ da empresa em Dados da Empresa.")
    uf = getattr(getattr(endereco, "estado", None), "value", getattr(endereco, "estado", None))
    if endereco is None or not codigo_ibge(endereco.cidade, uf):
        p("emitente", "municipio", "Não foi possível identificar a cidade da empresa. Confira cidade e UF em Dados da Empresa.")
    if not fiscal.codigo_tributacao_nacional:
        p("item", "codigo_tributacao_nacional", "Informe o código de tributação nacional do serviço.")
    if not fiscal.codigo_nbs and exige_nbs(rota):
        p("item", "codigo_nbs", "Informe o NBS do serviço.")
    falta.extend(pendencias_do_servico(rota, fiscal))
    if dados.valor - (dados.desconto or 0) <= 0:
        p("item", "valor", "O valor do serviço (menos o desconto) precisa ser maior que zero.")
    documento = "".join(c for c in (dados.tomador_documento or "") if c.isdigit())
    if documento and len(documento) not in (11, 14):
        p("destinatario", "documento", "O CPF/CNPJ do tomador está incompleto.")
    return falta


def _preparar(db: Session, empresa_id: int, dados):
    empresa = crud.get_empresa(db, empresa_id)
    endereco = crud.get_endereco_empresa(db, empresa_id)
    fiscal_settings = _obter_fiscal_settings(db, empresa_id)
    fiscal = _servico_fiscal(db, dados)
    rota = rota_da_empresa(db, empresa_id)
    pendencias = _pendencias(empresa, endereco, fiscal, dados, rota)
    if pendencias:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "codigo": "PENDENCIAS_FISCAIS",
                "mensagem": "Dados incompletos para a nota de serviço (NFS-e).",
                "pendencias": [x.model_dump() for x in pendencias],
            },
        )
    dps = montar_dps_avulsa(
        empresa, endereco, fiscal_settings, fiscal,
        descricao=dados.descricao, valor=dados.valor, desconto=dados.desconto or 0,
        tomador=tomador_digitado(dados.tomador_documento, dados.tomador_nome, dados.tomador_email),
        rota=rota,
    )
    return fiscal_settings, dps


def preview_nfse_avulsa(db: Session, empresa_id: int, dados) -> dict:
    _fs, dps = _preparar(db, empresa_id, dados)
    return {"dps": dps}


def emitir_nfse_avulsa(db: Session, empresa_id: int, dados, confirmar_duplicidade: bool = False) -> DocumentoFiscal:
    fiscal_settings, dps = _preparar(db, empresa_id, dados)

    ref = f"nfse-av-{uuid.uuid4().hex[:8]}"
    doc = DocumentoFiscal(
        tipo_documento="NFSE",
        origem_tipo="AVULSA",
        status="PROCESSANDO",
        ref_api=ref,
        idempotency_key=str(uuid.uuid4()),
        ambiente_emissao=fiscal_settings.ambiente_emissao,
        valor_total=dados.valor - (dados.desconto or 0),
        data_emissao=datetime.now(timezone.utc),
        papel=crud.papel_nfse(dps["codigo_tributacao_nacional_iss"]),
        destinatario_documento_enviado=dps.get("cnpj_tomador") or dps.get("cpf_tomador"),
        destinatario_nome_enviado=(dps.get("razao_social_tomador") or "")[:120] or None,
    )
    doc.itens = [DocumentoFiscalItem(
        numero_item=1, descricao=dados.descricao[:255], codigo_produto=dps["codigo_tributacao_nacional_iss"],
        quantidade_milesimos=1000, valor_unitario=dados.valor, valor_bruto=dados.valor,
        valor_desconto=dados.desconto or 0,
    )]
    crud.salvar_documento(db, doc)

    client = get_fiscal_client(fiscal_settings.ambiente_emissao, crud.get_licenca_token(db))
    try:
        resultado = client.emitir_nfse(
            ref, dps, idempotency_key=doc.idempotency_key, confirmar_duplicidade=confirmar_duplicidade,
        )
        recusar_se_nota_repetida(resultado)
        _aplicar_resultado(doc, resultado, client)
    except HTTPException:
        raise   # nota repetida: o rollback desfaz o documento
    except Exception as e:
        logger.error("[NFS-e] Falha de comunicação ao emitir a NFS-e avulsa ref=%s: %s", ref, e)
        doc.status = "INDETERMINADA"
        doc.mensagem_sefaz = (
            f"Não foi possível confirmar o resultado da NFS-e: {str(e)[:300]}. "
            "O documento será reconsultado automaticamente."
        )
    return doc
