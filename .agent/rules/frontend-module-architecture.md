# Regras: Arquitetura de Módulos do Frontend

## Princípio Fundamental

Frontend é organizado em **módulos auto-contidos** + **código compartilhado**:

```
modules/
├── auth/              ← Auto-contido (rotas, componentes, estado)
├── home/
├── order-service/
├── employees/
└── ...

shared/               ← Código reutilizável
├── components/ui/    ← BaseButton, BaseInput, etc.
├── composables/      ← useUser, useToast, useAppNavigation
├── services/         ← API global (não específico de módulo)
├── stores/           ← Pinia stores globais
├── types/            ← Tipos globais
└── utils/
```

---

## Regra 1: Estrutura de um Módulo

**Local**: `frontend/src/modules/{feature}/`

Cada módulo deve ter (se precisar):

```
modules/order-service/
├── views/                    # Páginas (Order list, detail)
│   ├── OrderList.vue
│   └── OrderDetail.vue
├── components/               # Componentes locais
│   ├── OrderForm.vue
│   ├── OrderItemTable.vue
│   └── OrderStatusBadge.vue
├── composables/              # Hooks locais (form, state)
│   ├── useOrderForm.ts
│   ├── useOrderService.ts
│   └── form/                 # Segmentação se complex
│       ├── useOrderClientForm.ts
│       └── useOrderItemForm.ts
├── stores/                   # Pinia stores locais
│   └── order.store.ts
├── services/                 # Chamadas API (opcional)
│   └── order.service.ts
├── types/                    # Types específicos
│   └── order.types.ts
├── schemas/                  # Zod schemas (validação)
│   └── order.schema.ts
├── constants/                # Constantes (opcional)
│   └── order.constant.ts
├── routes.ts                 # ⭐ AUTO-IMPORTADO
└── context/                  # Provide/inject (optional)
    └── useOrderContext.ts
```

**Regra**: `routes.ts` no root do módulo → auto-descoberto por `router/index.ts`

```typescript
// ✅ CORRETO: modules/order-service/routes.ts
import { RouteRecordRaw } from 'vue-router'
import OrderList from './views/OrderList.vue'
import OrderDetail from './views/OrderDetail.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/os',
    name: 'OrderServiceList',
    component: OrderList
  },
  {
    path: '/os/:id',
    name: 'OrderServiceDetail',
    component: OrderDetail
  }
]

export default routes
```

**Router agregador** (auto-load):

```typescript
// ✅ CORRETO: shared/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'

const routeModules = import.meta.glob<{ default: RouteRecordRaw[] }>(
  '@/modules/**/routes.ts',
  { eager: true }
)

const routes: RouteRecordRaw[] = []

for (const mod of Object.values(routeModules)) {
  routes.push(...mod.default)
}

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
```

---

## Regra 2: Importações Dentro de um Módulo

**Pode importar de**:
- ✅ Seus próprios arquivos (`./components/`, `./composables/`, etc.)
- ✅ `@/shared/` — Componentes e utils globais
- ✅ `@/modules/` — Outros módulos (se não criar ciclos)

**NÃO pode importar de**:
- ❌ `@/modules/{other}/` direto (usar shared como mediador)
- ❌ Arquivos deletados (mesmo que ainda existam em outro branch)

**Padrão**: Máxima coesão local, mínimo acoplamento global

```typescript
// ✅ CORRETO: modules/order-service/views/OrderList.vue
<script setup lang="ts">
import { useOrderForm } from '../composables/useOrderForm'  // Local
import { BaseButton } from '@/shared/components/ui'  // Shared
import { useAppNavigation } from '@/shared/composables'  // Shared
import { ORDER_API_ENDPOINTS } from '@/constants/core.constant'  // Global
import type { OrderServiceReadDataType } from '../types/order.types'  // Local

const { orders, isLoading } = useOrderForm()
const { navigate } = useAppNavigation()
</script>

// ❌ ERRADO: Import direto de outro módulo
import OrderDetail from '@/modules/order-service/views/OrderDetail.vue'
// ↑ Não! OrderDetail é internal. Use route navigation.

// ❌ ERRADO: Import de arquivo deletado
import { useOldComposable } from '../composables/useOrderForm'
// ↑ Se foi deletado em meu commit, não posso mais usar!
```

