# TASK008 — Motor ICMS-ST + derivação de CST/CFOP interestadual

**Status:** ✅ concluída · **Data:** 2026-09-19 · **Spec:** `specs/completed/TASK008 - MOTOR-ICMS-ST+DERIVACAO-CST-CFOP-INTERESTADUAL.md`

## Objetivo
`calcular_icms_st` (MVA, redução de base, dedução do ICMS próprio, piso zero), ST **dentro** do `valor_total_nota`, derivação determinística de CFOP (6102/6108/6404…) e CST/CSOSN (10/70, 201/202) para a operação interestadual, e a rota do contribuinte no resolver — a trava cai de vez quando há perfil. Payload intacto (TASK009).

## Verificação da spec contra o código
| Ponto da spec | O que o código diz | Decisão |
|---|---|---|
| "Ajusta o CFOP efetivo do item" no resolver | `payload_builder.py:328` lê `fiscal.cfop_padrao`; CST vem de `imp.icms_situacao_tributaria` (engine). `ImpostosItem` não tem CFOP | `ItemEntrada.cfop` recebe o derivado; `ImpostosItem.cfop` novo (copiado) para a TASK009 usar. Payload não muda agora |
| CST 10/70, CSOSN 201/202 | `icms.py` rejeita (`CSTNaoSuportadoError`); só 00/20/40/41/60 e 101/102/500 | Aceitos **apenas com `st_mva` preenchido** (própria como 00/20 e 101/102); sem ST continuam rejeitados — CST 10 sem grupo ST é nota rejeitada |
| `derivar_cfop_operacao(...)` nova, "não lança mais `DerivacaoAmbiguaError`" | `derivar_cfop(ctx)` serve o cadastro, que não sabe do perfil; `DerivacaoAmbiguaError` é a proteção certa lá | Nova função pura por operação (spec § 6.1) usada pelo resolver; `derivar_cfop(ctx)` intacta (ganha `existe_st_na_regra` opcional para deixar de lançar quando informado) |
| B2C interestadual → 6108 | 6108 é "adquirida de terceiros"; produção própria é 6107. O produto já diz se é produção própria (`cfop_padrao` 5101) | 6107/6108 pelo sufixo do CFOP interno do produto; idem 6101/6102 e 6403/6404 |
| "CST vira 00" no B2B sem ST / B2C | Produto pode ter CST 20/40 legítimos | Sem ST: CST/CSOSN do produto **não muda**; com ST: 10 (70 se há redução) / 201 (se era 101) ou 202 |
| Simples + não contribuinte (decisão TASK007) ficou com CFOP 5xxx | Interestadual exige 6xxx | Corrigido aqui: toda operação interestadual deriva CFOP, inclusive Simples |
| ICMS próprio deduzido na ST: `icms_proprio_informado=icms.valor` | No Simples `icms.valor` é 0 (CSOSN) — dedução zero superestima a ST. Conv. 142/2018 cl. 13: deduz-se o valor pela alíquota interestadual | Regime normal: `icms.valor` (real, com redução do 70); Simples: `None` → calculadora usa base × interestadual |
| Contribuinte exige perfil (§ 7.1) | — | Sim, nos dois regimes: é o `mva_st` da regra que diz se há ST |

## Plano TDD
1. RED `test/services/fiscal/test_tax_engine_icms_st.py`: calculadora (cenários 1–3, piso zero) + engine (ramo ST, vNF com ST, DIFAL fora, CST 10/70 e CSOSN 201/202 com ST, CST 10 sem ST → erro, `cfop` no `ImpostosItem`).
2. RED `test/services/fiscal/test_derivacao_interestadual.py`: `derivar_cfop_operacao` (interna, 5405, 6107/6108, 6101/6102, 6403/6404), `derivar_situacao_operacao`, `derivar_cfop(ctx, existe_st_na_regra=…)`.
3. RED em `test_resolver_interestadual.py`: contribuinte com/sem MVA, sem perfil, Simples contribuinte com ST, CFOP 6108 no B2C (normal e Simples).
4. GREEN → REFACTOR → code-quality.

## Arquivos
| Arquivo | O quê |
|---|---|
| `tax_engine/calculators/icms_st.py` | **novo** — `ResultadoICMSST` + `calcular_icms_st` (MVA, redução, dedução do próprio, piso zero) |
| `tax_engine/types.py` | `ItemEntrada.st_*` (4), `ImpostosItem.cfop` + `icms_st_*` (6), `TotaisNota.base_calculo_icms_st/valor_icms_st` |
| `tax_engine/constants.py` | `CST_ICMS_SUBSTITUTO{,_REDUZIDA}`, `CSOSN_SUBSTITUTO_{COM,SEM}_CREDITO` — **fora** dos conjuntos do cadastro |
| `tax_engine/calculators/icms.py` | 10/70 como 00/20 e 201/202 como 101/102, **só com `st_mva`** (`_assert_substituto_tem_regra_de_st`) |
| `tax_engine/engine.py` | `_calcular_st_do_item` (ramo exclusivo com o DIFAL; base cheia; próprio real no normal, `None` no Simples); `cfop` copiado ao resultado |
| `tax_engine/consolidador.py` | soma ST e **inclui no `valor_total_nota`** |
| `derivacao/cfop.py` | `derivar_cfop_operacao` pura, `_sufixo_interestadual`, sufixos 107/108/403/404 + naturezas; `derivar_cfop(ctx, existe_st_na_regra=…)` deixa de lançar quando informado |
| `derivacao/situacao.py` | `derivar_situacao_operacao` (10/70, 201/202; sem ST não muda) |
| `tax_engine/resolver.py` | `_operacao_interestadual` (substitui `_uf_destino_interestadual`), `_regra_do_perfil`, `_resolver_item_interestadual` + `_aplicar_regra`, `_ItemInterestadual`; CFOP/CST/CSOSN da operação em **toda** interestadual |

