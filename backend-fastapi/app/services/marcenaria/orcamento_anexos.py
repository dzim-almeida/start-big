# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/orcamento_anexos.py
# DESCRICAO: Fotos e PDFs da medicao do orcamento (Spec 06A, D27-D31, §7.7).
# ---------------------------------------------------------------------------
"""
- Imagem (JPG, PNG, WebP, ate 5 MB): passa pelo pipeline de `core/imagem.py`
  (corrige rotacao, reduz, grava em WebP).
- PDF (ate 10 MB): guardado como veio, conferido pelo inicio `%PDF`.

Os anexos sao do CODIGO, nao da versao (D30): todas as versoes veem os mesmos,
e a nova versao nao copia arquivo nenhum.

D31: incluir, excluir e mudar a legenda vale em QUALQUER status, menos
SUBSTITUIDO e APROVADO, e NAO soma na `revisao` (a foto do ambiente chega
depois do envio e nao muda o preco; somar daria conflito falso com quem esta
editando o rascunho).
"""

import os
from typing import Callable, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core import imagem
from app.db.crud.marcenaria import orcamento as crud
from app.db.models.marcenaria.orcamento import (
    MarcenariaOrcamento,
    MarcenariaOrcamentoAnexo,
    StatusOrcamento,
)
from app.services.marcenaria import erros
from app.services.marcenaria.orcamento_comum import carregar, registrar_evento, usuario_id

LIMITE_ANEXOS = 60            # por codigo (secao 5.1): protege o disco
CONTEXTO = "orcamento_anexo"  # chave do CONTEXTO_IMAGEM (pasta e qualidade)

MSG_NAO_SUPORTADO = "Arquivo não suportado. Envie JPG, PNG, WebP ou PDF."
_EXTENSOES_FOTO = {".jpg", ".jpeg", ".png", ".webp"}


def _anexo_em_dict(anexo: MarcenariaOrcamentoAnexo) -> dict:
    return {
        "id": anexo.id,
        "tipo": anexo.tipo,
        "nome_arquivo": anexo.nome_arquivo,
        "url": anexo.url,
        "legenda": anexo.legenda,
        "usuario_id": anexo.usuario_id,
        "data_criacao": anexo.data_criacao,
    }


def _exigir_anexos_editaveis(orc: MarcenariaOrcamento) -> None:
    """D31: SUBSTITUIDO e APROVADO nao mudam mais."""
    if orc.status in (StatusOrcamento.SUBSTITUIDO, StatusOrcamento.APROVADO):
        erros.conflito(
            erros.STATUS_NAO_EDITAVEL,
            f"Os anexos de um orçamento {erros.STATUS_NA_FRASE[orc.status]} não podem ser alterados.",
        )


def listar(db: Session, orcamento_id: int) -> list[dict]:
    """Anexos do codigo deste orcamento (os mesmos em todas as versoes)."""
    orc = carregar(db, orcamento_id)
    return [_anexo_em_dict(a) for a in crud.listar_anexos(db, orc.codigo)]


def _gravar_arquivo(arquivo: UploadFile, codigo: str) -> tuple[str, str]:
    """Confere e grava o arquivo. Devolve (tipo, url). Erros em 422 (secao 6.9)."""
    extensao = os.path.splitext(arquivo.filename or "")[1].lower()
    conteudo = arquivo.file.read()                          # bytes do upload

    if extensao == ".pdf":
        try:
            return "PDF", imagem.salvar_pdf(conteudo, codigo, CONTEXTO)
        except ValueError as erro:
            if str(erro) == "tamanho":
                erros.invalido(f"Arquivo maior que {imagem.TAMANHO_MAXIMO_PDF_BYTES // (1024 * 1024)} MB.")
            erros.invalido(MSG_NAO_SUPORTADO)               # nao comeca com %PDF

    if extensao in _EXTENSOES_FOTO:
        if len(conteudo) > imagem.TAMANHO_MAXIMO_BYTES:     # a mensagem desta spec, antes da do pipeline
            erros.invalido(f"Arquivo maior que {imagem.TAMANHO_MAXIMO_BYTES // (1024 * 1024)} MB.")
        arquivo.file.seek(0)                                # o pipeline le de novo do comeco
        try:
            return "FOTO", imagem.salvar_imagem(arquivo, codigo, CONTEXTO)
        except HTTPException as erro:
            if erro.status_code == 400:                     # tipo, extensao ou imagem corrompida
                erros.invalido(MSG_NAO_SUPORTADO)
            raise

    erros.invalido(MSG_NAO_SUPORTADO)


