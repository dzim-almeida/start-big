# Spec 04B — Base da Marcenaria (Frontend): Perda no Produto, Parâmetros e Permissões

| Campo        | Valor                                                                    |
|--------------|--------------------------------------------------------------------------|
| Status       | Implementada em 09/10/2026 (roteiro manual da §11 pendente)              |
| Camada       | Frontend (Vue 3 + TypeScript) ⚠️ código compartilhado                    |
| Dependências | Spec 04A                                                                 |
| Bloqueia     | Spec 06B                                                                 |
| Referência   | SPEC-00: F6, P4, T6 · SPEC-00 (Revisão 15): FB1 · PR1, PR4, PR6 · SPEC-04A |

> **Revisão 1 (08/10/2026) — convergência com a branch (SPEC-00 Revisão 15).** (1) **Cargos:** a matriz já tem o campo `segmento` nas linhas (a linha "Fábrica" usava `segmento: 'marcenaria'`), e o código de hoje já tira essas linhas do nível de acesso (`PERMISSION_KEYS` filtra `!item.modulo && !item.segmento`) e só as mostra no segmento certo (`PositionModal.matrizVisivel`). A linha nova usa esse mecanismo: **saem** o campo `capacidade` em `positions.types.ts`, a função `chavesConsideradas` e as mudanças em `PositionModal.vue` e `PositionsPanel.vue` (D16, D17 reescritas; §6.8 e §8). (2) **Produto:** a seção "Insumo da fábrica" sai na Spec 03B; o "Sofre perda" vira a caixa simples desta spec. Menos código compartilhado mexido.

---

## 1. Objetivo

Levar para as telas as três peças da Spec 04A. Tudo aparece **só onde o segmento declara `orcamento_tecnico`** (hoje, a marcenaria):

1. **Cadastro de produto:** caixa "Sofre perda no orçamento", com explicação.
2. **Configurações → Marcenaria:** seção nova com os parâmetros do orçamento, as etapas de produção e o checklist de vistoria. Os custos ficam ocultos para quem não tem permissão, e a seção fica somente leitura para quem não pode alterar.
3. **Cargos:** linha nova na matriz de permissões, "Custos da Marcenaria" (Ver = ver custos e margens; Gerenciar = alterar os parâmetros).

## 2. Escopo

**Dentro do escopo**
- Capacidade `orcamento_tecnico` no tipo do contrato e no `useCapacidades` (com fallback).
- Campo `sofre_perda` no formulário, no schema e no envio do produto.
- Seção `marcenaria` em Configurações: query, mutation, formulário, editor de listas, integração com o salvar do modal.
- Chaves `view_custos_marcenaria` e `manage_custos_marcenaria` em `PERMISSIONS` e na matriz de cargos (linha com `segmento`, mecanismo existente).
- Testes e roteiro manual.

**Fora do escopo**
- Telas de orçamento (Spec 06B), inclusive o aviso de "custo/hora não configurado" no orçamento.
- Proteção da seção por PIN do gerente: a seção é protegida por **permissão** (D7).
- Mostrar `sofre_perda` na lista ou no card de produto (só o formulário).

---

## 3. Arquivos afetados

```
frontend/src/
├── shared/constants/permissions.constants.ts          # ALTERAR ⚠️ — 2 chaves + alias
├── modules/
│   ├── order-service/shared/segmento/
│   │   ├── segmentDefinition.type.ts                  # ALTERAR — 'orcamento_tecnico' em SegmentCapability
│   │   └── useCapacidades.ts                          # ALTERAR — temOrcamentoTecnico + fallback
│   ├── products/inventory/
│   │   ├── schemas/product.schema.ts                  # ALTERAR ⚠️ — sofre_perda
│   │   ├── composables/useProductForm.ts              # ALTERAR ⚠️ — campo, carga, envio condicional
│   │   ├── types/products.types.ts                    # ALTERAR — tipo
│   │   └── components/form/DadosProdutoSection.vue    # ALTERAR ⚠️ — caixa "Sofre perda"
│   ├── configuracoes/
│   │   ├── types/configuracoes.types.ts               # ALTERAR — SecaoId 'marcenaria'
│   │   ├── services/configuracaoMarcenaria.service.ts # CRIAR — GET/PUT
│   │   ├── schemas/configuracaoMarcenaria.schema.ts   # CRIAR — zod da resposta e do formulário
│   │   ├── composables/queries/useConfiguracaoMarcenariaQuery.ts   # CRIAR
│   │   ├── composables/mutates/useSalvarConfiguracaoMarcenaria.ts  # CRIAR
│   │   ├── components/ConfiguracoesModal.vue          # ALTERAR ⚠️ — seção, visibilidade, salvar
│   │   └── components/sections/marcenaria/components/
│   │       ├── Marcenaria.vue                         # CRIAR — a seção
│   │       ├── ListaTextosEditavel.vue                # CRIAR — editor de etapas/checklist
│   │       └── __tests__/…                            # CRIAR
│   └── employees/
│       └── constants/positions.constants.ts           # ALTERAR ⚠️ — linha nova com `segmento: 'marcenaria'` (Revisão 1)
```

