# BigPDV Harness Engineering

Este diretório contém configurações e diretrizes para otimizar o desempenho de modelos de IA (como Claude) ao trabalhar com o codebase do BigPDV.

## Visão Geral do Sistema

**BigPDV** é um sistema ERP/PDV de desktop construído com:
- **Frontend**: Vue 3 + Tauri (port 1420)
- **Backend**: FastAPI Python (port 8000 dev, 8080-8083 produção)
- **Banco de Dados**: SQLAlchemy ORM com SQLite/PostgreSQL
- **Linguagem do Código**: Português

### Arquitetura em Camadas

```
┌─────────────────────────────────────────────────────┐
│  Frontend (Vue 3 + Tauri)                           │
│  - Componentes: shared/modules/                     │
│  - Estado: Pinia stores + TanStack Query            │
│  - Validação: VeeValidate + Zod                     │
│  - Comunicação: Axios → http://localhost:8000/api/v1│
└─────────────────────────────────────────────────────┘
                      ↓ HTTP REST
┌─────────────────────────────────────────────────────┐
│  Backend (FastAPI)                                  │
│  - Endpoints: api/v1/endpoints/                     │
│  - Serviços: services/ (lógica de negócio)          │
│  - CRUD: db/crud/ (acesso a dados)                  │
│  - Modelos: db/models/ (ORM SQLAlchemy)             │
│  - Schemas: schemas/ (validação Pydantic)           │
└─────────────────────────────────────────────────────┘
                      ↓ SQLAlchemy
┌─────────────────────────────────────────────────────┐
│  Database (SQLite dev / PostgreSQL prod)            │
│  - Migrations: alembic/                             │
│  - Transações: gerenciadas no endpoint level        │
└─────────────────────────────────────────────────────┘
```

## Estrutura de Diretórios Principais

### Frontend
```
frontend/src/
├── modules/              # Features auto-contidas
│   ├── auth/            # Login/autenticação
│   ├── home/            # Dashboard
│   ├── mainLayout/       # Shell principal
│   ├── order-service/   # Ordens de serviço
│   ├── employees/       # Funcionários
│   └── ...
├── shared/              # Código compartilhado
│   ├── components/ui/   # BaseButton, BaseInput, etc.
│   ├── stores/          # Pinia stores globais
│   ├── composables/     # Hooks reutilizáveis
│   ├── services/        # Chamadas API
│   └── utils/
├── api/
│   └── axios.ts        # Instância axios com interceptors
└── router/
    └── index.ts        # Auto-load de routes.ts dos módulos
```

### Backend
```
backend-fastapi/app/
├── api/v1/
│   ├── api.py          # Agregador de routers
│   └── endpoints/      # 28+ módulos (usuario.py, venda.py, etc.)
├── services/           # Lógica de negócio
│   ├── fiscal/         # Motor de cálculo de impostos
│   ├── estoque/        # Gestão de inventário
│   └── *.py            # Serviços por recurso
├── db/
│   ├── models/         # ORM SQLAlchemy
│   ├── crud/           # Operações de banco
│   ├── session.py      # Engine e SessionLocal
│   └── base.py         # Declarative Base
├── schemas/            # Validação Pydantic (input/output)
├── core/
│   ├── config.py       # Configurações via Pydantic Settings
│   ├── security.py     # Hash, JWT
│   ├── depends.py      # Middleware auth, _handle_db_transaction
│   └── enum.py         # Enums (VendaStatus, etc.)
└── helpers/
    └── exceptions.py   # Exceções customizadas
```

## Compilação e Execução

### Frontend

```bash
cd frontend/

# Desenvolvimento (Vite puro, backend separado)
npm run dev                 # http://localhost:5173

# Com Tauri (conecta ao backend em 8000)
npm run tauri dev          # Janela desktop

# Build
npm run build              # Vite + check:sidecar
npm run build:sidecar      # PyArmor + PyInstaller

# Outros
npm run lint               # ESLint
npm run format             # Prettier
npm run storybook          # Port 6006
```

### Backend

```bash
cd backend-fastapi/

# Ativar venv
source .venv/bin/activate  # Linux/Mac
.\.venv\Scripts\activate   # Windows

# Desenvolvimento (hotreload na 8000)
fastapi dev app/main.py    # http://localhost:8000

# Com Tauri (sem hotreload)
fastapi run app/main.py --port 8080

# Testes
pytest test/

# Migrations
alembic upgrade head
alembic downgrade -1
```

### Portas

| Acesso | Backend esperado | Origem |
|--------|-----------------|--------|
| Navegador `localhost:1420` | `8000` | fallback em `api/backendUrl.ts` |
| `npm run tauri dev` | `8000` | hardcoded em `src-tauri/src/network/config.rs` |
| App instalado | `8080-8083` | `system-config.json` do sidecar |

