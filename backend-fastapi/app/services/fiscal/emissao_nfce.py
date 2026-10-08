# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/emissao_nfce.py
# DESCRIÇÃO: Emissão de NFC-e (modelo 65) de uma venda, com as travas do cupom
# (consumidor identificado acima do teto, CSC configurado).
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
from app.db.models.empresa_fiscal_settings import EmpresaFiscalSettings
from app.db.crud import fiscal as crud
from .http import get_fiscal_client
from .payload_builder import montar_payload_nfce
from .snapshot import gravar_snapshot
from .espelho_nota import espelhar_na_nota_da_venda
from .tributos_xml import extrair_valor_tributos
from .emissao_nucleo import _fiscais_efetivos, _aplicar_resultado, _obter_fiscal_settings
from .emissao_nfe_venda import _preparar_dados_emissao, preview_nfe_venda

logger = logging.getLogger(__name__)


def preview_nfce_venda(db: Session, venda_id: int, empresa_id: int) -> dict:
    """Pré-visualização da NFC-e, sem emitir.

    Aproveita o preview da NF-e — itens, totais e tributos são os mesmos — e
    corrige só o que o modelo 65 vê diferente: o destinatário, que pode ser o
    CPF digitado no caixa ou simplesmente não existir.

    Roda as mesmas recusas da emissão (CSC e teto do consumidor anônimo) de
    propósito: é aqui que o operador descobre o impedimento com a venda ainda
    aberta, em vez de no botão de emitir com o cliente esperando.
    """
    preview = preview_nfe_venda(db, venda_id, empresa_id)

    fiscal_settings = _obter_fiscal_settings(db, empresa_id)
    venda = crud.get_venda_completa(db, venda_id)

    # Aqui a consulta à plataforma cai bem: o preview existe justamente para o
    # problema aparecer com a tela aberta, e não no botão de emitir com o
    # cliente esperando no balcão.
    _assert_csc_configurado(
        get_fiscal_client(fiscal_settings.ambiente_emissao, crud.get_licenca_token(db))
    )
    _assert_consumidor_identificado(venda, fiscal_settings)

    documento = _documento_do_consumidor(venda)
    if venda.cliente is not None:
        pass  # o nome do cadastro já veio do preview da NF-e
    elif documento:
        preview["destinatario"] = {"nome": "CONSUMIDOR", "documento": documento}
    else:
        preview["destinatario"] = {
            "nome": "CONSUMIDOR NÃO IDENTIFICADO",
            "documento": "",
        }

    return preview


def _reais(centavos: int) -> str:
    """Centavos -> 'R$ 10.000,00'. Só para mensagem lida por gente."""
    inteiro, resto = divmod(int(centavos), 100)
    return f"R$ {inteiro:,.0f}".replace(",", ".") + f",{resto:02d}"


def _documento_do_consumidor(venda) -> Optional[str]:
    """CPF/CNPJ que identifica o comprador nesta venda, ou None.

    Precedência: o cadastro do cliente vence o digitado no caixa, porque foi
    conferido uma vez. O do caixa cobre o consumidor de passagem.
    """
    cliente = venda.cliente
    if cliente is not None:
        documento = getattr(cliente, "cpf", None) or getattr(cliente, "cnpj", None)
        if documento:
            return re.sub(r"\D", "", documento)

    nota = venda.nota_fiscal
    if nota is not None and nota.documento_consumidor:
        return re.sub(r"\D", "", nota.documento_consumidor)

    return None


def _assert_consumidor_identificado(venda, fiscal_settings: EmpresaFiscalSettings) -> None:
    """Regra 3: acima do teto estadual, a NFC-e exige CPF/CNPJ do comprador.

    A conferência é feita ANTES de reservar número — recusa depois queimaria
    um número da sequência e obrigaria a inutilizá-lo por um erro de digitação.
    """
    limite = fiscal_settings.limite_consumidor_anonimo or 0
    if limite <= 0 or (venda.total or 0) < limite:
        return

    if _documento_do_consumidor(venda):
        return

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "codigo": "CONSUMIDOR_NAO_IDENTIFICADO",
            "mensagem": (
                f"Vendas a partir de {_reais(limite)} exigem o CPF ou CNPJ do "
                f"comprador na NFC-e. Informe o documento no fechamento ou "
                f"emita uma NF-e."
            ),
            "limite_centavos": limite,
        },
    )


