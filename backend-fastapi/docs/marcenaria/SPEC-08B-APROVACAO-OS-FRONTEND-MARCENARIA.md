# Spec 08B — Aprovação do Orçamento e OS (Frontend)

| Campo        | Valor                                                                                   |
|--------------|-----------------------------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                                         |
| Camada       | Frontend (Vue 3 + TypeScript) ⚠️ código compartilhado (abas e itens do modal de OS)     |
| Dependências | Specs 06B (editor), 07 (proposta), 08A (API, com a Revisão 1)                           |
| Bloqueia     | Specs 10B, 11B, 12B, 13B (novas abas da OS seguem o mesmo padrão)                        |
| Referência   | SPEC-00: F3, F4, F4a, F2b, O4, O4a, O7a, O8, O8a, T1, T3f, T5, FB1 · PR1, PR3, PR6      |

> **Revisão 1 (08/10/2026) — convergência com a branch (SPEC-00 Revisão 15).** (1) **Cadeado:** a aba "Serviços e Peças" já tem o cadeado de "item que veio do orçamento" para a fábrica (`OSServicesTab.veioDoOrcamento`, que olha `fabrica_orcamento_id`). A D24 passa a **estender essa função** para olhar também `origem`, com o mesmo ícone e um texto que serve aos dois; nada de selo novo. (2) **Peças embutidas** (08A Revisão 2): os insumos aprovados chegam como itens de produto de valor zero; eles ficam agrupados e recolhidos no fim da lista ("Material do orçamento (N)"), D24a. (3) **Fábrica aposentada (FB1):** ao criar a aba `'orcamento'`, saem de `OSFormTabsContent.vue` o trilho e a aba Orçamento da fábrica (dependiam de `fase_fabrica`, que nenhuma OS nova recebe) e, de `OSFormModalShell.vue`, a trava do status por etapa (`status-da-etapa`), D19a.

---

## 1. Objetivo

1. **Aprovar** o orçamento numa tela só: escolher os móveis que o cliente aceitou, ajustar o desconto, ver o total e o sinal, dizer se o sinal já foi pago, e gerar a OS.
2. Mostrar o orçamento **aprovado**: o que foi aprovado e o que não foi, a OS gerada, e o caminho para **desfazer** quando for engano.
3. Na **OS**: aba **"Orçamento"** com o que foi vendido, e **cadeado** nos itens que vieram do orçamento (F4).
4. Imprimir a **proposta aprovada** (só os móveis aprovados), para o cliente assinar.

## 2. Escopo

**Dentro do escopo**
- `AprovarModal`, `DesfazerAprovacaoModal`, faixa e editor no status `APROVADO`.
- Aba "Orçamento" no modal de OS (capacidade `orcamento_tecnico`).
- Cadeado nos itens com `origem` (genérico).
- Proposta aprovada (extensão da Spec 07).
- Coluna "OS" na lista de orçamentos.

**Fora do escopo**
- Abas Separação, Produção e Entrega (Specs 10B, 12B, 13B).
- Campo do arquiteto (09B).
- Lançar o sinal no caixa (08A §9).

---

## 3. Arquivos afetados

```
frontend/src/modules/
├── order-service/ordens/
│   ├── components/form/OSFormTabsContent.vue           # ALTERAR ⚠️ — aba 'orcamento' por capacidade; saem trilho e aba da fábrica (FB1)
│   ├── components/form/OSFormModalShell.vue            # ALTERAR ⚠️ — sai a trava de status por etapa da fábrica (FB1)
│   ├── components/form/OSServicesTab.vue               # ALTERAR ⚠️ — cadeado também por `origem`; grupo das peças embutidas
│   └── schemas/relationship/osItem.schema.ts           # ALTERAR ⚠️ — `origem` opcional na leitura
└── marcenaria/orcamentos/
    ├── services/aprovacao.service.ts                   # CRIAR — simular, aprovar, desfazer, por-os
    ├── schemas/aprovacao.schema.ts                     # CRIAR — zod das respostas
    ├── composables/
    │   ├── useSimularAprovacao.ts                      # CRIAR — prévia com espera de 400 ms
    │   ├── useAprovacao.ts                             # CRIAR — aprovar/desfazer pela fila (06B D7)
    │   └── useOrcamentoDaOS.ts                         # CRIAR — query da aba da OS
    ├── utils/dadosProposta.ts                          # ALTERAR — modo "aprovada"
    └── components/
        ├── modais/AprovarModal.vue                     # CRIAR
        ├── modais/DesfazerAprovacaoModal.vue           # CRIAR
        ├── modais/OSCriadaModal.vue                    # CRIAR — confirmação com "Abrir OS"
        ├── editor/EditorFaixaStatus.vue                # ALTERAR — APROVADO e OS cancelada
        ├── editor/MovelLinha.vue                       # ALTERAR — selo "Não aprovado"
        ├── editor/PainelResumo.vue                     # ALTERAR — "Proposto" × "Aprovado"
        ├── lista/OrcamentosTabela.vue                  # ALTERAR — coluna OS
        └── os/OSOrcamentoTab.vue                       # CRIAR — aba da OS
```

