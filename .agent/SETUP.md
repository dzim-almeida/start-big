# Setup Inicial — Harness Engineering

**Data de Criação:** 2026-09-16
**Status:** ✅ Concluído

---

## 📦 Arquivos Criados

```
.agent/
├── README.md                              # Este arquivo (visão geral)
├── AGENT.md                               # Guia completo para agentes IA ⭐
├── IMPROVEMENTS.md                        # Análise de melhorias
├── SETUP.md                               # Instruções de setup (você está aqui)
├── rules/
│   └── architecture-communication.md      # Regras rígidas de arquitetura ⭐
├── skills/                                # (estrutura futura para skills customizadas)
└── specs/                                 # (estrutura futura para OpenAPI specs)
```

---

## 🎯 Estrutura e Propósito

### 1. Para Agentes de IA (Modelos de Language)

**Leia nesta ordem:**

#### 🟢 ESSENCIAL — Antes de Qualquer Mudança
1. **[AGENT.md](./AGENT.md)** (20 min)
   - Stack técnico completo
   - Padrões de código (Zod + VeeValidate, monetário, etc.)
   - Troubleshooting conhecido
   - Checklist de code review

2. **[rules/architecture-communication.md](./rules/architecture-communication.md)** (15 min)
   - Padrão de resposta HTTP obrigatório
   - Contrato de dados (tipos base, enums)
   - Endpoints REST e paginação
   - Tratamento de erros
   - Máquina de estados

#### 🟡 CONTEXTO — Antes de Features Complexas
3. **[../CLAUDE.md](../CLAUDE.md)** (entender projeto)
   - Setup dev (portas, comandos)
   - Build sidecar
   - Papel servidor × terminal
   - Incidentes conhecidos

4. **[../memory/MEMORY.md](../memory/MEMORY.md)** (patterns recorrentes)
   - Padrões confirmados
   - Módulo Fiscal
   - Módulo Order Service
   - Regras transversais

### 2. Para Desenvolvedores Humanos

- **[README.md](./README.md)** — Visão geral visual (arquitetura em diagrama)
- **[CLAUDE.md](../CLAUDE.md)** — Setup, deployment, troubleshooting
- **[IMPROVEMENTS.md](./IMPROVEMENTS.md)** — Roadmap de qualidade

### 3. Para Code Review

Use o **checklist em AGENT.md § 9**:
- [ ] Código segue `rules/architecture-communication.md`
- [ ] Português em nomes + comentários
- [ ] Schemas Zod + Pydantic sincronizados
- [ ] Valores monetários: centavos (backend) / reais (frontend)
- [ ] Testes: unitário (backend) ou integração (frontend)
- [ ] Commit message: `<tipo>(<escopo>): <desc>`

---

## 🚀 Como Usar Este Harness

### Fluxo de Desenvolvimento

```
1. Feature Request
   ↓
2. Leia: AGENT.md + rules/architecture-communication.md
   ↓
3. Entenda: Arquitetura existente (nunca interprète de descrições)
   ↓
4. Valide: Seu design atende às regras?
   ├─ Frontend: módulo em modules/ + Zod schema
   ├─ Backend: endpoint + Pydantic schema + service
   └─ API: respeita pattern `{ "status": "success"/"error", "data": ... }`
   ↓
5. Implemente: Código seguindo padrões
   ├─ Português em nomes
   ├─ Sem over-engineering
   └─ Type-safe (TypeScript + Pydantic)
   ↓
6. Teste: Unitário (backend) ou integração (frontend)
   ↓
7. Commit: Mensagem padronizada
   └─ `feat(modulo): breve descricao`
   ↓
8. Code Review: Checklist AGENT.md § 9
```

### Troubleshooting Rápido (em AGENT.md § 7)

| Sintoma | Causa | Solução |
|---------|-------|---------|
| Login não funciona | Porta backend errada | Verificar: dev=8000, tauri=8000, app=8080 |
| Banco vazio | create_all() não rodou | Revisar migrations em create-all-antes-das-migrations.md |
| Sidecar desatualizado | Backend mudou | `npm run build:sidecar` |
| Fuso horário errado | Conversão perdida | Verificar: app/core/tempo.py |

