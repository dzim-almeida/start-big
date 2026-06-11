import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.db.session import SessionLocal, engine
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


def _aplicar_migracoes():
    """Aplica colunas novas que ainda não existem no banco (safe migrations)."""
    migracoes = [
        ("clientes", "saldo_credito", "ALTER TABLE clientes ADD COLUMN saldo_credito INTEGER NOT NULL DEFAULT 0"),
        ("vendas", "observacao_interna", "ALTER TABLE vendas ADD COLUMN observacao_interna VARCHAR(500)"),
        ("vendas", "numero_venda", "ALTER TABLE vendas ADD COLUMN numero_venda INTEGER"),
        ("vendas", "motivo_cancelamento", "ALTER TABLE vendas ADD COLUMN motivo_cancelamento VARCHAR(500)"),
    ]
    with engine.connect() as conn:
        for tabela, coluna, sql in migracoes:
            resultado = conn.execute(text(f"PRAGMA table_info({tabela})"))
            colunas = [row[1] for row in resultado]
            if coluna not in colunas:
                conn.execute(text(sql))
                conn.commit()
                logger.info("Migração aplicada: %s.%s", tabela, coluna)

        # Índice único para numero_venda (SQLite não aceita UNIQUE em ALTER TABLE ADD COLUMN)
        conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uix_vendas_numero_venda ON vendas (numero_venda) "
            "WHERE numero_venda IS NOT NULL"
        ))
        conn.commit()

        # Cria tabela configuracoes_vendas se não existir
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS configuracoes_vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa_id INTEGER NOT NULL UNIQUE REFERENCES empresas(id) ON DELETE CASCADE,
                permitir_desconto BOOLEAN NOT NULL DEFAULT 1,
                desconto_maximo_percent INTEGER NOT NULL DEFAULT 30,
                exigir_cliente_identificado BOOLEAN NOT NULL DEFAULT 0,
                valor_minimo_venda INTEGER NOT NULL DEFAULT 0,
                permitir_parcelamento BOOLEAN NOT NULL DEFAULT 1,
                parcelas_maximas INTEGER NOT NULL DEFAULT 12,
                data_atualizacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
        logger.info("Tabela configuracoes_vendas verificada/inicializada")

        # Cria tabela configuracoes_seguranca se não existir
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS configuracoes_seguranca (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa_id INTEGER NOT NULL UNIQUE REFERENCES empresas(id) ON DELETE CASCADE,
                pin_gerente VARCHAR(255),
                requer_pin_acessar_config_sensivel BOOLEAN NOT NULL DEFAULT 0,
                requer_pin_cancelar_venda BOOLEAN NOT NULL DEFAULT 0,
                requer_pin_reabrir_venda BOOLEAN NOT NULL DEFAULT 0,
                requer_pin_desconto_venda BOOLEAN NOT NULL DEFAULT 0,
                requer_pin_alterar_preco_venda BOOLEAN NOT NULL DEFAULT 0,
                requer_pin_cancelar_os BOOLEAN NOT NULL DEFAULT 0,
                requer_pin_reabrir_os BOOLEAN NOT NULL DEFAULT 0,
                requer_pin_desconto_os BOOLEAN NOT NULL DEFAULT 0,
                data_atualizacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
        logger.info("Tabela configuracoes_seguranca verificada/inicializada")

        # Cria tabela contador_venda se não existir e inicializa com o registro único
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS contador_venda (
                id INTEGER PRIMARY KEY,
                proximo_numero INTEGER NOT NULL DEFAULT 1
            )
        """))
        resultado = conn.execute(text("SELECT COUNT(*) FROM contador_venda"))
        if resultado.scalar() == 0:
            conn.execute(text("INSERT INTO contador_venda (id, proximo_numero) VALUES (1, 1)"))
        conn.commit()
        logger.info("Tabela contador_venda verificada/inicializada")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerenciador de ciclo de vida do FastAPI.
    Inicia tarefas em segundo plano ao iniciar e cancela ao encerrar.
    """
    _aplicar_migracoes()
    logger.info("Iniciando tarefa de limpeza automatica temporal...")
    tarefa = asyncio.create_task(_loop_limpeza_temporal())

    yield

    logger.info("Encerrando tarefa de limpeza automatica temporal...")
    tarefa.cancel()
    try:
        await tarefa
    except asyncio.CancelledError:
        pass
