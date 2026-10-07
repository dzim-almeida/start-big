# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/emissao_nucleo.py
# DESCRIÇÃO: Núcleo comum da emissão: aplicar o resultado da emissora no documento,
# arquivar DANFE/XML e ler as configurações fiscais da empresa.
#
# Saiu do emissao.py na F5 (07/10/2026), sem mudar comportamento: o código foi
# movido, não reescrito. Quem importa de `emissao` continua funcionando.
# ---------------------------------------------------------------------------

import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.models.empresa_fiscal_settings import EmpresaFiscalSettings
from app.db.crud import fiscal as crud
from .helpers import ambiente_do_protocolo
from .http import EmissaoResultado
from .http.client import CODIGO_NOTA_INEXISTENTE, RESULTADO_AUTORIZADO, RESULTADO_CANCELADO, RESULTADO_NAO_ENCONTRADO, RESULTADO_NAO_TRANSMITIDO, RESULTADO_PROCESSANDO

logger = logging.getLogger(__name__)


# Status que significam "esta nota FOI transmitida e o desfecho ainda está em
# aberto". São os únicos que vale consultar na emissora.
#
# PENDENTE ficou de fora de propósito: a emissão cria o documento já como
# PROCESSANDO, e `salvar_documento` só dá flush dentro da transação da request —
# um processo que morre no meio do HTTP não deixa linha nenhuma. PENDENTE só
# nascia da reemissão antiga, que NÃO transmitia (hoje ela emite de verdade, ver
# reemissao.py); as linhas que sobraram foram convertidas pela migration
# 89eb6b730bb3. Consultar uma dessas dava 404 eterno, e o 404 virava REJEITADA:
# nota que nunca saiu do prédio aparecia na tela como recusada pela SEFAZ.
STATUS_CONSULTAVEIS = ("PROCESSANDO", "INDETERMINADA")


# A nota não chegou à SEFAZ. Não é rejeição — não há protocolo, não há código de
# rejeição, e o número reservado não foi queimado.
STATUS_NAO_TRANSMITIDA = "NAO_TRANSMITIDA"


def _fiscais_efetivos(db, venda) -> dict:
    """
    A tributação efetiva de cada produto da venda (cascata produto → regra por
    NCM → padrão da loja).

    Resolvida AQUI porque é onde existe sessão: o `payload_builder` recebe o
    resultado pronto. Sem tributação padrão e sem regra de NCM cadastradas, o
    valor é o próprio `produto.fiscal` e o payload sai idêntico ao de antes.
    """
    from app.services.fiscal.tributacao import fiscal_efetivo

    mapa = {}
    for item in venda.itens:
        produto = getattr(item, "produto", None)
        if produto is not None and produto.id not in mapa:
            mapa[produto.id] = fiscal_efetivo(db, produto)
    return mapa


def _arquivar_danfe(doc: DocumentoFiscal, client) -> None:
    """
    Guarda o DANFE em PDF ao lado do XML.

    Separado do XML porque as consequências de falhar são diferentes: sem XML
    a loja fica sem o documento que é obrigada a guardar; sem DANFE ela só
    precisa de internet para reimprimir. Por isso aqui nem se devolve o
    conteúdo — ninguém depende dele em seguida.
    """
    from app.services.fiscal.arquivos import guardar_pdf

    if client is None or not doc.url_pdf or doc.caminho_pdf_local:
        return

    try:
        pdf = client.baixar_pdf(doc.url_pdf)
    except Exception as exc:
        logger.warning("[FISCAL] Não foi possível baixar o DANFE: %s", exc)
        return

    caminho = guardar_pdf(
        pdf, chave=doc.chave_acesso,
        fallback=f"doc-{doc.id}", quando=doc.data_autorizacao,
    )
    if caminho:
        doc.caminho_pdf_local = caminho


def _arquivar_xml(doc: DocumentoFiscal, client) -> Optional[str]:
    """
    Baixa o XML autorizado e guarda no computador da loja.

    Devolve o conteúdo, para quem precisar dele em seguida não baixar de novo
    (é o caso do `vTotTrib`).

    NUNCA levanta. Chega aqui com a nota já autorizada na SEFAZ; disco cheio,
    rede caída ou emissora fora do ar não podem virar erro para o operador —
    viram log, e o arquivo se recupera depois pelo mesmo caminho que o ZIP do
    contador usa.
    """
    from app.services.fiscal.arquivos import guardar_xml, ler_xml

    _arquivar_danfe(doc, client)

    if client is None or not doc.url_xml:
        return None

    # Já guardado: não baixa de novo. XML autorizado é imutável.
    if doc.caminho_xml_local:
        existente = ler_xml(doc.caminho_xml_local)
        if existente:
            return existente

    try:
        xml = client.baixar_xml(doc.url_xml)
    except Exception as exc:
        logger.warning("[FISCAL] Não foi possível baixar o XML para arquivar: %s", exc)
        return None

    if not xml:
        return None

    caminho = guardar_xml(
        xml,
        chave=doc.chave_acesso,
        fallback=f"doc-{doc.id}",
        quando=doc.data_autorizacao,
    )
    if caminho:
        doc.caminho_xml_local = caminho
    return xml


