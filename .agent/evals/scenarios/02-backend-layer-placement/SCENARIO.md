# 02 — Camada certa no backend

**Avalia:** `rules/backend-architecture.md` §2, §3 e §5

## Objetivo
Verificar se o agente separa endpoint, schema, service, crud e model, e se o `commit` fica só no `_handle_db_transaction`.

## Preparação
- Worktree ou clone a partir do `HEAD`, com a venv do backend ativa (`python -m pytest --version` funciona).
- Banco descartável: nenhum teste deste cenário toca o `start_big.db`.
- Domínio de referência: `cliente`.

## Prompt
> Preciso de um endpoint `GET /api/v1/clientes/aniversariantes?mes=11` que devolva os clientes da empresa que fazem aniversário no mês informado. Só o backend; pode incluir os testes.

## Resposta padrão (se o agente perguntar o formato)
> Lista de `id`, `nome` e `data_nascimento`, ordenada por dia do mês.

## Rubrica

| # | Critério | Crítico |
|---|----------|---------|
| 1 | Anunciou a trilha **completa** (endpoint novo) com o motivo | |
| 2 | Rota em `api/v1/endpoints/cliente.py`, **sem** consulta ao banco nem regra de negócio dentro dela | [crítico] |
| 3 | Schema de saída em `schemas/cliente/` (sem `empresa_id` na entrada, sem dado sensível na saída) | |
| 4 | Regra (validação de `mes` entre 1 e 12) no `services/cliente/` | |
| 5 | Consulta em `db/crud/cliente/`, filtrando por `empresa_id` | [crítico] |
| 6 | **Nenhum `db.commit()`** em service ou crud (leitura: sem wrapper ou com `_handle_db_transaction`, mas sem commit manual) | [crítico] |
| 7 | `empresa_id` lido de `user_token`, protegido por `check_permission(...)` | [crítico] |
| 8 | Imports na direção `endpoint → service → crud → model`; endpoint não importa `crud`/`models` | |
| 9 | Teste de service/rota **e** teste de isolamento (empresa B não vê os clientes da A) | |
| 10 | Avisou que o backend mudou e o **sidecar** precisa ser regerado (`npm run build:sidecar`), sem rodá-lo | |
| 11 | Código novo com comentários/docstrings em PT-BR explicando cada parte | |

**Máximo:** 22 pontos.
