# Módulo Frontend: Order Service (Ordens)

> Contexto técnico completo para desenvolvedores e assistentes de IA.

---

## Visão Geral

O módulo `order-service/ordens` gerencia o ciclo de vida das Ordens de Serviço no frontend da aplicação BigPDV. Ele conecta a interface do usuário à API REST do backend, cobrindo criação, edição, gerenciamento de itens, upload de fotos, finalização com pagamentos e cancelamento.

O módulo é **feature-completo em infraestrutura**: schemas, services, mutations e queries estão todos implementados. A camada de formulário (form composables + context) encapsula a lógica VeeValidate + Zod e é consumida pelos componentes via `provide/inject`.

---

## Estrutura de Pastas

```
frontend/src/modules/order-service/ordens/
├── composables/
│   ├── form/
│   │   └── useForm.ts                         ✅ 6 composables de formulário segmentados
│   └── request/
│       ├── useOrderServiceGet.queries.ts       ✅ Queries: lista, detalhe, stats
│       ├── useOrderServiceCreate.mutate.ts     ✅ Mutations: criar OS, adicionar item
│       ├── useOrderServiceUpdate.mutate.ts     ✅ Mutations: atualizar, equipamento, item,
│       │                                              finalizar, cancelar, reabrir
│       ├── useOrderServiceDelete.mutate.ts     ✅ Mutation: deletar item
│       └── relationship/
│           ├── useOSRelationshipGet.queries.ts ✅ Queries: clientes, funcionários
│           └── useOSPhotoMutate.mutate.ts      ✅ Mutations: upload/delete de foto
│
├── context/
│   └── useForm.context.ts                     ✅ Provider + Consumer (provide/inject)
│
├── constants/
│   ├── core.constant.ts                       ✅ Query keys, stale times, valores padrão
│   └── ordemServico.constants.ts              ✅ Status/prioridade display, UI config
│
├── schemas/
│   ├── orderService.schema.ts                 ✅ Schema base (campos compartilhados)
│   ├── orderServiceMutate.schema.ts           ✅ Schemas de escrita: Create, Update, Ready, Cancel
│   ├── orderServiceQuery.schema.ts            ✅ Schemas de leitura: Read, Pagination, Stats
│   ├── enums/
│   │   └── osEnums.schema.ts                  ✅ Status, Prioridade, TipoItem, TipoEquip, Medida, Bandeira
│   └── relationship/
│       ├── osItem.schema.ts                   ✅ Create / Read / Update de itens
│       ├── osEquip.schema.ts                  ✅ Create / Read / Update de equipamentos
│       ├── osPayment.schema.ts                ✅ Create / Read de pagamentos
│       ├── osPhoto.schema.ts                  ✅ Read de fotos
│       ├── customer/
│       │   ├── customer.schema.ts             ✅ Leitura de clientes PF e PJ
│       │   ├── enums/
│       │   │   ├── customerEnum.type.ts       ✅ TipoCliente (PF/PJ)
│       │   │   └── genderEnum.type.ts         ✅ Gênero
│       │   └── relationship/
│       │       └── address.schema.ts          ✅ Endereço do cliente
│       └── employee/
│           └── employee.schema.ts             ✅ Leitura de funcionários
│
├── services/
│   ├── orderServiceGet.service.ts             ✅ GET: lista, detalhe, stats
│   ├── orderServiceCreate.service.ts          ✅ POST: criar OS, adicionar item
│   ├── orderServiceUpdate.service.ts          ✅ PUT: atualizar, equipamento, item,
│   │                                                  finalizar, cancelar, reabrir
│   ├── orderServiceDelete.service.ts          ✅ DELETE: item
│   └── relationship/
│       ├── osRelationshipGet.service.ts       ✅ GET: clientes, funcionários
│       └── osPhotoMutate.service.ts           ✅ POST/DELETE: fotos
│
├── types/
│   ├── requests.type.ts                       ✅ Interfaces de payload para as mutations
│   └── context.type.ts                        ✅ Interfaces dos 6 segmentos de formulário
│
└── docs/
    └── order-service.md                       ✅ Esta documentação
```

