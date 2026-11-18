# TASK007 — Motor de cálculo DIFAL (não contribuinte)

**Status:** ✅ concluída · **Data:** 2026-09-18 · **Spec:** `specs/fiscal/completed/TASK007 - MOTOR-DIFAL.md`

## Objetivo
`calcular_difal` (base simples e dupla, FCP), DTOs expandidos, resolver consultando o perfil (TASK006) e liberando a operação interestadual **só** para não contribuinte com perfil em todos os itens, engine com o passo DIFAL após o ICMS, consolidador somando DIFAL/FCP fora do `valor_total_nota`. Payload não muda (TASK009).

## Verificação da spec contra o código
| Ponto da spec | O que o código diz | Decisão |
|---|---|---|
| Só descreve regime normal (ICMS próprio pela alíquota interestadual, `icms.base_calculo`) | No Simples o ICMS sai por CSOSN com base 0; sobrescrever `aliquota_icms` afetaria o crédito do CSOSN 101. Legal: STF ADI 5464 suspendeu o DIFAL de partilha para remetente do Simples — não há `ICMSUFDest` | **Simples Nacional: libera a operação sem DIFAL e sem exigir perfil** (premissa legal a confirmar com o contador — ver "Decisões"). Regime normal segue a spec |
| `calcular_difal(base_icms=icms.base_calculo)` + nota IMPORTANT sobre CST 20 | `ResultadoICMS.base_calculo` já vem reduzida no CST 20; `reducao_base` fica preenchido | Base do DIFAL = base cheia (`_base_calculo_padrao`) quando `icms.reducao_base` está preenchido |
| CST 40/41/60 em operação interestadual | `icms.base_calculo == 0` → DIFAL 0 | Aceito: isento/ST não gera diferencial; nada a fazer |
| `_cliente_nao_contribuinte` "mesma lógica do payload builder" | `payload_builder.py:166-179`: PJ com `ie` → 1, senão 9; PF → 9; sem cliente → 9 | Igual |
| Teste existente `test_operacao_nao_presencial_interestadual_continua_travada` (Simples + PF + sem perfil, espera erro `uf_destinatario`) | É exatamente o cenário que a spec libera | Teste passa a afirmar o novo comportamento (Simples → passa sem DIFAL); a trava continua testada para contribuinte |
| Spec pede `from .calculators.difal import` dentro do loop do engine | Imports no topo, como os outros calculators | Topo |

## Plano TDD
1. RED `test/services/fiscal/test_tax_engine_difal.py`: calculadora (cenários A–E, ValueError, negativo→0) + engine ponta a ponta (pipeline, totais, `valor_total_nota` intacto, CST 20 base cheia, item interno → None).
2. RED `test/services/fiscal/test_resolver_interestadual.py`: `_cliente_nao_contribuinte` (4), resolver: PF+perfil → DIFAL e ICMS pela interestadual; sem perfil → erro `perfil_tributario_id`; perfil sem regra → erro; PJ com IE → trava; PJ sem IE → DIFAL; interna/presencial → inalterado; Simples → sem DIFAL, sem erro.
3. GREEN → REFACTOR → code-quality.

## Arquivos
| Arquivo | O quê |
|---|---|
| `tax_engine/calculators/difal.py` | **novo** — `ResultadoDIFAL` + `calcular_difal` (base simples/dupla, FCP, nunca negativo, `ValueError` em ≥100%) |
| `tax_engine/types.py` | `ItemEntrada.difal_*` (4, opcionais), `ImpostosItem.difal_*`/`fcp_*` (8, `None` em operação interna), `TotaisNota.valor_difal/valor_fcp/base_calculo_fcp` (default 0) |
| `tax_engine/engine.py` | passo 2b `_calcular_difal_do_item` entre ICMS e PIS/COFINS; base cheia quando `icms.reducao_base` (CST 20) |
| `tax_engine/consolidador.py` | soma DIFAL/FCP/base FCP; **fora** do `valor_total_nota` |
| `tax_engine/resolver.py` | `_cliente_nao_contribuinte`, `_uf_destino_interestadual` (substitui a trava), `_resolver_difal` + `_DadosDIFAL`; ICMS próprio pela alíquota interestadual quando há DIFAL |
| `test/services/fiscal/test_gate_e_payload.py` | teste da trava reescrito para o comportamento novo (regime normal sem perfil → barrado; Simples → passa) |

