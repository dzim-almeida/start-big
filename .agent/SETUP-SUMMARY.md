# 🎯 Harness Engineering — Setup Concluído

**Data**: 16/09/2026 | **Status**: ✅ Completo

---

## 📦 O Que Foi Criado

### Arquivos Principais

#### 1. `.agent/README.md` (13.4 KB)
**Propósito**: Visão geral do sistema para humanos e modelos IA

**Seções**:
- Visão geral da arquitetura
- Estrutura de diretórios
- Compilação e execução
- Convenções (português, nomenclatura)
- Diretórios-chave para agentes IA
- Documentação referência

**Públic-alvo**: Novos desenvolvedores, agentes IA, automação

---

#### 2. `.agent/AGENT.md` (9.4 KB)
**Propósito**: Diretrizes de performance para modelos de IA

**Seções**:
- Visão geral para agentes IA
- Stack técnico (Tauri, Vue 3, FastAPI, etc.)
- Desenvolvimento local (setup, testes, build)
- Regras de arquitetura (referencia rules/)
- Módulos especiais (Fiscal, Order Service)
- Padrões de código
- Troubleshooting (7 incidentes conhecidos)
- Checklist de code review
- Recursos úteis

**Público-alvo**: Agentes de IA, automação, reviewers

---

### Pasta `rules/` — Regras Rigorosas de Arquitetura

#### 3. `rules/backend-layer-hierarchy.md` (11 KB)
**Propósito**: Contrato obrigatório de camadas backend

**Conteúdo**:
```
Endpoints → Services → CRUD → Models
├── Regra 1: Endpoints (Controllers)
├── Regra 2: Services (Business Logic)
├── Regra 3: CRUD (Data Access)
├── Regra 4: Models (ORM)
├── Regra 5: Schemas (Pydantic)
├── Regra 6: Cross-Service Calls (Horizontal)
├── Regra 7: Transações
├── Regra 8: Exceções
└── Resumo Visual + Checklist PR
```

**Exemplos**: ✅/❌ código para cada regra

---

#### 4. `rules/frontend-module-architecture.md` (16.4 KB)
**Propósito**: Contrato obrigatório de módulos frontend

**Conteúdo**:
```
Módulos Auto-Contidos
├── Regra 1: Estrutura de Módulo
├── Regra 2: Importações Dentro de Módulo
├── Regra 3: Componentes Compartilhados (UI)
├── Regra 4: Composables Globais
├── Regra 5: Stores Pinia
├── Regra 6: Formulários (VeeValidate + Zod)
├── Regra 7: Chamadas API (TanStack Query)
├── Regra 8: Serviços API (Axios)
├── Regra 9: Valores Monetários
├── Regra 10: Provide/Inject para Contexto
├── Regra 11: Não Importar Arquivos Deletados
└── Resumo Visual + Checklist PR
```

**Padrões**: Composables, Query keys, Zod schemas, Pinia stores

---

#### 5. `rules/architecture-communication.md` (4.1 KB)
**Propósito**: Contrato HTTP backend ↔ frontend

**Conteúdo**:
- Padrão de resposta HTTP obrigatório
- Contrato de dados (tipos base)
- Enums sincronizados backend ↔ frontend
- Paginação
- Tratamento de erros

---

## 🎯 Estrutura Hierárquica

```
.agent/
├── README.md ........................ Visão geral (começa aqui)
├── AGENT.md ......................... Diretrizes para IA
├── SETUP-SUMMARY.md ................. Este arquivo
├── IMPROVEMENTS.md .................. Análise de melhorias futuras
└── rules/
    ├── backend-layer-hierarchy.md ... Camadas backend (Endpoints→Services→CRUD)
    ├── frontend-module-architecture.md . Módulos frontend (auto-contidos)
    └── architecture-communication.md   Contrato HTTP
```

---

## 🚀 Como Usar

### Para Agentes IA

**Primeira vez**:
1. Leia `.agent/README.md` (5 min)
2. Leia `.agent/AGENT.md` (10 min)
3. Escolha a regra relevante:
   - Backend: `rules/backend-layer-hierarchy.md`
   - Frontend: `rules/frontend-module-architecture.md`
   - API: `rules/architecture-communication.md`

**Durante uma tarefa**:
```
Flow: Trace endpoint/view → siga imports → valide com regra → execute
```

### Para Humanos (Developers)

