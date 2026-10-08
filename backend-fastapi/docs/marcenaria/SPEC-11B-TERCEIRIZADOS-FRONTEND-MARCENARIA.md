# Spec 11B — Móveis Terceirizados (Frontend)

| Campo        | Valor                                                                                 |
|--------------|---------------------------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                                       |
| Camada       | Frontend (Vue 3 + TypeScript) ⚠️ código compartilhado (tela de Serviços)              |
| Dependências | Specs 10B (aba Separação), 11A (API) · módulo Compras (rotas `purchases-orders` e `purchases-receiving`, usadas como são) |
| Bloqueia     | Spec 12B (o terceirizado conferido aparece pronto na Produção)                        |
| Referência   | SPEC-00: E6, E6a, E6b, P3, P4, T1, FB2 · PR1, PR3, PR6                                |

> **Revisão 1 (08/10/2026) — spec reescrita (SPEC-00 Revisão 15, E6b).** Com o módulo Compras, "Pedir à central" cria o pedido de serviço **no Compras** (11A D9), e enviar, receber e lançar a conta são feitos lá: saem o passo 2 do "Receber" (oferta de conta) e o `LancarContaModal`. A seção da OS mostra a situação que vem do pedido e leva ao Compras com um clique. Sem o módulo, ficam as ações manuais (enviar com nº e previsão, receber). "Conferir", "registrar problema" e a aba "Terceirizados" em Serviços continuam como estavam.

---

## 1. Objetivo

1. Na **OS**: acompanhar os móveis que vêm prontos da central — pedir, ver o pedido andar, conferir, registrar problema.
2. Na tela de **Serviços**: uma aba **"Terceirizados"** com todos os pedidos em aberto, destacando os atrasados, para o dono cobrar as centrais de uma vez.

## 2. Escopo

**Dentro do escopo**
- Seção "Móveis da central" na aba Separação da OS.
- Pedir à central (com o Compras) ou enviar e receber à mão (sem ele); conferir; problema; voltar.
- Aba "Terceirizados" em Serviços (capacidade `orcamento_tecnico`).

**Fora do escopo**
- Telas do Compras (pedido, recebimento, contas): usadas como são.
- Tela de Contas a Pagar.

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
        ├── PedirCentralModal.vue                             # CRIAR — com o Compras
        ├── EnviarManualModal.vue · ReceberManualModal.vue    # CRIAR — sem o Compras
        ├── ProblemaModal.vue                                 # CRIAR
        └── TerceirizadosTab.vue                              # CRIAR — aba em Serviços
