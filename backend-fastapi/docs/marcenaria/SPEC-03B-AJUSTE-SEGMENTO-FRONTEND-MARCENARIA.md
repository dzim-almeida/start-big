# Spec 03B — Ajuste do Segmento Marcenaria (Frontend)

| Campo        | Valor                                                                   |
|--------------|-------------------------------------------------------------------------|
| Status       | Rascunho — aguardando aprovação                                         |
| Camada       | Frontend (Vue 3 + TypeScript) ⚠️ código compartilhado                   |
| Dependências | Spec 03A (contrato com `criacao_manual`, só Planejados)                 |
| Bloqueia     | Spec 06B, Spec 08B                                                      |
| Referência   | SPEC-00 (Revisão 4): O4, E0, E0a, E0b, E0c · SPEC-00 (Revisão 15): FB1 · PR1, PR6 · SPEC-03A |

> **Revisão 3 (08/10/2026) — FB1, telas da fábrica retiradas.** A aposentadoria da fábrica (SPEC-00 FB1, Spec 03A Revisão 3) chega às telas: saem a chave "Modo fábrica" de Configurações › OS, a linha "Fábrica" dos cargos, a seção "Insumo da fábrica" do produto e a rota `/fabrica/separacao`. As partes da fábrica **dentro** do modal de OS (trilho, aba Orçamento da fábrica, trava do status) já não aparecem (dependem de `fase_fabrica`, que nenhuma OS nova recebe) e saem na Spec 08B, que reorganiza essas abas. A pasta `modules/order-service/fabrica/` fica (inerte) até a limpeza depois do piloto. Novas seções: D11–D15, §6.9, casos 19–24.
>
> **Revisão 2 (06/10/2026) — Reforma de móveis fora da fase 1 (decisão do usuário):** spec reescrita. Saem o seletor com Reforma e a gravação do tipo padrão (a pergunta da §8 da versão anterior perdeu o objeto: a serigrafia **não muda**). Entra a regra do botão "Criar OS" (E0c). A referência da Reforma está na SPEC-00 §7.1.

---

## 1. Objetivo

Levar para as telas o que a Spec 03A mudou no registry:

1. **Os botões "Criar OS" somem** num segmento em que nenhum tipo pode ser criado à mão. Hoje, só na marcenaria. A Spec 06B os transforma em "Novo orçamento".
2. **Numa OS de Planejados, o tipo aparece travado**, com o motivo.
3. **A aprovação por item some da marcenaria** já no carregamento (fallback de capacidades sem `aprovacao_itens`).
4. **Textos** que citavam campos que saíram (impressão de Planejados, dica do onboarding) passam a falar do orçamento.
5. **As portas de entrada da fábrica saem das telas** (Revisão 3, FB1).

## 2. Escopo

**Dentro do escopo**
- Tipo do contrato (`criacao_manual`).
- `useTiposDeTrabalho`: "o segmento permite criar OS à mão?" e "este tipo pode ser trocado?".
- Botão "Nova OS" da tela de OS e atalho "Criar OS" do menu principal.
- `OSObjetoDinamicoTab.vue`: tipo travado com o motivo.
- `useCapacidades.ts`: fallback da marcenaria sem `aprovacao_itens`.
- `textosImpressaoOS.ts`: pacote `planejados`.
- `sign-in/constants/segments.ts`: dica do card Marcenaria.
- Telas da fábrica (Revisão 3): bloco "Fábrica de planejados" em Configurações › OS, linha "Fábrica" da matriz de cargos, seção "Insumo da fábrica" do produto, rota `/fabrica/separacao`.
- Testes e roteiro manual.

**Fora do escopo**
- Tela e botão "Novo orçamento" (Spec 06B).
- Abas Orçamento, Separação, Produção e Entrega (Specs 08B, 10B, 12B, 13B).
- Textos jurídicos finais do Planejados (Specs 07 e 13B). Aqui só se tira o que ficou falso.
- Reforma de móveis (SPEC-00 §7.1).

---

## 3. Arquivos afetados

