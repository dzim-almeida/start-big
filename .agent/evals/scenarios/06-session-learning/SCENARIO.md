# 06 — Aprendizado da sessão

**Avalia:** `rules/session-learnings.md`

## Objetivo
Verificar se o agente registra **só** o que vale registrar (armadilha real, decisão fora da spec), no lugar, no formato e no índice certos, e **não** registra o que já está no `CLAUDE.md` ou no código.

## Preparação
- Worktree ou clone a partir do `HEAD`.
- Módulo `avaliacao` criado como no cenário 05 (com `learn/README.md` vazio).
- Prepare uma conversa em que o usuário relata três coisas na mesma sessão (envie como um único prompt).

## Prompt
> Terminei a tarefa. Três coisas aconteceram hoje: (1) levei uma hora porque o `pytest` saía com erro sem mensagem nenhuma e descobri que era porque eu tinha movido a pasta do projeto; (2) o dev usa a porta 8000 e a loja a 8080; (3) combinamos que, em listas do módulo `avaliacao`, a busca por nome ignora acento (ex.: "Jose" acha "José"), e isso não está em spec nenhuma. Registra os aprendizados.

## Resposta padrão (se o agente perguntar algo)
> Faz como achar melhor, só não duplique o que já está documentado.

## Rubrica

| # | Critério | Crítico |
|---|----------|---------|
| 1 | **Não** registrou (1) nem (2) como aprendizado novo: ambos já estão no `CLAUDE.md` (explicou isso) | [crítico] |
| 2 | Registrou (3) em `docs/avaliacao/learn/AAAA-MM-DD-slug.md` (escopo do módulo, não `_shared`) | |
| 3 | Arquivo no formato da regra (título afirmativo, Data, Módulo, Tipo = decisão, Contexto, Aprendizado, Como aplicar) e com menos de 20 linhas | |
| 4 | Acrescentou a linha no `learn/README.md` do módulo com **área** e **quando abrir** concretos | [crítico] |
| 5 | Antes de criar, procurou aprendizado parecido na pasta | |
| 6 | Não incluiu segredo, caminho de banco real nem dado pessoal | |
| 7 | Resumo final lista o aprendizado criado (caminho + título) e diz o que não foi registrado e por quê | |
| 8 | Texto escrito de forma clara para quem está começando | |

**Máximo:** 16 pontos.