**Dev usa 8000; produção usa 8080-8083** (faixas separadas para não colidir quando a mesma máquina é servidor e dev).

## Padrões Arquiteturais Críticos

### Backend: Fluxo de Requisição

```
Request HTTP
  ↓
[Endpoint] (api/v1/endpoints/)
  ├ Valida schema Pydantic
  ├ Injeta dependências (DB, auth)
  └ Chama _handle_db_transaction
    ↓
[Service] (services/)
  ├ Aplica regras de negócio
  ├ Valida invariantes
  └ Chama CRUD
    ↓
[CRUD] (db/crud/)
  ├ Executa SQLAlchemy queries
  ├ db.flush() (não commit)
  └ Retorna model
    ↓
[Model] (db/models/)
  └ ORM SQLAlchemy (table definition)
    ↓
_handle_db_transaction commits/rollback
  ↓
Response 200/201/400/409...
```

### Frontend: Fluxo de Dados

```
Vue Component
  ↓
useForm() + VeeValidate
  ├ Validação Zod
  └ Field binding
    ↓
onSubmit → Mutation TanStack Query
  ├ Chamada Axios
  ├ Integração toast (onSuccess/onError)
  └ Invalidate queries (refresh)
    ↓
Response → Pinia store atualizado
  ↓
Vue reactivity → UI renderizada
```

## Convenções

### Linguagem do Código
- **Português**: variáveis, funções, comentários, campos DB, textos UI
- **Exceção**: Código externo (bibliotecas), IDs técnicos

### Nomes de Arquivos e Funções

**Backend**
| Camada | Padrão | Exemplo |
|--------|--------|---------|
| Endpoints | `{recurso_plural}.py` | `usuarios.py`, `vendas.py` |
| Services | `{recurso_singular}.py` | `usuario.py`, `venda.py` |
| CRUD | `{recurso_singular}.py` | `usuario.py`, `venda.py` |
| Models | `{recurso_singular}.py` | `usuario.py`, `venda.py` |
| Schemas | `{recurso_singular}.py` | `usuario.py`, `vendas.py` |

**Frontend**
| Tipo | Padrão | Exemplo |
|------|--------|---------|
| Componentes | `PascalCase.vue` | `UserForm.vue`, `BaseButton.vue` |
| Composables | `use*.ts` | `useForm.ts`, `useUser.ts` |
| Stores | `*.store.ts` | `auth.store.ts`, `user.store.ts` |
| Serviços | `*.service.ts` | `user.service.ts`, `produto.service.ts` |
| Tipos | `*.types.ts` | `usuario.types.ts`, `venda.types.ts` |
| Schemas | `*.schema.ts` | `usuario.schema.ts` |

### Valores Monetários
- **Backend**: armazena em **centavos** (inteiros)
- **Frontend**: trabalha em **reais** (floats)
- **Conversão**:
  - Populate: `valor / 100`
  - Save: `Math.round(valor * 100)`

## Diretórios Importantes para Agentes de IA

### Backend
- **Camada de Endpoints**: `backend-fastapi/app/api/v1/endpoints/` (HTTP contracts)
- **Camada de Services**: `backend-fastapi/app/services/` (lógica de negócio)
- **Camada CRUD**: `backend-fastapi/app/db/crud/` (acesso a dados)
- **Camada de Modelos**: `backend-fastapi/app/db/models/` (ORM)
- **Schemas Pydantic**: `backend-fastapi/app/schemas/` (validação)
- **Motor Fiscal**: `backend-fastapi/app/services/fiscal/tax_engine/` (cálculo de impostos)

### Frontend
- **Módulos**: `frontend/src/modules/{feature}/` (features auto-contidas)
- **Componentes Compartilhados**: `frontend/src/shared/components/ui/`
- **Composables Globais**: `frontend/src/shared/composables/`
- **Serviços API**: `frontend/src/shared/services/`
- **Stores Pinia**: `frontend/src/shared/stores/`
- **Tipos Compartilhados**: `frontend/src/shared/types/`

## 📚 Documentação para Agentes de IA

**Leia nesta ordem:**

1. **[AGENT.md](./AGENT.md)** — Guia completo para agentes IA (harness engineering)
   - Stack técnico, desenvolvimento, troubleshooting
   - Padrões de código (Zod + VeeValidate, valores monetários)
   - Checklist de code review
   - Módulos especiais (Fiscal, Order Service)

2. **[Regras de Arquitetura Backend](./rules/backend-layer-hierarchy.md)** — Hierarquia de camadas
   - Endpoints → Services → CRUD → Models
   - Import patterns e dependências
   - Transações e fluxo de erro

