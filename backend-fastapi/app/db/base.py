# ---------------------------------------------------------------------------
# ARQUIVO: base.py
# DESCRIÇÃO: Define a classe base declarativa para os modelos do SQLAlchemy.
#            Todos os modelos ORM (que representam tabelas do banco de dados)
#            deverão herdar desta classe 'Base'.
# ---------------------------------------------------------------------------

# Importa a função que cria a classe base.
import importlib
import pkgutil

from sqlalchemy.orm import declarative_base

# Cria a instância da Base. O SQLAlchemy usará esta classe para mapear
# todos os modelos que herdarem dela para as tabelas do banco de dados.
# É através dela que o Alembic, por exemplo, consegue encontrar seus modelos
# para gerar as migrações.
Base = declarative_base()

# Importa automaticamente todos os módulos de app/db/models, garantindo que
# fiquem registrados em Base.metadata mesmo que nenhum outro arquivo os
# importe manualmente — evita que uma tabela nova fique de fora do
# Base.metadata.create_all() por esquecimento.
import app.db.models as _models_package

for _module_info in pkgutil.iter_modules(_models_package.__path__, prefix="app.db.models."):
    importlib.import_module(_module_info.name)