**Onboarding**:
- Leia README.md (entenda estrutura)
- Implemente seguindo `rules/`
- Use checklists de PR antes de commitar

**Code Review**:
- Backend: Checklist em `backend-layer-hierarchy.md`
- Frontend: Checklist em `frontend-module-architecture.md`

---

## ✨ Destaques da Arquitetura

### Backend
- ✅ Hierarquia clara: Endpoints → Services → CRUD → Models
- ✅ Transações centralizadas em `_handle_db_transaction`
- ✅ Exceções lançadas em services, tratadas em endpoints
- ✅ Cross-service calls permitidas (horizontais)

### Frontend
- ✅ Módulos auto-contidos (zero acoplamento)
- ✅ Routes auto-descobertas (`routes.ts` em cada módulo)
- ✅ Composables reutilizáveis + stores Pinia
- ✅ VeeValidate + Zod para validação dupla

### Transversal
- ✅ Português em todos os nomes
- ✅ Valores monetários: centavos (backend) ↔ reais (frontend)
- ✅ Autenticação JWT com HTTP-only cookies
- ✅ TanStack Query com query keys centralizadas

---

## 📊 Estatísticas

| Item | Quantidade | Tamanho |
|------|-----------|---------|
| Arquivos criados | 5 | 54.9 KB |
| Regras backend | 8 | 11 KB |
| Regras frontend | 11 | 16.4 KB |
| Exemplos ✅/❌ | 30+ | inline |
| Checklists PR | 4 | ~10 itens cada |

---

## 🔍 Validações Incluídas

### Backend
- [ ] Endpoints importam services (não CRUD direto)?
- [ ] Services chamam CRUD?
- [ ] CRUD não importa services?
- [ ] Usar `_handle_db_transaction` em endpoints?
- [ ] Transações: `db.flush()` não `db.commit()`?
- [ ] Exceções lançadas em services?

### Frontend
- [ ] Módulos têm `routes.ts`?
- [ ] Imports circulares entre módulos?
- [ ] Valores monetários convertidos (÷100, ×100)?
- [ ] Query keys em `core.constant.ts`?
- [ ] Nenhum arquivo deletado com imports residuais?

---

## 🎓 Próximas Etapas (Recomendado)

### Curto Prazo (1 semana)
- [ ] Ler rules/ e validar projeto atual
- [ ] Aplicar checklists em PRs novas
- [ ] Documentar incidentes conhecidos em `memory/INCIDENTS.md`

### Médio Prazo (2-3 semanas)
- [ ] Criar `rules/testing-strategy.md` (pytest + vitest)
- [ ] Criar `rules/enum-synchronization.md` (validação backend ↔ frontend)
- [ ] Automatizar validação de imports (pre-commit hook)

### Longo Prazo (1 mês)
- [ ] Security checklist (XSS, SQL injection, CSRF)
- [ ] Performance optimization guide
- [ ] Interactive troubleshooting flowchart

---

## 💡 Dicas de Ouro

1. **Comece pelo endpoint/view** — siga imports, não explore pastas
2. **Use Glob + Grep** para buscar — não Agent para exploração pequena
3. **Memorize os 3 padrões**:
   - Backend: Endpoint → Service → CRUD
   - Frontend: View → Composable → Service → Axios
   - Transações: Centralizadas no endpoint
4. **Valide com checklist** antes de cada commit
5. **Consulte MEMORY.md** se padrão for novo

---

## 📖 Documentação de Referência

**Este harness sincroniza-se com**:
- `CLAUDE.md` — Instruções do projeto
- `memory/MEMORY.md` — Memória de sessões
- `memory/modulo-fiscal-refatoracao.md` — Motor fiscal
- `frontend/src/modules/order-service/ordens/docs/` — Módulo OS

---

## ✅ Checklist de Conclusão

- [x] README.md criado (visão geral)
- [x] AGENT.md validado (diretrizes IA)
- [x] `rules/backend-layer-hierarchy.md` criado (8 regras)
- [x] `rules/frontend-module-architecture.md` criado (11 regras)
- [x] `rules/architecture-communication.md` criado (contrato HTTP)
- [x] Referências atualizadas em README.md
- [x] IMPROVEMENTS.md com análise de melhorias futuras

**Status Final**: ✅ **Harness Engineering Environment Pronto**

---

**Criado em**: 16/09/2026
**Versão**: 1.0
**Mantém-se sincronizado com**: CLAUDE.md, MEMORY.md, master branch