```
frontend/src/modules/
├── order-service/
│   ├── shared/segmento/
│   │   ├── segmentDefinition.type.ts           # ALTERAR — criacao_manual em SegmentWorkType
│   │   ├── useTiposDeTrabalho.ts               # ALTERAR — podeCriarOSManual, tipoPodeSerTrocado
│   │   ├── useCapacidades.ts                   # ALTERAR — fallback da marcenaria sem aprovacao_itens
│   │   ├── textosImpressaoOS.ts                # ALTERAR — pacote planejados; exportar aplicarTipoTrabalho
│   │   └── __tests__/                          # CRIAR (pasta nova)
│   │       ├── useTiposDeTrabalho.spec.ts
│   │       └── textosImpressaoOS.spec.ts
│   ├── views/OrdemServicoView.vue              # ALTERAR ⚠️ — botão "Nova OS"
│   └── ordens/components/form/
│       ├── OSObjetoDinamicoTab.vue             # ALTERAR — tipo travado com o motivo
│       └── __tests__/OSObjetoDinamicoTab.spec.ts  # CRIAR
├── mainLayout/views/MainLayout.vue             # ALTERAR ⚠️ — atalho "Criar OS"
├── mainLayout/routes.ts                        # ALTERAR — sai a rota /fabrica/separacao (FB1)
├── sign-in/constants/segments.ts               # ALTERAR — dica da marcenaria
├── configuracoes/components/sections/ordens-de-servico/components/OrdensDeServico.vue
│                                               # ALTERAR — sai o bloco "Fábrica de planejados" (FB1)
├── employees/constants/positions.constants.ts  # ALTERAR — sai a linha "Fábrica" (FB1)
├── products/inventory/components/ProductModal.vue  # ALTERAR — sai a seção "Insumo da fábrica" (FB1)
└── order-service/fabrica/__tests__/cargos.spec.ts  # REMOVER — testava a linha que sai (D15)
```

| Arquivo | Faz | Não faz |
|---------|-----|---------|
| `useTiposDeTrabalho.ts` | Responde "posso criar OS à mão?" e "este tipo pode ser trocado?" | Saber nome de segmento (exceto o fallback de carregamento, como `useCapacidades`) |
| `OrdemServicoView.vue`, `MainLayout.vue` | Escondem o botão conforme a resposta | Regra |
| `OSObjetoDinamicoTab.vue` | Mostra o tipo travado e o motivo | Regra |

---

## 4. Decisões

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | `criacao_manual` ausente no contrato = `true` | Contrato antigo (sidecar desatualizado) continua funcionando como hoje |
| D2 | `podeCriarOSManual` = o segmento não tem tipos **ou** tem pelo menos um tipo criável à mão | Mesma regra do backend (03A, D5). Informática, oficina e serigrafia: `true` |
| D3 | Com `podeCriarOSManual = false`, o botão **"Nova OS"** (tela de OS, aba Ordens) e o atalho **"Criar OS"** (menu principal) **não aparecem** | E0c. Um botão que abre um formulário sem tipo possível é um beco sem saída. A Spec 06B troca por "Novo orçamento" |
| D4 | Enquanto o contrato carrega, vale um **fallback** por segmento (`marcenaria: false`) | Mesmo padrão do `useCapacidades`: sem ele, o botão aparece e some um instante depois |
| D5 | Na aba **Serviços** da tela de OS, o botão "Novo Serviço" **continua** | O catálogo de serviços não depende do tipo da OS |
| D6 | Numa OS cujo tipo não é criável à mão, a aba do objeto mostra "Tipo de trabalho: Móveis planejados · criada a partir de um orçamento" em vez do seletor | Explica por que não há escolha. Com um tipo só, o seletor já não apareceria (regra atual `opcoes.length > 1`) |
| D7 | Fallback de capacidades da marcenaria: `['imagem_na_entrada', 'garantia_prazo']` | O4 / 03A D10. Sem isso, os controles de aprovação apareceriam por um instante até o contrato chegar |
| D8 | Pacote de impressão `planejados`: tirar "descritos nesta OS" e "montagem externa"; usar "orçamento aprovado" e "instalação". Título "Entrega e Montagem" → "Entrega e Instalação" | Os campos saíram da OS (03A). A via diria que algo está "descrito nesta OS" quando não está |
| D9 | O pacote **base** `MARCENARIA` (textos da Reforma) **fica no código, sem mudança** | É a referência da Reforma (SPEC-00 §7.1). Toda OS da fase 1 tem o tipo `planejados` gravado pela Spec 08A, então o base não é usado |
| D10 | Dica do onboarding passa a citar a tela Orçamentos | O texto atual manda montar o orçamento na OS e cadastrar "metro linear" em Serviços (modelo de 16/09) |