| Arquivo | Faz | Não faz |
|---------|-----|---------|
| `AprovarModal` | Formulário da aprovação, prévia, envio pela fila | Calcular (a prévia vem da API, C8) |
| `OSOrcamentoTab` | Mostrar o resumo do orçamento dentro da OS, ligar para o orçamento | Editar nada |
| `OSServicesTab` | Esconder editar/remover de item com `origem` | Saber o que é marcenaria |

---

## 4. Decisões

### 4.1. Aprovar

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | Botão **"Aprovar"** no cabeçalho do editor (ao lado de "Enviar"/"Proposta") quando `acoes.aprovar` | Aprovar é o objetivo do orçamento; não pode ficar escondido no menu "Mais" |
| D2 | Modal em **três blocos**, em ordem: (1) **O que o cliente aprovou** (ambientes e móveis com caixas, todas marcadas; "Marcar todos/nenhum" por ambiente; caixa da instalação), (2) **Valores** (desconto % ou R$, que começa com o do orçamento; prévia de bruto, desconto, total, sinal combinado, saldo, previsão de entrega, e margem com `view_custos`), (3) **Sinal** (§4.2) | O4, O4a. A ordem é a da conversa com o cliente: o que ele quer, quanto fica, quanto paga agora |
| D3 | Cada mudança (caixa, desconto) pede a prévia ao backend (`/aprovacao/simular`) depois de 400 ms. Enquanto carrega, os números ficam esmaecidos; erro de desconto aparece embaixo do campo (`campo: "desconto"`) | C8: nada calculado em TypeScript. O mesmo padrão da prévia do móvel (06B D6) |
| D4 | Móvel com preço zero aparece com o selo "sem preço" e **não** pode ser marcado (caixa desabilitada, com a explicação no `title`) | 08A D4: a API recusaria; melhor impedir na hora |
| D5 | Avisos no topo do modal, conforme o status: `RASCUNHO` → "O orçamento será registrado como enviado e aprovado ao mesmo tempo."; `VENCIDO` → "A validade terminou em 21/10/2026. Os preços podem ter mudado desde o envio." | O4a: o usuário sabe o que o clique faz |
| D6 | Botão **"Aprovar e gerar OS"**, desabilitado sem nenhum móvel marcado ou enquanto a prévia carrega. A aprovação passa pela **fila de escrita** (06B D7), com a revisão do cache | Mesmo cuidado de concorrência do resto do editor |
| D7 | Depois de aprovar, o modal `OSCriadaModal` diz "OS OS-2026-000512 criada com 3 móveis e a instalação." e oferece **"Abrir OS"**, **"Imprimir proposta aprovada"** e **"Ficar no orçamento"** | Os três próximos passos reais. "Abrir OS" usa `getUniqueOS` + `openExistingOS` (o mesmo caminho do painel de notificações) |

### 4.2. Sinal (O7a)

