# TASK006 — Vínculo ProdutoFiscal → PerfilTributario + resolver de regra (backend)

**Status:** ✅ concluída (backend) · **Data:** 2026-09-18 · **Spec:** `specs/completed/TASK006 - VINCULO-PRODUTO-PERFIL-TRIBUTARIO.md`

## Objetivo
FK `produto_fiscal.perfil_tributario_id` (SET NULL) + migration, campo nos schemas do produto, `resolver_regra_perfil` (match por especificidade em uma query), e o guard real de exclusão de perfil. Nenhum cálculo novo; a trava interestadual continua. Frontend (spec § 7) fora desta rodada.

## Verificação da spec contra o código
| Ponto da spec | O que o código diz | Decisão |
|---|---|---|
| "Omitir `perfil_tributario_id` no JSON não altera o vínculo" (CA-2) | `crud.produto_fiscal.upsert` faz `ProdutoFiscalUpdate(**dados.model_dump())` — reinstancia com TODOS os campos, anulando o `exclude_unset` do `update()`. Hoje omitir qualquer campo já o zera. O formulário do frontend não conhece o campo novo → cada save do produto desvincularia o perfil | Corrigir `upsert` preservando o unset (`model_dump(exclude_unset=True)`); o frontend manda o objeto completo, então nada muda para ele. Teste cobre |
| Migration com `op.add_column` + `ForeignKey` | Baseline (armadilha 3): nunca `batch_alter_table` no upgrade com `foreign_keys=ON`; `ADD COLUMN … REFERENCES` é nativo no SQLite; decidir pela ausência da coluna (`u4v5w6x7y8z9` é o modelo) | `_tem_coluna → skip`, índice só se a coluna nasceu agora; downgrade em batch |
| `perfil_em_uso → bool` (§ 6) | TASK005 já deixou `produtos_que_usam → list[str]` porque o 409 lista os nomes | Preencher `produtos_que_usam` com a consulta real (`produto_fiscal ⨝ produtos`) |
| `resolver_regra_perfil` com `db.query` | Rules: `select()` moderno | Mesmo algoritmo (uma query, `ORDER BY` por especificidade), em `select()` |
| Perfil de outra empresa no `perfil_tributario_id` | Nada impede vincular por id um perfil alheio | Serviço valida que o perfil é da empresa (422) — coerente com CA-3 da TASK005 |
| `ProdutoFiscalRead.perfil_tributario_descricao` (opcional) | Sem frontend nesta rodada | YAGNI agora; fica na pendência da rodada de interface |
| CA-6: cascata (`tributacao.py`) e tax engine intactos | `FiscalEfetivo` copia campos por lista explícita — o novo campo não entra nela | Não tocar; a TASK007 decide como o motor lê `perfil_tributario_id` (do `produto.fiscal`, não do efetivo) |

## Plano TDD
1. RED `test/db/test_migracao_perfil_no_produto.py`: coluna nasce com FK SET NULL + índice; já existente não quebra; downgrade.
2. RED `test/services/fiscal/test_perfil_resolver.py`: CA-3 (6 casos) + apagar perfil no banco seta NULL no produto.
3. RED `test/services/fiscal/test_produto_fiscal_perfil.py`: vincular, desvincular com null, omitir mantém, perfil alheio 422, `produtos_que_usam` real, DELETE 409 via serviço.
4. GREEN → REFACTOR → code-quality.

## Arquivos
| Arquivo | O quê |
|---|---|
| `app/db/models/produto_fiscal.py` | `perfil_tributario_id` (FK `SET NULL`, index) + relationship `perfil_tributario` |
| `app/schemas/produto_fiscal.py` | `perfil_tributario_id: Optional[int]` em `ProdutoFiscalBase` (Create/Update/Read) |
| `alembic/versions/w6x7y8z9a0b1_perfil_tributario_no_produto.py` | **novo** — `ALTER TABLE … ADD COLUMN … REFERENCES … ON DELETE SET NULL` cru (o `op.add_column` com `ForeignKey` tenta `ADD CONSTRAINT`, que o SQLite não tem); pula se a coluna existe; downgrade em batch |
| `app/services/fiscal/tax_engine/perfil_resolver.py` | **novo** — `resolver_regra_perfil(db, perfil_id, uf, ncm)`: uma `select()` com `ORDER BY` por especificidade |
| `app/db/crud/produto_fiscal.py` | `upsert` preserva o unset no update (**bug pré-existente**: reinstanciar com o dump completo zerava os campos omitidos) |
| `app/db/crud/perfil_tributario.py` | `produtos_que_usam` real (`produtos ⨝ produto_fiscal`) |
| `app/services/produto_fiscal.py` | `_validar_perfil_da_empresa` → 422 `PERFIL_TRIBUTARIO_INVALIDO` |
| `app/services/fiscal/tributacao.py` | `perfil_tributario_id` em `FiscalEfetivo` e em `CAMPOS_DO_PRODUTO` (exigido pelo teste de contrato existente; sem cascata) |

