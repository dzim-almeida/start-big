"""
Migration: adiciona coluna situacao_equipamento na tabela ordens_servico.

Rode com:
    python migrate_situacao_equipamento.py
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "bigpdv.db")


def run():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(ordens_servico)")
    colunas = [row[1] for row in cur.fetchall()]

    if "situacao_equipamento" in colunas:
        print("Coluna 'situacao_equipamento' já existe. Nada a fazer.")
    else:
        cur.execute(
            "ALTER TABLE ordens_servico ADD COLUMN situacao_equipamento VARCHAR(20) DEFAULT NULL"
        )
        conn.commit()
        print("Coluna 'situacao_equipamento' adicionada com sucesso.")

    conn.close()


if __name__ == "__main__":
    run()
