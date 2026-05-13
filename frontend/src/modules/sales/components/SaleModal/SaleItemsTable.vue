<script setup lang="ts">
import { computed } from 'vue';
import { Trash2, Minus, Plus, PackagePlus } from 'lucide-vue-next';

import { formatCurrency } from '@/shared/utils/finance';

import {
  useUpdateItemSaleMutation,
  useDeleteItemSaleMutation,
} from '../../composables/mutates/useItemSaleMutation';

import type { SaleRead } from '../../schemas/sale.schema';

const props = defineProps<{
  sale: SaleRead | undefined;
  readonly?: boolean;
}>();

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const updateItemMutation = useUpdateItemSaleMutation();
const deleteItemMutation = useDeleteItemSaleMutation();

const items = computed(() => props.sale?.produtos ?? []);

function getProductDescription(item: SaleRead['produtos'][number]) {
  if (item.tipo_produto === 'AVULSO') {
    return 'Produto avulso';
  }

  return item.produto_id ? `SKU: #${item.sku}` : 'Produto cadastrado';
}

function decreaseQuantity(item: SaleRead['produtos'][number]) {
  if (props.readonly) return;
  if (!props.sale?.id) return;
  if (item.quantidade <= 1) return;

  updateItemMutation.mutate({
    saleId: props.sale.id,
    productId: item.id,
    payload: {
      quantidade: item.quantidade - 1,
    },
  });
}

function increaseQuantity(item: SaleRead['produtos'][number]) {
  if (props.readonly) return;
  if (!props.sale?.id) return;

  updateItemMutation.mutate({
    saleId: props.sale.id,
    productId: item.id,
    payload: {
      quantidade: item.quantidade + 1,
    },
  });
}

function removeItem(item: SaleRead['produtos'][number]) {
  if (props.readonly) return;
  if (!props.sale?.id) return;

  deleteItemMutation.mutate({
    saleId: props.sale.id,
    productId: item.id,
  });
}
</script>

<template>
  <section class="w-full overflow-hidden rounded-xl border border-zinc-200 bg-white">
    <div class="max-h-120 overflow-y-auto">
      <table class="w-full border-collapse text-sm">
        <thead class="sticky top-0 z-10 bg-zinc-50">
          <tr
            class="h-12 border-b border-zinc-200 bg-zinc-50 text-left text-[11px] font-bold uppercase text-zinc-600"
          >
            <th class="px-5">Produto</th>
            <th class="w-32.5 px-4 text-center">Qtde.</th>
            <th class="w-37.5 px-4 text-center">Preço unit.</th>
            <th class="w-35 px-4 text-center">Desconto</th>
            <th class="w-35 px-4 text-center">Total</th>
            <th v-if="!readonly" class="w-18 px-4 text-center"></th>
          </tr>
        </thead>
        <tbody class="max-h-96 overflow-y-scroll">
          <tr v-if="items.length === 0">
            <td :colspan="readonly ? 5 : 6" class="px-6 py-14">
              <div class="mx-auto flex max-w-md flex-col items-center justify-center text-center">
                <div
                  class="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-50 text-brand-primary"
                >
                  <PackagePlus class="h-8 w-8" />
                </div>

                <h3 class="text-base font-bold text-zinc-900">Nenhum produto adicionado</h3>

                <p class="mt-2 text-sm leading-6 text-zinc-500">
                  Use a busca acima para localizar um produto pelo nome, SKU ou código de barras e
                  adicioná-lo a esta venda.
                </p>
              </div>
            </td>
          </tr>

          <tr
            v-for="item in items"
            :key="item.id"
            class="h-23 border-b border-zinc-100 last:border-b-0 hover:bg-zinc-50/70"
          >
            <td class="px-5">
              <div class="flex items-center gap-4">
                <div
                  class="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-lg border border-zinc-200 bg-zinc-100"
                >
                  <img
                    v-if="'imagem_url' in item && item.imagem_url"
                    :src="`${API_BASE_URL}/${item.imagem_url}`"
                    :alt="item.nome"
                    class="h-full w-full object-fit"
                  />

                  <span v-else class="text-xs font-semibold text-zinc-400">
                    {{ item.nome.charAt(0).toUpperCase() }}
                  </span>
                </div>

                <div class="min-w-0">
                  <p class="truncate text-sm font-bold text-zinc-900">
                    {{ item.nome }}
                  </p>

                  <p class="mt-0.5 truncate text-xs text-zinc-500">
                    {{ getProductDescription(item) }}
                  </p>

                  <p
                    v-if="item.tipo_produto === 'CADASTRADO' && item.produto_id"
                    class="mt-0.5 truncate text-[11px] text-zinc-400"
                  >
                    Produto ID: {{ item.produto_id }}
                  </p>
                </div>
              </div>
            </td>

            <td class="px-4 text-center">
              <div
                class="mx-auto flex h-10 w-28 items-center justify-between rounded-lg border border-zinc-200 bg-white px-2 shadow-sm"
              >
                <button
                  type="button"
                  :disabled="readonly || item.quantidade <= 1 || updateItemMutation.isPending.value"
                  class="flex h-7 w-7 items-center justify-center rounded-md text-zinc-500 transition hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-40"
                  @click="decreaseQuantity(item)"
                >
                  <Minus class="h-4 w-4" />
                </button>

                <span class="min-w-6 text-center text-sm font-semibold text-zinc-800">
                  {{ item.quantidade }}
                </span>

                <button
                  type="button"
                  :disabled="readonly || updateItemMutation.isPending.value"
                  class="flex h-7 w-7 items-center justify-center rounded-md text-zinc-500 transition hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-40"
                  @click="increaseQuantity(item)"
                >
                  <Plus class="h-4 w-4" />
                </button>
              </div>
            </td>

            <td class="px-4 text-center text-sm font-medium text-zinc-700">
              {{ formatCurrency(item.valor_unitario) }}
            </td>

            <td class="px-4 text-center text-sm font-medium text-zinc-700">
              {{ formatCurrency(item.desconto) }}
            </td>

            <td class="px-4 text-center text-sm font-semibold text-zinc-800">
              {{ formatCurrency(item.total) }}
            </td>

            <td v-if="!readonly" class="px-4 text-center">
              <button
                type="button"
                :disabled="deleteItemMutation.isPending.value"
                class="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-zinc-200 bg-white text-zinc-500 shadow-sm transition hover:border-red-200 hover:bg-red-50 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-50"
                @click="removeItem(item)"
              >
                <Trash2 class="h-4 w-4" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
