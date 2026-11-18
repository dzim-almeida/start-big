# TASK001-FRONTEND — Interface de alerta e confirmação da numeração fiscal

**Status:** ✅ concluída · **Data:** 2026-09-17 · **Spec:** `specs/completed/TASK001-FRONTEND-InterfaceConfirmacaoNumeroFiscal.md`

## Objetivo
Mostrar ao lojista/implantador que a sequência precisa ser confirmada, orientar o preenchimento (empresa nova × migração) e enviar a confirmação ao salvar; interceptar tentativas de emissão antes da confirmação.

## Arquivos tocados
| Arquivo | O quê |
|---|---|
| `types/fiscal.types.ts` | `FiscalConfiguracao.numeracao_confirmada: boolean`; **novo** `FiscalConfiguracaoUpdate` (espelho de `FiscalSettingsUpdate`) |
| `services/fiscal.service.ts`, `composables/useFiscalConfiguracaoMutation.ts` | `atualizarConfiguracao(payload: FiscalConfiguracaoUpdate)` — removeu `Partial<FiscalConfiguracao>` e o `as any` do modal |
| `composables/useNumeracaoConfirmada.ts` | **novo** — `criarGuardaNumeracao(deps)` (puro, testável) + `useNumeracaoConfirmada()` (QueryClient + router + toast) |
| `shared/composables/useToast.ts` | `warning(message, description, { action })` — botão no toast (vue-sonner) |
| `shared/composables/useEmitirFiscal.ts` | guard antes de `emitirVenda`, `emitirNFCeVenda`, `emitirOS` |
| `components/emitir/FiscalEmitirNFeModal.vue`, `FiscalEmitirTesteModal.vue` | guard antes da emissão manual, em lote e de teste |
| `components/configuracoes/FiscalEmissaoEstadualModal.vue` | `numeracao_confirmada: true` no payload; chip "Sequência Confirmada"/"Confirmação pendente"; banner de orientação |
| `views/FiscalConfiguracoesView.vue` | chip âmbar "Ação necessária: confirme a numeração" / verde "Configurado e Confirmado"; CTA "Confirmar Numeração" |
| `vite.config.ts`, `package.json` | Vitest (jsdom), `npm run test` / `test:watch` |

## Testes
- `composables/__tests__/useNumeracaoConfirmada.spec.ts` — 4 casos: bloqueia + avisa; ação leva à configuração; libera quando confirmada; sem cache libera (backend decide). **4/4 verdes.**
- `npx vue-tsc --noEmit` → **0 erros** (exit 0).
- ESLint está quebrado no repositório (v9 sem flat config, `eslint-plugin-vue` ausente) — pré-existente; Prettier `--check` nos `.ts` novos passou.

## Critérios de aceite (verificados no navegador embutido, backend em mock com banco no scratchpad)
| # | Critério | Evidência | |
|---|---|---|---|
| 1 | Badge de ação necessária em instalação limpa | `/fiscal` com `numeracao_confirmada:false` → chip âmbar + CTA "Confirmar Numeração" | ✅ |
| 2 | PUT contém `numeracao_confirmada: true` | salvar o modal sem alterar nada → `GET /fiscal/configuracao` devolve `true` | ✅ |
| 3 | Reatividade sem F5 | após salvar, card mudou para "Configurado e Confirmado" e CTA voltou a "Configurar Emissão Estadual" (invalidação de `fiscalKeys.configuracao()`) | ✅ |
| 4 | Intercepção antes da emissão, sem request | "Emitir Teste" com flag pendente → toast com botão "Configurar", nenhum request `emitir*` no Network; o botão levou a `/fiscal` | ✅ |
| 5 | Design system | chips com as mesmas classes dos chips existentes (`rounded-full … bg-amber-50 text-amber-700 border-amber-200`) — ajustado após feedback do usuário | ✅ |

## Desvios da spec (aplicados e justificados)
1. **Sem classes `dark:`**: a spec pedia `dark:` nos chips, mas o app não tem tema escuro (só 2 usos isolados no repo). Com Tailwind v4 o `dark:` segue o `prefers-color-scheme` do SO — numa máquina em modo escuro o chip ficava marrom no meio de uma tela clara. Removidos.
2. **Chips no padrão do sistema** em vez das classes literais da spec (`rounded`, `font-medium`, `text-amber-800`): feedback do usuário durante o aceite.
3. **Guarda em 6 pontos**, não só em `useEmitirFiscal`: a spec citava "manual, contingência ou teste" — os modais do Centro Fiscal (manual, lote, teste) não passam por `useEmitirFiscal`.
4. **Guarda não adivinha sem cache**: se a configuração ainda não foi carregada, libera e deixa o gate do backend responder pelo modal de pendências (evita bloquear por falta de dado).
5. `FiscalConfiguracaoUpdate` criado como interface própria (não `Partial<FiscalConfiguracao>`), porque o PUT usa `ambiente_emissao` e o GET `ambiente`.

## Infra criada para o aceite (não versionada)
- `scratchpad/dev_server.py`: backend com `BIGPDV_DATA_DIR` no scratchpad, `FISCAL_MOCK_ENABLED`, `TESTING=1` e módulos NFE/NFCE concedidos + `/licenca/status` respondendo válido. `.claude/launch.json` aponta para ele (caminho da máquina — não commitar).