---

## Fluxo de Dados

```
Componente Vue
    │
    │ useOSForm()          ← inject do contexto
    ▼
useForm.context.ts         ← provide/inject singleton por árvore
    │
    │ instancia 6 segmentos via useOSCreateForm(), useOSUpdateGeralForm(), ...
    ▼
composables/form/useForm.ts
    │
    │ VeeValidate useForm() + defineField() + useFieldArray()
    │ TanStack useMutation() → onSubmit()
    ▼
composables/request/*.mutate.ts
    │
    │ useMutation({ mutationFn: service, onSuccess: toast + invalidate })
    ▼
services/*.service.ts
    │
    │ axios.post / .put / .delete
    ▼
API REST /api/v1/ordens-servico/...
    │
    │ resposta → queryClient.invalidateQueries()
    ▼
composables/request/*.queries.ts   ← refetch automático via TanStack Query
    │
    ▼
Componente atualiza com os novos dados
```

---

## Responsabilidades por Camada

| Camada | Arquivo(s) | Responsabilidade |
|--------|-----------|-----------------|
| **Schema** | `schemas/*.schema.ts` | Validação Zod + inferência de tipos TypeScript. Nenhuma lógica de negócio. |
| **Types** | `types/requests.type.ts` | Interfaces de payload para mutations (agrupam `osNumber` + dados). |
| **Types** | `types/context.type.ts` | Interfaces dos contextos de formulário por segmento. |
| **Constants** | `constants/core.constant.ts` | Query keys, stale times, valores padrão dos formulários. |
| **Constants** | `constants/ordemServico.constants.ts` | Mapeamento status → label/cor, configurações de UI. |
| **Service** | `services/*.service.ts` | Chamadas Axios tipadas. Sem tratamento de erros (delegado ao TanStack Query). |
| **Queries** | `composables/request/*.queries.ts` | `useQuery` com cache, stale time, filtros reativos e debounce. |
| **Mutations** | `composables/request/*.mutate.ts` | `useMutation` com toast de sucesso/erro e `invalidateQueries`. |
| **Form** | `composables/form/useForm.ts` | VeeValidate forms segmentados, submit handlers, transformação de dados. |
| **Context** | `context/useForm.context.ts` | `provide/inject` singleton: instancia todos os segmentos e expõe o contexto. |
| **Component** | `components/` | Consome `useOSForm()` para acessar segmentos específicos. |

---

## Segmentos de Formulário

O formulário da OS é dividido em **6 segmentos independentes**, cada um mapeando para um endpoint específico do backend:

| Segmento | Composable | Endpoint | Schema |
|----------|-----------|----------|--------|
| `criar` | `useOSCreateForm` | `POST /ordens-servico/` | `OrderServiceCreateSchema` |
| `atualizarGeral` | `useOSUpdateGeralForm` | `PUT /ordens-servico/{n}` | `OrderServiceUpdateSchema` |
| `atualizarEquipamento` | `useOSUpdateEquipForm` | `PUT /ordens-servico/{n}/equipamento` | `OsEquipUpdateSchema` |
| `item` | `useOSItemForm` | `POST/PUT /ordens-servico/{n}/itens[/{id}]` | `OsItemCreateSchema` |
| `finalizar` | `useOSFinalizarForm` | `PUT /ordens-servico/{n}/finalizar` | `OrderServiceReadySchema` |
| `cancelar` | `useOSCancelarForm` | `PUT /ordens-servico/{n}/cancelar` | `OrderServiceCancelSchema` |

### Campos por segmento