## TDD
| Arquivo | Casos | RED → GREEN |
|---|---|---|
| `test_tax_engine_icms_st.py` | 14 — cenários 1/2/3, próprio informado, piso zero, redução 0/None; engine: ramo ST, CST 70 + redução própria (141,60), vNF com ST, DIFAL fora + ST dentro (1632), frete na base, CST 10 sem ST → erro, CSOSN 202 no Simples (deduz 120), 201 sem ST → erro, `cfop` no resultado | `ModuleNotFoundError` → ✅ |
| `test_derivacao_interestadual.py` | 11 — interna/balcão, 5405, 6107/6108, 6101/6102 (1 e 2), 6403/6404, naturezas, `derivar_cfop(ctx)` com/sem resposta do perfil, `derivar_situacao_operacao` ×3 | `ImportError` → ✅ |
| `test_resolver_interestadual.py` (+10) | contribuinte com ST (MVA/redução, 6404, CST 10), CST 20 → 70, sem ST → 6102/00/12%, sem perfil → erro, Simples+ST → 202/6404 com alíquota intacta, Simples contribuinte exige perfil, B2C 6108, produção própria 6107, Simples B2C 6108, interna mantém 5102 | 1 falha (teste da TASK007 "contribuinte travado") → reescrito → ✅ |

Gate: `pytest test/services test/core test/db test/api/v1/fiscal` → **1043 passed** (1006 antes). Uma regressão no meio: `test_cst_fora_da_cobertura_e_barrado_no_cadastro` — ampliar `CST_ICMS_SUPORTADOS` liberava CST 70 no cadastro do produto; revertido (ver desvios).

## Critérios de aceite
| CA | Critério | Evidência | |
|---|---|---|---|
| 1 | Calculadora pura: MVA, redução, dedução do próprio, piso zero | 5 testes | ✅ |
| 2 | ST no `valor_total_nota`; sem ST/DIFAL não soma | `test_ramo_st_*` (1132), `test_difal_continua_fora_*` (1632), cenário 3 (1000) | ✅ |
| 3 | 6108/00, 6102/00, 6404/010 (070 c/ redução), sem `DerivacaoAmbiguaError` com regra | `test_derivacao_interestadual.py` + resolver | ✅ |
| 4 | Contribuinte com perfil passa; sem perfil / sem regra → `OperacaoInterestadualError` | resolver ×3 | ✅ |
| 5 | Interna inalterada; testes das calculadoras; roteamento DIFAL × ST; payload intacto | `test_operacao_interna_mantem_o_cfop_do_produto`; gate; `git status` | ✅ |

## Desvios da spec
1. **CST 10/70 e CSOSN 201/202 não entram em `CST_ICMS_SUPORTADOS`/`CSOSN_SUPORTADOS`** (conjuntos do cadastro, lidos por `validators.py`): a condição de substituto é da operação e é derivada na emissão; gravar CST 10 no produto quebraria a venda interna. O calculador aceita-os só com `st_mva`.
2. **Sem ST a situação do produto não muda** (spec: "CST vira 00"): CST 20/40 do produto continuam válidos fora do estado.
3. **6107 além de 6108** (e 6101/6403) pelo sufixo do `cfop_padrao` do produto (5101 = produção própria) — a spec só previa 6108.
4. **ICMS próprio deduzido na ST**: `icms.valor` real no regime normal (a spec usava isso); no Simples `None` → calculadora usa base × interestadual (Conv. 142/2018 cl. 13), senão a dedução seria zero e a ST superestimada.
5. **CFOP interestadual para o Simples não contribuinte** (6107/6108), que a TASK007 tinha deixado em 5xxx.
6. `derivar_cfop(ctx)` ganhou `existe_st_na_regra` opcional em vez de ser substituída: o cadastro continua sem chutar.

## Pendências
- TASK009: `payload_builder` lê `imp.cfop`, `icms_st_*` (grupo ICMS10/70, ICMSSN201/202: `vBCST`, `pMVAST`, `pRedBCST`, `pICMSST`, `vICMSST`), `difal_*`/`fcp_*` (`ICMSUFDest`), `idDest=2`, `indIEDest`, totais `vBCST`/`vST`/`vICMSUFDest`/`vFCPUFDest`; guardrails.
