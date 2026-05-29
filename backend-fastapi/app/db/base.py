# ---------------------------------------------------------------------------
# ARQUIVO: base.py
# DESCRIÇÃO: Define a classe base declarativa para os modelos do SQLAlchemy.
#            Todos os modelos ORM (que representam tabelas do banco de dados)
#            deverão herdar desta classe 'Base'.
# ---------------------------------------------------------------------------

# Importa a função que cria a classe base.
from sqlalchemy.orm import declarative_base

# Cria a instância da Base. O SQLAlchemy usará esta classe para mapear
# todos os modelos que herdarem dela para as tabelas do banco de dados.
# É através dela que o Alembic, por exemplo, consegue encontrar seus modelos
# para gerar as migrações.
Base = declarative_base()