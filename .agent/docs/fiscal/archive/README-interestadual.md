# Progresso — specs fiscais interestaduais (TASK004 → TASK009)

Branch: `claude/fiscal-nfe-agent-tasks-d5e35d` · Início: 2026-09-18 · Base: `feat/fiscal-nfe` (35a7946) + TASK001–003 (0a72b86)

Protocolo por spec (decidido com o desenvolvedor em 2026-09-18):
`specs/ → specs/active/` → verificar spec contra o código → doc em `docs/fiscal/archive/` → TDD backend (`skills/tdd`) → `skills/code-quality` → doc finalizada → `docs/fiscal/archive/` + `specs/fiscal/completed/` → **1 commit por task**.

Decisões da rodada:
- **Só backend** nesta rodada; a parte de interface das specs (TASK005/006/009) fica registrada como pendência no rodapé de cada doc.
- Divergência spec × código: adaptar ao código real e registrar em "Desvios da spec"; só parar para perguntar se mudar o desenho.
- `.agent/` **fora do git** (`/.agent` no `.gitignore`, removido do índice), como na `feat/fiscal-nfe`.
- Gate de regressão (ver [00-baseline.md](00-baseline.md)): `pytest test/services test/core test/db test/api/v1/fiscal -q` — a suíte completa não roda porque o lifespan toca o banco real.
- Python: `C:/dev/bigpdv/backend-fastapi/.venv/Scripts/python.exe` (a worktree não tem venv), rodado de `backend-fastapi/`.

| Ordem | Spec | Status | Commit | Doc |
|---|---|---|---|---|
| 1 | TASK004 — Modelagem PerfilTributario + RegraPerfilTributario | ✅ concluída | f79b960 (+ chore 48df9d8) | [TASK004.md](TASK004.md) |
| 2 | TASK005 — CRUD + API REST de perfis | 🔄 em andamento | — | [TASK005.md](TASK005.md) |
| 3 | TASK006 — Vínculo ProdutoFiscal → Perfil + resolver (backend) | ✅ concluída | 9415aec | [TASK006.md](TASK006.md) |
| 4 | TASK007 — Motor DIFAL | ✅ concluída | ecf7ac8 | [TASK007.md](TASK007.md) |
| 5 | TASK008 — Motor ICMS-ST + CST/CFOP interestadual | ✅ concluída | be458b8 | [TASK008.md](TASK008.md) |
| 6 | TASK009 — Payload interestadual (backend) | ✅ concluída | 8f85431 | [TASK009.md](TASK009.md) |

## Estado final (2026-09-19)
- Commits nesta branch: `48df9d8` (chore .agent) · `f79b960` TASK004 · `5674d59` TASK005 · `9415aec` TASK006 · `ecf7ac8` TASK007 · `be458b8` TASK008 · `8f85431` TASK009 · `37ca3bb` code review ([CODE-REVIEW-interestadual.md](CODE-REVIEW-interestadual.md), 5 achados corrigidos).
- Gate final: **1072 passed** (893 no início; +179 testes).
- Specs: 6/6 em `specs/fiscal/completed/`, cada uma com "Desvios aplicados" no rodapé; docs em `done/fiscal/TASK004..009.md`.
- Sem ADR novo: as decisões ficaram nas docs de cada task (a maior é a do Simples sem DIFAL — TASK007).

### Para o desenvolvedor decidir / confirmar
1. **Simples Nacional sem DIFAL** (TASK007) — premissa legal (STF ADI 5464) a confirmar com o contador; um `if` em `resolver._resolver_item_interestadual` reverte.
2. **Total da venda com ICMS-ST** (TASK009) — o checkout precisa somar a ST ao total a cobrar, senão o builder recusa (Rej. 767).
3. **Plataforma web** — aceitar os campos de `docs/contrato-api-fiscal-plataforma.md` § 3.1 no Zod (ou `.passthrough()`).
4. **`npm run build:sidecar`** antes de instalar em loja: o backend mudou (2 migrations novas: `v5w6x7y8z9a0`, `w6x7y8z9a0b1`).

### Rodada de interface (fora do escopo desta)
- TASK005 § 6: telas de perfis (`PerfisTributariosView`, `PerfilTributarioForm`, composables, rota).
- TASK006 § 7: select de perfil na aba fiscal do produto.
- TASK009 § 6: badges no checkout, linhas ICMS-ST/DIFAL no resumo, total com ST.