| Arquivo | Faz | Não faz |
|---------|-----|---------|
| `Marcenaria.vue` | Formulário: mostra, converte % e R$, expõe `form`/`isDirty`/`resetar` | Salvar (é o modal, como nas outras seções) |
| `ListaTextosEditavel.vue` | Adicionar, editar, remover, subir/descer itens | Saber o que é etapa ou checklist |
| `configuracaoMarcenaria.schema.ts` | Validar a resposta da API e o formulário (zod) | — |
| `positions.constants.ts` | Declarar a linha nova (dado) | Lógica: o filtro por segmento e a conta do nível já existem |

---

## 4. Decisões

| # | Decisão | Motivo |
|---|---------|--------|
| D1 | Tudo desta spec aparece só com `temOrcamentoTecnico` (capacidade, nunca nome de segmento) | Regra do registry |
| D2 | `useCapacidades`: fallback da marcenaria passa a ser `['imagem_na_entrada', 'garantia_prazo', 'orcamento_tecnico']` | Sem fallback, a seção e o campo apareceriam um instante depois do resto |
| D3 | No produto, `sofre_perda` só vai no envio quando `temOrcamentoTecnico`. Nos outros segmentos o payload é **idêntico** ao de hoje | PR1. O backend aceita o campo em qualquer segmento, mas não há por que mudar o que os outros enviam |
| D4 | A caixa fica em **Dados do Produto**, perto de Unidade/Categoria, com texto de ajuda: "Marque para chapas e fitas de borda: o orçamento acrescenta o percentual de perda do corte. Não marque ferragens e acessórios." | O dono decide por produto e precisa saber o efeito na hora de marcar |
| D5 | A seção **Marcenaria** entra em Configurações depois de "Ordens de Serviço", só com `temOrcamentoTecnico` | Mesma regra de visibilidade das outras seções (`secoesVisiveis`) |
| D6 | A seção usa **query própria** (`GET /configuracoes/marcenaria`), e não o `configuracoesStore` global | O store carrega no boot para todos os segmentos; a rota responde 404 fora da marcenaria. Uma query com `enabled: temOrcamentoTecnico` evita a chamada inútil |
| D7 | A seção é protegida por **permissão**, não por PIN. Ela **não** entra na lista de seções protegíveis da aba Segurança | A lista da Segurança aparece para todos os segmentos; um item "Marcenaria" lá seria ruído para os outros. A permissão já protege no backend |
| D8 | Sem `view_custos_marcenaria` (resposta com `inclui_custos = false`): o bloco **Preço e custos** some e aparece a frase "Os custos e margens estão ocultos para o seu perfil." | P4. A resposta nem traz os campos (04A, D9) |
| D9 | Sem `manage_custos_marcenaria` (e sem ser master): a seção inteira fica **somente leitura**, com a frase "Só quem tem a permissão de alterar os parâmetros da marcenaria pode editar." O rodapé não oferece "Salvar" | O `PUT` exige a permissão (04A, D10). Deixar editar e falhar ao salvar é pior |
| D10 | Percentuais exibidos em **%** com 2 casas e convertidos para basis points; dinheiro em **R$** convertido para centavos (PR4). Conversão com `Math.round`, nunca truncando | O usuário pensa em %, o banco guarda inteiro |
| D11 | Cada parâmetro tem uma linha de ajuda com **exemplo numérico**. Markup: "Custo de R$ 100,00 → preço de R$ 190,00 com 90%." Perda: "1 chapa no projeto → 1,1 chapa no custo com 10%." | O dono vai mexer nesses números poucas vezes; o exemplo evita a confusão entre markup e margem |
| D12 | Custo/hora em **R$ 0,00** mostra aviso âmbar: "Sem custo por hora, a mão de obra calculada por horas sai zerada nos orçamentos." | Spec 04A §4.1 |
| D13 | Modo do RT em dois botões de opção com explicação: **"Sai da margem"** (padrão: o preço não muda; a marcenaria paga o arquiteto com o próprio lucro) e **"Embutido no preço"** (o preço sobe para cobrir o RT) | C5c. Rótulo técnico sozinho ("MARGEM"/"PRECO") não diz o efeito |
| D14 | Editor de listas: adicionar no fim, editar no lugar, remover, subir e descer. Não deixa remover o **último** item. Recusa item vazio, longo demais e repetido, com a mesma regra do backend (04A §6.4) | Mesmas regras dos dois lados: o erro aparece ao digitar, não ao salvar |
| D15 | Aviso fixo no topo das listas: "Mudanças valem para os próximos orçamentos e OS. As que já existem mantêm as etapas e o checklist que receberam." | D7 da 04A: cada OS copia a lista. Sem o aviso, o dono espera que a mudança apareça nas OS abertas |
| D16 | Matriz de cargos: linha **"Custos da Marcenaria"** (Ver / Gerenciar, sem Excluir), declarada com **`segmento: 'marcenaria'`** (Revisão 1), como a linha "Fábrica" fazia. Marcar **Gerenciar** marca **Ver** junto | P4; `manage` implica `view` (04A, D8). O campo `segmento` é dado da matriz, não `if` em componente (mesmo caso dos mapas de fallback) |
| D17 | O **nível de acesso** e o "Selecionar tudo" **não mudam de código**: `PERMISSION_KEYS` já exclui as linhas com `segmento`/`modulo`, e `chavesMarcarTudo` já soma as linhas visíveis (Revisão 1) | O risco que a D17 original tratava (um cargo "Administrador" da informática virar "Gestor" ao somar 2 chaves) já está resolvido no código de 08/10 (§8) |