def _assert_csc_configurado(client) -> None:
    """
    Sem CSC não há QR Code, e sem QR Code o cupom não tem validade.

    QUEM RESPONDE É A PLATAFORMA, não um campo daqui. O CSC é cadastrado uma
    única vez na ficha da empresa dentro da Focus, junto do certificado A1 --
    nunca viajou no payload da nota. Perguntar ao nosso banco barraria uma loja
    corretamente configurada só porque o lojista não redigitou o segredo aqui.

    "Não sei" LIBERA. Se a consulta falhar, `consultar_config` devolve {} e a
    emissão segue: derrubar um cupom no balcão por causa de um diagnóstico
    indisponível troca a venda por um detalhe. O preço de errar para "tem" é um
    cupom sem QR Code, e esse a plataforma sinaliza em `pendencias`.

    Lembre que o CSC é POR AMBIENTE: o de homologação não vale em produção.
    """
    config = client.consultar_config()
    if config.get("cscConfigurado") is not False:
        return

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "codigo": "CSC_NAO_CONFIGURADO",
            "mensagem": (
                "O CSC (Código de Segurança do Contribuinte) não está "
                "cadastrado para esta empresa na emissora. Sem ele o cupom sai "
                "sem QR Code e não tem validade. Fale com o suporte para "
                "cadastrá-lo — e confirme o ambiente, porque o CSC de "
                "homologação não vale em produção."
            ),
        },
    )


def _completar_tributos_pelo_xml(doc: DocumentoFiscal, client) -> None:
    """Busca no XML autorizado o valor aproximado dos tributos (Lei 12.741).

    A Focus calcula o `vTotTrib` pela tabela IBPT, mas só o grava no XML — o
    JSON da emissão não o traz, e o cupom é obrigado a imprimi-lo. Este é o
    único jeito de ter o número sem manter tabela IBPT própria.

    É BEST-EFFORT de propósito. A nota já está autorizada quando chegamos
    aqui; falhar em baixar um arquivo não pode desfazer isso nem impedir a
    impressão. Sem o valor, o cupom sai sem a linha de tributos e o documento
    continua válido — e a reimpressão pode buscar de novo.
    """
    if doc.status != "AUTORIZADA" or doc.valor_tributos is not None:
        return
    if not doc.url_xml:
        return

    try:
        xml = client.baixar_xml(doc.url_xml)
    except Exception as exc:  # client sem o método, rede, o que for
        logger.warning("[FISCAL] Não foi possível baixar o XML da nota: %s", exc)
        return

    valor = extrair_valor_tributos(xml)
    if valor is None:
        logger.info(
            "[FISCAL] Documento %s sem vTotTrib no XML; cupom sai sem a linha "
            "de tributos aproximados.", doc.id,
        )
        return

    doc.valor_tributos = valor