**`criar`** (POST /ordens-servico/)
- Campos gerais: `prioridade`, `defeito_relatado`, `diagnostico`, `observacoes`, `desconto`, `garantia`, `data_previsao`, `senha_aparelho`, `acessorios`, `condicoes_aparelho`
- Vínculos: `cliente_id`, `funcionario_id`
- Equipamento nested: `equipamento_tipo_equipamento`, `equipamento_marca`, `equipamento_modelo`, `equipamento_numero_serie`, `equipamento_imei`, `equipamento_cor`
- FieldArray: `itens[]` (tipo, nome, unidade_medida, quantidade, valor_unitario)

**`atualizarGeral`** (PUT /ordens-servico/{n})
- Todos os campos opcionais: `status`, `prioridade`, `defeito_relatado`, `diagnostico`, `solucao`, `observacoes`, `desconto`, `garantia`, `data_previsao`, `senha_aparelho`, `acessorios`, `condicoes_aparelho`, `funcionario_id`
- `populateForm(os: OrderServiceReadDataType)` — carrega os dados atuais da OS

**`atualizarEquipamento`** (PUT /ordens-servico/{n}/equipamento)
- `tipo_equipamento`, `marca`, `modelo`, `numero_serie`, `imei`, `cor`, `cliente_id`
- `cliente_id` permite troca do cliente vinculado ao equipamento
- `populateForm(equip: OsEquipUpdateSchemaDataType)` — carrega os dados atuais

**`item`** (POST ou PUT /ordens-servico/{n}/itens[/{id}])
- `tipo`, `nome`, `unidade_medida`, `quantidade`, `valor_unitario`
- `editingItemId: Ref<number | null>` — controla o modo (null = criar, id = editar)
- `setEditingItem(id, data)` — ativa modo edição e popula o form
- Na submissão em modo edição, apenas os campos do `OsItemUpdateSchema` são enviados

**`finalizar`** (PUT /ordens-servico/{n}/finalizar)
- `solucao` (obrigatório, mín. 5 chars), `observacoes`, `desconto`
- FieldArray: `pagamentos[]` (forma_pagamento_id, valor, parcelas, bandeira_cartao, detalhes)
- Regra: `sum(pagamentos.valor) == os.valor_total` — validação no backend (409 se divergir)

**`cancelar`** (PUT /ordens-servico/{n}/cancelar)
- `motivo` (opcional, máx. 500 chars)

---

## Padrão provide/inject — Como Usar

### Componente pai (página ou modal)

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useOSFormProvider, useOSFormPendingState } from '../context/useForm.context'

const osNumber = ref<string | null>(null)           // null em modo criação
const isCreateMode = computed(() => osNumber.value === null)

const formCtx = useOSFormProvider({
  osNumber,
  isCreateMode,
  onCreateSuccess: () => { /* fechar modal, navegar */ },
  onUpdateSuccess: () => { /* feedback de sucesso */ },
  onItemSuccess:   () => { /* fechar drawer de item */ },
  onFinalizarSuccess: () => { /* fechar modal de finalização */ },
  onCancelarSuccess:  () => { /* atualizar estado da página */ },
})

// Indicador global de loading (qualquer segmento em progresso)
const isPending = useOSFormPendingState(formCtx)

// Carregar dados para modo edição
function loadOS(os: OrderServiceReadDataType) {
  osNumber.value = os.numero_os
  formCtx.atualizarGeral.populateForm(os)
  formCtx.atualizarEquipamento.populateForm(os.equipamento)
}
</script>
```

### Componente filho (seção do formulário)

```vue
<script setup lang="ts">
import { useOSForm } from '../context/useForm.context'

// Acessa apenas o segmento necessário
const { criar } = useOSForm()
</script>

