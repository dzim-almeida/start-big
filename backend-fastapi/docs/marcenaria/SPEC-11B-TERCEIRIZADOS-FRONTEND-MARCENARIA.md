# Spec 11B — Móveis Terceirizados (Frontend)

| Campo        | Valor                                                                                 |
|--------------|---------------------------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                                       |
| Camada       | Frontend (Vue 3 + TypeScript) ⚠️ código compartilhado (tela de Serviços)              |
| Dependências | Specs 10B (aba Separação), 11A (API)                                                  |
| Bloqueia     | Spec 12B (o terceirizado conferido aparece pronto na Produção)                        |
| Referência   | SPEC-00: E6, E6a, P3, P4, T1 · PR1, PR3, PR6                                          |

---

## 1. Objetivo

1. Na **OS**: acompanhar os móveis que vêm prontos da central — pedir, receber, conferir, registrar problema — e lançar a conta da central quando o móvel chega.
2. Na tela de **Serviços**: uma aba **"Terceirizados"** com todos os pedidos em aberto, destacando os atrasados, para o dono cobrar as centrais de uma vez.

## 2. Escopo

**Dentro do escopo**
- Seção "Móveis da central" na aba Separação da OS.
- Modais de pedido, recebimento (com a oferta de conta), problema.
- Aba "Terceirizados" em Serviços (capacidade `orcamento_tecnico`).

**Fora do escopo**
- Tela de Contas a Pagar (a conta aparece lá como qualquer outra).

---

## 3. Arquivos afetados

```
frontend/src/modules/
├── order-service/views/OrdemServicoView.vue                  # ALTERAR ⚠️ — aba por capacidade
└── marcenaria/terceirizados/
    ├── services/terceirizado.service.ts                      # CRIAR
    ├── schemas/terceirizado.schema.ts                        # CRIAR
    ├── composables/useTerceirizadosDaOS.ts                   # CRIAR
    ├── composables/useTerceirizadosEmAberto.ts               # CRIAR
    └── components/
        ├── SecaoTerceirizados.vue                            # CRIAR — dentro de OSSeparacaoTab (10B)
        ├── TerceirizadoLinha.vue                             # CRIAR
        ├── EnviarPedidoModal.vue                             # CRIAR
        ├── ReceberModal.vue                                  # CRIAR — recebimento + oferta de conta
        ├── LancarContaModal.vue                              # CRIAR
        ├── ProblemaModal.vue                                 # CRIAR
        └── TerceirizadosTab.vue                              # CRIAR — aba em Serviços
```

E `marcenaria/separacao/components/OSSeparacaoTab.vue` (10B) passa a montar a `SecaoTerceirizados` no topo.

---

## 4. Decisões

### 4.1. Na OS

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | Seção **"Móveis da central"** no **topo** da aba Separação, só quando a OS tem móvel terceirizado. Título com a contagem: "Móveis da central (2) · 1 atrasado" | SPEC-00 §8 ("na aba Separação"). No topo porque o atraso da central atrasa a obra inteira; não pode ficar no fim de uma lista de 30 chapas |
| D2 | Linhas agrupadas por **central**, com telefone ao lado do nome. Cada linha: móvel, ambiente, medidas, quantidade, a situação como selo (A pedir / Pedido enviado / Recebido / Conferido / Recebido com problema) e o pedido com a previsão ("Pedido 4521 · chega 20/10"). Atrasado: selo vermelho "Atrasado 3 dias" | Quem liga para a central precisa do número do pedido na frente |
| D3 | Caixas de seleção por linha e uma barra de ações **"Enviar pedido"**, **"Receber"**, **"Conferir"** que age sobre os marcados; cada botão só habilita quando todos os marcados estão na situação de onde ele parte e são da mesma central | 11A D2: um pedido cobre vários móveis. Botão desabilitado com `title` dizendo por quê ("Marque móveis da mesma central") |
| D4 | Menu da linha: **Registrar problema**, **Voltar um passo** (com confirmação dizendo para qual situação volta) | 11A D3, D4 |
| D5 | **Enviar pedido:** modal com "Nº do pedido na central" e "Previsão de chegada" (data), os dois opcionais, e a lista dos móveis que vão no pedido | 11A D2 |
| D6 | **Receber:** modal com a data (hoje). Ao confirmar, se a resposta trouxer `oferta_conta` **e** o usuário puder lançar (módulo Financeiro + `manage_financeiro`), o modal **continua** num segundo passo: "Lançar a conta da Madeiranit agora?" com valor (sugerido, só para quem vê custos; vazio para os demais), vencimento, parcelas e descrição, e os botões **"Lançar conta"** e **"Agora não"** | E6: oferecer, não lançar. No mesmo fluxo, porque a nota costuma chegar com o móvel |
| D7 | "Agora não" ou usuário sem permissão: a linha fica com o aviso **"Conta da central não lançada"** (visível só para quem pode lançar), com o botão **"Lançar conta"** | 11A D12: quem recebe na fábrica nem sempre é quem lança |
| D8 | Conta lançada: a linha mostra "Conta R$ 3.950,00 · vence 07/11 · Pendente" (valor só com custos; sem custos, "Conta lançada · Pendente") e o link "Ver em Contas a Pagar" | Fecha o ciclo de E6 na própria OS |
| D9 | Com `view_custos`, a linha mostra o valor orçado da central em cinza; no modal de conta, a diferença em tempo real: "Nota R$ 3.950,00 · orçado R$ 3.800,00 · +3,9%" | 11A D13; P4 |
| D10 | OS fechada: seção somente leitura, exceto **"Lançar conta"** em OS finalizada (11A D12) | A nota pode chegar depois de a obra terminar |

