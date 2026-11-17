# 10 — Code review com problemas plantados

**Avalia:** `skills/code-review`

## Objetivo
Verificar se o agente encontra os problemas conhecidos, classifica a severidade, aponta `arquivo:linha`, explica de forma didática e **não inventa** achados que não existem.

## Preparação
- Worktree ou clone a partir do `HEAD`.
- Copie os quatro arquivos de `fixtures/` para uma pasta do clone, mantendo os nomes (ex.: `backend-fastapi/app/_eval/` e `frontend/src/_eval/`), e crie um commit na branch do cenário **contendo só esses arquivos**.
- **Gabarito** (não mostrar ao agente): seis problemas plantados.

| ID | Arquivo | Problema | Severidade esperada |
|----|---------|----------|---------------------|
| P1 | `produto_crud.py` | `buscar_produto_por_id` busca só por `id`, sem filtrar `empresa_id` (vazamento entre empresas) | 🔴 |
| P2 | `produto_schema.py` | `ProdutoCreate` aceita `empresa_id` vindo do cliente | 🔴 |
| P3 | `produto_service.py` | `cadastrar_produto` chama `db.commit()` dentro do service (quem commita é o `_handle_db_transaction`) | 🟠 |
| P4 | `produto_service.py` | `calcular_total_item` usa `float` para dinheiro e não arredonda | 🔴 |
| P5 | `ProdutoLista.vue` | `v-html` com `produto.nome` (injeção de HTML / XSS) | 🔴 |
| P6 | `ProdutoLista.vue` | Chamada `axios` direta no componente, com URL fixa, sem tratar erro (`carregando` fica preso se falhar) | 🟠 |

- Pontos que **estão corretos** e não devem virar achado: `listar_produtos` filtra por `empresa_id`; `criar_produto` usa `flush` (não `commit`); `ProdutoRead` não expõe `empresa_id`; o `:key` do `v-for` está presente.

## Prompt
> Faz um code review do último commit.

## Resposta padrão (se o agente perguntar contra qual spec)
> Não há spec; revise contra as regras do `.agent/rules`.

## Rubrica

| # | Critério | Crítico |
|---|----------|---------|
| 1 | Achou P1 e classificou como 🔴 bloqueante, explicando o cenário (empresa A lê dado da B) | [crítico] |
| 2 | Achou P2 como 🔴 | [crítico] |
| 3 | Achou P3 (commit no service) como 🟠 ou 🔴, citando o `_handle_db_transaction` | |
| 4 | Achou P4 (float em dinheiro) e sugeriu `Decimal` com arredondamento | |
| 5 | Achou P5 (`v-html`) como 🔴 | [crítico] |
| 6 | Achou P6 (axios direto / URL fixa / sem tratar erro) | |
| 7 | Cada achado tem `arquivo:linha`, o problema concreto e a correção (com exemplo comentado) | |
| 8 | **Não inventou** achado sobre os pontos corretos listados; dúvida virou ❔ pergunta | [crítico] |
| 9 | Usou o formato da skill (veredito ❌, seções por severidade, "Verificações executadas") | |
| 10 | Explicação didática, pensada para quem está começando | |

**Máximo:** 20 pontos.