---

## Regra 3: Componentes Compartilhados (UI)

**Local**: `frontend/src/shared/components/ui/`

Componentes reutilizáveis em vários módulos:

```
shared/components/ui/
├── BaseButton.vue           # Button genérico
├── BaseInput.vue            # Input genérico
├── BaseSelect.vue           # Select genérico
├── BaseModal.vue            # Modal genérico
├── BaseCheckbox.vue
├── BaseTabs.vue
├── BaseTable.vue
└── ...
```

**Padrão**: Props genéricas, slots para customização

```vue
<!-- ✅ CORRETO: shared/components/ui/BaseButton.vue -->
<template>
  <button
    class="btn"
    :class="`btn--${variant}`"
    @click="$emit('click')"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
interface Props {
  variant?: 'primary' | 'secondary' | 'danger'
  disabled?: boolean
}

defineProps<Props>()
</script>

<!-- USO em módulo -->
<BaseButton variant="primary" @click="handleCreate">
  Criar
</BaseButton>
```

---

## Regra 4: Composables Globais

**Local**: `frontend/src/shared/composables/`

Hooks reutilizáveis em vários módulos (autenticação, notificações, navegação):

```
shared/composables/
├── useUser.ts                 # Acesso ao usuário logado
├── useToast.ts                # Notificações
├── useAppNavigation.ts        # Navegação global
├── useApi.ts                  # Axios + interceptors
├── useQueryClient.ts          # TanStack Query
└── ...
```

**Padrão**: Composable é independente, pode injetar providers

```typescript
// ✅ CORRETO: shared/composables/useToast.ts
import { useToast as vueUseToast } from 'vue-toastification'

export const useToast = () => {
  const toast = vueUseToast()

  return {
    success: (msg: string) => toast.success(msg),
    error: (msg: string) => toast.error(msg),
    info: (msg: string) => toast.info(msg)
  }
}

// USO em qualquer módulo
const { success, error } = useToast()
success('Ordem criada!')
```

---

## Regra 5: Stores Pinia (Estado)

**Global**: `frontend/src/shared/stores/`
**Local (módulo)**: `frontend/src/modules/{feature}/stores/`

Padrão Pinia setup:

```typescript
// ✅ CORRETO: shared/stores/auth.store.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Usuario } from '@/shared/types/usuario.types'

export const useAuthStore = defineStore('auth', () => {
  const usuario = ref<Usuario | null>(null)
  const isAuthenticated = computed(() => !!usuario.value)

  const setUsuario = (user: Usuario) => {
    usuario.value = user
  }

  const logout = () => {
    usuario.value = null
  }

  return { usuario, isAuthenticated, setUsuario, logout }
})

// ✅ CORRETO: modules/order-service/stores/order.store.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { OrderServiceReadDataType } from '../types/order.types'

export const useOrderStore = defineStore('order-service', () => {
  const currentOrder = ref<OrderServiceReadDataType | null>(null)

  const setCurrentOrder = (order: OrderServiceReadDataType) => {
    currentOrder.value = order
  }

  return { currentOrder, setCurrentOrder }
})
```

---

## Regra 6: Formulários (VeeValidate + Zod)

**Padrão**: Composable com `useForm()` + schema Zod