## TDD
| Arquivo | Casos | RED → GREEN |
|---|---|---|
| `test/db/test_migracao_perfil_no_produto.py` | 3 (coluna NULL + FK SET NULL + índice; já existente não quebra; downgrade preserva as linhas) | `Can't locate revision` → `NotImplementedError: No support for ALTER of constraints in SQLite` (op.add_column+FK) → inspector não lê `ON DELETE` de FK inline (teste passou a ler o PRAGMA) → ✅ |
| `test/services/fiscal/test_perfil_resolver.py` | 9 (CA-3 completo + UF normalizada + sem fallback → None + `(NULL, NCM)` ignorada + **uma única query**) | `ModuleNotFoundError` → contador pegava o reload do `perfil.id` expirado (teste) → ✅ |
| `test/services/fiscal/test_produto_fiscal_perfil.py` | 12 (coluna/FK, relationship, vincular, null desvincula, **omitir mantém**, perfil alheio 422, inexistente 422, `produtos_que_usam`, 409, SET NULL no banco, efetivo carrega o perfil sem cascata) | → ✅ |
| `test/api/v1/fiscal/test_produto_perfil_api.py` | 3 (PUT/GET `/produtos/{id}/fiscal` vincula/omite/desvincula; 422 com código; DELETE do perfil vinculado → 409 com o nome do produto) | → ✅ |

Boot de verdade (loja carimbada em `v5w6x7y8z9a0`, `produto_fiscal` com linha e sem a coluna): coluna nasce NULL, FK `SET NULL` no PRAGMA, linha intacta, head `w6x7y8z9a0b1`. ✅

Gate: `pytest test/services test/core test/db test/api/v1/fiscal` → **982 passed** (956 antes). O teste de contrato `test_efetivo_tem_os_mesmos_nomes_de_campo_do_produto_fiscal` quebrou ao adicionar a coluna e foi o que levou o campo ao `FiscalEfetivo`.

## Critérios de aceite
| CA | Critério | Evidência | |
|---|---|---|---|
| 1 | FK nullable SET NULL, relationship lazy, índice, migration + downgrade | `test_coluna_e_fk_set_null_com_indice`, `test_relationship_carrega_o_perfil`, migration ×3 | ✅ |
| 2 | Update aceita; `null` desvincula; omitir mantém; Read expõe | serviço ×3 + API | ✅ |
| 3 | Match por especificidade, `None` p/ perfil inexistente, uma query | `test_perfil_resolver.py` (9) | ✅ |
| 4 | Guard real: `produtos_que_usam`, DELETE 409 | `test_produtos_que_usam_lista_os_nomes`, `test_excluir_perfil_em_uso_e_409`, API 409 | ✅ |
| 5 | Frontend (select na aba fiscal) | **fora desta rodada** | ⏸ |
| 6 | Trava interestadual ativa; emissão interna não consulta perfil; engine/payload intactos | `resolver.py`/`engine.py`/`payload_builder.py` não tocados; gate 982 (inclui `test_tax_engine_*`, `test_gate_e_payload`) | ✅ |

## Desvios da spec
1. **`crud.produto_fiscal.upsert` corrigido** para preservar o unset (CA-2 era impossível sem isso; e sem a correção todo save do formulário atual, que não manda o campo, desvincularia o perfil). O frontend envia o objeto completo, então nada muda para ele.
2. **Migration com SQL cru** (`ALTER TABLE … ADD COLUMN … REFERENCES`): a forma `op.add_column(sa.Column(..., sa.ForeignKey(...)))` da spec § 8.1 não roda no SQLite.
3. **Validação do perfil da empresa** (422) no `upsert_dados_fiscais` — a spec não pede, mas sem isso um id de perfil alheio passaria.
4. **`perfil_tributario_id` no `FiscalEfetivo`/`CAMPOS_DO_PRODUTO`** — CA-6 diz "cascata não alterada", mas o teste de contrato do projeto exige paridade de campos, e é o que permite à TASK007 ler `fiscal.perfil_tributario_id` de qualquer um dos dois objetos. Sem semântica de cascata (só do produto).
5. **`produtos_que_usam → list[str]`** mantido (TASK005) no lugar de `perfil_em_uso → bool`.
6. **`ProdutoFiscalRead.perfil_tributario_descricao`** (opcional na spec) não adicionado — YAGNI sem a tela.

## Armadilhas registradas
- `op.add_column` + `ForeignKey` no SQLite → `NotImplementedError` (ALTER of constraints). Usar o `ADD COLUMN … REFERENCES` nativo via `op.execute`.
- O inspector do SQLAlchemy não devolve `ondelete` de FK inline acrescentada por `ADD COLUMN`; `PRAGMA foreign_key_list` devolve — e é o que o SQLite aplica.
- Contar queries com `before_cursor_execute`: capture ids/atributos **antes** de ligar o listener, senão o reload de objeto expirado pelo `commit` entra na conta.

## Pendências
- Frontend (spec § 7): select "Perfil Tributário (Interestadual)" no topo da aba fiscal do produto, opção "Nenhum" → `null`; `usePerfisTributariosQuery` (TASK005-FE); Zod do `ProdutoFiscalUpdate` ganha `perfil_tributario_id`.
- TASK007: o motor lê `fiscal.perfil_tributario_id` (ProdutoFiscal ou FiscalEfetivo) e chama `resolver_regra_perfil`; a trava de `resolver.py:130-139` sai lá.
