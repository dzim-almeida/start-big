# 00 — Baseline e infraestrutura de teste

Data: 2026-09-17 · Branch `claude/agent-specs-list-67a66e`

## Estado da suíte antes de qualquer mudança

| Escopo | Resultado | Tempo |
|---|---|---|
| `pytest test/services/fiscal` | **606 passed**, 1 skipped | 13 s |
| `pytest test/` (completa) | 880 passed, 1 skipped, **552 errors** | 6 min 49 s |

Python usado: `C:/dev/bigpdv/backend-fastapi/.venv/Scripts/python.exe` (a worktree não tem venv próprio), rodado de `backend-fastapi/`.

## Causa dos 552 erros (pré-existente, NÃO corrigida aqui)

Todos os testes que usam a fixture `client` de `test/conftest.py` erram no **setup**:

1. A fixture faz `with TestClient(app)`, o que dispara o `lifespan` de `app/core/tarefas.py`.
2. O lifespan roda `Base.metadata.create_all(bind=engine)` e `aplicar_migracoes()` no **engine real** (`app.db.session.engine`), não no SQLite em memória do conftest — o override de `get_db` só vale para as rotas.
3. `settings.DATABASE_URL` nesta máquina resolve para `%LOCALAPPDATA%\StartBigERP\data\start_big.db` (**o banco real da loja**, carimbado em `h1i2j3k4l5m6`).
4. A migration `f44a5daad28c_add_certificado_senha.py` faz `ADD COLUMN` sem checar existência → `duplicate column name: certificado_senha` → `_aplicar_uma_a_uma` tenta `stamp("+1")` → `Can't locate revision identified by '+1'` → o boot explode e a fixture falha.

⚠️ **Risco a reportar**: rodar `pytest test/` executa `create_all` + migrations **no banco de produção da máquina**. Deveria haver um `DATABASE_URL` de teste (ou o lifespan deveria ser pulado em teste). Fica como pendência fora do escopo destas specs.

## Contorno adotado para os testes novos de endpoint

`test/api/v1/fiscal/conftest.py` redefine `client` como `TestClient(app)` **sem** `with` → sem lifespan → nada toca o banco real; as rotas continuam usando o SQLite em memória via `get_db` override. As fixtures `create_test_empresa`, `db_session` e o login continuam funcionando porque só dependem das rotas.

## Segunda armadilha: `alembic/env.py` lê `settings.DATABASE_URL`

`env.py::get_url()` devolve `settings.DATABASE_URL` e **ignora** o `sqlalchemy.url` passado no `alembic.Config`. Qualquer teste que chame `command.upgrade/stamp` sem redirecionar `settings.DATABASE_URL` roda no banco real (aconteceu na sessão 1 — ver `TASK001-BACKEND.md`, restaurado). Padrão adotado: `monkeypatch.setattr(settings, "DATABASE_URL", url_tmp)` + assert de segurança antes de qualquer comando alembic.

## Gate de regressão usado nas sessões

- Rápido (a cada ciclo TDD): `pytest test/services/fiscal test/api/v1/fiscal -q`
- Antes de cada commit: `pytest test/services test/core test/db test/api/v1/fiscal -q` — todos os diretórios que **não** usam a fixture `client` com lifespan. Baseline após a sessão 1: **823 passed**.
- A suíte completa (`pytest test/`) **não é rodada** de propósito: o lifespan toca o banco real.

## Frontend

- Sem Vitest nem `*.spec.ts` antes desta sessão. Instalado em Fase 0: `vitest`, `@vue/test-utils`, `jsdom`; script `npm run test`; bloco `test` no `vite.config.ts`.
- Gates: `npx vitest run`, `npx vue-tsc --noEmit` (sem erros novos nos arquivos tocados — o projeto já tem erros de tipo pré-existentes; ver contagem abaixo), `npm run lint`.

## Terceira armadilha: `batch_alter_table` + `PRAGMA foreign_keys=ON`

O engine do app liga `foreign_keys=ON` (`app/db/session.py`). O batch do Alembic recria a tabela (move-and-copy), e o `DROP` da tabela original falha quando outra tabela a referencia com linhas — derrubou o boot na `u4v5w6x7y8z9` e deixou `_alembic_tmp_documento_fiscal` órfã (que faz a próxima tentativa falhar com "already exists"). **Regra:** migration de coluna usa `op.add_column` direto (ADD COLUMN nativo do SQLite). O teste de migration em `tmp_path` não pega isso (roda sem o pragma) — testar o boot de verdade também.
