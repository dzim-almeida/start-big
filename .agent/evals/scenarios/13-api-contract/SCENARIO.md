# 13 — Contrato da API

**Avalia:** `rules/api-contract.md`

## Objetivo
Verificar se o agente cria um endpoint novo seguindo o contrato (rota, método, status, formato de erro, paginação, permissão, `404` de outra empresa) e consome no frontend decidindo pelo **status**, não pelo texto da mensagem.

## Preparação
- Worktree ou clone a partir do `HEAD`, venv do backend e `npm i` em `frontend/`.
- Recurso de referência: `forma_pagamento` (rota `/api/v1/formas-pagamento` ou equivalente em `api.py`; confirme antes).

## Prompt
> Preciso de `DELETE` para apagar uma forma de pagamento, que só pode ser apagada se nunca foi usada em venda. No frontend, quero que o botão "Excluir" mostre a mensagem de erro certa. Implementa backend e frontend.

## Resposta padrão (se o agente perguntar a mensagem)
> Usa o texto da API quando for um erro de regra.

## Rubrica

| # | Critério | Crítico |
|---|----------|---------|
| 1 | Anunciou a trilha completa (endpoint + contrato) | |
| 2 | `DELETE /{id}` com `status_code` declarado (`204`, ou `200` justificado) | |
| 3 | Forma usada em venda → erro de regra com `HTTPException` (`400`/`409`) e mensagem clara em PT-BR no `detail` | |
| 4 | Forma inexistente **ou de outra empresa** → `404` | [crítico] |
| 5 | Rota com `check_permission(...)` e `empresa_id` vindo do token | [crítico] |
| 6 | Service sem `commit`; o endpoint usa `_handle_db_transaction` | |
| 7 | Frontend: service em `services/` (usa `@/api/axios`), composable traduz o erro **pelo status** e mostra o `detail` quando for texto | |
| 8 | **Não** comparou texto fixo de mensagem para decidir o fluxo | |
| 9 | Não alterou o formato de erro nem rota/campo já em uso (se precisou, **perguntou antes**) | [crítico] |
| 10 | Testes: sucesso, regra violada, `404`, permissão e isolamento | |
| 11 | Avisou sobre o sidecar e atualizou o `CHANGELOG` do módulo | |
| 12 | Código com comentários em PT-BR explicando cada parte | |

**Máximo:** 24 pontos.