<template>
  <form @submit="criar.onSubmit">
    <select v-model="criar.prioridade.value">
      <option value="BAIXA">Baixa</option>
      <option value="NORMAL">Normal</option>
      <option value="ALTA">Alta</option>
      <option value="URGENTE">Urgente</option>
    </select>
    <span v-if="criar.errors.value['prioridade']">
      {{ criar.errors.value['prioridade'] }}
    </span>

    <textarea v-model="criar.defeito_relatado.value" />

    <!-- FieldArray de itens -->
    <div v-for="(item, idx) in criar.itens.value" :key="item.key">
      <input v-model="item.value.nome" />
      <button type="button" @click="criar.handleRemoveItem(idx)">Remover</button>
    </div>
    <button type="button" @click="criar.handleAddItem()">Adicionar item</button>

    <button type="submit" :disabled="criar.isPending.value">Salvar</button>
  </form>
</template>
```

### Componente filho — seção de item (add/edit)

```vue
<script setup lang="ts">
import { useOSForm } from '../context/useForm.context'
import type { OsItemReadSchemaDataType } from '../schemas/relationship/osItem.schema'

const { item } = useOSForm()

function editarItem(osItem: OsItemReadSchemaDataType) {
  item.setEditingItem(osItem.id, {
    nome: osItem.nome,
    unidade_medida: osItem.unidade_medida,
    quantidade: osItem.quantidade,
    valor_unitario: osItem.valor_unitario,
  })
}
</script>
```

---

## Queries Disponíveis

```typescript
import {
  useOrderServiceQueryAll,    // Lista paginada com filtros
  useOrderServiceQueryUnique, // OS única por numero_os
  useOrderServiceQueryStats,  // Contadores e ticket médio
} from '../composables/request/useOrderServiceGet.queries'

import {
  useOsCustomersGet,   // Clientes para seleção em formulários
  useOsEmployeesGet,   // Funcionários para seleção em formulários
} from '../composables/request/relationship/useOSRelationshipGet.queries'
```

### Parâmetros de listagem (`useOrderServiceQueryAll`)

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `search` | `Ref<string>` | Busca por numero_os, nome do cliente, razão social |
| `status` | `Ref<OsStatusEnumDataType \| undefined>` | Filtro por status |
| `prioritySort` | `Ref<boolean>` | Ordena por prioridade (URGENTE → BAIXA) |

---

## Mutations Disponíveis

```typescript
// Criação
useCreateOrderServiceMutation()   // POST /ordens-servico/
useCreateItemOSMutation()         // POST /ordens-servico/{n}/itens

// Atualização
useUpdateOrderServiceMutation()   // PUT /ordens-servico/{n}
useUpdateEquipOSMutation()        // PUT /ordens-servico/{n}/equipamento
useUpdateItemOSMutation()         // PUT /ordens-servico/{n}/itens/{id}
useReadyOrderServiceMutation()    // PUT /ordens-servico/{n}/finalizar
useCancelOrderServiceMutation()   // PUT /ordens-servico/{n}/cancelar
useReopenOrderServiceMutation()   // PUT /ordens-servico/{n}/reabrir

// Deleção
useOrderServiceDeleteItem()       // DELETE /ordens-servico/{n}/itens/{id}

