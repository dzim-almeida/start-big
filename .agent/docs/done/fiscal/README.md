# Progresso — implementação das specs fiscais

Branch: `claude/agent-specs-list-67a66e` · Início: 2026-09-17

Protocolo por spec: `specs/ → specs/active/` → doc de progresso → TDD (backend) / Vitest + vue-tsc + lint (frontend) → aceite ponta a ponta → commit → `specs/completed/`.

| Ordem | Spec | Status | Commit | Doc |
|---|---|---|---|---|
| 0 | Infra de teste (fixture sem lifespan, Vitest) | ✅ concluída | de3f937, dd32a55 | [00-baseline.md](00-baseline.md) |
| 1 | TASK001-BACKEND — Locker de numeração | ✅ concluída | de3f937 | [TASK001-BACKEND.md](TASK001-BACKEND.md) |
| 2 | TASK001-FRONTEND — Interface de confirmação | ✅ concluída | dd32a55 | [TASK001-FRONTEND.md](TASK001-FRONTEND.md) |
| 3 | TASK002 — Carta de Correção (BE+FE) | ✅ concluída | 6c872ca | [TASK002.md](TASK002.md) · [ADR-001](../adrs/ADR-001_eventos_fiscais_em_tabela_propria.md) |
| 4 | TASK003-BACKEND — NF-e de devolução | ✅ concluída | b3d3f85 | [TASK003-BACKEND.md](TASK003-BACKEND.md) · [ADR-002](../adrs/ADR-002_devolucao_a_partir_do_snapshot.md) |
| 5 | TASK003-FRONTEND — Modal de devolução | ✅ concluída | 6c34529 | [TASK003-FRONTEND.md](TASK003-FRONTEND.md) |
| 6 | Code review (skill code-quality) | ✅ concluída — 7 achados corrigidos | 548eee6 | [CODE-REVIEW.md](CODE-REVIEW.md) |

## Decisões
- Execução sequencial numa única sessão; um commit por spec nesta branch.
- `.agent/` fica fora do git; ao final é espelhada para `C:\dev\bigpdv\.agent`.
- Frontend ganha Vitest (composables/mutations); TDD estrito só no backend.
- Erros pré-existentes da suíte (552) não são corrigidos — ver baseline.

## Estado final (2026-09-17)
- Commits: `de3f937` `dd32a55` `6c872ca` `b3d3f85` `6c34529` `548eee6` (branch `claude/agent-specs-list-67a66e`).
- Gates finais: backend `pytest test/services test/core test/db test/api/v1/fiscal` → **893 passed**; frontend Vitest **19/19**, `vue-tsc --noEmit` **0 erros**.
- Specs: 5/5 em `specs/completed/`, cada uma com "Desvios aplicados" no rodapé. ADRs: 001 (CC-e em tabela própria), 002 (devolução a partir do snapshot).
- Antes de instalar em loja: `npm run build:sidecar` (backend mudou); a rota `/erp/fiscal/nfe/carta-correcao` precisa existir na API intermediária para a CC-e sair em homologação.