---

## 5. Contratos consumidos

- `GET` e `PUT /configuracoes/marcenaria` (Spec 04A §5.2–5.4).
- Produto: `sofre_perda` em `ProdutoRead`, `ProdutoCreate`, `ProdutoUpdate` (Spec 04A §5.1).
- Contrato do segmento: `capacidades` inclui `orcamento_tecnico` na marcenaria (Spec 04A §6.1).

A resposta do `GET` é validada com **zod** (como as outras respostas de configuração), com união por `inclui_custos`:

```ts
const base = z.object({
  validade_dias: z.number().int(),
  prazo_entrega_dias: z.number().int(),
  etapas_producao: z.array(z.string()),
  checklist_vistoria: z.array(z.string()),
});

export const configuracaoMarcenariaSchema = z.discriminatedUnion('inclui_custos', [
  base.extend({ inclui_custos: z.literal(false) }),
  base.extend({
    inclui_custos: z.literal(true),
    markup_padrao_bp: z.number().int(),
    perda_padrao_bp: z.number().int(),
    custo_hora_centavos: z.number().int(),
    rt_padrao_bp: z.number().int(),
    rt_modo: z.enum(['MARGEM', 'PRECO']),
  }),
]);
```

---

## 6. Especificação técnica

### 6.1. Capacidade

```ts
// segmentDefinition.type.ts — acrescentar à união SegmentCapability:
  | 'orcamento_tecnico'

// useCapacidades.ts
  marcenaria: ['imagem_na_entrada', 'garantia_prazo', 'orcamento_tecnico'],
  // ...
  /** Orçamento técnico (marcenaria): parâmetros, "sofre perda", menu Orçamentos. */
  const temOrcamentoTecnico = computed(() => capacidades.value.includes('orcamento_tecnico'));
```

