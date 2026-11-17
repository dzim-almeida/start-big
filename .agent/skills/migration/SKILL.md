---
name: migration
description: Como criar, revisar, aplicar e testar migrações Alembic no backend do StartBig (SQLAlchemy, SQLite com render_as_batch, aplicação automática no startup). Cobre o registro de models no env.py, a revisão manual do autogenerate, o ciclo upgrade/downgrade em banco descartável e as regras para não quebrar o histórico nem o banco dos clientes. Use sempre que um model for criado ou alterado.
---

# Skill `migration` — Alembic no StartBig

> Caminhos com `@/` são relativos a `.agent/`. Comandos rodam em `backend-fastapi/` com a venv ativa.

**O que é uma migração?** Um arquivo Python que descreve **uma mudança no banco** (criar tabela, adicionar coluna). O Alembic guarda no banco qual foi a última migração aplicada (tabela `alembic_version`) e aplica as que faltam, em ordem. Assim o banco do cliente acompanha o código quando o app é atualizado.

## 0. Configuração atual

- Migrações em `backend-fastapi/alembic/versions/`; configuração em `alembic.ini` e `alembic/env.py`.
- O `env.py` **lista os models por `import`** (para o autogenerate enxergar as tabelas) e usa `render_as_batch=True`, porque o SQLite não suporta todo `ALTER TABLE`: o Alembic recria a tabela em "lote" quando preciso.
- **A URL do banco** vem de `settings.DATABASE_URL` (`app/core/config.py`). Em desenvolvimento, o `.env` aponta para `./start_big.db`; **a variável de ambiente `DATABASE_URL` vence o `.env`** — é assim que se aponta para um banco descartável.
- **No startup do app** (`app/core/tarefas.py` → `app/db/migrations.py`): primeiro roda `create_all()` (cria tabelas que faltam a partir dos models), **depois** `aplicar_migracoes()`, que avança a cadeia **uma migração por vez** e, se uma delas esbarra em tabela que o `create_all` já criou ("already exists"), carimba só aquela e segue.
- **Não há backup automático** antes de migrar. O banco do cliente fica em `%LOCALAPPDATA%\StartBigERP\data\start_big.db`.

---

## 1. Fluxo padrão

### 1.1. Alterar o model

Edite o model em `app/db/models/`. Use tipos que o SQLite entende; dinheiro com `Numeric`; texto com tamanho; `nullable` explícito. Toda tabela de negócio leva `empresa_id` (FK + índice). Comente a coluna com `doc="..."` quando o nome não for óbvio.

```python
# Exemplo comentado
class Marca(Base):
    __tablename__ = "marcas"                                   # nome da tabela no banco

    id: Mapped[int] = mapped_column(primary_key=True)          # chave primária (número que se auto-incrementa)
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id"), nullable=False, index=True  # de qual empresa é; indexado para as consultas filtrarem rápido
    )
    nome: Mapped[str] = mapped_column(String(80), nullable=False)  # texto de até 80 caracteres, obrigatório
```

### 1.2. Registrar o model no `env.py`

Model **novo** precisa de um `import app.db.models.<arquivo>` na lista do `alembic/env.py` (e, se for pacote, no `__init__` dele). Sem isso, o autogenerate não vê a tabela e gera migração vazia ou "apagando" a tabela.

### 1.3. Conferir o estado do banco (descartável!)

Nunca valide migração no `start_big.db` da loja nem no seu banco de trabalho com dados. Crie um banco só para o teste (a variável de ambiente vence o `.env`):

```bash
# Git Bash / Linux / Mac
export DATABASE_URL="sqlite:///./tmp_migracao.db"
# PowerShell:  $env:DATABASE_URL = "sqlite:///./tmp_migracao.db"

alembic upgrade head      # leva o banco descartável até a última migração atual
alembic current           # mostra em qual revisão ele está
alembic heads             # mostra a(s) ponta(s) da cadeia: deve haver UMA só
```

`alembic heads` mostrando **duas** pontas = duas migrações com o mesmo "pai" (conflito de ramo). Resolva antes de seguir (`alembic merge`), perguntando ao usuário.

### 1.4. Gerar a revisão

```bash
alembic revision --autogenerate -m "descricao_curta_em_snake_case"
```

O arquivo nasce em `alembic/versions/`. **Não edite nem apague migração já aplicada ou publicada** (§2).

### 1.5. Revisar o arquivo gerado (obrigatório)

O autogenerate **erra**. Leia o arquivo inteiro e confira:

- [ ] Só tem o que você mudou (nenhuma tabela "apagada" por falta de `import` no `env.py`).
- [ ] Coluna nova `NOT NULL` em tabela com dados tem `server_default` (senão a migração falha no banco do cliente).
- [ ] Alteração de coluna existente usa `with op.batch_alter_table("tabela") as batch_op:` (exigência do SQLite).
- [ ] `downgrade()` desfaz exatamente o `upgrade()`.
- [ ] Índices e constraints têm **nome explícito** (para poder removê-los depois).
- [ ] Migração de **dados** (copiar, converter) está separada da migração de **estrutura**, ou bem comentada.
- [ ] **Decide pelo schema antigo, não pela ausência do novo.** Como o `create_all` roda antes e já pode ter criado a tabela vazia, uma migração que só roda "se a tabela nova não existe" **nunca roda**. Teste a presença do que é **antigo** (tabela/coluna que será migrada). Modelo a seguir: `965c71a2da9a_refactor_equipamento_para_objeto_servico.py`.
- [ ] Idempotência: rodar de novo num banco que já tem a mudança não explode (`inspect(bind)` antes de criar).

### 1.6. Aplicar e provar que volta

No banco descartável, com `DATABASE_URL` apontando para ele:

```bash
alembic upgrade head       # aplica a migração nova
alembic downgrade -1       # desfaz só a última (confirma que o downgrade funciona)
alembic upgrade head       # aplica de novo (confirma que dá para repetir)
```

**Rode um comando por vez e leia o resultado de cada um.** Encadear com `&&` e `| tail` esconde falha: um `upgrade` que falha e um `downgrade -1` que segue desfaz a migração **anterior**.

### 1.7. Testar

- [ ] `alembic check` → "No new upgrade operations detected" (models e migrações batem).
- [ ] Teste de pytest para a **regra** que depende da coluna/tabela nova (skill `tdd`). O `conftest.py` usa `create_all` em memória; ele **não** testa a migração em si.
- [ ] Para migração que **converte dados**: monte um banco descartável no schema **antigo** com algumas linhas, aplique a migração e confira as linhas convertidas.
- [ ] Apague o banco descartável que **você** criou (`tmp_migracao.db`), e `unset DATABASE_URL` / limpe a variável.

---

## 2. Regras que não se quebram

1. **Nunca editar nem apagar** uma migração já aplicada em outro lugar (já commitada/publicada ou que já rodou no banco de algum cliente). Erro nela → **nova migração** corrigindo.
2. **Uma pasta, uma cadeia:** sempre uma única ponta (`alembic heads`).
3. **Nome do arquivo do banco não muda** (`start_big.db`). Renomear faz o `create_all` criar um banco vazio ao lado do real. Se for inevitável, acrescente o nome antigo em `LEGACY_DB_FILENAMES` (`app/core/config.py`) no mesmo commit.
4. **Nada de `DROP`/`TRUNCATE` de tabela com dados** sem spec, plano de backup e aprovação do usuário.
5. **Migração é a única forma de mudar schema** em produção. `create_all` só cria tabela que falta; **nunca** conserta coluna que falta em tabela existente.
6. **Fora do app, não use o banco do cliente.** Nem para "só olhar". Peça ao usuário um backup.
7. **Models legados** com nomes de constraint automáticos: não renomeie constraint existente sem necessidade.

---

## 3. Mudanças arriscadas (tabelas com dados)

| Mudança | Cuidado |
|---------|---------|
| Coluna `NOT NULL` nova | `server_default` obrigatório, ou migrar em 3 passos (adiciona nula → preenche → exige) |
| Renomear coluna/tabela | Usar `batch_alter_table`; ajustar models, crud, schemas, frontend e specs na mesma tarefa |
| Mudar tipo | Em SQLite, o lote recria a tabela copiando os dados: teste com linhas reais fictícias |
| Dividir/unir tabelas | Migração de dados explícita, com contagem antes/depois conferida no teste |
| Índice `UNIQUE` novo | Antes, conferir se já existem duplicados; senão a migração quebra no banco do cliente |
| Apagar coluna | Só depois de uma versão inteira sem uso; avisar o usuário |

Qualquer uma destas → **trilha completa** e pergunta ao usuário antes de implementar.

---

## 4. Produção (banco do cliente)

- A migração roda **sozinha** quando o cliente abre o app atualizado. Não há botão "voltar".
- Por isso: migração **pequena, testada em banco com dados fictícios e idempotente**.
- Antes de um release que traz migração de dados, **peça ao usuário** para orientar o cliente a copiar o `start_big.db` (backup manual) ou use a rotina de backup do sistema (módulo `backup`).
- O backend alterado precisa ir no instalador: lembre o usuário de `npm run build:sidecar` (`AGENT.md` §7).