### 4.2. Aba "Terceirizados" em Serviços

| # | Decisão | Motivo |
|---|---------|--------|
| D11 | Aba **"Terceirizados"** na tela de Serviços, depois de "Cadastro de Serviços", só com `temOrcamentoTecnico`. Mesmo mecanismo da aba "Revisões" da oficina (`temRevisoes`) | Precedente exato no código: aba por capacidade na mesma tela |
| D12 | Lista agrupada por **central**, com filtros "Situação" (padrão: **Pedido enviado**) e "Só atrasados"; colunas OS (link que abre a OS), cliente, móvel, pedido, enviado em, previsão, atraso | 11A D18. O padrão é o que se cobra: o que já foi pedido e não chegou |
| D13 | Cabeçalho de cada central com o telefone e a contagem ("Madeiranit · (85) 3333-0000 · 3 pedidos, 1 atrasado") | O dono liga para a central e resolve todos os móveis dela na mesma ligação |
| D14 | "Nova OS"/"Novo Serviço" do topo some nesta aba (como em "Revisões") | Nada a criar daqui |

---

## 5. Contratos consumidos

Spec 11A §6. Do sistema: `useModulosStore().temModulo(MODULOS.FINANCEIRO)`, `useCheckPermission` com `PERMISSIONS.manageFinance`, `getUniqueOS` + `openExistingOS`, `BaseMoneyInput`, `BaseDateInput`.

---

## 6. Telas

### 6.1. Seção na OS

```
Móveis da central (3) · 1 atrasado
Madeiranit · (85) 3333-0000
 [x] Torre Quente      Cozinha Gourmet  700×2200×600  1×  [Pedido enviado] Pedido 4521 · chega 20/10  ⚠ Atrasado 3 dias  ⋯
 [x] Painel TV         Sala de estar    …             1×  [Pedido enviado] Pedido 4521 · chega 20/10                    ⋯
Central Norte · (85) 3444-0000
 [ ] Ilha              Cozinha Gourmet  …             1×  [A pedir]                                                     ⋯
                                                       [Enviar pedido] [Receber] [Conferir]
```

### 6.2. Receber → oferta de conta

```
Receber móveis da Madeiranit                          Passo 2 de 2
✓ Torre Quente e Painel TV recebidos em 08/10/2026.

Lançar a conta da Madeiranit agora?
  Valor da nota R$ [3.950,00]   (orçado R$ 3.800,00 · +3,9%)
  Vencimento [07/11/2026]   Parcelas [1 ▾]
  Descrição  [Madeiranit — pedido 4521 — OS-2026-000512 (Torre Quente, Painel TV)]
                                                   [Agora não]  [Lançar conta]
```

---

## 7. Especificação técnica

### 7.1. Aba em Serviços — `OrdemServicoView.vue` ⚠️

```ts
const { temRevisoes, temOrcamentoTecnico } = useCapacidades();

// Abas extras por capacidade, na ordem: Revisões (oficina), Terceirizados (marcenaria).
const tabOptions = computed(() => [
  ...TAB_OPTIONS,
  ...(temRevisoes.value ? [{ id: 'revisoes', label: 'Revisões' }] : []),
  ...(temOrcamentoTecnico.value ? [{ id: 'terceirizados', label: 'Terceirizados' }] : []),
]);
```

- Título e subtítulo da aba: "Terceirizados" / "Móveis pedidos às centrais parceiras e ainda não conferidos."
- `mostrarBotaoAdicionar` (03B) devolve `false` também para `'terceirizados'`.
- Nos outros segmentos, `tabOptions` é exatamente a lista de hoje (snapshot).