```

E `marcenaria/separacao/components/OSSeparacaoTab.vue` (10B) passa a montar a `SecaoTerceirizados` no topo.

---

## 4. Decisões

### 4.1. Na OS

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | Seção **"Móveis da central"** no **topo** da aba Separação, só quando a OS tem móvel terceirizado. Título com a contagem: "Móveis da central (2) · 1 atrasado" | O atraso da central atrasa a obra inteira; não pode ficar no fim de uma lista de 30 chapas |
| D2 | Linhas agrupadas por **central**, com telefone ao lado do nome. Cada linha: móvel, ambiente, medidas, quantidade, a situação como selo (A pedir / Pedido em rascunho / Pedido enviado / Recebido / Conferido / Recebido com problema) e o pedido com a previsão ("PC-000123 · chega 20/10", ou "Pedido 4521 · chega 20/10" no modo manual). Atrasado: selo vermelho "Atrasado 3 dias" | Quem liga para a central precisa do número do pedido na frente |
| D3 | Caixas de seleção por linha e uma barra de ações que age sobre os marcados; cada botão só habilita quando todos os marcados estão na situação de onde ele parte e são da mesma central (`title` explica por quê) | 11A D9: um pedido cobre vários móveis |
| D4 | **Com o módulo Compras** (`modo_compras` da resposta, 11A) e a permissão de gerir compras: botão **"Pedir à central"** (móveis "A pedir"). O modal mostra a central, os móveis, "Previsão de chegada" e "Observação" (opcionais), e avisa: "O pedido nasce como rascunho no Compras. Envie e receba por lá." Ao confirmar, toast com **"Abrir pedido PC-000123"** (leva a `purchases-orders`) | E6b. O pedido é do Compras; a marcenaria só o cria com os dados do orçamento |
| D5 | Com o pedido do Compras, cada linha tem o link **"Ver no Compras"**: em "Pedido enviado", leva a `purchases-receiving` com `?pedido={id}` (receber); nos outros, a `purchases-orders` | Um clique entre a fábrica e quem recebe |
| D6 | **Sem o módulo Compras:** botões **"Enviar pedido"** (modal com "Nº do pedido na central" e "Previsão de chegada", opcionais) e **"Receber"** (modal com a data, hoje). Abaixo da seção, a dica: "Lance a conta da central em Contas a Pagar, numa categoria de despesa." | E6b, modo manual; 09A D14 |
| D7 | **"Conferir"** (móveis "Recebido") nos dois modos. Menu da linha: **Registrar problema**, **Voltar um passo** (com confirmação dizendo para qual situação volta; no modo Compras, só "Conferido → Recebido") | 11A D4, D5 |
| D8 | Com `view_custos_marcenaria`, a linha mostra o valor orçado da central em cinza | 11A D13; P4 |
| D9 | OS fechada: seção somente leitura | 11A D7 |

### 4.2. Aba "Terceirizados" em Serviços

| # | Decisão | Motivo |
|---|---------|--------|
| D10 | Aba **"Terceirizados"** na tela de Serviços, depois de "Cadastro de Serviços", só com `temOrcamentoTecnico`. Mesmo mecanismo da aba "Revisões" da oficina (`temRevisoes`) | Precedente exato no código: aba por capacidade na mesma tela |
| D11 | Lista agrupada por **central**, com filtros "Situação" (padrão: **Pedido enviado**) e "Só atrasados"; colunas OS (link que abre a OS), cliente, móvel, pedido, enviado em, previsão, atraso | 11A D17. O padrão é o que se cobra |
| D12 | Cabeçalho de cada central com o telefone e a contagem ("Madeiranit · (85) 3333-0000 · 3 pedidos, 1 atrasado") | O dono resolve todos os móveis da central na mesma ligação |
| D13 | "Nova OS"/"Novo Serviço" do topo some nesta aba (como em "Revisões") | Nada a criar daqui |

---

## 5. Contratos consumidos

Spec 11A §6. Do sistema: `useAcessoCompras` (`modules/compras/shared/composables`), as rotas `purchases-orders` e `purchases-receiving` (esta aceita `?pedido=`), `getUniqueOS` + `openExistingOS`, `BaseDateInput`.

---

## 6. Telas

### 6.1. Seção na OS (com o Compras)

```
Móveis da central (3) · 1 atrasado
Madeiranit · (85) 3333-0000
 [x] Torre Quente      Cozinha Gourmet  700×2200×600  1×  [Pedido enviado] PC-000123 · chega 20/10  ⚠ Atrasado 3 dias  Ver no Compras ⋯
 [x] Painel TV         Sala de estar    …             1×  [Pedido enviado] PC-000123 · chega 20/10                    Ver no Compras ⋯
Central Norte · (85) 3444-0000
 [ ] Ilha              Cozinha Gourmet  …             1×  [A pedir]                                                                   ⋯
                                                                    [Pedir à central] [Conferir]
```

### 6.2. Sem o Compras

```
                                                     [Enviar pedido] [Receber] [Conferir]
Lance a conta da central em Contas a Pagar, numa categoria de despesa.
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

### 7.2. Quem pode pedir

```ts
/** "Pedir à central" é ato do Compras: módulo e permissão de gerir compras (11A D10). */
const podePedirPeloCompras = computed(() =>
  dados.value?.modo_compras === true && acessoCompras.podeGerenciar.value,
);
```