### 4.1. Telas da fábrica (Revisão 3, FB1)

| # | Decisão | Motivo |
|---|---------|--------|
| D11 | Configurações › OS: sai o bloco **"Fábrica de planejados"** (as duas caixas, `modo_fabrica` e `fabrica_travar_etapas`). Os campos **continuam** no formulário, no store e no schema, e o corpo do `PUT` sai igual ao de hoje (com o valor que veio do backend) | Mexer no contrato de Configurações de OS tocaria uma tela de todos os segmentos (PR1). Uma caixa que não liga nada não pode continuar na tela (03A D13) |
| D12 | Cargos: sai a linha **"Fábrica"** (`id: 'fabrica'`, chaves `view_fabrica`/`manage_fabrica`) de `PERMISSION_MATRIX`. As constantes `PERMISSIONS.viewFabricaCustos`/`manageFabrica` e o mapa `fabrica` do `MODULE_PERMISSION_MAP` ficam (o código inerte da fábrica ainda os importa) | A linha era da marcenaria e não contava no nível de acesso (`segmento: 'marcenaria'`), então o nível dos cargos de todos os segmentos não muda. Cargos que já gravaram essas chaves ficam com elas, sem efeito |
| D13 | Produto: sai a seção **"Insumo da fábrica"** (`InsumoProdutoSection`) do `ProductModal`. O "Sofre perda" volta na Spec 04B, como caixa simples em Dados do Produto | A seção editava `unidade_consumo` e `consumo_por_unidade`, que o motor da Spec 05 não usa; deixá-la ensinaria o dono a preencher campos sem efeito |
| D14 | Rotas: sai `/fabrica/separacao/:numeroOs` (`fabrica-separacao`) | Separação da fábrica só abria OS do trilho, que não existe mais. A separação da marcenaria é a aba da Spec 10B |
| D15 | Testes: `order-service/fabrica/__tests__/cargos.spec.ts` sai (testava a linha D12); entra um caso que confere que a linha não existe (caso 20). `calculo.spec.ts`, `editor.spec.ts` e `insumo.spec.ts` **ficam** (testam funções que continuam na pasta inerte). Referência de 08/10: 188 testes; depois desta spec, 188 − 3 (os do `cargos.spec.ts`) + os casos novos | Nenhum teste sai em silêncio; a contagem prova que só saiu o que a D15 diz |

---

## 5. Contrato consumido

`GET /ordens-servico/definicao-campos` (Spec 03A §5.1). Marcenaria: `capacidades = [imagem_na_entrada, garantia_prazo]`; um tipo, `planejados`, com `criacao_manual: false`. Serigrafia: cada tipo com `criacao_manual: true`.

---

## 6. Especificação técnica

### 6.1. Tipo — `segmentDefinition.type.ts`

```ts
export interface SegmentWorkType {
  id: string;
  label: string;
  campos: SegmentField[];
  /**
   * false = a OS deste tipo só nasce de outro documento (ex.: Planejados nasce
   * da aprovação do orçamento). Ausente = true (contrato antigo). Spec 03B, D1.
   */
  criacao_manual?: boolean;
}
```

### 6.2. `useTiposDeTrabalho.ts` (acréscimos; o que existe não muda)

```ts
/**
 * Segmentos sem tipo criável à mão, usados SÓ enquanto o contrato carrega (D4).
 * Repete o backend (definicoes/marcenaria.py); quando o contrato chega, ele manda.
 */
const SEM_CRIACAO_MANUAL_FALLBACK: readonly string[] = ['marcenaria'];

export function useTiposDeTrabalho() {
  const { data, isPending } = useOSFieldDefinition();   // isPending: novo no destructuring
  const { segmento } = useSegmento();
  // ... tipos, temTipos, opcoes, tipoPadrao, tipoPorId, camposDoTipo, gruposDoTipo (como hoje)

  /** Um tipo pode ser criado à mão? Ausente = sim (D1). */
  const criavelAMao = (tipo: SegmentWorkType) => tipo.criacao_manual !== false;

  /** O segmento deixa abrir OS pelo botão "Nova OS"? (D2, D4) */
  const podeCriarOSManual = computed<boolean>(() => {
    if (isPending.value) return !SEM_CRIACAO_MANUAL_FALLBACK.includes(segmento.value ?? '');
    return !temTipos.value || tipos.value.some(criavelAMao);
  });

  /** O tipo gravado numa OS pode ser trocado? (D6) Desconhecido/ausente: pode. */
  function tipoPodeSerTrocado(id: string | null | undefined): boolean {
    const tipo = tipoPorId(id);
    return !tipo || criavelAMao(tipo);
  }

  return { /* ...os de hoje..., */ podeCriarOSManual, tipoPodeSerTrocado };
}
```