---

## 📚 Documentação por Tema

### Autenticação & Segurança
- JWT em cookies HttpOnly: AGENT.md § 4.1
- Dependência FastAPI: CLAUDE.md
- Refresh token: rules/architecture-communication.md § 4

### Valores Monetários
- Centavos no banco: AGENT.md § 6.2
- Conversão frontend: AGENT.md § 6.2
- Exemplos: IMPROVEMENTS.md § 2

### Validação (Zod + VeeValidate + Pydantic)
- Padrão: AGENT.md § 6.1
- Schemas duplos: rules/architecture-communication.md § 2.2
- Exemplos: IMPROVEMENTS.md § 2

### Módulo Fiscal
- Leitura obrigatória: memory/modulo-fiscal-refatoracao.md
- Resumo: AGENT.md § 5.1

### Módulo Order Service (OS)
- Leitura obrigatória: frontend/src/modules/order-service/ordens/docs/order-service.md
- Resumo: AGENT.md § 5.2

### Sidecar & Deployment
- Build PyArmor + PyInstaller: CLAUDE.md
- Banco preservado: CLAUDE.md
- Portas dev vs prod: CLAUDE.md

---

## ✅ Checklist de Setup

### Para Agentes de IA
- [ ] Ler AGENT.md
- [ ] Ler rules/architecture-communication.md
- [ ] Consultar CLAUDE.md se precisar de contexto histórico
- [ ] Usar checklist de code review (AGENT.md § 9) antes de enviar código

### Para Humanos (Onboarding)
- [ ] Ler README.md (visão geral)
- [ ] Ler CLAUDE.md (setup dev)
- [ ] Fazer `npm run dev` (frontend) + `fastapi dev` (backend)
- [ ] Testar login em localhost:1420
- [ ] Ler memory/MEMORY.md (padrões do projeto)

### Para Mantedores
- [ ] Revisar IMPROVEMENTS.md (roadmap)
- [ ] Designar Sprint 1: OpenAPI specs + pre-commit hooks
- [ ] Adicionar ADRs em decisions/ conforme decisões
- [ ] Atualizar AGENT.md quando mudanças arquiteturais

---

## 🔄 Próximas Melhorias (IMPROVEMENTS.md)

### Sprint 1 (Semana 1) — Alta Prioridade
- [ ] OpenAPI specs (FastAPI auto-docs)
- [ ] Pre-commit hooks (validação de arquitetura)

### Sprint 2 (Semana 2)
- [ ] TypeScript type generation (Zod → TS)
- [ ] Exemplos em schemas Pydantic

### Sprint 3 (Semana 3)
- [ ] Fixtures e factories (testes)
- [ ] ADRs (decisões arquiteturais)

### Backlog
- [ ] Diagramas Mermaid
- [ ] CI/CD GitHub Actions
- [ ] MkDocs portal

---

## 📝 Convenções Consolidadas

### Linguagem de Código
- **Português**: variáveis, funções, comentários, nomes DB
- **Exceção**: Código externo (libs), IDs técnicos

### Padrões Backend
- Endpoint → Service → CRUD → Model
- Validação em Pydantic (schema)
- Serviços sem DB direto (injeção de dep)

### Padrões Frontend
- Módulos auto-contidos em `modules/`
- VeeValidate + Zod para validação
- TanStack Query + Pinia para estado
- UI components com prefixo `Base`

### API HTTP
```json
{
  "status": "success",
  "data": <T>
}
```

```json
{
  "status": "error",
  "message": "descrição amigável",
  "error_code": "UPPER_SNAKE_CASE",
  "details": {}
}
```

---

## 🤝 Feedback & Melhorias

Se encontrar:
- **Ambiguidade nas regras** → atualizar `rules/`
- **Padrão recorrente** → documentar em `memory/MEMORY.md`
- **Incidente conhecido** → descrever em `AGENT.md § 7`
- **Decisão arquitetural** → criar ADR em `decisions/`

---

**Status:** ✅ Setup completo e operacional
**Data:** 2026-09-16
**Próxima revisão:** Após Sprint 1 (IMPROVEMENTS.md)