## TDD
| Arquivo | Casos | RED → GREEN |
|---|---|---|
| `test/services/fiscal/test_tax_engine_difal.py` | 13 — calculadora: cenários A, B, C (137,86 / 25,16 exatos), D, negativo → 0, ≥100% → `ValueError`, dataclass com 2 casas; engine: cenário E, pipeline, totais fora do vNF, frete na base, **CST 20 base cheia**, base dupla | `ModuleNotFoundError` → ✅ |
| `test/services/fiscal/test_resolver_interestadual.py` | 11 — `_cliente_nao_contribuinte` ×2 (PF, PJ sem IE, IE vazia, sem cliente / PJ com IE); PF+perfil → DIFAL e ICMS 12%; fallback por UF; PJ sem IE; sem perfil → `perfil_tributario_id` item 2; sem regra → erro com a UF; contribuinte → `uf_destinatario`; interna e balcão inalteradas; **Simples sem DIFAL e sem perfil** | `ImportError` → ✅ |

Gate: `pytest test/services test/core test/db test/api/v1/fiscal` → **1006 passed** (982 antes; 4 do teste antigo da trava reescritos).

## Critérios de aceite
| CA | Critério | Evidência | |
|---|---|---|---|
| 1 | Calculadora (A–D, ValueError, pura, PRECISAO) | 7 testes da calculadora | ✅ |
| 2 | DTOs retrocompatíveis; cenário E | `test_cenario_e_*`; nenhum chamador alterado; 982 testes anteriores passam | ✅ |
| 3 | Resolver: perfil → DIFAL; sem perfil → erro; contribuinte → trava; interna/balcão inalteradas; `_cliente_nao_contribuinte` | `test_resolver_interestadual.py` | ✅ |
| 4 | Pipeline ICMS → DIFAL → PIS/COFINS; base sem redução; totais; fora do vNF; `valor_icms` pela interestadual | `test_pipeline_*`, `test_cst_20_*`, `test_totais_*` | ✅ |
| 5 | Números A–E | exatos (C: 137,86 e 25,16 sem tolerância) | ✅ |
| 6 | Testes unitários + integração + existentes | 24 novos; gate | ✅ |
| 7 | `payload_builder.py` não tocado; `local_destino` = 1 | `git status` | ✅ |

## Decisões (fora da spec) — confirmar com o contador
1. **Simples Nacional não calcula DIFAL e não exige perfil.** A spec só trata do regime normal. Para remetente optante do Simples, o STF (ADI 5464) suspendeu a cláusula nona do Convênio 93/2015 — não há DIFAL de partilha nem `ICMSUFDest`. A operação interestadual a não contribuinte passa a ser **liberada** para o Simples (antes era travada por "DIFAL não implementado", motivo que não se aplica). Se a contabilidade discordar, basta trocar o `if simples_nacional: return None` em `_uf_destino_interestadual` por `raise`. ⚠️ Até a TASK008 (CFOP 6xxx) e TASK009 (`idDest`), uma nota interestadual emitida sairia com CFOP 5xxx e `local_destino=1` — mesma condição transitória do regime normal prevista pela spec.
2. **CST 20**: DIFAL sobre a base cheia (a spec pedia validar com a contabilidade) — implementado como a nota IMPORTANT descreve.
3. **CST 40/41/60 interestaduais**: `icms.base_calculo == 0` → DIFAL 0. Não bloqueia; assume que isenção/ST já recolhido não gera diferencial.

## Desvios da spec
1. Trava reestruturada em `_uf_destino_interestadual` (devolve a UF ou `None`) em vez de flags no corpo do `resolver_aliquotas_venda` — a função já tinha 100+ linhas (code-quality § 3.2).
2. Imports dos calculators no topo do `engine.py` (a spec sugeria import dentro do loop).
3. `_DadosDIFAL` (dataclass congelada) no lugar de 4 variáveis soltas no loop.
4. `getattr(fiscal, "perfil_tributario_id")` basta: `FiscalEfetivo` carrega o campo (TASK006), não é preciso voltar ao `produto.fiscal`.

## Pendências
- TASK008: rota do contribuinte (ICMS-ST) em `_uf_destino_interestadual`; CST/CFOP interestaduais.
- TASK009: `payload_builder` lê `ImpostosItem.difal_*`/`fcp_*` → `<ICMSUFDest>`; `idDest=2`; totais `vICMSUFDest`, `vFCPUFDest`.