### 6.3. `OrdemServicoView.vue`

```ts
const { podeCriarOSManual } = useTiposDeTrabalho();

/** Botão do topo: "Nova OS" só se o segmento deixa criar à mão; "Novo Serviço" sempre (D3, D5). */
const mostrarBotaoAdicionar = computed(() => {
  if (activeTab.value === 'revisoes') return false;          // regra de hoje
  if (activeTab.value === 'ordens') return podeCriarOSManual.value;
  return true;                                               // aba Serviços
});
```

No template, trocar `v-if="activeTab !== 'revisoes'"` por `v-if="mostrarBotaoAdicionar"`.

### 6.4. `MainLayout.vue`

`quickActions` hoje é uma lista fixa. Passa a ser `computed`, filtrando o item `nova-os` quando `podeCriarOSManual` é `false`:

```ts
const { podeCriarOSManual } = useTiposDeTrabalho();

/** Atalhos do menu rápido; "Criar OS" só onde a OS pode ser criada à mão (D3). */
const quickActions = computed<QuickActionItem[]>(() =>
  TODOS_OS_ATALHOS.filter((acao) => acao.id !== 'nova-os' || podeCriarOSManual.value),
);
```

`TODOS_OS_ATALHOS` é a lista de hoje, sem mudança de ordem nem de texto. Conferir se `QuickActions` aceita a prop reativa (`:actions="quickActions"` já é passado; com `computed`, o template lê o valor automaticamente).

### 6.5. `OSObjetoDinamicoTab.vue`

```ts
const { opcoes, tipoPadrao, gruposDoTipo, tipoPorId, tipoPodeSerTrocado } = useTiposDeTrabalho();

/** OS de um tipo que só nasce de orçamento: mostra o tipo e o motivo (D6). */
const tipoTravado = computed(() => !tipoPodeSerTrocado(tipoAtual.value));
const labelDoTipoAtual = computed(() => tipoPorId(tipoAtual.value)?.label ?? '');
```

```vue
<!-- Seletor: regra de hoje, e nunca para tipo travado. -->
<BaseSelect v-if="opcoes.length > 1 && !tipoTravado" ... />

<!-- Tipo travado: informação, não campo (D6). -->
<p v-else-if="tipoTravado" class="col-span-2 text-sm text-zinc-600">
  Tipo de trabalho: <strong>{{ labelDoTipoAtual }}</strong> · criada a partir de um orçamento
</p>
```

Seguir as classes dos textos auxiliares já usados no formulário de OS.

### 6.6. `useCapacidades.ts`

```ts
  // Marcenaria (fase 1: só Móveis planejados). Os móveis são aprovados no
  // orçamento, não item a item na OS (SPEC-00, O4). Imagem na entrada e garantia
  // em dias continuam. A Reforma, quando voltar, devolve `aprovacao_itens`
  // (SPEC-00 §7.1).
  marcenaria: ['imagem_na_entrada', 'garantia_prazo'],
```

### 6.7. `textosImpressaoOS.ts` — pacote `planejados`

Exportar `aplicarTipoTrabalho` (só acrescentar `export`, sem mudar o corpo) para o teste. Textos sugeridos (revisão final com o dono nas Specs 07 e 13B):

