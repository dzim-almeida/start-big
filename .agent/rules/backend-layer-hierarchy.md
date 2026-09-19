# Regras: Hierarquia de Camadas do Backend

## Princípio Fundamental

**Import flow é estritamente UNI-DIRECIONAL** (top → bottom):

```
Endpoints → Services → CRUD → Models
   ↑         ↑         ↑
   │         │         └─→ [Ninguém importa modelos para lógica]
   │         └─────────────→ Services importam CRUD + Services cruzados
   └─────────────────────→ Endpoints importam Services + Schemas + Core
```

## Regra 1: Endpoints (Controllers)

**Local**: `backend-fastapi/app/api/v1/endpoints/`

**Responsabilidades**:
- Validar contrato HTTP (status code, response model)
- Injetar dependências (DB, auth, validações)
- Delegar lógica para services

**Pode importar de**:
- ✅ `app.services.*` — Chamadas de serviço
- ✅ `app.schemas.*` — Validação Pydantic (request/response)
- ✅ `app.core.depends` — Middleware (get_db, get_current_user, _handle_db_transaction)
- ✅ `app.core.security` — Password hashing, JWT
- ✅ `fastapi` — Router, Depends, status, HTTPException

**NÃO pode importar de**:
- ❌ `app.db.models` — Direto (use schemas para tipos)
- ❌ `app.db.crud` — Direto (vai via services)
- ❌ Outros endpoints (circular)

**Padrão**: Usar `_handle_db_transaction` para wrapping automático

```python
# ✅ CORRETO
from app.services import usuario as usuario_service
from app.schemas.usuario import UsuarioCreate, UsuarioRead

@router.post("/", response_model=UsuarioRead, status_code=201)
def create(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    return _handle_db_transaction(
        db,
        usuario_service.create_usuario,
        usuario
    )

# ❌ ERRADO
from app.db.crud import usuario as usuario_crud  # Não! Vai via service
from app.db.models.usuario import Usuario  # Não! Use schema
```

---

## Regra 2: Services (Business Logic)

**Local**: `backend-fastapi/app/services/`

**Responsabilidades**:
- Aplicar regras de negócio
- Validar invariantes
- Orquestrar múltiplas operações CRUD
- Chegar a outras services (horizontalmente)

**Pode importar de**:
- ✅ `app.db.crud.*` — CRUD operations (como alias)
- ✅ `app.db.models.*` — Para type hints
- ✅ `app.schemas.*` — Para type hints de input/output
- ✅ `app.core.enum` — Enums de status
- ✅ `app.core.security` — Hash, JWT
- ✅ `app.helpers.exceptions` — Exceções customizadas
- ✅ `app.services.*` — Outros services (cross-service calls)
- ✅ Bibliotecas stdlib e externas

**NÃO pode importar de**:
- ❌ `app.api.*` — Endpoints (upward!)
- ❌ FastAPI direto (é detalhe de transporte)

**Padrão**: Não gerenciar transações (deixa pra endpoint via `_handle_db_transaction`)

```python
# ✅ CORRETO
from app.db.crud import usuario as usuario_crud
from app.services.cliente import cliente_exists
from app.core.enum import VendaStatus

def create_sale(db: Session, sale_data: VendaCreate):
    # Validar: cliente existe?
    if not cliente_exists(db, sale_data.cliente_id):
        raise BadRequestException(...)
    # CRUD
    return venda_crud.create_sale(db, sale_obj)

# ❌ ERRADO
from app.api.v1.endpoints import venda  # Upward import!
db.commit()  # Não! Commit é no endpoint
```

---

## Regra 3: CRUD (Data Access)

**Local**: `backend-fastapi/app/db/crud/`

**Responsabilidades**:
- Executar queries SQLAlchemy
- Não aplicar lógica de negócio
- Usar `flush()`, nunca `commit()`

**Pode importar de**:
- ✅ `app.db.models.*` — Para type hints e queries
- ✅ `sqlalchemy` — Queries, joins, filters
- ✅ `sqlalchemy.orm` — Session, joinedload, etc.
- ✅ Bibliotecas stdlib

**NÃO pode importar de**:
- ❌ `app.services.*` — Circular! (services chamam CRUD)
- ❌ `app.api.*`
- ❌ `app.schemas.*` — Use models direto

**Padrão**: Use `select()` moderno (SQLAlchemy 2.0)

```python
# ✅ CORRETO
from sqlalchemy import select
from app.db.models.usuario import Usuario as UsuarioModel

def get_usuario_by_email(db: Session, email: str):
    stmt = select(UsuarioModel).where(UsuarioModel.email == email)
    return db.scalars(stmt).first()

def create_usuario(db: Session, usuario_obj: UsuarioModel):
    db.add(usuario_obj)
    db.flush()  # Não commit!
    db.refresh(usuario_obj)  # Load generated ID
    return usuario_obj

# ❌ ERRADO
from app.services import usuario_service  # Circular!
db.commit()  # Commit está no endpoint
```

---

## Regra 4: Models (ORM)

**Local**: `backend-fastapi/app/db/models/`

**Responsabilidades**:
- Definir estrutura de tabelas
- Declarar relacionamentos
- Type hints com `Mapped[Type]`

**Pode importar de**:
- ✅ `sqlalchemy.*` — Colunas, relacionamentos, tipos
- ✅ `app.db.base` — Base declarativo
- ✅ `typing` — TYPE_CHECKING, Optional, etc.

