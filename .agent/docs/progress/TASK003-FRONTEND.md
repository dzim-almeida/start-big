# TASK003-FRONTEND — Modal e ações de devolução no Centro Fiscal

**Status:** ✅ concluída · **Data:** 2026-09-17 · **Spec:** `specs/completed/TASK003-FRONTEND-NotaDevolucao.md`

## Arquivos
| Arquivo | O quê |
|---|---|
| `types/fiscal.types.ts` | `ItemDevolucaoPayload`, `DestinatarioAvulsoPayload`, `EmissaoDevolucaoPayload`; `DocumentoItemResumo.quantidade_milesimos/quantidade_devolvida_acumulada`; `DocumentoFiscalRead.finalidade_emissao/documento_referenciado_id/chave_documento_referenciado/totalmente_devolvida` |
| `shared/types/viaCep.types.ts` | `ibge` (o código IBGE que a NF-e exige) |
| `services/fiscal.service.ts` | `emitirDevolucao(id, payload)` |
| `composables/useDevolucaoItens.ts` | **novo** — funções puras (`prazoCancelamentoExpirado`, `montarItensLocais`, `validarQuantidade`, `valorTotalEstimado`, `totalmenteDevolvida`, `destinatarioAvulsoValido`, `sanitizarDestinatario`) + composable reativo |
| `composables/useFiscalDevolucaoMutation.ts` | **novo** — toast por desfecho (AUTORIZADA/PROCESSANDO/outros); invalida `documentos`, `resumo`, `documento(origem)`, `historico(origem)` |
| `components/detalhes/FiscalEmitirDevolucaoModal.vue` | **novo** — resumo da origem, modo TOTAL/PARCIAL, tabela com saldo e input por linha, destinatário avulso com ViaCEP, motivo, estoque, total em tempo real |
| `components/detalhes/FiscalDocumentoDetailsDrawer.vue` | banner de prazo expirado, "Devolver Itens" × "Emitir NF-e de Devolução" (primário), cancelamento oculto fora do prazo, badge "totalmente devolvida", abre o documento novo ao autorizar |

## Testes
- `composables/__tests__/useDevolucaoItens.spec.ts` — 10 casos (janela NF-e/NFC-e/fallbacks, saldo, item sem snapshot, totalmente devolvida, validação de quantidade, total, destinatário avulso). **18/18** no Vitest total.
- `npx vue-tsc --noEmit` → 0 erros. Prettier nos `.ts` novos.

## Critérios de aceite (spec § 6) — verificados no navegador embutido (backend mock, banco no scratchpad)
| # | Critério | Evidência | |
|---|---|---|---|
| 1 | Expiração (30 min NFC-e / 24 h NF-e) bloqueia cancelar e destaca devolução | com `data_autorizacao` −2 dias: banner âmbar, botão de cancelar sumiu, "Emitir NF-e de Devolução" primário; dentro do prazo: "Devolver Itens" ao lado de "Cancelar NF-e" | ✅ |
| 2 | Parcial não passa do saldo | digitar 5 com saldo 1 → "Acima do saldo disponível (1)" e botão desabilitado | ✅ |
| 3 | NFC-e/nota anônima: avulso obrigatório + ViaCEP | CEP 01001000 preencheu logradouro, bairro, município, UF e **IBGE 3550308** | ✅ |
| 4 | Motivo < 15 bloqueia | "defeito" → `disabled=true`; texto completo → `false` | ✅ |
| 5 | Cache: origem e lista atualizam sem reload | após autorizar: drawer abriu o doc nº 2, contador Autorizadas 1→2, e a origem reabriu com saldo 0,5 | ✅ |
| 6 | `vue-tsc --noEmit` sem erros | exit 0 | ✅ |

## Desvios da spec
1. **ViaCEP reaproveitado** de `shared/services/cep.service.ts::getAddressByCep` (já existia) em vez de um `buscarCep` novo em `fiscal.service.ts` — DRY; só o tipo ganhou `ibge`.
2. **Tipos**: a spec definia `DocumentoFiscalHistoricoItem`/`DocumentoFiscalItem` novos; o projeto já tem `DocumentoFiscalRead`/`DocumentoItemResumo` — estendidos em vez de duplicados.
3. **Sem `modelo`/`destinatario_dados`** no tipo (não existem no backend); a pista para "tem destinatário" é `destinatario_id`, com fallback: se o backend responder `DESTINATARIO_OBRIGATORIO`, o modal abre a seção do avulso na hora.
4. **Lógica pura em `useDevolucaoItens.ts`** (não dentro do modal) para ser testável — 10 testes sem montar componente.
5. A própria NF-e de devolução (`finalidade_emissao === 4`) não oferece "devolver" nem "cancelar fora do prazo" (não previsto na spec; evita devolver uma devolução).

## Incidente durante a sessão (backend, corrigido antes do commit da TASK003-BACKEND ser fechado)
A migration `u4v5w6x7y8z9` usava `batch_alter_table` (recria a tabela). No boot o engine roda com `PRAGMA foreign_keys=ON` e o DROP de `documento_fiscal` falha porque `documento_fiscal_item`/`carta_correcao_fiscal` a referenciam — o primeiro boot caiu e deixou `_alembic_tmp_documento_fiscal` órfã. Corrigido: `op.add_column` direto (ADD COLUMN nativo, sem recriar) + limpeza da temp órfã; a `s2t3u4v5w6x7` (TASK001) foi padronizada do mesmo jeito. Fica como **regra**: migrations de coluna neste projeto não usam batch. Ver `00-baseline.md`.