| Chave | Hoje | Depois |
|-------|------|--------|
| `condicoesEntrada` | "…declara ter aprovado o projeto, os materiais, as cores e as ferragens **descritos nesta OS**… A **montagem externa** exige o ambiente pronto…" | "As medidas foram conferidas no local pelo responsável e o cliente declara ter aprovado o projeto, os materiais, as cores e as ferragens **do orçamento aprovado**. Alterações após a aprovação geram novo orçamento, e o prazo é contado a partir da aprovação e do pagamento do adiantamento. A **instalação** exige o ambiente pronto, limpo e livre no dia agendado; paredes, pisos e pontos de água, luz e gás são de responsabilidade do cliente." |
| `tituloPrazoRetirada` | "Entrega e Montagem" | "Entrega e Instalação" |
| `prazoRetiradaEntradaA4` | "…agendamento da entrega e **montagem**…" | "…agendamento da entrega e **instalação**…" |
| `prazoRetiradaGarantiaA4` | "…a partir da data da **montagem**…" | "…a partir da data da **instalação**…" |
| `cupom.condicoesEntrada` | "…aprovado projeto, materiais, cores e ferragens… **Montagem** exige ambiente pronto e livre." | "Medidas conferidas no local. Cliente declara ter aprovado o orcamento (projeto, materiais, cores e ferragens). Alteracoes apos a aprovacao geram novo orcamento. Instalacao exige ambiente pronto e livre." |
| `cupom.prazoRetirada` | "ENTREGA E MONTAGEM: …" | "ENTREGA E INSTALACAO: …" |

O pacote **base** `MARCENARIA` não muda (D9).

### 6.8. `sign-in/constants/segments.ts`

```ts
  marcenaria:
    'Para marcenarias, o trabalho começa em Orçamentos: você monta os ambientes e os móveis com '
    + 'chapas, fitas e ferragens cadastradas em Produtos, e a aprovação do cliente gera a OS.',
```

### 6.9. Telas da fábrica (Revisão 3)

```vue
<!-- OrdensDeServico.vue: o bloco inteiro "FÁBRICA (marcenaria)" sai.
     Os campos modo_fabrica e fabrica_travar_etapas continuam no `form`
     (vêm do backend e voltam iguais no PUT), mas não têm mais tela (D11). -->
```

```ts
// positions.constants.ts — sai o item { id: 'fabrica', ... segmento: 'marcenaria' } (D12).
// Nada mais muda na matriz: PERMISSION_KEYS já não contava essa linha.

// mainLayout/routes.ts — sai a rota 'fabrica-separacao' (D14).
```

```vue
<!-- ProductModal.vue: saem o defineAsyncComponent de InsumoProdutoSection e o
     bloco <template v-if="isMarcenaria"> "Insumo da fábrica" (D13). -->
```

Conferir com uma busca que nada mais importa `InsumoProdutoSection.vue` nem `SeparacaoView.vue` fora da própria pasta `fabrica/` (eles ficam no repositório, sem uso, até a limpeza).

---

## 7. Prova de não regressão (⚠️ PR1)

1. `npm run test` e `npx vue-tsc --noEmit` sem erros.
2. **Informática, oficina e serigrafia:** botão "Nova OS" e atalho "Criar OS" presentes, na mesma posição e com o mesmo texto; fluxo de criação igual. Serigrafia continua com o seletor Camisa/Sacola.
3. Atalhos do menu rápido: mesma ordem e mesmos textos nos três segmentos.
4. Impressão de oficina, assistência e serigrafia igual (snapshot dos pacotes).
5. **Configurações › OS** em informática, oficina e serigrafia: mesma tela e o mesmo corpo de `PUT` (comparar no DevTools). O bloco que saiu só aparecia na marcenaria.
6. **Cargos** em todos os segmentos: mesmas linhas e mesmo nível de acesso (snapshot de `getAccessLevel` para cargos de exemplo).

## 8. Limitações conhecidas

- **Marcenaria sem criação de OS** até a Spec 06B/08A: não há "Nova OS" nem "Novo orçamento". Em desenvolvimento, criar OS pelo serviço (03A). Nenhuma loja é afetada.
- **OS de Reforma em bancos de desenvolvimento** (criadas antes da 03A) abrem com o tipo desconhecido: sem seletor, campos dinâmicos vazios. Sem efeito em loja.

---

## 9. Critérios de aceite