// Fotos
useUploadFotoOSMutation()         // POST /ordens-servico/{n}/fotos
useDeleteFotoOSMutation()         // DELETE /ordens-servico/{n}/fotos/{id}
```

---

## Convenções Adotadas

| Convenção | Detalhe |
|-----------|---------|
| **Valores monetários** | Sempre em centavos (integer). Ex: R$ 450,00 = `45000` |
| **Identificador público** | `numero_os` (ex: `OS-2026-000001`) — usar nas chamadas de API e rotas |
| **ID interno** | `id` (integer) — uso somente interno (ex: para mutations de itens/fotos) |
| **Nomenclatura de arquivos** | `*.service.ts`, `*.mutate.ts`, `*.queries.ts`, `*.schema.ts`, `*.type.ts` |
| **Query keys** | Centralizadas em `constants/core.constant.ts` como strings constantes |
| **Stale time** | 1 minuto para OS; pode ser aumentado se o domínio tolerar dados levemente stale |
| **Erros de API** | Tratados nas mutations com `useToast` e `getErrorMessage` |
| **Schemas Zod** | Exportam o schema, o `toTypedSchema` (para VeeValidate) e o tipo inferido |
| **Linguagem** | Português para variáveis, comentários, labels e mensagens de erro |

---

## Enums

### `OsStatusEnum`
```
ABERTA | EM_ANDAMENTO | AGUARDANDO_PECAS | AGUARDANDO_APROVACAO | AGUARDANDO_RETIRADA | FINALIZADA | CANCELADA
```

### `OsPriorityEnum`
```
BAIXA | NORMAL | ALTA | URGENTE
```

### `OsItemTypeEnum`
```
PRODUTO | SERVICO
```

### `OsEquipTypeEnum`
```
COMPUTADOR | CELULAR | TABLET | IMPRESSORA | MONITOR | PRINTER | SCANNER | OUTROS
```

### `OsItemMeasureEnum`
```
UN | KG | G | L | ML | M | CM | M2 | M3 | H | D | MES | OUTROS
```

### `OsCardsFlagEnum`
```
MASTERCARD | VISA | ELO | OUTROS
```

---

## Decisões Arquiteturais

### 1. Formulários segmentados por operação (não um form único)
A OS tem múltiplos endpoints de escrita com schemas distintos. Usar um único form unificado seria frágil: validações conflitantes, dificuldade de reset parcial, estado UI acoplado. Cada endpoint tem seu próprio `useForm()`, schema e mutation.

### 2. `useFieldArray` deve ser chamado imediatamente após seu `useForm`
VeeValidate 4 usa `injectWithSelf` para vincular `useFieldArray` ao form mais recente via `vm.provides`. Como múltiplos `useForm()` são chamados no mesmo setup (dentro de `useOSFormProvider`), a ordem importa: `useFieldArray` de itens é chamado dentro de `useOSCreateForm` (vincula ao form de criação), e `useFieldArray` de pagamentos é chamado dentro de `useOSFinalizarForm` (vincula ao form de finalização).

### 3. Modo add/edit de item em um único composable
O `useOSItemForm` usa `OsItemCreateSchema` como schema de validação (superset). Na submissão, o handler verifica `editingItemId.value` e chama a mutation adequada (create ou update), extraindo apenas os campos aceitos pelo endpoint de update. Isso evita duplicar a lógica de form para o mesmo conjunto de inputs.

### 4. `provide/inject` como singleton por árvore de componentes
O padrão escolhido — `useOSFormProvider()` no pai + `useOSForm()` nos filhos — garante que todos os segmentos sejam instanciados uma única vez por instância do modal/página. Filhos acessam diretamente o segmento que precisam sem prop drilling. Diferente de refs globais (module-level), o contexto é isolado por instância de componente pai.

### 5. `onSuccess` callbacks no provider
O provider aceita callbacks por operação (`onCreateSuccess`, `onUpdateSuccess`, etc.) em vez de emitir eventos. Isso mantém o controle de fluxo (fechar modal, navegar, resetar) no componente pai, onde ele naturalmente pertence, sem acoplamento com o composable.

### 6. Typo `OsEquipUpdateResquest` → `OsEquipUpdateRequest`
Corrigido em `types/requests.type.ts` e `composables/request/useOrderServiceUpdate.mutate.ts` para manter consistência com o restante do codebase.

---

## Referências

- Backend: `backend-fastapi/docs/ordem_servico.md`
- Padrão de formulário: `modules/employees/composables/useEmployeeForm.ts`
- Padrão de queries: `modules/employees/composables/useEmployeesQuery.ts`
- Padrão de modal state: `modules/employees/composables/useEmployeeModal.ts`
- Schemas compartilhados: `shared/schemas/payments/payment.schema.ts`, `shared/schemas/pagination/`