### 6.2. Permissões — `permissions.constants.ts`

```ts
  /** Ver custo, margem, markup e RT do orçamento de marcenaria (Spec 04A). */
  viewCustosMarcenaria: 'view_custos_marcenaria',
  /** Alterar os parâmetros de preço da marcenaria. Inclui o que `view` permite. */
  manageCustosMarcenaria: 'manage_custos_marcenaria',

// PERMISSION_ALIASES: quem gere também vê.
  [PERMISSIONS.viewCustosMarcenaria]: ['manage_custos_marcenaria'],
```

`hasPermission` não considera `is_master`. Onde a tela decidir pela permissão, usar `isMaster || hasPermission(...)`, como os outros pontos que já checam `is_master`.

### 6.3. Produto

- `product.schema.ts`: `sofre_perda: z.boolean().default(false)`.
- `useProductForm.ts`:
  - valor inicial `false`; ao carregar um produto, `product.sofre_perda ?? false`;
  - no envio (criação e edição): `...(temOrcamentoTecnico.value ? { sofre_perda: formData.sofre_perda } : {})` (D3).
- `DadosProdutoSection.vue`:

```vue
<!-- Só no segmento com orçamento técnico (D1, D4). -->
<div v-if="temOrcamentoTecnico" class="col-span-12">
  <BaseCheckbox v-model="sofre_perda" :disabled="disabled">
    Sofre perda no orçamento
  </BaseCheckbox>
  <p class="text-xs text-zinc-500 mt-1">
    Marque para chapas e fitas de borda: o orçamento acrescenta o percentual de perda
    do corte. Não marque ferragens e acessórios.
  </p>
</div>
```

### 6.4. Seção Marcenaria — estrutura da tela

```
Configurações › Marcenaria
├── [Bloco] Preço e custos                      (só com inclui_custos; D8)
│   ├── Markup padrão (%)          + ajuda com exemplo (D11)
│   ├── Perda padrão (%)           + ajuda com exemplo
│   ├── Custo da mão de obra por hora (R$)  + aviso se 0 (D12)
│   ├── RT padrão do arquiteto (%)
│   └── Modo do RT: ( ) Sai da margem  ( ) Embutido no preço  (D13)
├── [Bloco] Prazos
│   ├── Validade do orçamento (dias)
│   └── Prazo de entrega padrão (dias)  "contado da aprovação"
├── [Aviso] Mudanças valem para os próximos orçamentos e OS… (D15)
├── [Bloco] Etapas de produção     <ListaTextosEditavel max=20 maxChars=60>
└── [Bloco] Checklist de vistoria  <ListaTextosEditavel max=30 maxChars=120>
```

- Sem `inclui_custos`: no lugar do primeiro bloco, a frase do D8.
- Sem permissão de gerir: todos os campos `disabled`, a frase do D9 no topo, e o modal não mostra "Salvar" para esta seção.
- Carregando: esqueleto (mesmo componente de carregamento das outras seções). Erro: mensagem e "Tentar de novo".

### 6.5. `Marcenaria.vue` — formulário

