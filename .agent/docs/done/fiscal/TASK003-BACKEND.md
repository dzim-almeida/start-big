# TASK003-BACKEND — NF-e de devolução (finalidade 4)

**Status:** ✅ concluída · **Data:** 2026-09-17 · **Spec:** `specs/completed/TASK003-BACKEND-NotaDevolucao.md` · **ADR:** [ADR-002](../adrs/ADR-002_devolucao_a_partir_do_snapshot.md)

## Objetivo
Emitir NF-e de devolução (modelo 55, entrada, finalidade 4), total ou parcial, a partir de NF-e/NFC-e autorizada, com os 4 pilares da Focus/SEFAZ, controle de saldo por item e entrada no estoque quando autorizada.

## Arquivos
| Arquivo | O quê |
|---|---|
| `app/db/models/documento_fiscal.py` | `finalidade_emissao`, `documento_referenciado_id`, `chave_documento_referenciado`, `devolver_estoque` |
| `app/db/models/documento_fiscal_item.py` | `quantidade_devolvida_acumulada` |
| `app/core/enum.py` | `MovimentacaoOrigem.DEVOLUCAO` |
| `alembic/versions/u4v5w6x7y8z9_campos_devolucao.py` | por coluna, `_tem_coluna → skip` |
| `app/schemas/emissao_fiscal.py` | `ItemDevolucaoRequest`, `DestinatarioAvulsoRequest` (sanitiza CPF/CNPJ/CEP, IE p/ contribuinte), `EmissaoDevolucaoRequest` |
| `app/schemas/documento_fiscal.py` + `services/documento_fiscal.py` | `finalidade_emissao`, `documento_referenciado_id`, `chave_documento_referenciado`, `totalmente_devolvida`; por item `quantidade_milesimos`, `quantidade_devolvida_acumulada` |
| `app/services/fiscal/derivacao/cfop.py` | `cfop_devolucao(saida, interestadual)` + mapa `SUFIXOS_DEVOLUCAO_DE_VENDA` |
| `app/services/fiscal/payload_builder.py` | `montar_payload_devolucao`, `_montar_itens_devolucao`, `_montar_destinatario_avulso` |
| `app/services/fiscal/devolucao.py` | **novo** — pré-requisitos, saldos, destinatário, motor, emissão, `aplicar_efeitos_autorizacao` |
| `app/services/fiscal/emissao.py` | `consultar_documento` aplica os efeitos na transição → AUTORIZADA (polling) |
| `app/api/v1/endpoints/fiscal.py` | `POST /documentos/{id}/devolucao` (`requer_modulo_fiscal`) |

## TDD
| Arquivo | Casos | RED → GREEN |
|---|---|---|
| `test/services/fiscal/test_emissao_devolucao.py` | 33 (CFOP ×10, schemas ×3, payload ×3, documento ×2, saldos ×4, destinatário ×3, origem ×4, estoque ×2, rede/rejeição ×2) | `ModuleNotFoundError` → 11 falhas (destinatário; fixture sem venda) → 1 (produto_id no snapshot) → 1 (FK venda_id) → ✅ |
| `test/api/v1/fiscal/test_devolucao_api.py` | 3 | ✅ |
| `test/db/test_migracao_campos_devolucao.py` | 2 | ✅ |

Gate: `pytest test/services test/core test/db test/api/v1/fiscal` → **890 passed** (852 antes).

## Critérios de aceite (spec § 6)
| # | Critério | Teste | |
|---|---|---|---|
| 1 | Payload: modelo 55, `tipo_documento 0`, `finalidade_emissao 4`, forma 90 zerada, `notas_referenciadas` | `test_payload_tem_os_quatro_pilares` | ✅ |
| 2 | CFOP 5102→1202, 5405→1411, 6102→2202 | `test_cfop_de_devolucao` (10 casos) + `test_itens_da_devolucao_total_espelham_o_snapshot…` | ✅ |
| 3 | Excedente → 422 | `test_quantidade_acima_do_saldo_e_422` | ✅ |
| 4 | Duas parciais de 50% ok; terceira → 422 | `test_duas_parciais_de_50_por_cento_e_a_terceira_e_barrada` | ✅ |
| 5 | NFC-e anônima: 422 sem avulso; sucesso com | `test_nfce_anonima_*` (serviço e API) | ✅ |
| 6 | Falha de rede: número consumido e commitado; INDETERMINADA | `test_falha_de_rede_consome_o_numero_e_fica_indeterminada` | ✅ |
| + | Estoque entra só quando autorizada e `devolver_estoque` | `test_autorizada_devolve_os_itens_ao_estoque`, `test_devolver_estoque_false…`, `test_rejeicao_da_sefaz_nao_consome_saldo` | ✅ |

## Desvios da spec
1. **Serviço em arquivo próprio** (`devolucao.py`), não em `emissao.py` (1300+ linhas) — code-quality.
2. **Tributos pelo motor** sobre dados congelados do snapshot, não "multiplicar por `fator_proporcao`" — ver ADR-002 (o snapshot não tem PIS/COFINS).
3. **Coluna `devolver_estoque`** adicionada (não prevista): a decisão precisa sobreviver até o polling.
4. **`origem_tipo`/`origem_id` da devolução copiam os da origem** (venda) — permite o drawer e o espelho da venda encontrarem a devolução; a spec não dizia.
5. **Migration manual idempotente**; "PostgreSQL" e `autogenerate` da spec não se aplicam (SQLite).
6. **`interestadual` fixo em `False`**: o motor bloqueia operação interestadual na emissão normal; o gancho existe em `emitir_devolucao`.
7. `commit` antes do HTTP (spec § 5.5): quem comita é `_handle_db_transaction` (rule backend-layer § 7); o `flush` + número reservado já garantem que uma falha de rede deixa o registro INDETERMINADA com o número consumido (testado).

## Limitações conhecidas
- Notas anteriores a 05/09/2026 (sem snapshot de itens) não são devolvíveis pelo sistema (422 explicativo).
- `_parear_itens` casa por `codigo_produto`; nota com o mesmo produto em dois itens acumula no primeiro.
