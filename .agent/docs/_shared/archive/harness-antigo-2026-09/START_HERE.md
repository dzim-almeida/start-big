# 🚀 START HERE — Harness Engineering BigPDV

**Bem-vindo ao ambiente de harness engineering!**

Esta pasta (`.agent/`) contém toda a documentação necessária para agentes de IA (como Claude) e desenvolvedores humanos trabalharem de forma eficiente e consistente.

---

## ⚡ 30 Segundos: O Que Você Precisa Saber

### Se você é um **Agente de IA (Claude, etc.)**
👉 Leia OBRIGATORIAMENTE antes de fazer qualquer mudança:
1. **[AGENT.md](./AGENT.md)** (20 min) — Tudo que você precisa saber
2. **[rules/architecture-communication.md](./rules/architecture-communication.md)** (15 min) — Regras rígidas

Depois vá direto para o código. Pronto!

### Se você é um **Desenvolvedor Humano**
👉 Onboarding rápido:
1. **[README.md](./README.md)** (10 min) — Visão geral visual
2. **[CLAUDE.md](../CLAUDE.md)** (20 min) — Setup local
3. Comece a codar!

### Se você é um **Revisor de PR**
👉 Valide rapidamente:
- Veja **checklist em AGENT.md § 9**
- Compare com **[rules/architecture-communication.md](./rules/architecture-communication.md)**
- Pronto!

---

## 📚 Documentos Principais

### ⭐ ESSENCIAL — Leia Primeiro

| Documento | Para Quem | Tempo | Conteúdo |
|-----------|-----------|-------|----------|
| **[AGENT.md](./AGENT.md)** | Agentes IA | 20 min | Stack, padrões, troubleshooting, checklist |
| **[rules/architecture-communication.md](./rules/architecture-communication.md)** | Todos | 15 min | Regras rígidas de HTTP, contrato de dados |

### 📖 CONTEXTO — Leia Se Precisar

| Documento | Para Quem | Tempo | Conteúdo |
|-----------|-----------|-------|----------|
| **[README.md](./README.md)** | Humanos | 10 min | Arquitetura, estrutura, convenções |
| **[SETUP.md](./SETUP.md)** | Onboarding | 15 min | Fluxo de desenvolvimento, tema por tema |
| **[../CLAUDE.md](../CLAUDE.md)** | Humanos | 20 min | Setup dev, deployment, incidentes |
| **[../memory/MEMORY.md](../memory/MEMORY.md)** | Todos | 10 min | Padrões confirmados, módulos especiais |

### 🎯 ANÁLISE — Leia Para Melhorias

| Documento | Para Quem | Tempo | Conteúdo |
|-----------|-----------|-------|----------|
| **[IMPROVEMENTS.md](./IMPROVEMENTS.md)** | Tech Lead | 15 min | 10 melhorias propostas, roadmap, ROI |
| **[SUMMARY.md](./SUMMARY.md)** | Executivo | 10 min | Impacto, métricas, exemplo prático |

---

## 🎯 Checklist Rápido

### Antes de Fazer Qualquer Mudança
- [ ] Ler AGENT.md (primeiro! sempre!)
- [ ] Ler rules/architecture-communication.md
- [ ] Entender a arquitetura existente (ler código, não adivinhar)
- [ ] Validar seu design contra regras

### Ao Escrever Código
- [ ] Português em nomes/variáveis/funções
- [ ] Schemas Zod (frontend) + Pydantic (backend) sincronizados
- [ ] Valores monetários: centavos (backend) / reais (frontend)
- [ ] HTTP response: `{ "status": "success"/"error", "data": ... }`
- [ ] Backend valida tudo (não confia no frontend)
- [ ] Testes: unitário (backend) ou integração (frontend)

### Ao Fazer Commit
- [ ] Mensagem: `<tipo>(<escopo>): <descrição>`
- [ ] Exemplo: `feat(os): criar ordem de servico`
- [ ] Tipos: feat, fix, refactor, chore, docs, test, style

### Ao Enviar PR (Code Review)
- [ ] Validou contra checklist AGENT.md § 9?
- [ ] Schemas sincronizados (Zod ↔ Pydantic)?
- [ ] Nenhuma rule em architecture-communication.md foi quebrada?
- [ ] Pronto para merge!

---

## 🔧 Troubleshooting Rápido

