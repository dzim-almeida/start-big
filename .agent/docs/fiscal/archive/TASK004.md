# TASK004 — Modelagem: PerfilTributario e RegraPerfilTributario

**Status:** ✅ concluída · **Data:** 2026-09-18 · **Spec:** `specs/fiscal/completed/TASK004 - MODELAGEM-BANCO-PERFIL-TRIBUTARIO.md`

## Objetivo
Duas tabelas novas (`perfil_tributario`, `regra_perfil_tributario`) + migration, sem tocar em nada que já existe. Um perfil agrupa N regras (UF destino × NCM exceção) com alíquota interestadual, alíquota interna do destino, FCP, base dupla, MVA-ST e redução de base.

## Verificação da spec contra o código (antes de implementar)
| Ponto da spec | O que o código diz | Decisão |
|---|---|---|
| Registrar em `app/db/models/__init__.py` "para o autogenerate" | `app/db/base.py` já importa todos os módulos por `pkgutil`; o `__init__.py` é a lista explícita usada pelo `alembic/env.py`. Nenhuma migration do projeto usa `autogenerate` | Adicionado ao `__init__.py` (convenção); migration escrita à mão |
| Migration "xxxx_criar_perfil_tributario" com create_table simples | `create_all()` roda **antes** de `upgrade("head")` no boot (`tarefas.py:366/377`); toda migration decide pela **ausência** do schema antigo (`t3u4v5w6x7y8` é o modelo para tabela nova) | `if not insp.has_table(...)` por tabela; ID sequencial `v5w6x7y8z9a0` (head anterior `u4v5w6x7y8z9`) |
| `ondelete=CASCADE` deve apagar perfis ao apagar empresa | Não há `relationship` em `Empresa` para tabelas fiscais (`tributacao_padrao` também não tem); a cascata é do banco, com `PRAGMA foreign_keys=ON` ligado por listener em `app/db/session.py` | Cascata só no banco (CA-3 proíbe mexer em `Empresa`); o teste importa `app.db.session` para herdar o pragma |
| PK Integer, alíquotas em centésimos, `String(120)`, `String(2)`/`String(8)` | Confere com `ProdutoFiscal`, `AliquotaUF`, `RegraTributariaNcm` | Seguida |
| Unique `(perfil_id, uf_destino, ncm_excecao)` com NULLs | SQLite trata NULL como distinto → dois fallbacks passam pelo banco | Como a spec prevê: unicidade do fallback fica para o serviço (TASK005) |
| Dois arquivos de model (um por classe) | `tributacao.py` agrupa duas classes num arquivo, mas CA-1 exige os dois arquivos | Dois arquivos; `TYPE_CHECKING` + string no `relationship` evita ciclo |

## Arquivos
| Arquivo | O quê |
|---|---|
| `app/db/models/perfil_tributario.py` | **novo** — `PerfilTributario` (id, empresa_id FK CASCADE, descricao 120, data_criacao, data_atualizacao) + `regras` com `all, delete-orphan` |
| `app/db/models/regra_perfil_tributario.py` | **novo** — `RegraPerfilTributario` (10 colunas da spec; `server_default` em `percentual_fcp`/`calculo_base_dupla`) + `uq_regra_perfil_uf_ncm` |
| `app/db/models/__init__.py` | +2 imports (única mudança em arquivo existente) |
| `alembic/versions/v5w6x7y8z9a0_perfil_tributario.py` | **novo** — cria as duas tabelas se ausentes; downgrade dropa regra → perfil |

## TDD
| Arquivo | Casos | RED → GREEN |
|---|---|---|
| `test/db/test_perfil_tributario_modelo.py` | 11 (nomes, colunas/tipos/FKs ×2, unique, `doc=` em todas, defaults, duplicata → IntegrityError, delete-orphan, perfil → regras, empresa → perfil → regra pelo banco, `__repr__`) | `ModuleNotFoundError` → ✅ 11/11 |
| `test/db/test_migracao_perfil_tributario.py` | 5 (banco antigo ganha as tabelas, defaults num INSERT cru, FKs/unique/índices, tabelas já criadas pelo `create_all` não quebram, downgrade na ordem) | `Can't locate revision` → 1 falha (cache de schema do SQLite no pool — ver armadilha) → ✅ 5/5 |

Boot de verdade (fora do pytest, `DATABASE_URL`+`BIGPDV_DATA_DIR` num tmp): banco carimbado em `u4v5w6x7y8z9` sem as tabelas → `create_all` cria → `aplicar_migracoes` pula sem "already exists" → head `v5w6x7y8z9a0`. ✅

Gate: `pytest test/services test/core test/db test/api/v1/fiscal` → **909 passed** (893 antes).

## Critérios de aceite
| CA | Critério | Evidência | |
|---|---|---|---|
| 1 | Models, campos, relacionamentos, unique | `test_colunas_*`, `test_regra_tem_unique_*`, `test_remover_regra_da_colecao_*` | ✅ |
| 2 | Migration aplica em banco limpo; downgrade na ordem; nada existente alterado | `test_banco_antigo_*`, `test_downgrade_*` (`empresas` intacta) | ✅ |
| 3 | Zero impacto: só `__init__.py` tocado; cascata, engine, payload, frontend intactos | `git status` — 5 arquivos novos + `__init__.py`; gate 909 | ✅ |
| 4 | Integer PK, centésimos, `doc=` em todos os campos, `__repr__`, snake_case singular | `test_todas_as_colunas_tem_doc`, `test_repr_e_legivel`, `test_tabelas_tem_os_nomes_da_spec` | ✅ |
| 5 | CASCADE empresa → perfil → regra | `test_apagar_empresa_apaga_perfis_e_regras_pelo_banco`, `test_constraints_no_banco` | ✅ |

## Desvios da spec
1. **`server_default`** em `percentual_fcp` e `calculo_base_dupla` (a spec só pede `default`): garante o valor num INSERT cru e no `reconciliar_colunas()` do boot, e casa com o DDL da migration.
2. **Sem `autogenerate`**: o projeto não usa; migration à mão no padrão `t3u4v5w6x7y8`.
3. **Índice em `id`** (`ix_<tabela>_id`) além dos pedidos — é o padrão de todas as tabelas do projeto.

## Armadilha registrada
Teste de migration que reflete FKs por um engine cujo pool já tinha conexão aberta antes do Alembic: o SQLite mantém o schema em cache e `PRAGMA foreign_key_list` numa tabela nova devolve **vazio** (um `SELECT` em `sqlite_master` força o reload, por isso `get_table_names` "conserta"). Solução: `engine.dispose()` antes de `sa.inspect(engine)` (`_inspector` no teste).

## Pendências para as próximas tasks
- Unicidade da regra de fallback (dois `NULL/NULL`) — serviço, TASK005.
- Validação de UF válida e NCM 8 dígitos — schema Pydantic, TASK005.
- Nenhuma parte de interface nesta spec.
