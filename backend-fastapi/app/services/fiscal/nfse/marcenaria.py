# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/nfse/marcenaria.py
# DESCRIÇÃO: A NFS-e da instalação dos móveis (docs/nfse-fase2-plano.md, G5).
# ---------------------------------------------------------------------------
"""
Só existe com o faturamento dos móveis ligado e `instalacao_modo = NFSE`.

DECISÕES (Alan, 28/10/2026):
- UMA NFS-e de instalação por OS, com o valor inteiro da instalação (o item
  "Instalação e montagem" da OS), menos a fatia do desconto da OS que cabe a
  ela. Por entrega fica para quando alguém precisar.
- O local da prestação é a cidade da OBRA (endereço da obra do orçamento,
  "…, Cidade/UF, CEP …"); sem ler a obra, a do cliente; sem as duas, a da loja.

A NF-e dos móveis não muda: o adaptador só embute a instalação no modo EMBUTIDA
(`adaptador_marcenaria`), então NFSE já a deixa fora — sem cobrar duas vezes.
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
from app.schemas.fiscal.verificacao import PendenciaFiscal
from app.services.fiscal.emissoes.nucleo import _aplicar_resultado, _obter_fiscal_settings, recusar_se_nota_repetida
from app.services.fiscal.http import get_fiscal_client
from app.services.fiscal.nfse.espelho import espelhar_nfse_na_os
from app.services.fiscal.nfse.municipio import codigo_ibge
from app.services.fiscal.nfse.payload import montar_dps_instalacao

logger = logging.getLogger(__name__)

MODO_NFSE = "NFSE"
PAPEL_INSTALACAO = "NFSE:INSTALACAO"
# "…, Iguatu/CE, CEP 63500-000": a última "Cidade/UF" do texto.
_CIDADE_UF = re.compile(r"([^,]+?)\s*/\s*([A-Za-z]{2})\b")


def cidade_uf_do_endereco(texto: Optional[str]) -> Optional[tuple[str, str]]:
    achados = _CIDADE_UF.findall(texto or "")
    if not achados:
        return None
    cidade, uf = achados[-1]
    return cidade.strip(), uf.upper()


def _config_nfse(db: Session, empresa_id: int):
    from app.services.marcenaria.faturamento import configuracao_ligada

    config = configuracao_ligada(db, empresa_id)
    return config if config is not None and config.instalacao_modo == MODO_NFSE else None


def _itens_instalacao(os_obj) -> list:
    from app.core.enum import OrdemServicoItemAprovacao
    from app.services.marcenaria.aprovacao import NOME_INSTALACAO, ORIGEM

    return [i for i in os_obj.itens
            if i.origem == ORIGEM and i.nome == NOME_INSTALACAO
            and i.status_aprovacao != OrdemServicoItemAprovacao.REPROVADO]


def municipio_da_obra(db: Session, os_obj) -> tuple[Optional[str], str]:
    """(código IBGE, de onde veio) — obra, cliente ou None (fica a loja)."""
    from app.db.crud.marcenaria import orcamento as crud_orcamento

    orcamento = crud_orcamento.get_orcamento_por_os(db, os_obj.id)
    par = cidade_uf_do_endereco(getattr(orcamento, "endereco_obra", None))
    if par and codigo_ibge(*par):
        return codigo_ibge(*par), "obra"
    cliente = getattr(os_obj.objeto, "cliente", None) if os_obj.objeto else None
    end = (getattr(cliente, "endereco", None) or [None])[0]
    if end is not None:
        uf = end.estado.value if hasattr(end.estado, "value") else end.estado
        codigo = codigo_ibge(end.cidade, uf)
        if codigo:
            return codigo, "cliente"
    return None, "loja"


def _valores(os_obj) -> tuple[int, int]:
    """(valor da instalação, a fatia do desconto da OS que cabe a ela), em centavos."""
    valor = sum(i.valor_total or 0 for i in _itens_instalacao(os_obj))
    bruto = os_obj.valor_bruto or 0
    desconto = min(valor, round((os_obj.desconto or 0) * valor / bruto)) if bruto > 0 and valor > 0 else 0
    return valor, desconto


def nfse_da_instalacao(db: Session, numero_os: str) -> Optional[DocumentoFiscal]:
    """A NFS-e de instalação viva da OS (trava: uma por OS)."""
    return db.query(DocumentoFiscal).filter(
        DocumentoFiscal.origem_tipo == "OS",
        DocumentoFiscal.origem_numero_os == numero_os,
        DocumentoFiscal.tipo_documento == "NFSE",
        DocumentoFiscal.papel == PAPEL_INSTALACAO,
        DocumentoFiscal.status.in_(crud.STATUS_DOCUMENTO_VIVO),
    ).order_by(DocumentoFiscal.id.desc()).first()


def situacao(db: Session, empresa_id: int, os_obj) -> Optional[dict]:
    """O que o painel de notas da OS mostra da instalação. None fora do modo NFSE."""
    if _config_nfse(db, empresa_id) is None:
        return None
    valor, desconto = _valores(os_obj)
    doc = nfse_da_instalacao(db, os_obj.numero_os)
    return {
        "valor": valor - desconto,
        "documento": None if doc is None else {
            "id": doc.id, "status": doc.status, "numero": doc.numero_documento,
            "codigo_verificacao": doc.codigo_verificacao, "url_consulta": doc.url_consulta,
            "mensagem": doc.mensagem_sefaz,
        },
    }


def _preparar(db: Session, numero_os: str, empresa_id: int):
    config = _config_nfse(db, empresa_id)
    if config is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
            "codigo": "INSTALACAO_SEM_NFSE",
            "mensagem": "A instalação só sai em NFS-e com a opção ligada em Configurações › Marcenaria.",
        })
    os_obj = crud.get_os_completa(db, numero_os)
    if not os_obj:
        raise HTTPException(status_code=404, detail="Ordem de Serviço não encontrada.")

    empresa = crud.get_empresa(db, empresa_id)
    endereco = crud.get_endereco_empresa(db, empresa_id)
    fiscal = crud.get_servico_fiscal(db, config.servico_instalacao_id) if config.servico_instalacao_id else None
    valor, desconto = _valores(os_obj)

    falta = []
    if len("".join(c for c in (empresa.documento or "") if c.isdigit())) != 14:
        falta.append(("emitente", "cnpj", "Informe o CNPJ da empresa em Dados da Empresa."))
    uf = endereco.estado.value if endereco and hasattr(endereco.estado, "value") else getattr(endereco, "estado", None)
    if endereco is None or not codigo_ibge(endereco.cidade, uf):
        falta.append(("emitente", "municipio", "Não foi possível identificar a cidade da empresa."))
    if not fiscal or not fiscal.codigo_tributacao_nacional or not fiscal.codigo_nbs:
        falta.append(("item", "servico_instalacao",
                      "O serviço da instalação precisa de código de tributação nacional e NBS (cadastro do serviço)."))
    if valor - desconto <= 0:
        falta.append(("item", "valor", "Esta OS não tem instalação a faturar."))
    if falta:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={
            "codigo": "PENDENCIAS_FISCAIS",
            "mensagem": "Dados incompletos para a NFS-e da instalação.",
            "pendencias": [PendenciaFiscal(categoria=c, campo=k, mensagem=m).model_dump() for c, k, m in falta],
        })

    municipio, origem = municipio_da_obra(db, os_obj)
    fiscal_settings = _obter_fiscal_settings(db, empresa_id)
    dps = montar_dps_instalacao(
        empresa, endereco, fiscal_settings, fiscal, os_obj,
        valor=valor, desconto=desconto, municipio_obra=municipio,
    )
    return os_obj, fiscal_settings, dps, valor - desconto, origem


def preview_nfse_instalacao(db: Session, numero_os: str, empresa_id: int) -> dict:
    _os, _fs, dps, _valor, origem = _preparar(db, numero_os, empresa_id)
    return {"dps": dps, "local_da_prestacao": origem}


def emitir_nfse_instalacao(
    db: Session, numero_os: str, empresa_id: int, confirmar_duplicidade: bool = False,
) -> DocumentoFiscal:
    os_obj, fiscal_settings, dps, valor, _origem = _preparar(db, numero_os, empresa_id)

    viva = nfse_da_instalacao(db, numero_os)
    if viva:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
            "codigo": "NFSE_INSTALACAO_JA_EMITIDA",
            "mensagem": f"A instalação desta OS já tem NFS-e ({viva.status.lower()}).",
            "documento_id": viva.id,
        })

    tentativas = crud.contar_documentos_por_os(db, numero_os, tipo_documento="NFSE", papel=PAPEL_INSTALACAO)
    ref = re.sub(r"[^A-Za-z0-9._-]", "-",
                 f"os-{numero_os}-nfse-inst" + ("" if tentativas == 0 else f"-{tentativas + 1}"))[:50]
    doc = DocumentoFiscal(
        tipo_documento="NFSE", origem_tipo="OS", origem_id=os_obj.id, origem_numero_os=numero_os,
        status="PROCESSANDO", ref_api=ref, idempotency_key=str(uuid.uuid4()),
        ambiente_emissao=fiscal_settings.ambiente_emissao, valor_total=valor,
        data_emissao=datetime.now(timezone.utc), papel=PAPEL_INSTALACAO,
        destinatario_documento_enviado=dps.get("cnpj_tomador") or dps.get("cpf_tomador"),
        destinatario_nome_enviado=(dps.get("razao_social_tomador") or "")[:120] or None,
    )
    doc.itens = [DocumentoFiscalItem(
        numero_item=1, descricao="Instalação e montagem", codigo_produto=dps["codigo_tributacao_nacional_iss"],
        quantidade_milesimos=1000, valor_unitario=valor, valor_bruto=valor,
    )]
    crud.salvar_documento(db, doc)

    client = get_fiscal_client(fiscal_settings.ambiente_emissao, crud.get_licenca_token(db))
    resultado = None
    try:
        resultado = client.emitir_nfse(
            ref, dps, idempotency_key=doc.idempotency_key, confirmar_duplicidade=confirmar_duplicidade,
        )
        recusar_se_nota_repetida(resultado)
        _aplicar_resultado(doc, resultado, client)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[NFS-e] Falha de comunicação na NFS-e da instalação ref=%s: %s", ref, e)
        doc.status = "INDETERMINADA"
        doc.mensagem_sefaz = (
            f"Não foi possível confirmar o resultado da NFS-e: {str(e)[:300]}. "
            "O documento será reconsultado automaticamente."
        )
    espelhar_nfse_na_os(db, doc, resultado)
    return doc