```ts
const { data, isPending, isError, refetch } = useConfiguracaoMarcenariaQuery();   // enabled só com a capacidade
const { isMaster } = useUsuarioAtual();                                           // ou o padrão local
const { hasPermission } = useCheckPermission();
const podeGerir = computed(() => isMaster.value || hasPermission(PERMISSIONS.manageCustosMarcenaria));

/** Valores da API convertidos para a tela: bp → %, centavos → R$ (D10). */
function paraTela(api: ConfiguracaoMarcenaria): FormMarcenaria {
  return {
    validade_dias: api.validade_dias,
    prazo_entrega_dias: api.prazo_entrega_dias,
    etapas_producao: [...api.etapas_producao],             // cópia: editar não mexe no cache
    checklist_vistoria: [...api.checklist_vistoria],
    ...(api.inclui_custos && {
      markup_percentual: api.markup_padrao_bp / 100,       // 9000 bp -> 90 %
      perda_percentual: api.perda_padrao_bp / 100,
      custo_hora_reais: api.custo_hora_centavos / 100,     // 0 centavos -> R$ 0,00
      rt_percentual: api.rt_padrao_bp / 100,
      rt_modo: api.rt_modo,
    }),
  };
}

/** Formulário → corpo do PUT. Só manda custos se a tela os mostrou (D8). */
function paraApi(form: FormMarcenaria): ConfiguracaoMarcenariaUpdate {
  return {
    validade_dias: form.validade_dias,
    prazo_entrega_dias: form.prazo_entrega_dias,
    etapas_producao: form.etapas_producao.map((t) => t.trim()),
    checklist_vistoria: form.checklist_vistoria.map((t) => t.trim()),
    ...(form.markup_percentual !== undefined && {
      markup_padrao_bp: Math.round(form.markup_percentual * 100),   // arredonda, nunca trunca
      perda_padrao_bp: Math.round(form.perda_percentual! * 100),
      custo_hora_centavos: Math.round(form.custo_hora_reais! * 100),
      rt_padrao_bp: Math.round(form.rt_percentual! * 100),
      rt_modo: form.rt_modo!,
    }),
  };
}

const form = ref<FormMarcenaria>(...);       // preenchido quando `data` chega
const isDirty = computed(() => JSON.stringify(form.value) !== JSON.stringify(paraTela(data.value!)));
function resetar() { form.value = paraTela(data.value!); }
defineExpose({ form, isDirty, resetar, paraApi, podeGerir });
```

A validação do formulário usa um schema zod com os **mesmos limites** da Spec 04A §4.1, em %, R$ e dias, com as mesmas mensagens.

### 6.6. `ListaTextosEditavel.vue`

```ts
defineProps<{
  modelValue: string[];
  maxItens: number;
  maxCaracteres: number;
  rotuloItem: string;        // "etapa", "item do checklist" — usado nas mensagens e nos aria-label
  disabled?: boolean;
}>();
```

- Cada item: campo de texto, botões "subir", "descer" e "remover" com `aria-label` ("Subir etapa Corte").
- "Adicionar {rotuloItem}" no fim; desabilitado ao chegar em `maxItens`.
- "Remover" desabilitado quando só resta 1 item (D14).
- Erros ao lado do item: vazio, longo demais, repetido (comparação sem diferenciar maiúsculas e sem os espaços das pontas).
- Ao adicionar, o foco vai para o campo novo.
- Fica dentro da pasta da seção. Se as Specs 12B ou 13B precisarem do mesmo editor, ele sobe para `shared/components`.

### 6.7. `ConfiguracoesModal.vue`

- `secoes`: `{ id: 'marcenaria', label: 'Marcenaria', icone: Hammer }`, depois de "Ordens de Serviço".
- `componenteMap['marcenaria'] = Marcenaria`.
- `secoesVisiveis`: `if (s.id === 'marcenaria') return temOrcamentoTecnico.value`.
- `secoesFuncionais`: incluir `'marcenaria'` **só** quando `comp.podeGerir` for verdadeiro (senão o rodapé mostraria "Salvar" numa seção somente leitura; D9).
- `salvar()`: novo `case 'marcenaria'` chamando a mutation com `comp.paraApi(comp.form)` e o mesmo `fecharAposSalvar` dos outros casos. A mutation invalida a query da seção e mostra o toast de sucesso; erro `422` mostra a mensagem do backend.

### 6.8. Cargos — linha nova (Revisão 1)

```ts
// positions.constants.ts — linha nova, no fim da matriz:
  {
    id: 'marcenaria_custos',                 // identificador da linha na tela
    label: 'Custos da Marcenaria',
    description: 'Ver custos e margens; alterar markup, perda e RT',
    icon: Calculator,
    viewKey: 'view_custos_marcenaria',       // a MESMA chave que o backend confere (04A D8)
    manageKey: 'manage_custos_marcenaria',
    // Só na marcenaria, e fora do nível de acesso dos outros segmentos:
    // mecanismo que a matriz já tem (PERMISSION_KEYS e PositionModal.matrizVisivel).
    segmento: 'marcenaria',
  },
```