```typescript
// ✅ CORRETO: modules/order-service/composables/useOrderForm.ts
import { useForm, useFieldArray } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { orderCreateSchema } from '../schemas/order.schema'
import type { OrderCreateType } from '../types/order.types'

export const useOrderForm = () => {
  const { values, errors, handleSubmit, setFieldValue } = useForm<OrderCreateType>({
    validationSchema: toTypedSchema(orderCreateSchema),
    initialValues: DEFAULT_ORDER_VALUES
  })

  // Array de items
  const { fields, push, remove } = useFieldArray('items')

  const onSubmit = handleSubmit(async (data) => {
    const response = await orderService.create(data)
    return response
  })

  return {
    values,
    errors,
    fields,
    push,
    remove,
    onSubmit,
    setFieldValue
  }
}

// ✅ CORRETO: modules/order-service/schemas/order.schema.ts
import { z } from 'zod'

export const orderCreateSchema = z.object({
  cliente_id: z.number().int(),
  items: z.array(z.object({
    produto_id: z.number().int(),
    quantidade: z.number().min(1)
  }))
})

export type OrderCreateType = z.infer<typeof orderCreateSchema>

// ✅ CORRETO: modules/order-service/views/OrderForm.vue
<script setup lang="ts">
import { useOrderForm } from '../composables/useOrderForm'
import { BaseButton, BaseInput } from '@/shared/components/ui'

const { values, errors, onSubmit } = useOrderForm()
</script>

<template>
  <form @submit="onSubmit">
    <BaseInput
      v-model="values.cliente_id"
      :error="errors.cliente_id"
      label="Cliente"
    />
    <BaseButton type="submit">Salvar</BaseButton>
  </form>
</template>
```

---

## Regra 7: Chamadas API (TanStack Query)

**Query Keys Centralizadas**: `frontend/src/constants/core.constant.ts`

```typescript
// ✅ CORRETO: constants/core.constant.ts
export const QUERY_KEYS = {
  orders: {
    all: ['orders'] as const,
    list: () => [...QUERY_KEYS.orders.all, 'list'] as const,
    detail: (id: string) => [...QUERY_KEYS.orders.all, 'detail', id] as const
  },
  users: {
    all: ['users'] as const,
    me: () => [...QUERY_KEYS.users.all, 'me'] as const
  }
}

// ✅ CORRETO: modules/order-service/composables/useOrderService.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { QUERY_KEYS } from '@/constants/core.constant'
import { useToast } from '@/shared/composables/useToast'

export const useOrderQueryAll = () => {
  return useQuery({
    queryKey: QUERY_KEYS.orders.list(),
    queryFn: () => orderService.getAll(),
    staleTime: 1000 * 60  // 1 min
  })
}

export const useCreateOrderMutation = () => {
  const queryClient = useQueryClient()
  const { success, error } = useToast()

  return useMutation({
    mutationFn: (data: OrderCreateType) => orderService.create(data),
    onSuccess: (data) => {
      success('Ordem criada!')
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.orders.list() })
    },
    onError: (err) => {
      error(getErrorMessage(err))
    }
  })
}
```

---

## Regra 8: Serviços API (Axios)

**Local**: `frontend/src/shared/services/` (global) ou `modules/{feature}/services/`

```typescript
// ✅ CORRETO: shared/services/api.service.ts
import { api } from '@/api/axios'
import { z } from 'zod'

const usuarioReadSchema = z.object({
  id: z.number(),
  nome: z.string(),
  email: z.string()
})

export const usuarioService = {
  getMe: async () => {
    const response = await api.get('/usuarios/me')
    const parsed = usuarioReadSchema.safeParse(response.data)
    if (!parsed.success) {
      console.warn('Invalid usuario response', parsed.error)
      return response.data as typeof usuarioReadSchema._output
    }
    return parsed.data
  }
}

// ✅ PADRÃO: safeParse + console.warn + fallback as Type
// (nunca .parse() que lança ZodError)
```

---

## Regra 9: Valores Monetários

**Backend**: Armazena centavos (inteiros)
**Frontend**: Trabalha em reais (floats)

**Padrão**: Conversão em composables ou serviços

