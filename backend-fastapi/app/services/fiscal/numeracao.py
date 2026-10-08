# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/numeracao.py
# DESCRIÇÃO: Regras da sequência de numeração que não cabem em `emissao.py`
#            (teto de bytecode do PyArmor). F3 do plano de refatoração.
#
# O caso que motivou (06/10/2026): o primeiro cliente em produção já emitia por
# outro sistema. O StartBig começou do 1, a SEFAZ devolveu a Rejeição 539
# ("duplicidade com diferença na chave") no nº 4 da série 2 — número emitido em
# 09/2026 pelo sistema antigo — e:
#   - nada no sistema sabia transformar a 539 em "ajuste a numeração";
#   - a sugestão de inutilização listava TODO número de 1 até o contador, inclusive
#     os usados pelo sistema antigo — e inutilizar número usado a SEFAZ recusa.
# ---------------------------------------------------------------------------

import re
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.crud import fiscal as crud
from app.db.models.documento_fiscal import DocumentoFiscal

# cStat que dizem "este número JÁ EXISTE na SEFAZ":
#   204 — duplicidade (a mesma nota já autorizada);
#   539 — duplicidade com diferença na chave (outra nota, quase sempre de outro
#         sistema, usou o número).
# Número com uma dessas rejeições NÃO é buraco: não se inutiliza.
CSTAT_NUMERO_JA_USADO = (204, 539)

_RE_CHAVE = re.compile(r"chNFe:\s*(\d{44})")


def ler_chave_da_mensagem(*textos: Optional[str]) -> Optional[dict]:
    """Série, número e modelo da chave que a SEFAZ devolve na 539.

    Chave (44): UF(2) AAMM(4) CNPJ(14) modelo(2) série(3) número(9) tpEmis(1)
    código(8) DV(1).
    """
    for texto in textos:
        achado = _RE_CHAVE.search(texto or "")
        if achado:
            chave = achado.group(1)
            return {
                "chave": chave,
                "modelo": int(chave[20:22]),
                "serie": int(chave[22:25]),
                "numero": int(chave[25:34]),
                "ano_mes": chave[2:6],
            }
    return None


def numeros_usados_fora(db: Session, tipo_documento: str, serie: int) -> set[int]:
    """Números que a SEFAZ disse já existirem (rejeições 204/539) nesta série."""
    return {
        n for (n,) in db.query(DocumentoFiscal.numero_documento).filter(
            DocumentoFiscal.tipo_documento == tipo_documento,
            DocumentoFiscal.serie == serie,
            DocumentoFiscal.numero_documento.isnot(None),
            DocumentoFiscal.codigo_status_sefaz.in_(CSTAT_NUMERO_JA_USADO),
        ).all()
    }


def numeros_reservados_pelo_startbig(db: Session, tipo_documento: str, serie: int) -> set[int]:
    """Todo número que um documento DESTE sistema já ocupou nesta série."""
    return {
        n for (n,) in db.query(DocumentoFiscal.numero_documento).filter(
            DocumentoFiscal.tipo_documento == tipo_documento,
            DocumentoFiscal.serie == serie,
            DocumentoFiscal.numero_documento.isnot(None),
        ).all()
    }


def maior_numero_do_startbig(db: Session, tipo_documento: str, serie: int) -> int:
    maior = db.query(func.max(DocumentoFiscal.numero_documento)).filter(
        DocumentoFiscal.tipo_documento == tipo_documento,
        DocumentoFiscal.serie == serie,
    ).scalar()
    return int(maior or 0)


def validar_novo_ultimo_numero(
    db: Session, tipo_documento: str, serie: int, ultimo: int,
) -> None:
    """Recusa voltar o contador para trás de uma nota que o próprio StartBig fez.

    Voltar para trás faria a próxima emissão repetir um número deste sistema:
    Rejeição 204/539 garantida, número gasto. Subir é sempre permitido (é o
    caso de quem descobre que o sistema antigo foi mais longe).
    """
    maior = maior_numero_do_startbig(db, tipo_documento, serie)
    if ultimo < maior:
        nome = "NF-e" if tipo_documento == "NFE" else "NFC-e"
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"O último número da {nome} série {serie} não pode ser {ultimo}: o "
                f"StartBig já usou o nº {maior} nesta série. Informe {maior} ou mais."
            ),
        )


def ajustar_numeracao_por_duplicidade(
    db: Session, empresa_id: int, documento_id: int, ultimo_numero: int,
) -> dict:
    """Depois de uma 539: leva o contador para depois do que o outro sistema usou.

    O lojista informa o último número usado fora (perguntado ao contador); a
    tela já vem preenchida com o número que a SEFAZ acusou. Nunca anda para trás
    e nunca troca a série — só o contador da série da própria nota.
    """
    doc = crud.get_documento_fiscal(db, documento_id)
    # Um banco por empresa (como na reemissão): não há dono a conferir.
    if doc is None:
        raise HTTPException(status_code=404, detail="Documento fiscal não encontrado.")

    if doc.codigo_status_sefaz != 539:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Só uma rejeição por número já usado (539) ajusta a numeração por aqui.",
        )

    usada = ler_chave_da_mensagem(doc.mensagem_sefaz, doc.motivo_rejeicao)
    numero_acusado = usada["numero"] if usada else (doc.numero_documento or 0)

    fs = crud.get_fiscal_settings(db, empresa_id)
    if fs is None:
        raise HTTPException(status_code=422, detail="Configurações fiscais não cadastradas.")

    nfe = doc.tipo_documento == "NFE"
    serie_atual = fs.serie_nfe if nfe else fs.serie_nfce
    if doc.serie != serie_atual:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"A nota recusada é da série {doc.serie}, e a configuração atual usa a "
                f"série {serie_atual}. Ajuste em Centro Fiscal › Configurações."
            ),
        )

    atual = fs.ultimo_numero_nfe if nfe else fs.ultimo_numero_nfce
    minimo = max(numero_acusado, atual)
    if ultimo_numero < minimo:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"O último número precisa ser pelo menos {minimo}.",
        )

    if nfe:
        fs.ultimo_numero_nfe = ultimo_numero
        # Até aqui é do sistema anterior: não sugerir inutilizar.
        fs.numeracao_piso_nfe = ultimo_numero
    else:
        fs.ultimo_numero_nfce = ultimo_numero
    fs.numeracao_confirmada = True
    db.flush()

    return {
        "tipo_documento": doc.tipo_documento,
        "serie": serie_atual,
        "ultimo_numero": ultimo_numero,
        "proximo_numero": ultimo_numero + 1,
        "mensagem": (
            f"Numeração ajustada: a próxima nota da série {serie_atual} sai como "
            f"nº {ultimo_numero + 1}. Agora reemita a nota."
        ),
    }
