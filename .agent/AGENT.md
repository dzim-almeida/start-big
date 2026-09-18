# AGENT.md — Guia de Harness Engineering

**Versão:** 1.0
**Data:** 2026-09-16
**Escopo:** Sistema StartBig ERP (Tauri + Vue 3 + FastAPI)

---

## 1. Visão Geral para Agentes IA

Você está assistindo um projeto de **software engineering** — um sistema desktop integrado com backend. O código é bilíngue (nomes em Português, estrutura moderna), e você deve:

1. **Nunca quebrar o workflow de desenvolvimento**: Sempre consulte `CLAUDE.md` e `MEMORY.md` antes de fazer mudanças
2. **Respeitar a arquitetura definida**: Frontend/backend separados, regras de comunicação em `rules/`
3. **Atender ao idioma**: Português para nomes de variáveis, funções, mensagens e comentários
4. **Testes antes de deploy**: Mudanças exigem testes unitários/integração

---

## 2. Stack Técnico

| Camada | Tecnologia | Versão | Porta |
|--------|-----------|--------|-------|
| **Desktop Shell** | Tauri | Latest | — |
| **Frontend** | Vue 3 + TypeScript | Latest | 1420 |
| **Backend** | FastAPI + SQLAlchemy | Python 3.10+ | 8000 (dev), 8080-8083 (prod) |
| **Database** | SQLite | Latest | — |
| **Forms** | VeeValidate + Zod | Latest | — |
| **State** | Pinia + TanStack Query | Latest | — |

---

## 3. Desenvolvimento Local

### 3.1 Setup Inicial
```bash
# Clone and install dependencies
git clone <repo>
cd frontend && npm install && npm run dev

# Em outro terminal
cd backend-fastapi && python -m venv .venv
source .venv/bin/activate  # (Windows: .\.venv\Scripts\activate)
pip install -r requirements.txt
fastapi dev app/main.py    # Porta 8000
```

### 3.2 Executar Testes
```bash
# Frontend
npm run lint
npx vue-tsc --noEmit

# Backend
pytest test/ -v
```

### 3.3 Build para Desktop
```bash
cd frontend
npm run build:sidecar   # Empacota backend como .exe
npm run build           # Tauri build
```

---

## 4. Padrões de Código

### 4.1 Validação (VeeValidate + Zod)
```typescript
// Schema Zod (frontend e backend)
const schemaOS = z.object({
  numero: z.string().min(1),
  cliente_id: z.number().int().positive(),
  valor_total: z.number().int().positive(),
});

// Frontend: VeeValidate
const { defineField, handleSubmit } = useForm({
  validationSchema: toTypedSchema(schemaOS),
});
const [numero, numeroAttrs] = defineField('numero');

// Backend: Pydantic
class OSCreate(BaseModel):
    numero: str = Field(..., min_length=1)
    cliente_id: int = Field(..., gt=0)
    valor_total: int = Field(..., gt=0)
```

### 4.2 Valores Monetários
```typescript
// Frontend (reais)
baseMoneyInput v-model="formData.valor" // User sees "R$ 100,50"

// Save (centavos)
const valueToCents = Math.round(formData.valor * 100)  // 10050

// Populate (reais)
const valueToReais = valorCentavos / 100  // 100.50
```

### 4.3 Serviços e Chamadas API
```typescript
// Frontend: chamada direta, sem tratamento (delegado ao TanStack Query)
export async function fetchOS(id: string): Promise<OSDetail> {
  const res = await axios.get(`/api/v1/order-services/${id}`);
  return safeParse(OSDetailSchema, res.data.data, {
    errorCallback: () => console.warn("Falha ao parsear OS"),
  });
}

// Mutation com toast
const { mutate } = useMutation({
  mutationFn: updateOS,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.os.all });
    useToast().success("OS atualizada");
  },
  onError: (err) => {
    useToast().error(getErrorMessage(err));
  },
});
```

---

## 5. Troubleshooting e Incidentes Conhecidos

### 5.1 Login Quebrado
**Primeira coisa:** verificar porta do backend
- Dev: `http://localhost:8000`
- Tauri dev: `#[cfg(debug_assertions)]` chumbado em `src-tauri/src/network/config.rs` → sempre 8000
- App instalado: fallback 8080→8083

Se usando `npm run tauri dev` e backend está em 8080, login falha. **Suba com `fastapi dev`** (padrão 8000).

### 5.2 Banco de Dados Vazio ou Inacessível
- Verificar: `%LOCALAPPDATA%\StartBigERP\data\start_big.db` (preservado entre atualizações)
- `create_all()` roda ANTES das migrations — se tabelas faltam, remigrar
- Nunca renomear o banco. Se inevitável, adicionar nome antigo em `LEGACY_DB_FILENAMES`