def emitir_nfce_venda(
    db: Session, venda_id: int, empresa_id: int,
    tentativa_anterior_id: Optional[int] = None,
) -> DocumentoFiscal:
    """
    Emite NFC-e (modelo 65) para uma venda do PDV.

    Espelha `emitir_nfe_venda`, com quatro diferenças que importam:

    1. Exige CSC configurado e consumidor identificado acima do teto — as duas
       conferências acontecem ANTES de reservar número.
    2. Usa o contador de NFC-e, independente do de NF-e.
    3. É SÍNCRONA: não há polling. O caixa está com o cliente na frente.
    4. Bloqueia duplicata pelo documento ativo da venda, igual à NF-e — uma
       venda não pode ter NF-e e NFC-e ao mesmo tempo.

    O gate roda como "nfce", e isso é a quinta diferença: o modelo 65 omite o
    endereço do destinatário, então exigi-lo aqui reprovaria o cupom de todo
    consumidor de balcão — que é o caso normal do PDV.
    """
    empresa, endereco, venda, simples, resultado_calculo = _preparar_dados_emissao(
        db, venda_id, empresa_id, tipo_documento="nfce",
    )

    fiscal_settings = _obter_fiscal_settings(db, empresa_id)

    from app.core.enum import VendaStatus
    if venda.status != VendaStatus.FINALIZADA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Apenas vendas finalizadas podem gerar NFC-e.",
        )

    # O client nasce AQUI, e não junto da emissão lá embaixo: a trava do CSC
    # pergunta à plataforma, e descobrir o problema depois de reservar o número
    # queimaria uma numeração à toa.
    token = crud.get_licenca_token(db)
    client = get_fiscal_client(fiscal_settings.ambiente_emissao, token)

    _assert_csc_configurado(client)
    _assert_consumidor_identificado(venda, fiscal_settings)

    # Bloqueio de duplicata — mesma regra e mesmas mensagens da NF-e.
    doc_ativo = crud.get_documento_ativo_por_venda(db, venda.numero_venda)
    if doc_ativo:
        if doc_ativo.status == "AUTORIZADA":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "codigo": "NF_JA_AUTORIZADA",
                    "mensagem": (
                        f"Esta venda já possui documento fiscal autorizado "
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
                        "A emissão anterior desta venda não teve retorno confirmado da "
                        "SEFAZ. O documento pode estar autorizado. Consulte antes de "
                        "emitir novamente para não gerar cupom duplicado."
                    ),
                    "documento_id": doc_ativo.id,
                },
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "codigo": "NF_EM_PROCESSAMENTO",
                "mensagem": "Esta venda já possui uma emissão em andamento.",
                "documento_id": doc_ativo.id,
            },
        )

    # Número reservado só depois de todas as recusas possíveis.
    numero_venda = venda.numero_venda
    numero = crud.reservar_proximo_numero_nfce(db, empresa_id)

    payload = montar_payload_nfce(
        empresa, endereco, fiscal_settings, venda, venda.nota_fiscal,
        resultado_calculo=resultado_calculo,
        numero=numero,
        fiscais=_fiscais_efetivos(db, venda),
    )

    tentativas_existentes = crud.contar_documentos_por_venda(db, numero_venda)
    ref = (
        f"nfce-{numero_venda}"
        if tentativas_existentes == 0
        else f"nfce-{numero_venda}-{tentativas_existentes + 1}"
    )

    doc = DocumentoFiscal(
        tipo_documento="NFCE",
        origem_tipo="VENDA",
        origem_id=numero_venda,
        status="PROCESSANDO",
        numero_documento=numero,
        serie=fiscal_settings.serie_nfce,
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

    try:
        resultado = client.emitir_nfce(ref, payload, idempotency_key=doc.idempotency_key)
        _aplicar_resultado(doc, resultado, client)
    except NotImplementedError as e:
        doc.status = "REJEITADA"
        doc.mensagem_sefaz = str(e)
    except Exception as e:
        # Mesma razão da NF-e: falha de comunicação NÃO é rejeição. Marcar
        # REJEITADA liberaria a venda para nova emissão e geraria cupom
        # duplicado. Fica INDETERMINADA até a reconciliação resolver.
        logger.error("[FISCAL] Falha de comunicação ao emitir NFC-e ref=%s: %s", ref, e)
        doc.status = "INDETERMINADA"
        doc.mensagem_sefaz = (
            f"Não foi possível confirmar o resultado junto à SEFAZ: {str(e)[:300]}. "
            f"O documento será reconsultado automaticamente."
        )

    _completar_tributos_pelo_xml(doc, client)

    # Espelha na nota da venda o que a tela do PDV lê para imprimir o cupom.
    espelhar_na_nota_da_venda(db, doc)

    # O contador NÃO é revertido — ver a nota em `emitir_nfe_venda`.
    return doc