- `PERMISSION_KEYS`, `buildPermissionDefaults`, `PositionModal.vue` e `PositionsPanel.vue` **não mudam**: a linha com `segmento` já fica fora da base e só aparece no segmento certo. Um cargo novo nos outros segmentos é criado com o mesmo JSON de hoje.
- Marcar **Gerenciar** de "Custos da Marcenaria" marca **Ver** junto; desmarcar **Ver** desmarca **Gerenciar** (D16). Conferir como a matriz faz isso nas outras linhas e reaproveitar; se a regra não existir, ela entra só para as linhas com `segmento` (para não mudar as outras).
- `MODULE_PERMISSION_MAP`: **não** recebe a linha nova (as chaves são iguais no backend; 04A §8).

---

## 7. Prova de não regressão (⚠️ PR1)

1. `npm run test` e `npx vue-tsc --noEmit` sem erros.
2. **Produto:** em informática, oficina, serigrafia e PDV, criar e editar produto. O payload enviado é **idêntico** ao de antes (comparar no DevTools); a tela não mostra a caixa nova.
3. **Configurações:** nos outros segmentos, a lista de seções é a mesma, na mesma ordem; nenhuma chamada a `/configuracoes/marcenaria` no DevTools.
4. **Cargos:** nos outros segmentos, a matriz tem as mesmas linhas; `PERMISSION_KEYS` é igual ao de antes (snapshot); o **nível de acesso** de cada cargo existente é o mesmo (snapshot de `getAccessLevel` para cargos de exemplo: tudo marcado, metade, nada, `all`); "Selecionar tudo" marca as mesmas chaves de hoje.
5. **PDV:** a regra atual de Serviços (escondida, mas contada) continua igual.

## 8. Por que a D17 não precisa de código (Revisão 1)

`getPermissionStats` divide as chaves marcadas pelo total de `PERMISSION_KEYS`, e o nível sai da proporção (Administrador a partir de 85%, Gestor a partir de 55%). Se as 2 chaves da marcenaria entrassem em `PERMISSION_KEYS`, um cargo da informática com 28 de 31 chaves (90,3%, **Administrador**) passaria a 28 de 33 (84,8%, **Gestor**) sem ninguém mexer nele. O código de 08/10 já evita isso: `PERMISSION_KEYS = chavesDe(PERMISSION_MATRIX.filter((item) => !item.modulo && !item.segmento))`, e `chavesMarcarTudo` só soma as linhas com `modulo`/`segmento` que estão visíveis. Declarar a linha com `segmento: 'marcenaria'` basta; o teste 07 confere que `PERMISSION_KEYS` não mudou.

## 9. Limitações conhecidas

- O aviso de "custo/hora não configurado" **no orçamento** é da Spec 06B. Aqui ele aparece só na seção.
- A seção não mostra **quem** alterou os parâmetros por último (a tabela guarda só a data).

---

## 10. Critérios de aceite

- [ ] Marcenaria: caixa "Sofre perda no orçamento" com ajuda; grava e recarrega certo.
- [ ] Outros segmentos: produto sem a caixa e com payload idêntico ao de antes.
- [ ] Marcenaria, master: seção Marcenaria completa, editável; salvar aplica e fecha como as outras seções.
- [ ] Cargo com `view_custos_marcenaria`: vê tudo, somente leitura, sem "Salvar".
- [ ] Cargo sem nenhuma das duas: sem o bloco de custos (frase do D8), somente leitura.
- [ ] Percentuais e R$ convertem sem perder centavo (ex.: 12,35% → 1235 bp → 12,35%).
- [ ] Listas: adicionar, editar, reordenar e remover funcionam; não remove o último; recusa vazio, longo e repetido ao digitar.
- [ ] Custo/hora R$ 0,00 mostra o aviso âmbar.
- [ ] Matriz de cargos da marcenaria mostra "Custos da Marcenaria"; Gerenciar marca Ver.
- [ ] Nível de acesso dos cargos dos outros segmentos idêntico ao de antes (§7.4).
- [ ] Nada desta spec aparece sem a capacidade, nem durante o carregamento.
- [ ] Código novo comentado (PR6).

## 11. Casos de teste

### Unidade