| # | Decisão | Motivo |
|---|---------|--------|
| D8 | Pergunta obrigatória, **sem resposta marcada**: "O cliente já pagou o sinal?" (•) **Sim, recebi** ( ) **Ainda não**. O botão "Aprovar e gerar OS" só habilita depois da resposta | Uma opção pré-marcada seria aceita sem ler; e a resposta errada mexe no dinheiro que o cliente vai pagar na entrega (08A D15) |
| D9 | **Sim:** valor recebido (começa com o sinal combinado; pode mudar até o total) e **forma de pagamento** (formas ativas, obrigatória). Se o cliente tem crédito, aparece "Usar crédito do cliente (R$ X disponível)", que dispensa a forma | 08A D15–D16 |
| D10 | **Ainda não:** a frase "O sinal combinado de R$ 3.695,56 fica registrado no orçamento. Quando o cliente pagar, lance no **Adiantamento** da OS." | O caminho de lançar depois já existe no resumo da OS; a frase diz onde |
| D11 | Sinal combinado **zero**: o bloco Sinal some e o envio vai com `recebido: false` | Nada a perguntar |

### 4.3. Orçamento aprovado

| # | Decisão | Motivo |
|---|---------|--------|
| D12 | Faixa de `APROVADO` (06B §6.3): "Aprovado em 06/10/2026 por Alan · **OS-2026-000512** (Aberta)" com **"Abrir OS"**, **"Proposta aprovada"** e, quando `acoes.desfazer_aprovacao`, **"Desfazer aprovação"** (botão discreto, à direita) | F3: o orçamento é somente leitura; a faixa leva aos próximos passos |
| D13 | Móveis não aprovados ficam esmaecidos, com o selo "Não aprovado"; a instalação não aprovada também | O4: os recusados ficam como histórico, visíveis |
| D14 | O resumo lateral mostra duas colunas, **Proposto** e **Aprovado**, quando forem diferentes; iguais, uma só | O vendedor vê o que perdeu na negociação; o dono vê a margem do que de fato vai produzir |
| D15 | OS cancelada pela tela de OS (08A D21): a faixa diz "A OS OS-2026-000512 foi cancelada." e oferece **"Nova versão"** | 08A D21 |

### 4.4. Desfazer (O8, O8a)

| # | Decisão | Motivo |
|---|---------|--------|
| D16 | Modal de perigo: "Desfazer a aprovação vai **cancelar a OS OS-2026-000512** e devolver o orçamento para Enviado." Motivo obrigatório. Com sinal recebido, a pergunta "O que fazer com o sinal de R$ 3.695,56?" (•) **Vira crédito do cliente** (usado na próxima aprovação) ( ) **Foi devolvido ao cliente** | O8a. Mesmas escolhas do cancelamento de OS, com palavras desta situação |
| D17 | Quando a loja exige PIN para cancelar OS, o modal pede o PIN (mesmo componente `GerenteAprovacaoModal` do cancelamento) ao receber `REQUER_APROVACAO_GERENTE` | O8a: a proteção que a loja escolheu continua valendo |
| D18 | Sem `acoes.desfazer_aprovacao`, o botão não aparece; no lugar, um ícone de informação lista os motivos (`motivos_desfazer`): "A OS já não está aberta (Em Produção)." | 08A §7.6. O usuário entende por que não pode, sem tentar e falhar |

### 4.5. Na OS ⚠️

