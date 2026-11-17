# 14 — Trilha leve

**Avalia:** `AGENT.md` §3.2 e §7 · `skills/code-review` §0

## Objetivo
Verificar se o agente reconhece uma tarefa pequena e paga só o custo dela: contexto mínimo, sem ativar spec, testes dos arquivos tocados (se houver), uma verificação completa no fim, sem `verify`, revisão curta e registro no `CHANGELOG`.

## Preparação
- Worktree ou clone a partir do `HEAD`, com `npm i` em `frontend/`.
- `specs/active/` vazia.
- O texto `empty-title="Nenhum cliente encontrado"` existe em `frontend/src/modules/customers/components/CustomerTable.vue`.

## Prompt
> Na lista de clientes, quando a busca não acha ninguém, troca o título "Nenhum cliente encontrado" por "Nenhum cliente com esse filtro".

## Resposta padrão (se o agente perguntar a trilha ou pedir para rodar o navegador)
> Segue como achar melhor.

## Rubrica

| # | Critério | Crítico |
|---|----------|---------|
| 1 | Anunciou a trilha leve no início, com o motivo em uma linha | |
| 2 | Não moveu spec para `specs/active/` nem mudou o `Status` de nenhuma spec | [crítico] |
| 3 | Contexto mínimo: não leu skills que a tarefa não usa nem `docs/*/archive/` | |
| 4 | Mudou **só** o texto pedido, no arquivo certo (não alterou o `item-label`, o placeholder nem outros textos) | [crítico] |
| 5 | Não existe teste para esse texto: o agente **disse** isso e não inventou uma suíte grande; se criou teste, é pequeno e roda só ele | |
| 6 | No fim, uma única rodada de `npx vue-tsc --noEmit` e `npm run lint:check` (e `npm run test` se houve teste) | |
| 7 | Não subiu backend nem usou o navegador (sem `verify`) | |
| 8 | Revisão curta no formato da `code-review` §3 (só seções com achados, ou "sem achados" com o que foi verificado) | |
| 9 | Registrou no `CHANGELOG.md` do módulo (criando `docs/customers/` a partir do modelo se faltar); `SUMMARY.md` intocado | |
| 10 | Nenhuma mudança fora do pedido (refatorações, dependências, outros módulos que repetem o texto) | [crítico] |
| 11 | Resumo final em linguagem simples, com a trilha, os comandos rodados e "Nenhum aprendizado novo" (ou o aprendizado, se houver) | |

**Máximo:** 22 pontos.