3. **[Regras de Arquitetura Frontend](./rules/frontend-module-architecture.md)** — Módulos auto-contidos
   - Estrutura modular
   - Composables, Pinia stores, TanStack Query
   - Provide/inject para contexto
   - Valores monetários (centavos ↔ reais)

4. **[CLAUDE.md](../CLAUDE.md)** — Instruções do projeto (setup, deployment)
   - Desenvolvimento local (portas, comandos)
   - Build do sidecar (PyArmor + PyInstaller)
   - Banco de dados e migrations
   - Papel da máquina (servidor × terminal)

5. **[Memory](../memory/MEMORY.md)** — Memória de sessões (padrões confirmados)
   - Padrões de form management (VeeValidate + Zod)
   - Módulo Fiscal (tax engine, refatoração)
   - Módulo Order Service (OS - ordens de serviço)
   - Regras transversais (timezone, create_all, conexão local)

**Para humanos:**
- Este [README.md](./README.md) — Visão geral do sistema

## Stack Técnico

### Frontend
- Vue 3 (Options + Composition API)
- Tauri 2 (desktop shell)
- TanStack Query (server state)
- Pinia (client state)
- VeeValidate + Zod (validação de formulários)
- Axios (HTTP client)

### Backend
- FastAPI 0.100+
- SQLAlchemy 2.0+ (ORM moderno)
- Pydantic v2 (validação)
- Alembic (migrations)
- pytest (testes)
- PyArmor (ofuscação em prod)
- PyInstaller (empacotamento)

### Deploy
- Tauri + PyInstaller → `.exe` (Windows) / `.dmg` (macOS) / `.AppImage` (Linux)
- Sidecar backend: `erp-api-<target-triple>.exe`
- Banco: `%LOCALAPPDATA%\StartBigERP\data\start_big.db`
- Config: `%APPDATA%\br.com.startbig.erp\StartBigERP\system-config.json`

---

## 🤖 Como Agentes de IA Devem Usar Este Harness

### Antes de Qualquer Mudança de Código

1. **Consulte a documentação em ordem:**
   - `AGENT.md` → regras arquiteturais
   - `rules/architecture-communication.md` → contrato backend/frontend
   - `CLAUDE.md` → setup e convenções do projeto
   - `memory/MEMORY.md` → padrões confirmados

2. **Valide contra as regras:**
   - Seu código segue os padrões em `rules/`?
   - Variáveis/funções em Português?
   - Schemas Zod + Pydantic sincronizados?
   - Valores monetários em centavos (backend) / reais (frontend)?

3. **Antes de sugerir uma solução:**
   - Leia o arquivo/função existente (não interprète de descrições)
   - Entenda a arquitetura atual
   - Evite refatorações não solicitadas
   - Mantenha simplicidade (não over-engineer)

### Troubleshooting Rápido

| Problema | Solução |
|----------|---------|
| Login quebrado | Verificar porta: dev=8000, tauri=8000, app=8080-8083 |
| Banco vazio | `create_all()` roda ANTES das migrations |
| Sidecar desatualizado | `npm run build:sidecar` (PyArmor + PyInstaller) |
| Fuso horário errado | Conversão única em `app/core/tempo.py` (UTC→local) |
| Enum não sincroniza | Mudança backend = PR no frontend (verificar em code review) |

### Comandos Importantes

```bash
# Frontend
cd frontend
npm run dev              # Vite (backend separado)
npm run tauria dev      # Tauri window (backend na 8000)
npm run lint            # ESLint
npx vue-tsc --noEmit    # Type check

# Backend
cd backend-fastapi
fastapi dev app/main.py --port 8000  # Dev com hotreload
pytest test/ -v                       # Testes

# Build
npm run build:sidecar   # PyArmor + PyInstaller
npm run build           # Tauri build final
```

### Checklist de Commit

Antes de enviar código, valide:

- [ ] Leu `AGENT.md` e `rules/architecture-communication.md`
- [ ] Código em Português (variáveis, funções, comentários)
- [ ] Schemas Zod + Pydantic sincronizados (se validação)
- [ ] Valores monetários: centavos (backend) / reais (frontend)
- [ ] Backend valida tudo (não confia no frontend)
- [ ] Testes: unitários (backend) ou integração (frontend)
- [ ] Sem console.log (usar logger)
- [ ] Mensagens de erro amigáveis + error_code
- [ ] HTTP response: `{ "status": "success"/"error", "data": ... }`
- [ ] Commit message: `<tipo>(<escopo>): <descrição>`

---

**Última atualização**: 16/09/2026
**Ambiente de Harness**: StartBig ERP (Tauri + Vue 3 + FastAPI)