**NÃO pode importar de**:
- ❌ Nada do `app/` — Zero dependências em app!
- ❌ `app.services`
- ❌ `app.schemas`

**Padrão**: Use TYPE_CHECKING para evitar imports circulares

```python
# ✅ CORRETO
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base

if TYPE_CHECKING:
    from .empresa import Empresa  # Evita circular em runtime

class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(Integer, ForeignKey("empresas.id"))
    empresa: Mapped["Empresa"] = relationship(back_populates="usuarios")

# ❌ ERRADO
from app.services.usuario import create_usuario  # Importa lógica!
```

---

## Regra 5: Schemas (Pydantic Validation)

**Local**: `backend-fastapi/app/schemas/`

**Responsabilidades**:
- Validar requests (input)
- Serializar responses (output)
- Documentar API via Pydantic

**Pode importar de**:
- ✅ `app.schemas.*` — Schemas nested (referências cruzadas)
- ✅ `pydantic` — BaseModel, Field, ConfigDict
- ✅ `typing` — Optional, List, etc.

**NÃO pode importar de**:
- ❌ `app.services.*`
- ❌ `app.db.crud.*`
- ❌ `app.api.*`

**Padrão**: Separar *Base*, *Create*, *Update*, *Read*

```python
# ✅ CORRETO
from pydantic import BaseModel, Field, ConfigDict

class UsuarioBase(BaseModel):
    nome: str = Field(..., max_length=255)
    model_config = ConfigDict(from_attributes=True)

class UsuarioCreate(UsuarioBase):
    senha: str = Field(..., min_length=8)

class UsuarioRead(UsuarioBase):
    id: int
    ativo: bool
    # NÃO inclui senha_hash!

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    ativo: Optional[bool] = None
```

---

## Regra 6: Cross-Service Calls (Horizontal)

Services podem chamar outras services **para orquestração**, MAS deve-se evitar ciclos:

```
usuario_service.create()
  → venda_service.create_related()  ✅ OK
      → usuario_service.validate()  ✅ OK (se não for circular)
          → venda_service.xxx()     ❌ CIRCULAR!
```

**Padrão**: Composição explícita de dependências

```python
# ✅ CORRETO: usuario_service chama venda_service
def create_usuario_with_initial_sale(db: Session, usuario: UsuarioCreate, sale_data):
    usuario_obj = create_usuario(db, usuario)
    from app.services.venda import create_sale
    create_sale(db, {**sale_data, "usuario_id": usuario_obj.id})
    return usuario_obj

# ❌ ERRADO: Ciclo venda ↔ usuario
# venda_service.py: from app.services.usuario import xyz
# usuario_service.py: from app.services.venda import xyz
```

---

## Regra 7: Transações

**Quem gerencia?** Apenas `app/core/depends.py` → `_handle_db_transaction`

**Como?**
```python
# ✅ CORRETO: No endpoint
return _handle_db_transaction(
    db,
    usuario_service.create_usuario,
    usuario_create,
    is_master=True
)

# _handle_db_transaction:
# - try: service_func(*args)
# - if OK: db.commit()
# - if error: db.rollback(); re-raise

# ❌ ERRADO: No service
db.commit()  # Não! Deixa pro endpoint
db.rollback()  # Não!
```

---

## Regra 8: Exceções

**Padrão**: Lançar do service, tratar no endpoint

```python
# ✅ CORRETO
# service:
if not cliente_exists(db, cliente_id):
    raise BadRequestException(detail="Cliente não existe")

# endpoint:
# (deixa _handle_db_transaction tratar)
return _handle_db_transaction(db, service.create_venda, venda)
# _handle_db_transaction captura e passa pra FastAPI
```

---

## Resumo Visual

```
┌─────────────────────────────────────────────┐
│ ENDPOINT (HTTP boundary)                    │
│ ├─ Valida com Pydantic schema               │
│ ├─ Chama _handle_db_transaction             │
│ └─ Retorna response (200/400/409)           │
└────────────────┬────────────────────────────┘
                 │ calls (com Session)
┌────────────────▼────────────────────────────┐
│ SERVICE (business logic)                    │
│ ├─ Valida invariantes                       │
│ ├─ Chama CRUD (1 ou N)                      │
│ └─ Lança exceções se erro                   │
└────────────────┬────────────────────────────┘
                 │ calls
┌────────────────▼────────────────────────────┐
│ CRUD (data access)                          │
│ ├─ Executa SQLAlchemy queries               │
│ ├─ db.flush() (não commit)                  │
│ └─ Retorna model ou lista                   │
└────────────────┬────────────────────────────┘
                 │ queries
┌────────────────▼────────────────────────────┐
│ MODEL (SQLAlchemy ORM)                      │
│ ├─ Table definitions                        │
│ └─ Relationships (type hints)                │
└─────────────────────────────────────────────┘
```

---

## Checklist para Revisão de PR

- [ ] Endpoints importam services (não CRUD direto)?
- [ ] Services importam CRUD (como alias)?
- [ ] CRUD não importa services?
- [ ] Modelos sem imports de `app/`?
- [ ] Schemas com `from_attributes=True`?
- [ ] Transações via `_handle_db_transaction`?
- [ ] Não há imports circulares?
- [ ] Exceções lançadas em services, não endpoints?
- [ ] db.flush/refresh em CRUD, não db.commit?

---

**Versão**: 1.0
**Data**: 16/09/2026
