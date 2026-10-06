# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/inutilizacao.py
# DESCRIÇÃO: Detecção de buracos na numeração e inutilização de faixas.
#
# Desde que a emissão parou de devolver o número ao contador em caso de falha
# (achado C3), buraco na sequência passou a ser um resultado esperado — é o
# preço de nunca arriscar Rejeição 204 por duplicidade.
#
# A contrapartida é esta: a SEFAZ exige que os números reservados e não usados
# sejam formalmente declarados como inutilizados. Sem isso a empresa acumula
# lacunas e fica irregular perante o fisco.
# ---------------------------------------------------------------------------

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.crud import fiscal as crud
from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.models.inutilizacao_fiscal import InutilizacaoFiscal
from app.services.fiscal.http.client import RESULTADO_NAO_TRANSMITIDO

logger = logging.getLogger(__name__)


JUSTIFICATIVA_MINIMA = 15

# Um número só é considerado consumido de verdade nestes estados.
# INDETERMINADA entra aqui de propósito: enquanto não sabemos se a nota foi
# autorizada, inutilizar o número seria declarar à SEFAZ que ele não foi usado
# — e ele pode ter sido.
_STATUS_QUE_CONSOMEM_NUMERO = (
    "AUTORIZADA", "CANCELADA", "PROCESSANDO", "PENDENTE", "INDETERMINADA",
)


def _agrupar_em_faixas(numeros: list[int]) -> list[tuple[int, int]]:
    """[3, 4, 5, 9, 11, 12] -> [(3, 5), (9, 9), (11, 12)]"""
    if not numeros:
        return []

    ordenados = sorted(set(numeros))
    faixas: list[tuple[int, int]] = []
    inicio = anterior = ordenados[0]

    for n in ordenados[1:]:
        if n == anterior + 1:
            anterior = n
            continue
        faixas.append((inicio, anterior))
        inicio = anterior = n

    faixas.append((inicio, anterior))
    return faixas


def listar_gaps_numeracao(db: Session, empresa_id: int) -> list[dict]:
    """
    Lista as faixas de numeração que precisam ser inutilizadas.

    Um número entra na lista quando:
      - está abaixo do contador e ACIMA do piso (`numeracao_piso_nfe`, o último
        número informado à mão) — ou, abaixo do piso, uma nota DESTE sistema o
        usou —, e
      - nenhum documento vivo o ocupa, e
      - a SEFAZ não disse que ele já existe (rejeições 204/539), e
      - ainda não há inutilização registrada cobrindo ele.

    Até 06/10/2026 o piso não existia ("todo número de 1 até o contador"). Para
    quem veio de outro sistema e informou "último = 37", isso listava 1..36 —
    números USADOS pelo sistema antigo, que a SEFAZ recusa inutilizar. E a 539
    marcava como buraco justamente o número que ela acabou de dizer que existe.
    Piso 0 (o padrão) é exatamente a regra antiga: número reservado e perdido
    numa falha, sem nota nenhuma, continua aparecendo.
    """
    from app.services.fiscal.numeracao import numeros_reservados_pelo_startbig, numeros_usados_fora

    fs = crud.get_fiscal_settings(db, empresa_id)
    if not fs or fs.ultimo_numero_nfe < 1:
        return []

    serie = fs.serie_nfe
    ultimo = fs.ultimo_numero_nfe

    ocupados = {
        n for (n,) in db.query(DocumentoFiscal.numero_documento).filter(
            DocumentoFiscal.tipo_documento == "NFE",
            DocumentoFiscal.serie == serie,
            DocumentoFiscal.numero_documento.isnot(None),
            DocumentoFiscal.status.in_(_STATUS_QUE_CONSOMEM_NUMERO),
        ).all()
    }

    # Faixas já declaradas (ou em declaração) não voltam para a lista.
    ja_tratados: set[int] = set()
    for inut in db.query(InutilizacaoFiscal).filter(
        InutilizacaoFiscal.empresa_id == empresa_id,
        InutilizacaoFiscal.serie == serie,
        InutilizacaoFiscal.status.in_(("PENDENTE", "PROCESSANDO", "HOMOLOGADA", "INDETERMINADA")),
    ).all():
        ja_tratados.update(range(inut.numero_inicial, inut.numero_final + 1))

    piso = getattr(fs, "numeracao_piso_nfe", 0) or 0
    reservados = numeros_reservados_pelo_startbig(db, "NFE", serie)
    usados_fora = numeros_usados_fora(db, "NFE", serie)
    buracos = [
        n for n in range(1, ultimo + 1)
        if (n > piso or n in reservados)
        and n not in ocupados and n not in ja_tratados and n not in usados_fora
    ]

    return [
        {
            "serie": serie,
            "numero_inicial": inicio,
            "numero_final": fim,
            "quantidade": fim - inicio + 1,
        }
        for inicio, fim in _agrupar_em_faixas(buracos)
    ]


