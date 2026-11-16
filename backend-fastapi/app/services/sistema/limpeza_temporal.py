import os
import sys
import glob
import shutil
import tempfile
import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enum import VendaStatus
from app.db.models.venda import Venda
from app.db.models.orcamento import Orcamento

logger = logging.getLogger(__name__)

DIAS_EXPIRACAO_VENDA_ATIVA = 3
DIAS_EXPIRACAO_ORCAMENTO = 7


def cancelar_vendas_ativas_expiradas(db: Session) -> int:
    """
    Deleta vendas ATIVAS (rascunhos) que nao foram atualizadas nos ultimos
    DIAS_EXPIRACAO_VENDA_ATIVA dias. Retorna a quantidade deletada.
    """
    limite = datetime.now() - timedelta(days=DIAS_EXPIRACAO_VENDA_ATIVA)

    stmt = select(Venda).where(
        Venda.status == VendaStatus.ATIVA,
        Venda.atualizado_em < limite,
    )
    vendas_expiradas = db.scalars(stmt).all()
    quantidade = len(vendas_expiradas)

    for venda in vendas_expiradas:
        db.delete(venda)

    if quantidade > 0:
        db.commit()
        logger.info(
            "Limpeza automatica: %d rascunho(s) de venda deletado(s) (anterior a %s)",
            quantidade,
            limite.isoformat(),
        )
    else:
        logger.debug("Limpeza automatica: nenhuma venda ativa expirada encontrada.")

    return quantidade


def limpar_orcamentos_expirados(db: Session) -> int:
    """
    Remove orcamentos nao convertidos que nao foram atualizados nos ultimos
    DIAS_EXPIRACAO_ORCAMENTO dias. Retorna a quantidade removida.
    """
    limite = datetime.now() - timedelta(days=DIAS_EXPIRACAO_ORCAMENTO)

    stmt = select(Orcamento).where(
        Orcamento.convertido == False,
        Orcamento.atualizado_em < limite,
    )
    orcamentos_expirados = db.scalars(stmt).all()
    quantidade = len(orcamentos_expirados)

    for orcamento in orcamentos_expirados:
        db.delete(orcamento)

    if quantidade > 0:
        db.commit()
        logger.info(
            "Limpeza automatica: %d orcamento(s) removido(s) (anterior a %s)",
            quantidade,
            limite.isoformat(),
        )
    else:
        logger.debug("Limpeza automatica: nenhum orcamento expirado encontrado.")

    return quantidade

def _e_pasta_do_startbig(pasta: str) -> bool:
    """A pasta de extracao do NOSSO .exe tem `alembic/` e `dist/` (run.spec)."""
    return os.path.isdir(os.path.join(pasta, "alembic")) and os.path.isdir(os.path.join(pasta, "dist"))


def _mesma_pasta(a: str, b: str | None) -> bool:
    if not b:
        return False
    try:
        return os.path.samefile(a, b)
    except OSError:
        return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def limpar_temp_data(temp_dir: str | None = None) -> int:
    """Apaga as pastas `%TEMP%/_MEI*` que execucoes ENCERRADAS do .exe deixaram.

    O PyInstaller (onefile) extrai o programa numa `_MEIxxxx` e a apaga ao sair;
    quando o processo e derrubado, ela fica (~40 MB cada). Esta limpeza tira as
    que sobraram. Devolve quantas apagou.

    Ate 12/10/2026 apagava TODA `_MEI*` menos a propria, inclusive a de processos
    VIVOS: uma segunda instancia do StartBig (tarefa StartBigServer + sidecar do
    app, ou um reinicio com o antigo ainda no ar) perdia os arquivos de migracao
    e caia; outros programas PyInstaller do cliente perdiam os deles. E fora do
    .exe nao havia "a propria" a poupar: a suite de testes apagava todas. Agora
    tres travas:
    - so roda no .exe (`sys.frozen`); em desenvolvimento e nos testes, nada;
    - so mexe em pasta do StartBig (`alembic/` + `dist/`), nunca na de outro app;
    - so apaga o que ninguem usa: primeiro RENOMEIA. No Windows, renomear pasta
      com arquivo aberto ou DLL carregada falha -- e o caso de qualquer processo
      vivo, que tem o python3xx.dll carregado dali. Falhou: esta em uso, fica.
    """
    if not getattr(sys, "frozen", False):
        return 0

    temp_dir = temp_dir or tempfile.gettempdir()
    propria = getattr(sys, "_MEIPASS", None)
    apagadas = 0

    for pasta in glob.glob(os.path.join(temp_dir, "_MEI*")):
        if not os.path.isdir(pasta) or _mesma_pasta(pasta, propria):
            continue
        if not _e_pasta_do_startbig(pasta):
            continue                                   # de outro programa: nao e nossa
        alvo = pasta + ".removendo"
        try:
            os.rename(pasta, alvo)                     # falha se algum processo usa a pasta
        except OSError:
            logger.info("Limpeza automática: %s em uso por outro processo; mantida.", pasta)
            continue
        try:
            shutil.rmtree(alvo)
            apagadas += 1
            logger.info("Limpeza automática: diretório temporário removido: %s", pasta)
        except Exception as e:  # noqa: BLE001 -- sobra para a proxima limpeza
            logger.error("Erro ao remover diretório temporário %s: %s", alvo, str(e))

    return apagadas