`useAcessoCompras` é o composable do próprio Compras: `podeGerenciar` já combina o módulo ativo com a permissão `managePurchases` (conferido em 08/10).

### 7.3. Seleção e ações

```ts
/** A ação só habilita quando todos os marcados partem da mesma situação e da mesma central (D3). */
function podeAplicar(acao: 'pedir' | 'enviar' | 'receber' | 'conferir'): { ok: boolean; motivo?: string } {
  const origem = { pedir: 'A_PEDIR', enviar: 'A_PEDIR', receber: 'ENVIADO', conferir: 'RECEBIDO' }[acao];
  const marcados = linhas.value.filter((l) => selecionados.value.has(l.movel_id));
  if (!marcados.length) return { ok: false, motivo: 'Marque pelo menos um móvel.' };
  if (new Set(marcados.map((l) => l.central.id)).size > 1) return { ok: false, motivo: 'Marque móveis da mesma central.' };
  if (marcados.some((l) => l.situacao !== origem)) return { ok: false, motivo: `Só móveis "${ROTULO[origem]}".` };
  if (acao === 'pedir' && marcados.some((l) => l.pedido)) return { ok: false, motivo: 'Há móvel com pedido em rascunho.' };
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
4. Telas do Compras sem mudança.

## 9. Limitações conhecidas

- Sem aviso ativo (notificação) de atraso: o atraso aparece quando alguém abre a OS ou a aba.
- Sem o Compras, a conta da central é lançada à mão.

---

## 10. Critérios de aceite

- [ ] Seção "Móveis da central" no topo da Separação, só com terceirizados, agrupada por central, com atraso em destaque.
- [ ] Com o Compras: "Pedir à central" cria um pedido para vários móveis; a situação acompanha o pedido; "Ver no Compras" leva ao pedido ou ao recebimento.
- [ ] Sem o Compras: enviar (nº e previsão) e receber à mão, com a dica da conta.
- [ ] Conferir, registrar problema e voltar um passo, com confirmação.
- [ ] Valor orçado só com custos.
- [ ] Aba "Terceirizados" em Serviços com o filtro padrão "Pedido enviado" e "Só atrasados".
- [ ] Prova de não regressão (§8); código comentado (PR6).

## 11. Casos de teste

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | `OrdemServicoView`, informática / oficina / marcenaria | Abas de hoje / com Revisões / com Terceirizados |
| 02 | `OSSeparacaoTab` sem terceirizados | Sem a seção |
| 03 | `podeAplicar('pedir')` com centrais diferentes | Motivo "Marque móveis da mesma central." |
| 04 | `podeAplicar('conferir')` com um "A pedir" marcado | Motivo de situação |
| 05 | `modo_compras = true` e permissão de gerir compras | "Pedir à central"; sem "Enviar pedido"/"Receber" manuais |
| 06 | `modo_compras = false` | "Enviar pedido" e "Receber"; dica da conta |
| 07 | Pedido criado | Toast com "Abrir pedido PC-…" |
| 08 | Linha "Pedido enviado" com pedido do Compras | "Ver no Compras" leva a `purchases-receiving?pedido={id}` |
| 09 | `TerceirizadoLinha` atrasado 3 dias | Selo "Atrasado 3 dias" |
| 10 | Voltar um passo de "Conferido" | Confirmação "Voltar para Recebido?" |
| 11 | `TerceirizadosTab` padrão | Só "Pedido enviado", agrupado por central |
| 12 | Sem `view_custos_marcenaria` | Sem valor orçado |

### Roteiro manual (dev)

1. Com o módulo Compras: OS com 2 móveis terceirizados da mesma central e 1 de outra. Pedir os 2 juntos; abrir o pedido no Compras, enviar, receber (com a conta); conferir na OS.
2. Aba Serviços › Terceirizados: ver o atraso agrupado pela central.
3. Sem o módulo Compras (licença sem COMPRAS): enviar e receber à mão; lançar a conta em Contas a Pagar.
4. Registrar problema no terceiro; voltar um passo.
5. Informática e oficina: §8.