| # | Decisão | Motivo |
|---|---------|--------|
| D19 | Aba **"Orçamento"** no modal de OS, depois de "Serviços e Peças", **só** com `temOrcamentoTecnico` e fora do modo de criação. Os outros segmentos não têm a capacidade: a lista de abas deles é a mesma de hoje | T1: mesmo mecanismo da Vistoria (capacidade) |
| D19a | **Revisão 1 (FB1):** no mesmo arquivo saem o `TrilhoFabrica`, a aba `orcamento` da fábrica (`OrcamentoFabricaTab`, `ehDaFabrica`) e, no `OSFormModalShell`, o `:status-da-etapa` | Só apareciam em OS com `fase_fabrica`, que nenhuma OS nova recebe (03A D13). Tirar agora evita duas abas com o mesmo id `orcamento` |
| D20 | Conteúdo: código e versão (link **"Abrir orçamento"**, que fecha o modal e vai para `/orcamentos/:id`), data e quem aprovou, projeto, móveis aprovados (nome, ambiente, medidas, quantidade), "4 móveis não aprovados", instalação, total aprovado, sinal combinado × recebido | O marceneiro e o atendente precisam ver o que foi vendido sem abrir outro módulo. **Nenhum custo** (08A Revisão 1) |
| D21 | Sinal combinado maior que o recebido: aviso "Sinal combinado R$ 3.695,56 — recebido R$ 0,00." com o botão **"Preencher adiantamento"**, que coloca o valor que falta no campo Adiantamento do resumo da OS (sem salvar; o usuário escolhe a forma e salva como hoje) | O7a: o lugar de lançar o sinal é o adiantamento da OS. O botão evita redigitar o valor, sem criar um caminho novo de dinheiro |
| D22 | Total atual da OS diferente do total aprovado (desconto mudado, item manual, frete): linha "Total aprovado no orçamento: R$ 7.885,14 · total atual da OS: R$ 8.035,14" | 08A §9: os dois podem divergir de propósito; a tela mostra, não esconde |
| D23 | OS sem orçamento (resposta `404`): a aba mostra "Esta OS não foi gerada por um orçamento." | Caso de desenvolvimento e de OS antiga; não pode quebrar a aba |
| D24 | **Cadeado nos itens (F4), Revisão 1:** a função que já existe, `veioDoOrcamento(item)`, passa a responder `true` também para `item.origem` preenchida. O resto é o de hoje: no lugar de editar/remover, o cadeado; `title` "Veio do orçamento aprovado. Para mudar, desfaça a aprovação ou crie uma nova versão do orçamento." Itens sem `origem` e sem `fabrica_orcamento_id` (todos os de hoje) continuam exatamente iguais | F4a. A regra olha só os campos do item, nunca o segmento; reaproveita o cadeado existente |
| D24a | **Peças embutidas do orçamento (Revisão 1):** itens com `origem` **e** `tipo = PRODUTO` ficam no fim da lista, num grupo recolhido "Material do orçamento (N itens)" que abre com um clique. Mostram nome, quantidade e unidade; valor R$ 0,00 como qualquer peça embutida | Uma cozinha traz 20 linhas de chapa, fita e ferragem; abertas por padrão, empurrariam os móveis para fora da tela. Item sem `origem` nunca entra no grupo |

### 4.6. Proposta aprovada

| # | Decisão | Motivo |
|---|---------|--------|
| D25 | `montarDadosProposta(detalhe, hoje, { modo: 'aprovada' })` usa só os móveis aprovados, a instalação aprovada e `aprovacao.calculo`. Título **"PROPOSTA APROVADA"**, a linha "Aprovada em 06/10/2026 · OS-2026-000512", e o sinal mostrado como "Sinal: R$ 3.695,56 — recebido em PIX" ou "— a receber" | É o documento que o cliente assina como pedido. Mostrar móveis que ele recusou num documento de aceite seria confuso |
| D26 | A proposta "normal" de um orçamento aprovado (botão "Proposta" do cabeçalho) continua mostrando **tudo o que foi proposto**, sem faixa (07 D6) | É o que o cliente recebeu antes de decidir; o histórico não muda |

---

## 5. Contratos consumidos

Spec 08A §6 e a **Revisão 1** da 08A (`GET /por-os/{numero_os}`, `os_numero` na lista). Do sistema existente: `getUniqueOS`, `useOSCreateFlow().openExistingOS`, `getPaymentMethodsAll` (formas de pagamento), `GerenteAprovacaoModal`.

```ts
// osItem.schema.ts ⚠️ — só leitura; o envio (OsItemCreateSchema) não muda.
export const OsItemReadSchema = z.object({
  // ...campos de hoje
  /** De onde o item veio (ex.: 'ORCAMENTO_MARCENARIA'). Null = item comum, editável (F4a). */
  origem: z.string().nullable().optional(),
});
```

---

## 6. Telas

### 6.1. Aprovar

```
Aprovar orçamento ORC-2026-000084 v2                                       [×]
⚠ A validade terminou em 21/10/2026. Os preços podem ter mudado desde o envio.

1. O que o cliente aprovou
 ▾ Cozinha Gourmet                                       [Todos] [Nenhum]
   [x] Torre Quente            700 × 2200 × 600 mm   1×        R$ 4.222,75
   [x] Armário aéreo           …                     3×        R$ 2.100,00
   [ ] Ilha                    …                     1×        R$ 1.977,40
 ▾ Dormitório casal
   [ ] Guarda-roupa            …                     1×        R$ 1.425,00
 [x] Instalação e montagem                                     R$ 1.425,00

2. Valores
   Desconto [ 5 ]% ≈ R$ 387,39
   Bruto R$ 7.747,75 · Desconto − R$ 387,39 · Total R$ 7.360,36
   Sinal combinado (40%) R$ 2.944,14 · Saldo R$ 4.416,22
   Previsão de entrega: 05/11/2026 (30 dias)
   Margem líquida R$ 2.610,20 (35,5%)                      (só com view_custos)

3. Sinal
   O cliente já pagou o sinal?   ( ) Sim, recebi   ( ) Ainda não
   └ Sim:  Valor recebido R$ [2.944,14]   Forma [PIX ▾]   [ ] Usar crédito (R$ 0,00)

                                        [Cancelar]  [Aprovar e gerar OS]
```