```typescript
// ✅ CORRETO: Conversão no populate (backend → frontend)
const response = await api.get('/vendas/1')
const vendaData = {
  ...response.data,
  total: response.data.total / 100  // Centavos → Reais
}

// ✅ CORRETO: Conversão no save (frontend → backend)
const handleSubmit = async (formData) => {
  const payload = {
    ...formData,
    total: Math.round(formData.total * 100)  // Reais → Centavos
  }
  await api.post('/vendas', payload)
}

// ✅ CORRETO: Use BaseMoneyInput (vue-currency-input)
<BaseMoneyInput
  v-model="values.total"
  label="Total"
/>
// ↑ Converte automaticamente float ↔ string formatado
```

---

## Regra 10: Provide/Inject para Contexto

**Padrão**: `InjectionKey<Type>` → `useXxxProvider()` (provide) + `useXxx()` (inject)

```typescript
// ✅ CORRETO: modules/order-service/context/useOrderContext.ts
import { provide, inject, InjectionKey } from 'vue'
import type { OrderCreateType } from '../types/order.types'

interface OrderContextType {
  formData: Ref<OrderCreateType>
  onSubmit: (data: OrderCreateType) => Promise<void>
}

const OrderContextKey: InjectionKey<OrderContextType> = Symbol('OrderContext')

export const useOrderFormProvider = () => {
  const formData = ref<OrderCreateType>(DEFAULT_VALUES)

  const onSubmit = async (data: OrderCreateType) => {
    await orderService.create(data)
  }

  provide(OrderContextKey, { formData, onSubmit })

  return { formData, onSubmit }
}

export const useOrderForm = () => {
  const context = inject(OrderContextKey)
  if (!context) {
    throw new Error('useOrderForm must be used within OrderFormProvider')
  }
  return context
}

// USO: modules/order-service/views/OrderFormModal.vue
<script setup lang="ts">
const { formData } = useOrderFormProvider()  // ← Primeiro, no root component
</script>

// Child component: modules/order-service/components/OrderItemForm.vue
<script setup lang="ts">
const { formData } = useOrderForm()  // ← Injected do pai
</script>
```

---

## Regra 11: Não Importar Arquivos Deletados

Se um arquivo foi deletado por você em um commit, ele não pode mais ser importado em nenhum lugar.

```typescript
// ❌ ERRO: Arquivo deletado em meu commit anterior
import { useOldComposable } from '@/modules/order-service/composables/useOrderForm'
// useOrderForm.ts foi deletado → Erro de import!

// ✅ CORRETO: Remover o import também
// (ou migrar pra novo nome/local)
import { useNewComposable } from '@/modules/order-service/composables/useNewOrderForm'
```

---

## Resumo Visual

```
┌─────────────────────────────────────────────┐
│ MÓDULO (Auto-contido)                       │
├─────────────────────────────────────────────┤
│ views/ + components/ + composables/         │
│ stores/ + types/ + schemas/                 │
│ routes.ts (auto-descoberto)                 │
└────────────────┬────────────────────────────┘
                 │ imports
┌────────────────▼────────────────────────────┐
│ SHARED (Global, Reutilizável)               │
├────────────────────────────────────────────┤
│ components/ui/ — UI genéricos               │
│ composables/ — Hooks globais                │
│ services/ — API wrappers                    │
│ stores/ — Pinia global                      │
│ types/ — Tipos globais                      │
│ utils/ — Helpers                            │
│ constants/ — Constantes (QUERY_KEYS, etc.)  │
└─────────────────────────────────────────────┘
```

---

## Checklist para Revisão de PR (Frontend)

- [ ] Componentes novos em `shared/components/ui/` são genéricos?
- [ ] Composables reutilizáveis estão em `shared/composables/`?
- [ ] Módulos têm `routes.ts` no root?
- [ ] Imports circulares entre módulos?
- [ ] Valores monetários convertidos (centavos ↔ reais)?
- [ ] Nenhum import de arquivo deletado?
- [ ] Query keys centralizadas em `core.constant.ts`?
- [ ] Schemas Zod com `safeParse()` (não `.parse()`)?
- [ ] Provide/inject em contexto compartilhado?
- [ ] Não há hardcodes de URLs de API?

---

**Versão**: 1.0
**Data**: 16/09/2026
