import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.session import SessionLocal
from app.services.limpeza_temporal import cancelar_vendas_ativas_expiradas, limpar_orcamentos_expirados

logger = logging.getLogger(__name__)

INTERVALO_LIMPEZA_HORAS = 6


async def _loop_limpeza_temporal():
    """Loop em segundo plano que executa a limpeza periodicamente."""
    while True:
        try:
            db = SessionLocal()
            try:
                cancelar_vendas_ativas_expiradas(db)
                limpar_orcamentos_expirados(db)
            finally:
                db.close()
        except Exception:
            logger.exception("Erro na limpeza automatica temporal")

        await asyncio.sleep(INTERVALO_LIMPEZA_HORAS * 3600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerenciador de ciclo de vida do FastAPI.
    Inicia tarefas em segundo plano ao iniciar e cancela ao encerrar.
    """
    logger.info("Iniciando tarefa de limpeza automatica temporal...")
    tarefa = asyncio.create_task(_loop_limpeza_temporal())

    yield

    logger.info("Encerrando tarefa de limpeza automatica temporal...")
    tarefa.cancel()
    try:
        await tarefa
    except asyncio.CancelledError:
        pass
