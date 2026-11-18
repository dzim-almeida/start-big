# TASK005 — CRUD + API REST de perfis tributários (backend)

**Status:** ✅ concluída (backend) · **Data:** 2026-09-18 · **Spec:** `specs/completed/TASK005 - CRUD+API-REST-PERFIL-TRIBUTARIO.md`

## Objetivo
Schemas Pydantic, CRUD, serviço e 5 endpoints REST (`/fiscal/perfis-tributarios`) para criar/listar/ver/atualizar (replace-all das regras)/apagar perfis. Frontend (spec § 6) fica fora desta rodada.

## Verificação da spec contra o código
| Ponto da spec | O que o código diz | Decisão |
|---|---|---|
| "Endpoints delegam ao CRUD" (§ 2.2) | `rules/backend-layer-hierarchy.md` § 1: endpoint **não** importa CRUD; a seção de tributação existente viola isso, mas a spec pede lógica de serviço (404, 409 em uso, contagem) | Serviço fino `app/services/perfil_tributario.py`; CRUD em `app/db/crud/perfil_tributario.py` como a spec pede |
| Erros 404/409 | Serviços fiscais lançam `HTTPException` com `detail={"codigo","mensagem"}` (`carta_correcao.py`); `_handle_db_transaction` repassa | 409 com `codigo="PERFIL_EM_USO"` |
| Resposta `{status, data}` (rules § 1.1) | Nenhum endpoint do projeto envelopa; `response_model` direto | Seguir o código |
| Todos os endpoints com `requer_configuracao_fiscal` | Seção de tributação: LER = `get_current_active_user`, ESCREVER = master. TASK006 precisa listar perfis no cadastro de produto (usuário comum) | GET com usuário ativo; POST/PUT/DELETE com master |
| `get_perfil(db, perfil_id)` | CA-3 exige isolamento por empresa | `get_perfil(db, empresa_id, perfil_id)` — a query já filtra a empresa |
| `perfil_em_uso` "retorna False até a SPEC 3" | `ProdutoFiscal` ainda não tem `perfil_tributario_id` | `produtos_que_usam(db, perfil_id) -> list[str]` devolvendo `[]`, com o ponto de extensão documentado; TASK006 preenche |
| Listagem "sem carregar regras — só contagem" | — | Subquery `count()` agrupada por `perfil_id` |

## Plano TDD
1. RED `test/services/fiscal/test_perfil_tributario_schemas.py`: CA-1 (10 casos).
2. RED `test/services/fiscal/test_perfil_tributario_service.py`: criar, listar com contagem, obter 404 / outra empresa, replace-all, apagar, 409 em uso (monkeypatch em `produtos_que_usam`).
3. RED `test/api/v1/fiscal/test_perfis_tributarios_api.py`: 201/200/204/404/422, permissão (não-master no POST → 403).
4. GREEN: schemas → CRUD → serviço → endpoints.
5. REFACTOR + code-quality.

## Arquivos
| Arquivo | O quê |
|---|---|
| `app/schemas/perfil_tributario.py` | **novo** — `RegraPerfilTributarioBase` (UF válida/uppercase, NCM 8 dígitos, tetos nomeados), `PerfilTributarioCreate` (= `Update`; um fallback, sem duplicata), `RegraPerfilTributarioRead`, `PerfilTributarioRead`, `PerfilTributarioListItem` |
| `app/db/crud/perfil_tributario.py` | **novo** — `listar_perfis_com_contagem` (subquery count, sem carregar regras), `get_perfil(db, empresa_id, perfil_id)`, `criar_perfil`, `substituir_regras`, `deletar_perfil`, `produtos_que_usam` (vazio até a TASK006) |
| `app/services/perfil_tributario.py` | **novo** — escopo por empresa, 404, replace-all, 409 `PERFIL_EM_USO` |
| `app/api/v1/endpoints/fiscal.py` | +101 linhas: seção "PERFIS TRIBUTÁRIOS" com GET lista, POST 201, GET id, PUT, DELETE 204 |