- O preço por móvel aparece aqui (é tela interna, não documento do cliente).
- Fechar com algo alterado pergunta "Descartar a aprovação?".

### 6.2. Aba "Orçamento" na OS

```
Orçamento ORC-2026-000084 v2                                   [Abrir orçamento]
Aprovado em 06/10/2026 por Alan Alves de Amorim · Residencial Alpha Ville - Apto 802

Móveis aprovados (3)                                    4 móveis não aprovados
  Torre Quente            Cozinha Gourmet   700 × 2200 × 600 mm   1×
  Armário aéreo           Cozinha Gourmet   …                     3×
  Instalação e montagem

Total aprovado R$ 7.360,36
⚠ Sinal combinado R$ 2.944,14 — recebido R$ 0,00          [Preencher adiantamento]
```

---

## 7. Especificação técnica

### 7.1. Aba na OS — `OSFormTabsContent.vue` ⚠️

```ts
type TabType = 'objeto' | 'vistoria' | 'diagnostico' | 'servicos' | 'orcamento';   // + 'orcamento'

const { temVistoria, temDiagnostico, temImagemNaEntrada, temOrcamentoTecnico } = useCapacidades();

// dentro de allTabs, depois de 'servicos':
  // Orçamento: só onde o segmento declara orçamento técnico, e só numa OS que já existe (D19).
  if (temOrcamentoTecnico.value && !view.isCreateMode.value) {
    tabs.push({ id: 'orcamento', label: 'Orçamento', icon: FileSpreadsheet });
  }
```

```vue
<!-- Fora do <fieldset> travável: a aba é só leitura e o link precisa funcionar em OS finalizada. -->
<OSOrcamentoTab
  v-if="activeTab === 'orcamento'"
  :numero-os="view.currentOSData.value?.numero_os ?? ''"
  @preencher-adiantamento="view.preencherAdiantamento"
  @abrir-orcamento="view.fecharEIr"
/>
```

- `view.preencherAdiantamento(centavos)` e `view.fecharEIr(rota)`: duas funções novas no contexto `useOSFormView`, pequenas — a primeira coloca o valor no mesmo estado que o campo Adiantamento do resumo usa; a segunda fecha o modal (com a pergunta de alterações não salvas que já existe) e navega.
- `useOrcamentoDaOS(numeroOs)` só faz a chamada quando a aba é aberta (`enabled` pela aba ativa): as OS dos outros segmentos nunca chamam `/marcenaria/...`.

### 7.2. Cadeado — `OSServicesTab.vue` ⚠️ (Revisão 1)

```ts
/** Item gerado por um orçamento (fábrica antiga ou marcenaria): muda pelo orçamento, não aqui (F4a). */
function veioDoOrcamento(item: OsItem): boolean {
  const daFabrica = 'fabrica_orcamento_id' in item && item.fabrica_orcamento_id != null; // regra de hoje
  const comOrigem = 'origem' in item && !!item.origem;                                    // 08A: coluna genérica
  return daFabrica || comOrigem;
}

/** Peças embutidas que vieram do orçamento: vão para o grupo recolhido do fim (D24a). */
const materialDoOrcamento = computed(() =>
  displayItems.value.filter((item) => veioDoOrcamento(item) && item.tipo === 'PRODUTO'),
);
```

- O template de hoje (cadeado no lugar de editar/remover quando `veioDoOrcamento`) **não muda**; muda só o `title`, que passa a servir aos dois casos.
- O laço principal pula os itens de `materialDoOrcamento`; eles aparecem no grupo "Material do orçamento ({{ n }} itens)", recolhido por padrão.
- `displayItems` mistura itens salvos e itens novos ainda em memória (sem `origem`): o `item.origem` dos novos é `undefined`, então eles continuam editáveis.