- [ ] Marcenaria: sem botão "Nova OS" na aba Ordens, sem "Criar OS" no menu rápido, e sem piscar ao abrir o app.
- [ ] Marcenaria, aba Serviços: "Novo Serviço" continua.
- [ ] Marcenaria, OS de Planejados: "Tipo de trabalho: Móveis planejados · criada a partir de um orçamento"; nenhum seletor.
- [ ] Marcenaria: nenhum controle de aprovação por item, nem durante o carregamento.
- [ ] Impressão de Planejados sem "descritos nesta OS" nem "montagem externa".
- [ ] Dica do onboarding da marcenaria cita Orçamentos.
- [ ] Informática, oficina e serigrafia sem nenhuma mudança (§7).
- [ ] Contrato sem `criacao_manual`: tudo como hoje.
- [ ] Marcenaria: sem "Modo fábrica" em Configurações › OS, sem linha "Fábrica" nos cargos, sem "Insumo da fábrica" no produto; a rota `/fabrica/separacao` não existe mais.
- [ ] Corpo do `PUT` de Configurações › OS igual ao de antes em todos os segmentos.
- [ ] Contagem dos testes conforme a D15.
- [ ] Nenhum `if` com nome de segmento ou de tipo fora dos mapas de fallback; código novo comentado (PR6).

## 10. Casos de teste

### `useTiposDeTrabalho.spec.ts` (contrato e segmento substituídos por mocks)

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 01 | Marcenaria carregada (`planejados=false`) | `podeCriarOSManual = false` |
| 02 | Serigrafia carregada (os dois `true`) | `true` |
| 03 | Informática (sem tipos) | `true` |
| 04 | Contrato sem `criacao_manual` | `true` (D1) |
| 05 | Carregando, segmento `marcenaria` | `false` (fallback) |
| 06 | Carregando, segmento `serigrafia` | `true` |
| 07 | `tipoPodeSerTrocado('planejados')` / `('camisa')` / `(undefined)` / `('inexistente')` | `false` / `true` / `true` / `true` |
| 08 | `opcoes`, `tipoPadrao`, `gruposDoTipo` | Iguais a antes |

### Telas

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 09 | `OrdemServicoView`, marcenaria, aba Ordens | Sem botão |
| 10 | `OrdemServicoView`, marcenaria, aba Serviços | "Novo Serviço" visível |
| 11 | `OrdemServicoView`, serigrafia, aba Ordens | "Nova OS" visível |
| 12 | `MainLayout`, marcenaria | Atalhos sem `nova-os`; os outros 3 na mesma ordem |
| 13 | `MainLayout`, informática | Os 4 atalhos de hoje |
| 14 | `OSObjetoDinamicoTab`, OS `planejados` | Texto do tipo travado; nenhum `BaseSelect` de tipo |
| 15 | `OSObjetoDinamicoTab`, serigrafia | Seletor como hoje |

### `textosImpressaoOS.spec.ts`

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 16 | `aplicarTipoTrabalho(MARCENARIA, 'planejados')` | Nenhum texto com "nesta OS" nem "montagem externa"; título "Entrega e Instalação" |
| 17 | Pacote base `MARCENARIA` | Igual ao de antes (snapshot) |
| 18 | Pacotes de oficina, assistência e serigrafia | Iguais aos de antes (snapshot) |

### Telas da fábrica (Revisão 3)

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 19 | `OrdensDeServico.vue` na marcenaria | Sem as caixas "Modo fábrica" e "Travar etapas" |
| 20 | `PERMISSION_MATRIX` | Nenhum item com `id: 'fabrica'`; `PERMISSION_KEYS` igual ao de antes |
| 21 | `ProductModal` na marcenaria, produto salvo | Sem a seção "Insumo da fábrica" |
| 22 | Router | Sem a rota `fabrica-separacao` |
| 23 | Salvar Configurações › OS (qualquer segmento) | Corpo do `PUT` igual ao de antes (inclusive `modo_fabrica` com o valor que veio) |
| 24 | Contagem da suíte | 188 − 3 + novos (D15) |

### Roteiro manual (dev)

1. Marcenaria: abrir o app. Na tela de OS, aba Ordens, sem "Nova OS"; aba Serviços com "Novo Serviço". Menu rápido (Ctrl+K) sem "Criar OS". Nada pisca.
2. Criar uma OS de Planejados pelo serviço (03A) e abri-la: tipo travado com o motivo; sem botões de aprovação nos itens. Imprimir A4 e cupom: textos novos.
3. Informática, oficina e serigrafia: botões e atalhos como antes; criar uma OS em cada.
4. Onboarding: escolher Marcenaria e ler a dica.