def incluir(
    db: Session, orcamento_id: int, arquivo: UploadFile, legenda: Optional[str], usuario_token: dict,
) -> dict:
    """Inclui um anexo (D27, D28). Nao soma na revisao (D31)."""
    orc = carregar(db, orcamento_id)
    _exigir_anexos_editaveis(orc)
    legenda = (legenda or "").strip() or None
    if legenda is not None and len(legenda) > 120:
        erros.invalido("A legenda pode ter até 120 caracteres.")
    if crud.contar_anexos(db, orc.codigo) >= LIMITE_ANEXOS:
        erros.limite_atingido(LIMITE_ANEXOS, "anexos")

    tipo, url = _gravar_arquivo(arquivo, orc.codigo)
    try:
        anexo = MarcenariaOrcamentoAnexo(
            codigo_orcamento=orc.codigo,
            tipo=tipo,
            nome_arquivo=(arquivo.filename or "arquivo")[:255],
            url=url,
            legenda=legenda,
            usuario_id=usuario_id(usuario_token),
        )
        db.add(anexo)
        db.flush()                                          # o anexo ganha id para o evento
        registrar_evento(db, orc, "ANEXO_INCLUIDO", f"Anexo incluído: {anexo.nome_arquivo}.", usuario_token,
                         {"anexo_id": anexo.id, "tipo": tipo, "nome_arquivo": anexo.nome_arquivo})
        db.commit()
    except Exception:
        db.rollback()
        imagem.deletar_imagem(url)                          # nao deixa arquivo sem linha no banco
        raise
    return _anexo_em_dict(anexo)


def _anexo(db: Session, orc: MarcenariaOrcamento, anexo_id: int) -> MarcenariaOrcamentoAnexo:
    anexo = crud.get_anexo(db, anexo_id, orc.codigo)
    if anexo is None:
        erros.nao_encontrado("Anexo não encontrado.")
    return anexo


def alterar_legenda(db: Session, orcamento_id: int, anexo_id: int, legenda: Optional[str]) -> dict:
    """PATCH da legenda (Revisao 1). Edicao de campo: sem evento, sem revisao."""
    orc = carregar(db, orcamento_id)
    _exigir_anexos_editaveis(orc)
    anexo = _anexo(db, orc, anexo_id)
    anexo.legenda = legenda
    db.commit()
    return _anexo_em_dict(anexo)


def remover(db: Session, orcamento_id: int, anexo_id: int, usuario_token: dict) -> None:
    """Remove o anexo de TODAS as versoes (D30) e apaga o arquivo do disco."""
    orc = carregar(db, orcamento_id)
    _exigir_anexos_editaveis(orc)
    anexo = _anexo(db, orc, anexo_id)
    url, nome = anexo.url, anexo.nome_arquivo
    db.delete(anexo)
    registrar_evento(db, orc, "ANEXO_REMOVIDO", f"Anexo removido: {nome}.", usuario_token,
                     {"anexo_id": anexo_id, "nome_arquivo": nome})
    db.commit()
    imagem.deletar_imagem(url)                              # so depois de gravar no banco


def apagar_anexos_do_codigo(db: Session, codigo: str) -> list[Callable[[], None]]:
    """Tira as linhas dos anexos do codigo (sem commit) e devolve as funcoes que
    apagam os arquivos -- para chamar SO depois do commit (excluir, D18)."""
    remocoes = []
    for anexo in crud.listar_anexos(db, codigo):
        url = anexo.url
        db.delete(anexo)
        remocoes.append(lambda url=url: imagem.deletar_imagem(url))   # `url=url` fixa o valor de cada volta
    return remocoes
