# TASK009 — Payload interestadual (Focus NFe) e guardrails — backend

**Status:** ✅ concluída (backend) · **Data:** 2026-09-19 · **Spec:** `specs/completed/TASK009 - PAYLOAD-INTERESTADUAL-INTERFACE.md`

## Objetivo
`payload_builder` passa a emitir, com a nomenclatura da Focus NFe, o grupo DIFAL/FCP (`ICMSUFDest`) e o grupo ST por item, os totais de ST/DIFAL e o `local_destino` dinâmico; CFOP do item vem da operação. Guardrails antes de reservar número. Interface do PDV (§ 6) fora desta rodada.

## Verificação da spec contra o código
| Ponto da spec | O que o código diz | Decisão |
|---|---|---|
| § 4.1 `local_destino` recalculado a partir de endereço/presença | `derivacao/operacao.py::derivar_local_destino` avisa: idDest tem que sair da **mesma decisão** do 1º dígito do CFOP. O resolver já decidiu (TASK008) e o CFOP viaja em `ImpostosItem.cfop` | `local_destino` = grupo dos CFOPs calculados (2 se `6xxx`); itens com grupos diferentes → `ValueError` (guard 3 por construção) |
| § 4.4 totais de ST/DIFAL sempre presentes com `0.0` | `test_contrato_payload_campos` exige exatamente as chaves atuais na venda interna; a plataforma poda o que não está no Zod | Campos ST/DIFAL (item e totais) entram **só quando há valor**; contrato documentado em `docs/contrato-api-fiscal-plataforma.md` |
| § 5.1 guard "indIEDest=1 sem IE" | `indicador_ie = 1 if cliente.ie else 9` — impossível por construção. O risco é IE mal formada ("ISENTO") | `verificar_ie_destinatario_interestadual`: PJ com IE em operação interestadual precisa de 2–14 dígitos (pontuação ignorada) |
| § 5.2 endereço completo | `verificar_endereco_destinatario` já roda para NF-e em `core.py` | Nada a fazer (teste de regressão cobre) |
| § 5.3 CFOP × destino | Ver § 4.1 | Por construção + `ValueError` |
| "antes de reservar o número" | `_preparar_dados_emissao` (gate + resolver + engine) roda antes de `reservar_proximo_numero_nfe` | OK — `OperacaoInterestadualError` vira 422 sem queimar número |
| Preview mostra `cfop_padrao` do produto | Interestadual mostraria 5102 | Preview usa o CFOP calculado |
| Simples Nacional | `difal_*` = None (TASK007) | Sem `ICMSUFDest`; ST sai com CSOSN 201/202 e os mesmos campos `icms_*_st` |

## Plano TDD
1. RED `test/services/fiscal/test_payload_interestadual.py`: DIFAL (chaves Focus, `local_destino` 2, `cfop` 6108, totais), ST (chaves, `valor_total` com ST), Simples ST, interna sem chaves novas, grupos misturados → erro, preview com CFOP calculado.
2. RED `test/services/fiscal/test_guardrails_interestadual.py`: IE mal formada interestadual → pendência; IE com pontuação → ok; interna → sem pendência; PF → sem pendência.
3. GREEN → REFACTOR → code-quality → contrato doc.

## Arquivos
| Arquivo | O quê |
|---|---|
| `app/services/fiscal/payload_builder.py` | `_campos_difal`, `_campos_icms_st`, `_totais_interestaduais`, `_local_destino` (grupo do CFOP; grupos misturados → `ValueError`); item usa `imp.cfop`; totais só quando existem |
| `app/services/fiscal/validators.py` | `verificar_ie_destinatario_interestadual` (2–14 dígitos, pontuação tolerada; "ISENTO"/texto → pendência `ie`, Rejeição 232) |
| `app/services/fiscal/core.py` | `_interestadual()` + guard da IE só na NF-e interestadual |
| `app/services/fiscal/tax_engine/resolver.py` | `eh_operacao_interestadual` público (mesma régua para gate e motor) |
| `app/services/fiscal/emissao.py` | preview mostra o CFOP calculado (6xxx) |
| `docs/contrato-api-fiscal-plataforma.md` | § 3.1 — campos opcionais da operação interestadual para o Zod da plataforma |

## TDD
| Arquivo | Casos | RED → GREEN |
|---|---|---|
| `test/services/fiscal/test_payload_interestadual.py` | 9 — DIFAL (8 chaves Focus + valores), totais DIFAL sem mexer no `valor_total`, `local_destino` 2, ST (chaves, redução, `valor_total` 1081,60 = vNF), ST sem redução omite, Simples 202, interna sem chave nova, grupos misturados → `ValueError`, sem motor → 1 | 7 falhas → ✅ |
| `test/services/fiscal/test_guardrails_interestadual.py` | 11 — IE mal formada ×4, IE com pontuação ×3, PJ sem IE/PF, gate barra na interestadual, gate ignora interna/balcão | `ImportError` → ✅ |

Gate: `pytest test/services test/core test/db test/api/v1/fiscal` → **1063 passed** (1043 antes). `test_contrato_payload_campos` continua exato para venda interna.

## Critérios de aceite
| CA | Critério | Evidência | |
|---|---|---|---|
| 1 | Chaves exatas da Focus (DIFAL/ST), nenhuma tag XML crua | `CHAVES_DIFAL`/`CHAVES_FCP`/`CHAVES_ST` nos testes; contrato § 3.1 | ✅ (repasse `.passthrough()` na plataforma é do time web) |
| 2 | `local_destino` 2 fora, 1 interna/balcão; CFOP 6 quando 2 | `_local_destino` sai do CFOP; `test_itens_com_grupos_*` | ✅ |
| 3 | Totais: ST soma no `valor_total`, DIFAL não | `test_st_sai_*`, `test_difal_nos_totais_*` | ✅ |
| 4 | IE inválida bloqueada antes de reservar número; endereço incompleto idem | gate roda em `_preparar_dados_emissao`, antes de `reservar_proximo_numero_nfe`; endereço já coberto por `verificar_endereco_destinatario` | ✅ |
| 5 | Interface do PDV | **fora desta rodada** | ⏸ |

## Desvios da spec
1. **`local_destino` pelo grupo do CFOP calculado**, não recalculado do endereço (§ 4.1): garante a mesma decisão do resolver (guard 3 por construção).
2. **Campos ST/DIFAL só quando existem** (§ 4.4 pedia `0.0`): o contrato com a plataforma é exato para a venda interna e o Zod poda o desconhecido.
3. **Guard da IE valida formato**, não presença: "sem IE" já vira `indIEDest 9` por construção.
4. Guard do endereço não foi recriado — já existia.

## ⚠️ Pendência de negócio descoberta
Com ICMS-ST o vNF é produtos + ST, e `_validar_fechamento_pagamentos` (Rejeição 767) exige que a **venda do PDV** feche com esse total. Hoje o serviço de venda calcula `total` sem ST → uma venda B2B interestadual com ST **será recusada no builder** ("Pagamentos não fecham") até o checkout somar a ST ao total a cobrar (spec § 6.2 "(+) ICMS-ST Retido"). É trabalho do serviço de venda + PDV (rodada de interface); o backend está pronto para recebê-lo.

## Pendências (interface)
- Badge "Interestadual B2C (DIFAL)" / "B2B (ICMS-ST)" no checkout; linha "(+) ICMS-ST Retido" e "DIFAL (incluso)" no resumo; total a cobrar com ST.
- Plataforma web: aceitar os campos de `docs/contrato-api-fiscal-plataforma.md` § 3.1.
