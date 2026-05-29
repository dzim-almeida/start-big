# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BigPDV is a Point of Sale (PDV) system built as a desktop application using Tauri with a Vue 3 frontend and FastAPI Python backend.

## Development Commands

### Frontend (from `frontend/` directory)
```bash
npm run dev          # Start both Vite dev server and FastAPI backend concurrently
npm run build        # Type-check and build for production
npm run lint         # ESLint with auto-fix
npm run format       # Prettier formatting
npm run storybook    # Storybook component development (port 6006)
npm run tauri        # Tauri CLI commands
```

### Backend (from `backend-fastapi/` directory)
```bash
# Activate virtual environment first
.\.venv\Scripts\activate      # Windows
source .venv/bin/activate     # Linux/Mac

fastapi dev app/main.py       # Development server with hot-reload
pytest test/                  # Run tests
```

### Environment
- Frontend runs on port 1420 (Vite/Tauri)
- Backend API runs on port 8000
- API base URL: `http://localhost:8000/api/v1`

## Architecture

### Frontend (`frontend/src/`)

**Module-based architecture** where each feature is a self-contained module:

```
modules/
├── auth/          # Login flow
├── home/          # Dashboard
├── mainLayout/    # Main app shell (sidebar, header, layout)
├── onboarding/    # Initial company setup wizard
└── employees/     # Employee management
```

Each module contains:
- `views/` - Page components
- `components/` - Module-specific components
- `routes.ts` - Auto-loaded by `router/index.ts` via glob import
- `services/` - API calls
- `composables/` - Vue composables
- `types/` - TypeScript types
- `schemas/` - Zod validation schemas
- `store/` - Pinia stores (module-specific)

**Shared code** (`shared/`):
- `components/ui/` - Reusable UI components (BaseButton, BaseInput, BaseSelect, etc.)
- `stores/` - Global stores (auth.store.ts)
- `composables/` - Global composables (useUser, useToast, useAppNavigation)
- `services/` - Global services

**Key patterns:**
- Routes are auto-discovered from `@/modules/**/routes.ts`
- TanStack Query for server state management
- Pinia for client state
- VeeValidate + Zod for form validation
- Axios instance in `api/axios.ts` with auth interceptors

### Backend (`backend-fastapi/app/`)

**Layered architecture:**

```
app/
├── api/v1/
│   ├── api.py         # Router aggregation
│   └── endpoints/     # Route handlers
├── core/
│   ├── config.py      # Pydantic settings from .env
│   ├── security.py    # Password hashing (bcrypt), JWT tokens
│   └── depends.py     # FastAPI dependencies
├── db/
│   ├── session.py     # SQLAlchemy engine and session
│   ├── base.py        # Base model class
│   ├── models/        # SQLAlchemy ORM models
│   └── crud/          # Database operations
├── schemas/           # Pydantic request/response schemas
└── services/          # Business logic
```

**Key entities:** Usuario, Funcionario, Cliente, Empresa, Produto, Servico, Fornecedor, Cargo, Endereco, Estoque

**Auth flow:** JWT tokens with blocklist for logout. Tokens stored as HTTP-only cookies.

### Tauri (`frontend/src-tauri/`)

Rust-based desktop shell using:
- `tauri-plugin-stronghold` - Secure storage
- `tauri-plugin-keyring` - System keychain integration
- `rust-argon2` - Password hashing

## API Endpoints

All endpoints under `/api/v1/`:
- `/auth` - Login/logout
- `/usuarios` - User management
- `/empresas` - Companies
- `/funcionarios` - Employees
- `/cargos` - Job positions
- `/clientes` - Customers
- `/fornecedores` - Suppliers
- `/produtos` - Products
- `/servicos` - Services
- `/enderecos` - Addresses

## Language

The codebase uses Portuguese for:
- Variable and function names
- Comments and documentation
- Database fields and API responses
- UI text

Maintain this convention when adding new code.
