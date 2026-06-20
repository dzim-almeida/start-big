"""
Migration: adiciona novos campos fiscais/cadastrais na tabela empresas.

Campos adicionados:
  - indicador_ie: Indicador de IE para NF-e (1=Contribuinte, 2=Isento, 9=Não contribuinte)
  - natureza_juridica: Natureza jurídica (MEI, ME, EPP, LTDA, SA, EI, SLU)
  - tipo_atividade: Tipo de atividade (COMERCIO, INDUSTRIA, SERVICO, MISTO)
  - cnaes_secundarios: CNAEs secundários separados por vírgula
  - data_abertura: Data de abertura no formato YYYY-MM-DD
  - website: Site da empresa

Rode com:
    python migrate_empresa_novos_campos.py
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "bigpdv.db")

NOVAS_COLUNAS = [
    ("indicador_ie", "VARCHAR(1) DEFAULT NULL"),
    ("natureza_juridica", "VARCHAR(50) DEFAULT NULL"),
    ("tipo_atividade", "VARCHAR(20) DEFAULT NULL"),
    ("cnaes_secundarios", "VARCHAR(500) DEFAULT NULL"),
    ("data_abertura", "VARCHAR(10) DEFAULT NULL"),
    ("website", "VARCHAR(255) DEFAULT NULL"),
]


def run():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(empresas)")
    colunas_existentes = [row[1] for row in cur.fetchall()]

    adicionadas = []
    ignoradas = []

    for nome_coluna, definicao in NOVAS_COLUNAS:
        if nome_coluna in colunas_existentes:
            ignoradas.append(nome_coluna)
        else:
            cur.execute(f"ALTER TABLE empresas ADD COLUMN {nome_coluna} {definicao}")
            adicionadas.append(nome_coluna)

    conn.commit()
    conn.close()

    if adicionadas:
        print(f"Colunas adicionadas com sucesso: {', '.join(adicionadas)}")
    if ignoradas:
        print(f"Colunas já existentes (ignoradas): {', '.join(ignoradas)}")
    if not adicionadas and not ignoradas:
        print("Nenhuma alteração necessária.")


if __name__ == "__main__":
    run()
