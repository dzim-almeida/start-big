# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/emissao_teste.py
# DESCRIÇÃO: NF-e de teste de homologação (sem venda por trás).
#
# Saiu do emissao.py na F5 (07/10/2026), sem mudar comportamento: o código foi
# movido, não reescrito. Quem importa de `emissao` continua funcionando.
# ---------------------------------------------------------------------------

import logging
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.crud import fiscal as crud
from .http import get_fiscal_client
from .payload_builder import montar_payload_teste_nfe
from .snapshot import gravar_snapshot
from .emissao_nucleo import _aplicar_resultado, _obter_fiscal_settings

logger = logging.getLogger(__name__)


def emitir_teste_nfe(db: Session, empresa_id: int) -> DocumentoFiscal:
    """
    Emissão de teste com dados fictícios. Apenas em homologação.
    Não precisa de venda ou OS real.
    """
    fiscal_settings = _obter_fiscal_settings(db, empresa_id)

    # O gate vem ANTES da ida à plataforma: ele é local e barato, e com a
    # trava de numeração fechada (Rejeição 204) não há por que gastar uma
    # chamada à emissora para descobrir um "não" que já se sabe aqui.
    #
    # O emitente precisa estar completo ANTES de reservar numeração.
    #
    # A emissão real passa por `_preparar_dados_emissao`, que já verifica isto.
    # A de teste não passava por nada: com CNPJ, IE ou regime tributário em
    # branco ela reservava o número, montava a nota, e a plataforma recusava com
    # 4xx antes de chegar na Focus. Como o corpo do 4xx vira `mensagem_sefaz`, o
    # lojista lia "CNPJ do emitente não autorizado" achando que era a SEFAZ
    # falando -- quando o dado faltava aqui e a nota nunca saiu da nossa rede.
    #
    # Verificar antes do `ultimo_numero_nfe + 1` também evita queimar numeração
    # à toa: a reversão existe, mas depende de o fluxo chegar até ela.
    from . import validators

    pendencias = validators.verificar_emitente(db, empresa_id)
    if pendencias:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "codigo": "EMITENTE_INCOMPLETO",
                "mensagem": (
                    "Os dados da empresa ainda não permitem emitir. "
                    "Complete-os em Dados da Empresa e tente de novo."
                ),
                "pendencias": [p.mensagem for p in pendencias],
            },
        )

    # Quem responde é a PLATAFORMA. O campo local `ambiente_emissao` não
    # decide para onde a nota vai, então perguntar a ele deixava passar uma
    # nota de teste — destinatário fictício, R$ 1,00 — como documento REAL
    # quando a plataforma estava em produção. Sem confirmação de homologação
    # (plataforma fora do ar inclusive) a resposta é não: o preço de errar
    # para "pode" é uma nota fiscal verdadeira que só sai por cancelamento.
    token = crud.get_licenca_token(db)
    client = get_fiscal_client(2, token)
    ambiente_plataforma = (client.consultar_config() or {}).get("ambiente")
    if ambiente_plataforma != 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "A plataforma de emissão está em produção para esta loja — "
                "uma nota de teste sairia como documento fiscal real."
                if ambiente_plataforma == 1 else
                "Não foi possível confirmar com a plataforma que a loja está "
                "em homologação. Emissão de teste só com essa confirmação."
            ),
        )

    empresa = crud.get_empresa(db, empresa_id)
    endereco = crud.get_endereco_empresa(db, empresa_id)

    if not empresa or not endereco:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Empresa ou endereço não cadastrados.",
        )


    payload = montar_payload_teste_nfe(empresa, endereco, fiscal_settings)

    ref = f"teste-{uuid.uuid4().hex[:12]}"
    numero = fiscal_settings.ultimo_numero_nfe + 1

    doc = DocumentoFiscal(
        tipo_documento="NFE",
        origem_tipo="VENDA",
        status="PROCESSANDO",
        numero_documento=numero,
        serie=fiscal_settings.serie_nfe,
        ref_api=ref,
        ambiente_emissao=2,
        valor_total=100,  # R$ 1,00 em centavos
        data_emissao=datetime.now(timezone.utc),
    )
    
    fiscal_settings.ultimo_numero_nfe = numero
    # A nota de teste nao tem venda, entao o detalhe so tem o snapshot para
    # dizer o que foi enviado -- foi a falta dele que escondeu qual CNPJ saiu.
    gravar_snapshot(doc, payload)
    crud.salvar_documento(db, doc)

    try:
        resultado = client.emitir_nfe(ref, payload)
        _aplicar_resultado(doc, resultado, client)
    except Exception as e:
        logger.error("[FISCAL] Erro ao emitir teste NF-e: %s", e)
        doc.status = "REJEITADA"
        doc.mensagem_sefaz = f"Erro no teste: {str(e)[:400]}"

    # Reverter numeração se emissão falhou
    if doc.status == "REJEITADA":
        fiscal_settings.ultimo_numero_nfe = numero - 1

    return doc
