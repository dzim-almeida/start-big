# 01 — Camada certa no frontend

**Avalia:** `rules/frontend-architecture.md`

## Objetivo
Verificar se o agente cria cada arquivo na pasta certa do módulo, respeita a direção dos imports e reaproveita os componentes `Base*`.

## Preparação
- Worktree ou clone a partir do `HEAD` (ver `evals/README.md`), com `npm i` em `frontend/`.
- Módulo de referência: `frontend/src/modules/customers/`.
- **Não** peça para rodar o app. A avaliação é só pela estrutura criada.

## Prompt
> No módulo de clientes, quero uma tela nova "Aniversariantes do mês": lista os clientes que fazem aniversário no mês escolhido. Vai chamar `GET /api/v1/clientes/aniversariantes?mes=11`. Pode criar os arquivos, sem implementar o backend.

## Resposta padrão (se o agente perguntar o formato da resposta)
> Devolve uma lista simples com `id`, `nome` e `data_nascimento`.

## Rubrica

| # | Critério | Crítico |
|---|----------|---------|
| 1 | Anunciou a trilha **completa** (tela nova = rota + service) com o motivo em uma linha | |
| 2 | `views/AniversariantesView.vue` só monta a página (sem chamada HTTP, sem lógica de formulário) | |
| 3 | A chamada HTTP está em `services/*.service.ts`, usando `@/api/axios` (não `axios` direto nem URL fixa no componente) | [crítico] |
| 4 | Existe schema Zod em `schemas/` e o service valida a resposta com ele | |
| 5 | A orquestração (vue-query + formatação) está em `composables/` (a consulta em `composables/request/`) | |
| 6 | Rota declarada em `modules/customers/routes.ts`, sem editar `router/index.ts` | |
| 7 | Usou `Base*` existentes (`BaseSelect`, `BaseButton`...) em vez de `<select>`/`<button>` crus | |
| 8 | Nenhum import de outro módulo (`modules/*`) e nenhum `shared/` importando de `modules/` | [crítico] |
| 9 | URL base em `constants/`, não repetida em string solta | |
| 10 | Código novo com **comentários em PT-BR explicando** o que cada bloco faz | |

**Máximo:** 20 pontos.
