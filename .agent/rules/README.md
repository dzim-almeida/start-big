# `rules/` — Regras obrigatórias

Regras que o agente **sempre** segue. Diferente das skills (procedimentos que o agente usa quando a tarefa pede), as regras valem em qualquer tarefa que toque o escopo delas.

## Arquivos

| Regra | Escopo | Resumo |
|-------|--------|--------|
| [`frontend-architecture.md`](./frontend-architecture.md) | `frontend/src/` | Arquitetura por módulos: estrutura, responsabilidade de cada camada, direção dos imports |
| [`backend-architecture.md`](./backend-architecture.md) | `backend-fastapi/app/` | Camadas endpoint → service → crud → model, transação, isolamento por empresa |
| [`api-contract.md`](./api-contract.md) | `endpoints/` e `schemas/` do backend; `services/` e composables do frontend | URLs, métodos, códigos HTTP, formato de erro, paginação, tratamento de erro no frontend |
| [`session-learnings.md`](./session-learnings.md) | Toda sessão | Quando e como registrar aprendizados em `docs/{módulo}/learn/` |

## Contrato

- Regra é **curta, verificável e sem ambiguidade**. Se não dá para dizer "cumpriu" ou "não cumpriu", ela não está pronta.
- Cada regra cita a **origem** (spec, decisão ou trecho do `CLAUDE.md`) no cabeçalho.
- **Hierarquia:** a spec ativa vence as regras. Em conflito, o agente para e pergunta. A regra é atualizada **na mesma tarefa** em que a decisão for tomada.
- Regra nova ou alterada → rodar os cenários de `evals/` relacionados.
- Aprendizado de `docs/*/learn/` que vire padrão permanente pode ser promovido a regra (com aprovação do usuário).
- Exemplos de código dentro das regras levam comentários explicando cada linha importante (o usuário é iniciante).