def _aplicar_resultado(doc: DocumentoFiscal, resultado: EmissaoResultado, client=None) -> None:
    """Atualiza DocumentoFiscal com o resultado da API.

    Três desfechos que antes viravam um só, e é por isso que uma lista de
    "rejeitadas" não dizia quais tinham chegado na SEFAZ:

      nunca transmitida (404 na consulta)     -> status intocado + mensagem
      recusada antes da SEFAZ (4xx na emissão) -> NAO_TRANSMITIDA
      rejeitada PELA SEFAZ                     -> REJEITADA, com o código
    """
    status_api = resultado.get("status", "")

    if status_api == RESULTADO_NAO_ENCONTRADO:
        # 404. Quem decide o que ele significa é o CÓDIGO do corpo, não o status
        # HTTP: a plataforma responde 404 tanto para "a nota não está na
        # emissora" quanto para os pré-voos dela (licença não encontrada,
        # empresa sem configuração fiscal), e os pré-voos não afirmam nada sobre
        # a nota.
        #
        # Só `NOTA_NAO_ENCONTRADA_NA_EMISSORA` conclui. Sem ele — pré-voo, ou
        # plataforma antiga que ainda não manda código — o status fica INTOCADO.
        #
        # Errar para o lado de mexer seria o pior desfecho possível: uma
        # INDETERMINADA que na verdade está autorizada na SEFAZ deixaria de
        # trancar a venda, e a próxima emissão viraria nota duplicada, as duas
        # válidas, no mesmo CNPJ. É o que o `EmissaoIncertaError` impede na
        # emissão — e que entrava por esta porta.
        #
        # Nada além da mensagem é sobrescrito: os campos lá embaixo apagariam
        # chave de acesso e protocolo de um documento que já os tinha.
        doc.mensagem_sefaz = resultado.get("mensagem_sefaz")
        if resultado.get("codigo") == CODIGO_NOTA_INEXISTENTE:
            doc.status = STATUS_NAO_TRANSMITIDA
        return

    if status_api == RESULTADO_AUTORIZADO:
        doc.status = "AUTORIZADA"
        doc.data_autorizacao = datetime.now(timezone.utc)
        # A nota é da loja a partir de agora: guarda o XML no disco dela.
        # Best-effort — a autorização já aconteceu e nada aqui pode desfazê-la.
        _arquivar_xml(doc, client)
    elif status_api == RESULTADO_PROCESSANDO:
        doc.status = "PROCESSANDO"
    elif status_api == RESULTADO_CANCELADO:
        doc.status = "CANCELADA"
    elif status_api == RESULTADO_NAO_TRANSMITIDO:
        # A plataforma ou a emissora recusaram o payload. A SEFAZ não viu nada.
        doc.status = STATUS_NAO_TRANSMITIDA
    elif resultado.get("status_focus") == "denegado":
        # Denegada é decisão da SEFAZ sobre o CONTRIBUINTE, não sobre a nota:
        # reenviar não adianta, e o lojista precisa saber que a diferença existe.
        # Caía no balde `erro` -> REJEITADA, que convida a reemitir para sempre.
        doc.status = "DENEGADA"
    else:
        # A SEFAZ respondeu "não". Isso é diferente de não sabermos a resposta
        # — falha de comunicação vira INDETERMINADA, nunca REJEITADA.
        doc.status = "REJEITADA"

    doc.chave_acesso = resultado.get("chave_acesso")
    doc.protocolo_autorizacao = resultado.get("protocolo")
    # O ambiente gravado na criação era o palpite local. O protocolo diz o que
    # a SEFAZ fez de verdade — e é ele que o cupom, o drawer e o diagnóstico
    # passam a ler. Sem protocolo (rejeitada, processando) o palpite fica, e a
    # tela o trata como "não confirmado".
    ambiente_real = ambiente_do_protocolo(doc.protocolo_autorizacao)
    if ambiente_real is not None:
        doc.ambiente_emissao = ambiente_real
    doc.url_pdf = resultado.get("url_pdf")
    doc.url_xml = resultado.get("url_xml")
    # O número é o que não engana. O texto da SEFAZ já chegou dizendo
    # "destinatário" enquanto citava o CNPJ do emitente — meia hora perdida
    # atrás do campo errado. Os dois são gravados: o código para decidir, o
    # texto para ler.
    doc.codigo_status_sefaz = resultado.get("codigo_sefaz")
    doc.mensagem_sefaz = resultado.get("mensagem_sefaz")
    if resultado.get("status_focus"):
        doc.status_focus = resultado["status_focus"]

    if resultado.get("numero"):
        doc.numero_documento = resultado["numero"]
    if resultado.get("serie"):
        doc.serie = resultado["serie"]

    # Campos de NFC-e. A NF-e não os devolve; o `if` evita apagar o que já
    # estava gravado numa reconsulta que venha sem eles.
    if resultado.get("qrcode"):
        doc.qrcode = resultado["qrcode"]
    if resultado.get("url_consulta"):
        doc.url_consulta = resultado["url_consulta"]
    if resultado.get("valor_tributos") is not None:
        doc.valor_tributos = int(round(float(resultado["valor_tributos"]) * 100))


def _obter_fiscal_settings(db: Session, empresa_id: int) -> EmpresaFiscalSettings:
    fs = crud.get_fiscal_settings(db, empresa_id)
    if not fs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Configurações fiscais não cadastradas para esta empresa.",
        )
    return fs


def _avisos(empresa, cliente) -> list[str]:
    # Import local: mantém o bytecode deste arquivo (teto do PyArmor) sem a
    # lógica dos avisos, que mora em `avisos.py`.
    from app.services.fiscal.avisos import avisos_da_emissao
    return avisos_da_emissao(empresa, cliente)