| # | Arquivo / cenário | Resultado esperado |
|---|-------------------|--------------------|
| 01 | `paraTela` com 9000 bp, 1000 bp, 0 centavos | 90, 10, 0 |
| 02 | `paraApi` com 12,35% e R$ 45,50 | 1235 bp e 4550 centavos |
| 03 | `paraApi` com 0,005% (meio basis point) | Arredonda (1 bp), não trunca |
| 04 | `paraTela` com `inclui_custos = false` | Sem nenhum campo de custo |
| 05 | `paraApi` de um formulário sem custos | Corpo sem nenhuma chave de custo |
| 06 | Schema zod da resposta com `inclui_custos = true` sem `markup_padrao_bp` | Rejeitada |
| 07 | `PERMISSION_KEYS` | Igual ao de antes (snapshot); sem `view_custos_marcenaria` nem `manage_custos_marcenaria` |
| 08 | Linha `marcenaria_custos` | `segmento = 'marcenaria'`; chaves em `ALL_PERMISSION_KEYS` |
| 09 | `getAccessLevel` para 4 cargos de exemplo | Mesmo nível de antes (snapshot) |
| 10 | `useCapacidades`, carregando, segmento marcenaria | `temOrcamentoTecnico = true` |

### `ListaTextosEditavel`

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 11 | Adicionar | Item vazio no fim, com foco; emite a lista nova |
| 12 | Subir o 2º item | Troca com o 1º |
| 13 | Lista com 1 item | "Remover" desabilitado |
| 14 | Item "corte" com "Corte" já na lista | Erro "repetido" no item |
| 15 | `maxItens` atingido | "Adicionar" desabilitado |
| 16 | `disabled` | Nenhum botão nem campo editável |

### Telas

| # | Cenário | Resultado esperado |
|---|---------|--------------------|
| 17 | `ConfiguracoesModal`, informática | Sem "Marcenaria" na lista; query não chamada |
| 18 | `ConfiguracoesModal`, marcenaria, master | Seção visível; "Salvar" chama o `PUT` com o corpo de `paraApi` |
| 19 | Marcenaria, sem `manage` | Sem "Salvar"; campos desabilitados; frase do D9 |
| 20 | `DadosProdutoSection`, informática | Sem a caixa |
| 21 | `useProductForm`, informática, enviar | Payload sem `sofre_perda` |
| 22 | `PositionModal`, informática | Sem a linha nova; "Selecionar tudo" marca as mesmas chaves de antes |
| 23 | `PositionModal`, marcenaria, marcar Gerenciar | Ver marcado junto |

> **Nota da implementação (09/10/2026).** (1) As conversões (% ↔ bp, R$ ↔ centavos) e as regras das listas ficaram em `sections/marcenaria/marcenariaForm.ts`, funções puras testadas (01–06); a validação usa essas funções, com as mesmas mensagens do backend, no lugar de um segundo schema zod. (2) O envio condicional do "Sofre perda" é `campoSofrePerda()` (`products/inventory/composables/sofrePerda.ts`, caso 21). (3) A regra "Gerenciar marca Ver" é `chavesAoAlternar()` em `positions.constants.ts`, aplicada só às linhas com `segmento` (casos 22–23). (4) Os casos 17–18 (modal inteiro) foram cobertos pelas partes: a query não dispara sem a capacidade (17) e a seção expõe `podeGerir`/`paraApi`, que o modal usa para mostrar "Salvar" e montar o corpo do `PUT`. O "Salvar" confere os erros antes de mandar.

### Roteiro manual (dev)

1. Marcenaria, como master: Produtos → novo produto "MDF Branco 18mm", marcar "Sofre perda", salvar, reabrir.
2. Configurações → Marcenaria: mudar markup para 85,5%, perda para 12%, custo/hora para R$ 45,00, RT 8% "Embutido no preço"; reordenar etapas; adicionar um item ao checklist; salvar; reabrir e conferir.
3. Zerar o custo/hora: aviso âmbar aparece.
4. Cargos: criar "Vendedor" sem permissões de custo e "Gerente de Produção" com Ver; logar com cada um e abrir a seção.
5. Informática: Produtos, Configurações e Cargos iguais a antes (inclusive o nível de acesso dos cargos existentes).