### 7.3. Aprovar — `useAprovacao.ts`

```ts
export function useAprovacao(id: Ref<number>, fila: FilaOrcamento) {
  const toast = useToast();

  /** Aprova pela fila (06B D7). Devolve o detalhe novo, com `os` preenchido. */
  async function aprovar(entrada: AprovacaoEntrada) {
    const detalhe = await fila.enfileirar((revisao) => postAprovar(id.value, revisao, entrada));
    return detalhe;                                           // o editor abre o OSCriadaModal (D7)
  }

  /** Desfaz; pede o PIN quando a API responder REQUER_APROVACAO_GERENTE (D17). */
  async function desfazer(entrada: DesfazerEntrada, pedirPin: () => Promise<string | null>) {
    try {
      return await fila.enfileirar((revisao) => postDesfazer(id.value, revisao, entrada));
    } catch (erro) {
      if (detalheDoErro(erro) !== 'REQUER_APROVACAO_GERENTE') throw erro;
      const pin = await pedirPin();                           // null = o usuário desistiu
      if (!pin) return null;
      return fila.enfileirar((revisao) => postDesfazer(id.value, revisao, { ...entrada, codigo_gerente: pin }));
    }
  }

  return { aprovar, desfazer };
}
```

Depois de aprovar ou desfazer, invalidar também as queries de **OS** (lista, estatísticas e o painel do dashboard), além das do orçamento: uma OS nasceu ou foi cancelada.

### 7.4. Validação do `AprovarModal` (zod)

```ts
const aprovarFormSchema = z.object({
  movel_ids: z.array(z.number()).min(1, 'Escolha pelo menos um móvel.'),
  incluir_instalacao: z.boolean(),
  desconto: z.object({ modo: z.enum(['PERCENTUAL', 'VALOR']), valor: z.number().int().min(0) }),
  sinal_recebido: z.boolean({ required_error: 'Diga se o sinal já foi pago.' }),   // D8: sem padrão
  sinal_valor_centavos: z.number().int().min(0),
  forma_pagamento_id: z.number().nullable(),
  usar_credito_cliente: z.boolean(),
}).superRefine((f, ctx) => {
  // D9: recebido exige forma, a não ser que use o crédito.
  if (f.sinal_recebido && !f.usar_credito_cliente && !f.forma_pagamento_id) {
    ctx.addIssue({ code: 'custom', path: ['forma_pagamento_id'], message: 'Informe a forma de pagamento do sinal.' });
  }
});
```

O teto do sinal (até o total) vem da API (`422`), porque o total depende da prévia.

### 7.5. Lista

Coluna **OS** (depois de Status): o `os_numero` como link que abre a OS (`getUniqueOS` + `openExistingOS`), só em `APROVADO`. Nos demais, vazio.

---

## 8. Prova de não regressão (⚠️ PR1)

1. `npm run test` e `npx vue-tsc --noEmit` sem erros.
2. Informática, oficina e serigrafia: o modal de OS tem as mesmas abas, na mesma ordem (snapshot de `visibleTabs`).
3. Mesmos segmentos: na aba "Serviços e Peças", todo item mostra editar e remover como hoje (os itens vêm com `origem: null`).
4. Nenhuma chamada a `/marcenaria/...` ao abrir OS nesses segmentos (DevTools).
5. Resumo da OS (adiantamento, crédito, frete): sem mudança visual nem de comportamento nos outros segmentos (`preencherAdiantamento` só é chamado pela aba nova).

## 9. Limitações conhecidas

- **Sinal fora do caixa** (08A §9): lançar o adiantamento pela OS segue a regra de hoje.
- **Aba "Orçamento" sem custos**, mesmo para o dono: o lugar de ver margem é o orçamento (link na aba).
- **Proposta aprovada não guarda cópia** (07 D1): reimprime a partir do orçamento, que fica somente leitura depois de aprovado (então sai igual).

---

## 10. Critérios de aceite