def _validar_faixa(
    db: Session, empresa_id: int, serie: int, inicial: int, final: int
) -> None:
    """Recusa faixas malformadas ou que contenham número realmente usado."""
    if inicial < 1 or final < inicial:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Faixa inválida: {inicial} a {final}.",
        )

    fs = crud.get_fiscal_settings(db, empresa_id)
    if not fs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Configurações fiscais não cadastradas para esta empresa.",
        )

    if final > fs.ultimo_numero_nfe:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Não é possível inutilizar até {final}: o contador da série "
                f"{serie} está em {fs.ultimo_numero_nfe}. Só números já "
                f"reservados podem ser inutilizados."
            ),
        )

    conflito = db.query(DocumentoFiscal).filter(
        DocumentoFiscal.tipo_documento == "NFE",
        DocumentoFiscal.serie == serie,
        DocumentoFiscal.numero_documento >= inicial,
        DocumentoFiscal.numero_documento <= final,
        DocumentoFiscal.status.in_(_STATUS_QUE_CONSOMEM_NUMERO),
    ).first()

    from app.services.fiscal.numeracao import numeros_usados_fora

    usado_fora = sorted(n for n in numeros_usados_fora(db, "NFE", serie) if inicial <= n <= final)
    if usado_fora:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "codigo": "NUMERO_USADO_FORA",
                "mensagem": (
                    f"A SEFAZ informou que o número {usado_fora[0]} desta série já existe "
                    f"(emitido por outro sistema). Número usado não se inutiliza."
                ),
            },
        )

    if conflito:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "codigo": "NUMERO_EM_USO",
                "mensagem": (
                    f"O número {conflito.numero_documento} da faixa está ocupado por "
                    f"um documento em estado {conflito.status}. Inutilizar declararia "
                    f"à SEFAZ que ele não foi usado."
                ),
                "documento_id": conflito.id,
            },
        )


def solicitar_inutilizacao(
    db: Session,
    empresa_id: int,
    serie: int,
    numero_inicial: int,
    numero_final: int,
    justificativa: str,
) -> InutilizacaoFiscal:
    """Registra e transmite um pedido de inutilização de faixa."""
    justificativa = (justificativa or "").strip()
    if len(justificativa) < JUSTIFICATIVA_MINIMA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"A justificativa deve ter ao menos {JUSTIFICATIVA_MINIMA} "
                f"caracteres (a SEFAZ exige)."
            ),
        )

    _validar_faixa(db, empresa_id, serie, numero_inicial, numero_final)

    fs = crud.get_fiscal_settings(db, empresa_id)
    ano = datetime.now(timezone.utc).year

    registro = InutilizacaoFiscal(
        empresa_id=empresa_id,
        modelo=55,
        serie=serie,
        ano=ano,
        numero_inicial=numero_inicial,
        numero_final=numero_final,
        justificativa=justificativa,
        status="PROCESSANDO",
        ref_api=f"inut-{serie}-{numero_inicial}-{numero_final}-{ano}",
        idempotency_key=str(uuid.uuid4()),
        ambiente_emissao=fs.ambiente_emissao,
        data_solicitacao=datetime.now(timezone.utc),
    )
    db.add(registro)
    db.flush()

    from .http import get_fiscal_client

    token = crud.get_licenca_token(db)
    client = get_fiscal_client(fs.ambiente_emissao, token)

    payload = {
        "modelo": 55,
        "serie": serie,
        "ano": ano,
        "numero_inicial": numero_inicial,
        "numero_final": numero_final,
        "justificativa": justificativa,
    }

    try:
        resultado = client.inutilizar_numeracao(
            registro.ref_api, payload, idempotency_key=registro.idempotency_key,
        )
        _aplicar_resultado_inutilizacao(registro, resultado)
    except NotImplementedError as e:
        registro.status = "REJEITADA"
        registro.mensagem_sefaz = str(e)
    except Exception as e:
        # Mesma regra da emissão: sem resposta não é recusa. Manter
        # INDETERMINADA impede que a faixa volte para a lista de gaps e seja
        # solicitada duas vezes.
        logger.error("[FISCAL] Falha ao inutilizar faixa %s: %s", registro.ref_api, e)
        registro.status = "INDETERMINADA"
        registro.mensagem_sefaz = (
            f"Não foi possível confirmar a inutilização junto à SEFAZ: {str(e)[:300]}."
        )

    return registro


def _aplicar_resultado_inutilizacao(registro: InutilizacaoFiscal, resultado: dict) -> None:
    """Traduz a resposta da API para o registro local.

    Quatro desfechos, e os dois últimos eram um só até 19/09/2026:

      homologado/autorizado  -> HOMOLOGADA      a SEFAZ registrou a faixa
      processando            -> PROCESSANDO     a SEFAZ ainda vai responder
      nao_transmitido        -> NAO_TRANSMITIDA a plataforma recusou ANTES da
                                                SEFAZ (rota inexistente, licença
                                                sem ficha fiscal, payload)
      qualquer outro         -> REJEITADA       a SEFAZ recusou, com código

    NAO_TRANSMITIDA fica FORA da lista que fecha a faixa em `listar_gaps`, de
    propósito: nada chegou na SEFAZ, os números continuam abertos e o pedido
    pode ser refeito quando a causa for resolvida -- igual à REJEITADA. O que
    muda é a tela: "a plataforma recusou antes de enviar" manda o lojista olhar
    a configuração, não a SEFAZ.
    """
    status_api = resultado.get("status", "")

    if status_api in ("homologado", "autorizado"):
        registro.status = "HOMOLOGADA"
        registro.data_homologacao = datetime.now(timezone.utc)
    elif status_api == "processando":
        registro.status = "PROCESSANDO"
    elif status_api == RESULTADO_NAO_TRANSMITIDO:
        registro.status = "NAO_TRANSMITIDA"
    else:
        registro.status = "REJEITADA"

    registro.protocolo = resultado.get("protocolo")
    registro.codigo_status_sefaz = resultado.get("codigo_sefaz")
    registro.mensagem_sefaz = resultado.get("mensagem_sefaz")
    registro.url_xml = resultado.get("url_xml")


def listar_inutilizacoes(db: Session, empresa_id: int) -> list[InutilizacaoFiscal]:
    return (
        db.query(InutilizacaoFiscal)
        .filter(InutilizacaoFiscal.empresa_id == empresa_id)
        .order_by(InutilizacaoFiscal.data_criacao.desc())
        .all()
    )
