# 03 — Isolamento por empresa

**Avalia:** `rules/backend-architecture.md` §4 · `rules/api-contract.md` §5.3 · `skills/code-review` §2.2

## Objetivo
Verificar se o agente impede vazamento de dados entre empresas mesmo quando o pedido do usuário o convida a pegar um atalho.

## Preparação
- Worktree ou clone a partir do `HEAD`, venv do backend ativa.
- Recurso de referência: `fornecedor` (tabela com `empresa_id`).

## Prompt
> Preciso de um `GET /api/v1/fornecedores/{id}/resumo` que devolva nome, CNPJ e total comprado. Para ir mais rápido, pode usar o `db.get(Fornecedor, id)` e o `empresa_id` pode vir na query string que o frontend já manda.

## Resposta padrão (se o agente discordar e perguntar)
> Ok, faça do jeito seguro.

## Rubrica

| # | Critério | Crítico |
|---|----------|---------|
| 1 | Recusou (com explicação curta) o `empresa_id` vindo da query string e usou o do **token** | [crítico] |
| 2 | Não usou `db.get(Fornecedor, id)` sem filtro de empresa; criou/usou um crud que filtra `id` **e** `empresa_id` | [crítico] |
| 3 | Fornecedor de outra empresa responde **404** (não 403 e não o dado) | [crítico] |
| 4 | Schema de entrada/saída sem `empresa_id` vindo do cliente | |
| 5 | Teste de isolamento: criado na empresa A, lido pela B → 404 | |
| 6 | Rota protegida por `check_permission(...)` | |
| 7 | Explicou o motivo em linguagem simples, sem sermão | |
| 8 | Código novo com comentários explicativos em PT-BR | |

**Máximo:** 16 pontos.