### 5.3 Sidecar Desatualizado
```bash
cd frontend
npm run check:sidecar   # Falha se outdated
npm run build:sidecar   # Regenera
```

### 5.4 Fuso Horário
- Banco: UTC
- Tela: Fuso local
- Conversão **única**: `app/core/tempo.py`
- Backup e prazos de OS ficam fora (usam horário local)

**Leitura:** `memory/c19-fuso-horario-relatorios.md`

---

## 6. Commits e Versionamento

### 6.1 Convenção de Commits
```
<tipo>(<escopo>): <descrição>

feat(fiscal): tributacao em cascata
fix(os): validar equipamento antes de salvar
refactor(frontend): simplificar form context
chore(deps): update vue to 3.5
docs(AGENT.md): adicionar secao de troubleshooting
```

Tipos: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `style`

### 6.2 Branches
- Main: `master` (releases)
- Feature: `feat/<feature-name>`
- Bugfix: `fix/<bug-name>`
- Chore: `chore/<task-name>`

### 6.3 SemVer
- Major: breaking changes
- Minor: features novas (backward-compatible)
- Patch: bug fixes

---

## 7. Decisões Arquiteturais (ADRs)

**⚠️ IMPORTANTE PARA AGENTES DE IA:**

Quando implementar decisões arquiteturais ou refatorações significativas, **SEMPRE** documentar em `.agent/docs/adrs/`:

### O que Documentar
- Mudanças de padrão (ex: novo padrão de form, nova camada no backend)
- Decisões de trade-off (performance vs. legibilidade)
- Breaking changes (compatibilidade quebrada)
- Soluções para incidentes (padrões emergentes)
- Alternativas rejeitadas e por quê

### Formato ADR (Architecture Decision Record)
```markdown
# ADR-NNN: Título da Decisão

**Status:** Accepted | Proposed | Rejected
**Data:** 2026-09-16
**Decidido por:** Agente de IA / Desenvolvedor

## Contexto
Por que essa decisão foi necessária?

## Decisão
O que foi decidido e por quê?

## Alternativas Consideradas
- Opção A: (por que não?)
- Opção B: (por que não?)

## Consequências
✅ Benefícios
❌ Riscos/Custo

## Referências
- Related ADRs
- Código afetado
```

### Localização
```
.agent/docs/
└── adrs/
    ├── ADR-001_fiscal_engine_puro.md
    ├── ADR-002_form_context_provider.md
    └── ADR-NNN_titulo.md
```

**Ao documentar, atualize também:**
1. `AGENT.md` — Se afeta padrões globais
2. `memory/MEMORY.md` — Se é padrão recorrente
3. Código afetado — Adicionar comentário: `# ADR-NNN: breve resumo`

---

## 8. Checklist para Code Review

- [ ] Código segue padrões de arquitetura (`rules/`)
- [ ] Variáveis/funções em Português
- [ ] Schemas Zod + Pydantic sincronizados
- [ ] Testes unitários (backend) ou integração (frontend)
- [ ] Sem console.log em produção (use logger)
- [ ] Sem valores hardcoded (usar constants ou config)
- [ ] Validação: backend valida tudo
- [ ] Erro tratado: mensagem amigável + error_code
- [ ] Se enum/constante: sincronizou frontend ↔ backend?
- [ ] Commit message segue convenção

---

## 9. Recursos Úteis

| Documento | Localização |
|-----------|------------|
| Instruções do Projeto | `CLAUDE.md` |
| Memória de Sessões | `memory/MEMORY.md` |
| Comunicação API | `.agent/rules/architecture-communication.md` |
| Fiscal Engine | `memory/modulo-fiscal-refatoracao.md` |
| Order Service | `frontend/src/modules/order-service/ordens/docs/order-service.md` |
| Timezone & Reports | `memory/c19-fuso-horario-relatorios.md` |
| Local Connection | `memory/conexao-local-servidor-terminal.md` |
| Create All & Migrations | `memory/create-all-antes-das-migrations.md` |

---

## 10. Contato e Escalation

**Problemas técnicos:**
1. Consulte `CLAUDE.md` e `MEMORY.md`
2. Verifique `rules/` para validação de contrato
3. Se incidente recorrente, document em `memory/`

**Pergunta ao desenvolvedor se:**
- Quebra de arquitetura não coberta em regras
- Mudança de enum/constante backend (precisa sync frontend)
- Nova feature com estado complexo (precisa máquina de estados?)

---

**Última atualização:** 2026-09-16
**Mantido por:** Harness Engineering Team
