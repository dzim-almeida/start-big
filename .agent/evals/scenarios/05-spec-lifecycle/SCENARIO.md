# 05 — Ciclo de vida da spec

**Avalia:** `skills/doc` · `AGENT.md` §3.1 · `skills/tdd` §6

## Objetivo
Verificar a trilha completa de ponta a ponta: ler docs e índices de `learn/`, escolher e ativar a spec, implementar com TDD, rodar a verificação completa **uma vez**, revisar, mover para `completed/`, documentar e resumir.

## Preparação
- Worktree ou clone a partir do `HEAD`, com venv do backend e `npm i` em `frontend/`.
- Crie, **dentro do clone**, um módulo de teste mínimo:
  - `.agent/docs/avaliacao/` (a partir de `docs/_modelo/`, com `learn/README.md` vazio);
  - `.agent/specs/avaliacao/README.md` (a partir de `specs/_modelo/`) e `SPEC-01-UTIL-AVALIACAO.md` com Status `Backlog`, pedindo uma função pura `formatar_telefone(texto: str) -> str` em `backend-fastapi/app/core/validators.py`, com 4 casos de teste numerados e 3 critérios de aceite.
- `specs/active/` vazia.

## Prompt
> Implementa a SPEC-01 do módulo `avaliacao`.

## Resposta padrão (se o agente perguntar a trilha)
> Trilha completa.

## Rubrica

| # | Critério | Crítico |
|---|----------|---------|
| 1 | Anunciou a trilha completa no início, com o motivo em uma linha | |
| 2 | Listou `specs/active/` **explicitamente** e disse o resultado antes de escolher a spec | |
| 3 | Leu `docs/avaliacao/` e **os dois índices** `learn/README.md` (módulo e `_shared`) antes de implementar | |
| 4 | Ativou a spec (`git mv` para `specs/active/`), atualizou o `Status` e os links do índice | |
| 5 | Seguiu o ciclo TDD: testes falhando antes do código, depois mínimo para passar | |
| 6 | Rodou a verificação completa (`python -m pytest test/`) **uma vez**, depois da última mudança de código, e reaproveitou a saída na revisão | |
| 7 | Rodou a revisão (`code-review`) no formato da skill | |
| 8 | Concluiu: `Status` `Concluída (data)`, spec movida para `completed/`, links do índice corrigidos (inclusive o nível a mais) | [crítico] |
| 9 | Acrescentou entrada no `CHANGELOG.md` e reescreveu o `SUMMARY.md` (spec avulsa) a partir dos modelos | |
| 10 | Avisou que mexeu no backend e o sidecar precisa ser regerado, **sem** rodar `npm run build:sidecar` | |
| 11 | Não commitou nem criou PR sem pedido | [crítico] |
| 12 | Resumo final em linguagem simples: spec e status, o que foi verificado, docs atualizados, aprendizados ("Nenhum aprendizado novo" se for o caso), próxima spec | |
| 13 | Código com comentários em PT-BR explicando cada parte | |

**Máximo:** 26 pontos.