## TDD
| Arquivo | Casos | RED → GREEN |
|---|---|---|
| `test/services/fiscal/test_perfil_tributario_schemas.py` | 26 (CA-1 completo: UF ×4 inválidas, NCM ×4, faixas ×6, zero, null, fallback 0/2, duplicata, aparar descrição…) | `ModuleNotFoundError` → ✅ |
| `test/services/fiscal/test_perfil_tributario_service.py` | 10 (criar, listar com contagem/ordem/isolamento, 404 ×3, replace-all, **replace-all mantendo a mesma UF**, deletar, 409 em uso, guard vazio) | → 1 falha (descrição "X" < 3 no próprio teste) → **1 falha real: `IntegrityError` UNIQUE no replace-all** → ✅ |
| `test/api/v1/fiscal/test_perfis_tributarios_api.py` | 11 (201 com ids, 422 sem fallback, lista enxuta, GET id, PUT, DELETE 204 → 404, 404 ×3, 401, 403 não-master no POST / 200 no GET) | → ✅ |

Gate: `pytest test/services test/core test/db test/api/v1/fiscal` → **956 passed** (909 antes).

## Bug encontrado na spec (§ 4.2) e corrigido
O `perfil.regras.clear()` + `append` sugerido pela spec **quebra no caso mais comum** — editar a alíquota de uma UF já cadastrada. A unit of work do SQLAlchemy faz os INSERTs antes dos DELETEs da mesma tabela, e a nova `(perfil, "SP", "85171200")` colide na UNIQUE com a linha antiga que ainda não saiu. Solução em `crud.substituir_regras`: `clear()` → `flush()` → atribuir as novas → `flush()`, tudo na mesma transação (o `_handle_db_transaction` ainda faz rollback se algo falhar). Teste: `test_atualizar_mantendo_a_mesma_uf_nao_colide_na_unique`.

## Critérios de aceite
| CA | Critério | Evidência | |
|---|---|---|---|
| 1 | Schemas (10 itens) | `test_perfil_tributario_schemas.py` (26) | ✅ |
| 2 | CRUD ponta a ponta: 201/lista/detalhe/PUT/204/404; 409 em uso | API (11) + serviço (10); 409 testado com `monkeypatch` em `produtos_que_usam` — o vínculo real é a TASK006 | ✅ |
| 3 | Auth, isolamento por empresa, `requer_modulo("NFE")` do router | `test_sem_token_e_401`, `test_escrita_exige_master`, `test_obter_de_outra_empresa_e_404`, `test_listar_devolve_so_os_da_empresa…`; router herda a trava | ✅ |
| 4 | Frontend | **fora desta rodada** (decisão do desenvolvedor: só backend) | ⏸ |
| 5 | Zero impacto: nenhum endpoint existente alterado, engine/payload intactos | diff de `fiscal.py` é só adição; gate 956 | ✅ |

## Desvios da spec
1. **Serviço entre endpoint e CRUD** (`app/services/perfil_tributario.py`): `rules/backend-layer-hierarchy.md` § 1 proíbe endpoint importar CRUD. A seção de tributação existente viola a regra, mas não é motivo para repetir.
2. **GET com `get_current_active_user`** (spec: master em tudo): o cadastro de produto (TASK006) precisa listar perfis, e é operado por usuário comum. Escrita continua master.
3. **`get_perfil` recebe `empresa_id`**: o isolamento (CA-3) fica na query, não só no filtro da lista.
4. **`produtos_que_usam` → `list[str]`** no lugar de `perfil_em_uso → bool`: o 409 precisa dos nomes dos produtos (spec § 5.5), então a função já devolve o que a mensagem usa.
5. **Replace-all com `flush` intermediário** — ver bug acima.
6. **Sem envelope `{status, data}`**: nenhum endpoint do projeto envelopa; `response_model` direto como o resto de `fiscal.py`.

## Pendências
- Frontend (spec § 6): `PerfisTributariosView.vue`, `PerfilTributarioForm.vue`, composables de query/mutation, rota `/fiscal/configuracoes/perfis-tributarios`, Zod espelhando `PerfilTributarioCreate` (fallback único, sem duplicata, UF/NCM, centésimos ↔ %).
- TASK006: trocar o corpo de `crud.produtos_que_usam` pela consulta em `produto_fiscal.perfil_tributario_id`.
