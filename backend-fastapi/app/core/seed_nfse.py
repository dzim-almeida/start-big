# ---------------------------------------------------------------------------
# ARQUIVO: app/core/seed_nfse.py
# DESCRIÇÃO: Carga no boot das tabelas oficiais da NFS-e (código de tributação
#            nacional, NBS e a correlação entre eles). docs/nfse-plano.md, F1.
# ---------------------------------------------------------------------------
"""
Mesma regra do `_seed_ncm` (core/tarefas.py), de onde este arquivo foi tirado
para não engordar o tarefas.py:

- IDEMPOTENTE e barato: se a contagem do banco bate com a do arquivo, sai sem
  gravar. Só recarrega quando o arquivo muda (versão nova do portal) ou o banco
  está vazio.
- NUNCA derruba o boot. Sem as tabelas, os campos de código nacional e NBS
  continuam aceitando digitação direta.

Os arquivos são gerados por `scripts/gerar_tabelas_nfse.py` a partir das
planilhas oficiais do gov.br/nfse.
"""

import csv
import gzip
import logging
import os

from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def caminho_dado(nome: str) -> str:
    """
    Onde está um arquivo de `app/data`, em dev e no app instalado.

    No sidecar o código roda ofuscado de dentro de `dist/`, e o PyArmor só copia
    `.py`. Os dados chegam pelo `run.spec` (`('app/data', 'app/data')`) no
    `STARTBIG_BUNDLE_DIR` que o `run.py` publica. Sem a variável (dev), vale o
    caminho do código-fonte.
    """
    bundle = os.environ.get("STARTBIG_BUNDLE_DIR")
    if bundle:
        empacotado = os.path.join(bundle, "app", "data", nome)
        if os.path.exists(empacotado):
            return empacotado
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", nome)


def ler_csv_gz(nome: str) -> list[dict]:
    caminho = caminho_dado(nome)
    with gzip.open(caminho, "rt", encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def _carregar(db, modelo, arquivo: str) -> None:
    linhas = ler_csv_gz(arquivo)
    if db.query(modelo).count() == len(linhas):
        return
    db.query(modelo).delete()
    db.bulk_insert_mappings(modelo, linhas)
    db.commit()
    logger.info("[NFS-e] %s: %d linhas carregadas.", modelo.__tablename__, len(linhas))


def seed_tabelas_nfse() -> None:
    from app.db.models.nfse_tabelas import Nbs, NfseCorrelacaoNbs, NfseServicoNacional

    db = SessionLocal()
    try:
        _carregar(db, NfseServicoNacional, "nfse_servicos_nacionais.csv.gz")
        _carregar(db, Nbs, "nbs.csv.gz")
        _carregar(db, NfseCorrelacaoNbs, "nfse_correlacao_nbs.csv.gz")
    except Exception:
        db.rollback()
        logger.exception("[NFS-e] Falha ao carregar as tabelas; os campos seguem como digitação livre.")
    finally:
        db.close()
