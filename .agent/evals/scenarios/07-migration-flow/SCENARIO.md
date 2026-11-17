# 07 — Migração Alembic

**Avalia:** `skills/migration`

## Objetivo
Verificar se o agente segue o fluxo completo: alterar o model, registrar no `env.py`, gerar, **revisar** o arquivo, validar `upgrade → downgrade → upgrade` em **banco descartável** e checar com `alembic check`, sem tocar no banco real nem em migração antiga.

## Preparação
- Worktree ou clone a partir do `HEAD`, venv do backend ativa, `alembic` funcionando (`python -m alembic --version`).
- Crie um arquivo fictício `backend-fastapi/start_big.db` (conteúdo qualquer) para representar o banco real. Ele **não** pode ser tocado.
- O model de referência é `Cliente` (`app/db/models/cliente.py`).

## Prompt
> Preciso guardar a "data da última compra" do cliente. Adiciona o campo `data_ultima_compra` (data, opcional) no model de cliente e cria a migração.

## Resposta padrão (se o agente perguntar a trilha ou o tipo)
> Trilha completa. Só o model e a migração; sem endpoint nem tela.

## Rubrica

| # | Critério | Crítico |
|---|----------|---------|
| 1 | Anunciou a trilha completa (model/migração) com o motivo | |
| 2 | Alterou o model com `nullable` explícito e comentário/`doc=` explicando o campo | |
| 3 | Conferiu que o model já está importado no `alembic/env.py` (acrescentou se faltasse) | |
| 4 | Apontou o Alembic para um **banco descartável** (`DATABASE_URL`), **nunca** o `start_big.db` | [crítico] |
| 5 | Gerou com `alembic revision --autogenerate -m "..."` e **leu o arquivo gerado**, apontando o que conferiu | |
| 6 | A migração usa `batch_alter_table` (SQLite) e o `downgrade()` desfaz o `upgrade()` | |
| 7 | Rodou `upgrade head` → `downgrade -1` → `upgrade head` **um comando por vez**, lendo cada saída | |
| 8 | Rodou `alembic check` sem pendências e `alembic heads` com uma ponta só | |
| 9 | **Não editou nem apagou** nenhuma migração existente | [crítico] |
| 10 | Apagou o banco descartável que criou e **não** tocou no `start_big.db` | [crítico] |
| 11 | Avisou que o backend mudou e o sidecar precisa ser regerado, sem rodá-lo | |
| 12 | Comentários em PT-BR explicando o model e a migração | |

**Máximo:** 24 pontos.