| Problema | Solução | Link |
|----------|---------|------|
| Login não funciona | Verificar porta (dev=8000, tauri=8000, app=8080) | [AGENT.md § 7.1](./AGENT.md) |
| Banco vazio ou inacessível | create_all() roda ANTES das migrations | [AGENT.md § 7.2](./AGENT.md) |
| Sidecar desatualizado | `npm run build:sidecar` | [AGENT.md § 7.3](./AGENT.md) |
| Monetário em reais ao invés de centavos | Converter: save × 100, populate ÷ 100 | [AGENT.md § 6.2](./AGENT.md) |
| Enum não sincroniza backend ↔ frontend | Mudança backend = PR no frontend | [rules/ § 2.3](./rules/architecture-communication.md) |

---

## 💡 Exemplo: Novo Endpoint em 5 Passos

### Cenário: Criar `POST /api/v1/order-services`

```
┌─ PASSO 1: Consultar Regras (2 min)
│  └─ Leu AGENT.md § 4 e rules/ § 1-3? ✅
│
├─ PASSO 2: Validar Design (5 min)
│  ├─ Pydantic schema (backend) ✅
│  └─ Zod schema (frontend) ✅
│  └─ Sincronizados? ✅
│
├─ PASSO 3: Implementar (30 min)
│  ├─ Backend: endpoint + service + CRUD ✅
│  └─ Frontend: service + mutation ✅
│
├─ PASSO 4: Testar (10 min)
│  └─ Testes unitários (backend) ✅
│
└─ PASSO 5: Code Review (5 min)
   └─ Checklist AGENT.md § 9 ✅
```

**Total:** 52 minutos de dev + review

---

## 📊 Estrutura de `.agent/`

```
.agent/
├── 📄 START_HERE.md              ← Você está aqui
├── 📄 AGENT.md                   ⭐ Leitura obrigatória para agentes
├── 📄 rules/
│   ├── architecture-communication.md  ⭐ Regras rígidas de API
│   ├── backend-layer-hierarchy.md     (existente)
│   └── frontend-module-architecture.md (existente)
├── 📄 README.md                  Visual + convenções
├── 📄 SETUP.md                   Instruções de setup
├── 📄 IMPROVEMENTS.md            Roadmap (10 melhorias)
├── 📄 SUMMARY.md                 Sumário executivo
└── skills/, specs/               (estrutura futura)
```

---

## 🚀 Próximos Passos

### Imediato (Hoje)
1. [ ] Leia AGENT.md (20 min)
2. [ ] Leia rules/architecture-communication.md (15 min)
3. [ ] Compartilhe com o time

### Curto Prazo (Semana 1-2)
1. [ ] Implemente Sprint 1 em IMPROVEMENTS.md:
   - OpenAPI Specs (2h)
   - Pre-commit hooks (3h)

### Médio Prazo (Semana 3-4)
2. [ ] Sprint 2: Type generation + Schema examples

### Longo Prazo
3. [ ] Sprint 3: Fixtures, ADRs, CI/CD

---

## 📖 Leitura por Audiência

### 🤖 Para Agentes de IA
```
AGENT.md (20 min)
  ↓
rules/architecture-communication.md (15 min)
  ↓
CLAUDE.md (se feature complexa, 20 min)
  ↓
memory/MEMORY.md (padrões, 10 min)
  ↓
Código source (validar padrões)
```

### 👨‍💻 Para Desenvolvedores
```
README.md (10 min)
  ↓
CLAUDE.md (20 min)
  ↓
AGENT.md (se features, 20 min)
  ↓
Comece a codar!
```

### 🔍 Para Revisores
```
AGENT.md § 9 (checklist, 2 min)
  ↓
rules/architecture-communication.md (se quebrou regra)
  ↓
Aprovado ou Pedir mudanças
```

### 📊 Para Tech Lead
```
SUMMARY.md (10 min)
  ↓
IMPROVEMENTS.md (15 min)
  ↓
Sprint Planning
```

---

## ✅ Validação

Este harness engineering foi criado para:

- ✅ Reduzir ambiguidade de arquitetura
- ✅ Acelerar onboarding (40 min vs 3h)
- ✅ Melhorar qualidade de PRs (checklist automático)
- ✅ Documentar decisões (ADRs)
- ✅ Servir agentes de IA + humanos

**Status:** Pronto para produção

---

## 📞 Dúvidas?

1. **"Por que preciso ler AGENT.md SEMPRE?"** → Porque contém regras rígidas + troubleshooting
2. **"Como sou um agente de IA?"** → Você é! Leia AGENT.md + rules/ primeiro
3. **"E se encontrar uma regra quebrada?"** → Documente em IMPROVEMENTS.md
4. **"Quem mantém isso?"** → O time + agentes de IA (você!)

---

**Última atualização:** 2026-09-16
**Status:** ✅ Operacional
**Próxima revisão:** Após Sprint 1