### 7.2. Pode lançar conta

```ts
/** Lançar conta é ato financeiro: módulo contratado e permissão de gerir (11A D12). */
const podeLancarConta = computed(() =>
  modulos.temModulo(MODULOS.FINANCEIRO) && (isMaster.value || hasPermission(PERMISSIONS.manageFinance)),
);
```

### 7.3. Seleção e ações

```ts
/** A ação só habilita quando todos os marcados partem da mesma situação e da mesma central (D3). */
function podeAplicar(acao: 'enviar' | 'receber' | 'conferir'): { ok: boolean; motivo?: string } {
  const origem = { enviar: 'A_PEDIR', receber: 'ENVIADO', conferir: 'RECEBIDO' }[acao];
  const marcados = linhas.value.filter((l) => selecionados.value.has(l.movel_id));
  if (!marcados.length) return { ok: false, motivo: 'Marque pelo menos um móvel.' };
  if (new Set(marcados.map((l) => l.central.id)).size > 1) return { ok: false, motivo: 'Marque móveis da mesma central.' };
  if (marcados.some((l) => l.situacao !== origem)) return { ok: false, motivo: `Só móveis "${ROTULO[origem]}".` };
  return { ok: true };
}
```

Se a resposta de **conferir** ou **voltar** trouxer `sugestao_status` (12A §7), abrir o `SugestaoStatusModal` da 12B.

Depois de cada ação: limpar a seleção, atualizar a seção e invalidar a lista da aba "Terceirizados" e a aba Produção (12B), que mostra o terceirizado conferido como pronto.

---

## 8. Prova de não regressão (⚠️ PR1)

1. `npm run test` e `npx vue-tsc --noEmit`.
2. Tela de Serviços na informática e na serigrafia: abas "Ordens" e "Cadastro de Serviços" (snapshot); na oficina, com "Revisões" no mesmo lugar.
3. Nenhuma chamada a `/marcenaria/...` nesses segmentos.

## 9. Limitações conhecidas

- Sem aviso ativo (notificação) de atraso: o atraso aparece quando alguém abre a OS ou a aba. Um aviso no painel de notificações pode vir depois, com o uso real.

---

## 10. Critérios de aceite

- [ ] Seção "Móveis da central" no topo da Separação, só com terceirizados, agrupada por central, com atraso em destaque.
- [ ] Enviar vários móveis no mesmo pedido; receber; conferir; registrar problema; voltar um passo com confirmação.
- [ ] Receber oferece a conta no mesmo modal para quem pode lançar; "Agora não" deixa o aviso e o botão na linha.
- [ ] Valor sugerido e diferença só com custos.
- [ ] Aba "Terceirizados" em Serviços com o filtro padrão "Pedido enviado" e "Só atrasados".
- [ ] Prova de não regressão (§8); código comentado (PR6).

## 11. Casos de teste

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | `OrdemServicoView`, informática / oficina / marcenaria | Abas de hoje / com Revisões / com Terceirizados |
| 02 | `OSSeparacaoTab` sem terceirizados | Sem a seção |
| 03 | `podeAplicar('enviar')` com centrais diferentes | Motivo "Marque móveis da mesma central." |
| 04 | `podeAplicar('receber')` com um "A pedir" marcado | Motivo de situação |
| 05 | `ReceberModal` com `oferta_conta` e `podeLancarConta` | Passo 2 aparece |
| 06 | Mesmo, sem `podeLancarConta` | Fecha no passo 1; a linha não mostra o aviso para este usuário |
| 07 | `LancarContaModal` sem `view_custos` | Valor vazio; sem "orçado" |
| 08 | `TerceirizadoLinha` atrasado 3 dias | Selo "Atrasado 3 dias" |
| 09 | Voltar um passo de "Recebido" | Confirmação "Voltar para Pedido enviado?" |
| 10 | `TerceirizadosTab` padrão | Só "Pedido enviado", agrupado por central |

### Roteiro manual (dev)

1. OS com 2 móveis terceirizados da mesma central e 1 de outra: enviar os 2 juntos com pedido e previsão de ontem → atraso.
2. Aba Serviços › Terceirizados: ver o atraso agrupado pela central.
3. Receber os 2; lançar a conta com valor diferente do orçado, em 3x; ver em Contas a Pagar.
4. Registrar problema no terceiro; voltar um passo.
5. Como funcionário sem permissão financeira: receber sem ver a oferta.
6. Informática e oficina: §8.