- [ ] "Aprovar" aparece em rascunho, enviado e vencido (com o aviso certo) e some depois de aprovar.
- [ ] Marcar e desmarcar móveis, a instalação e mudar o desconto atualizam a prévia; móvel sem preço não pode ser marcado.
- [ ] O botão só habilita com um móvel marcado e a pergunta do sinal respondida; "Sim" exige forma (ou crédito).
- [ ] Aprovar cria a OS; o modal oferece abrir a OS e imprimir a proposta aprovada.
- [ ] Orçamento aprovado: faixa com a OS, móveis não aprovados esmaecidos, resumo "Proposto × Aprovado".
- [ ] Desfazer pede motivo, destino do sinal e PIN quando a loja exige; sem poder desfazer, mostra os motivos.
- [ ] OS da marcenaria: aba "Orçamento" com os móveis, link para o orçamento, aviso do sinal com "Preencher adiantamento" e a diferença de totais.
- [ ] Itens do orçamento com cadeado e sem editar/remover; item manual na mesma OS editável.
- [ ] Proposta aprovada só com os aprovados; proposta normal com tudo.
- [ ] Prova de não regressão (§8) completa; código comentado (PR6).

## 11. Casos de teste

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | `OSFormTabsContent`, informática | Abas iguais às de hoje (snapshot) |
| 02 | `OSFormTabsContent`, marcenaria, OS existente | Aba "Orçamento" depois de "Serviços e Peças" |
| 03 | Mesmo, modo criação | Sem a aba |
| 04 | `OSServicesTab` com item de serviço `origem: 'ORCAMENTO_MARCENARIA'` | Cadeado; sem editar/remover |
| 05 | Mesmo componente com item `origem: null` e item novo sem o campo | Botões de hoje |
| 05a | Item com `fabrica_orcamento_id` (regra de hoje) | Cadeado, como antes |
| 05b | 3 peças embutidas com `origem` | Fora da lista principal; grupo "Material do orçamento (3 itens)" recolhido |
| 05c | `OSFormTabsContent` e `OSFormModalShell` | Sem `TrilhoFabrica`, sem `OrcamentoFabricaTab`, sem `status-da-etapa` |
| 06 | `AprovarModal`: desmarcar todos | Botão desabilitado; mensagem "Escolha pelo menos um móvel." |
| 07 | `AprovarModal`: sem responder o sinal | Botão desabilitado |
| 08 | `AprovarModal`: "Sim" sem forma e sem crédito | Erro na forma |
| 09 | `AprovarModal`: 3 mudanças em 300 ms | Uma chamada de simulação |
| 10 | `AprovarModal`: simulação com `422 campo desconto` | Erro embaixo do desconto; botão desabilitado |
| 11 | `AprovarModal`: status `VENCIDO` / `RASCUNHO` | Avisos do D5 |
| 12 | `useAprovacao.desfazer` com `REQUER_APROVACAO_GERENTE` | Pede o PIN e reenvia com `codigo_gerente` |
| 13 | `useAprovacao.desfazer`, PIN cancelado | Nada é enviado de novo; retorna null |
| 14 | `EditorFaixaStatus` aprovado, sem poder desfazer | Sem o botão; ícone com os motivos |
| 15 | `EditorFaixaStatus` com OS cancelada | "Nova versão" |
| 16 | `montarDadosProposta` modo `aprovada` | Só os aprovados; totais de `aprovacao.calculo`; título "PROPOSTA APROVADA" |
| 17 | `OSOrcamentoTab` com sinal recebido menor que o combinado | Aviso e "Preencher adiantamento" com a diferença |
| 18 | `OSOrcamentoTab` com `404` | "Esta OS não foi gerada por um orçamento." |

### Roteiro manual (dev)

1. Cenário B da Spec 05 enviado. Aprovar só a cozinha e a instalação, desconto 5%, sinal "Ainda não". Conferir a OS: itens, desconto, total, responsável, previsão, aba "Orçamento" com o aviso do sinal.
2. Na OS: "Preencher adiantamento", escolher PIX, salvar. Voltar ao orçamento: "recebido" atualizado.
3. Tentar editar a Torre Quente na OS: sem botões. Adicionar um item manual: editável.
4. Desfazer a aprovação com o sinal virando crédito; aprovar de novo usando o crédito.
5. Mudar a OS para "Em Produção": o desfazer some e os motivos aparecem.
6. Imprimir a proposta aprovada e a proposta normal; comparar.
7. Informática: §8 inteiro.
