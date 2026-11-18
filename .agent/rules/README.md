# `rules/` — Regras obrigatórias

Regras que o agente **sempre** segue. Diferente das skills (procedimentos que o agente usa quando a tarefa pede), as regras valem em qualquer tarefa que toque o escopo delas.

## Arquivos

| Regra | Escopo | Resumo |
|-------|--------|--------|
| [`frontend-architecture.md`](./frontend-architecture.md) | `frontend/src/` | Arquitetura por módulos: estrutura, responsabilidade de cada camada, direção dos imports |
| [`backend-architecture.md`](./backend-architecture.md) | `backend-fastapi/app/` | Camadas endpoint → service → crud → model, transação, isolamento por empresa |
| [`api-contract.md`](./api-contract.md) | `endpoints/` e `schemas/` do backend; `services/` e composables do frontend | URLs, métodos, códigos HTTP, formato de erro, paginação, tratamento de erro no frontend |
| [`architecture-communication.md`](./architecture-communication.md) | Backend ↔ frontend | Regras rígidas de comunicação: resposta e erro da API, contrato de dados, endpoints, autenticação, estado. ⚠️ Ver o aviso abaixo |
| [`backend-layer-hierarchy.md`](./backend-layer-hierarchy.md) | `backend-fastapi/app/` | Hierarquia de camadas (endpoints → services → crud → models), schemas, chamadas entre services, transações, exceções, checklist de PR |
| [`frontend-module-architecture.md`](./frontend-module-architecture.md) | `frontend/src/` | Módulos auto-contidos: estrutura, imports, UI compartilhada, stores, formulários, TanStack Query, valores monetários, provide/inject |
| [`session-learnings.md`](./session-learnings.md) | Toda sessão | Quando e como registrar aprendizados em `docs/{módulo}/learn/` |

## Atenção: regras que se sobrepõem

Três regras (`architecture-communication`, `backend-layer-hierarchy`, `frontend-module-architecture`) foram acrescentadas depois e tratam dos mesmos assuntos de `api-contract`, `backend-architecture` e `frontend-architecture`. **Em caso de divergência, o agente para e pergunta** (`AGENT.md` §3). Divergência já identificada:

| Assunto | `architecture-communication.md` diz | O código atual faz (`api-contract.md`) |
|---------|-------------------------------------|----------------------------------------|
| Resposta de sucesso | Envelope `{ "data": ..., "status": "success" }` | Objeto direto, sem envelope |
| Corpo de erro | `{ "status": "error", "message", "error_code", "details" }` | `{ "error", "detail" }` (`core/exceptions.py`) |

Decisão pendente do usuário: ou o código migra para o envelope, ou a regra é ajustada ao que a API faz.

## Contrato

- Regra é **curta, verificável e sem ambiguidade**. Se não dá para dizer "cumpriu" ou "não cumpriu", ela não está pronta.
- Cada regra cita a **origem** (spec, decisão ou trecho do `CLAUDE.md`) no cabeçalho.
- **Hierarquia:** a spec ativa vence as regras. Em conflito, o agente para e pergunta. A regra é atualizada **na mesma tarefa** em que a decisão for tomada.
- Regra nova ou alterada → rodar os cenários de `evals/` relacionados.
- Aprendizado de `docs/*/learn/` que vire padrão permanente pode ser promovido a regra (com aprovação do usuário).
- Exemplos de código dentro das regras levam comentários explicando cada linha importante (o usuário é iniciante).
