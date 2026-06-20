<script setup lang="ts">
import { computed, ref } from 'vue';
import { Trash2, Minus, Plus, PackagePlus } from 'lucide-vue-next';

import { formatCurrency } from '@/shared/utils/finance';
import AvisoEstoqueNegativoModal from './AvisoEstoqueNegativoModal.vue';

import {
  useUpdateItemSaleMutation,
  useDeleteItemSaleMutation,
} from '../../composables/mutates/useItemSaleMutation';
import {
  useUpdateItemOrcamentoMutation,
  useDeleteItemOrcamentoMutation,
} from '../../composables/mutates/useItemOrcamentoMutation';

import { useItemModal } from '../../composables/flows/useItemModal';

import type { SaleRead } from '../../schemas/sale.schema';
import type { OrcamentoRead } from '../../schemas/orcamento.schema';
import { getBackendBaseUrl } from '@/api/backendUrl';

type SaleOrOrcamento = SaleRead | OrcamentoRead;

const props = defineProps<{
  sale: SaleOrOrcamento | undefined;
  readonly?: boolean;
  isOrcamento?: boolean;
}>();

const { openEditItemModal } = useItemModal();

const avisoEstoqueOpen = ref(false);
const pendingItem = ref<SaleOrOrcamento['produtos'][number] | null>(null);

const updateSaleMut = useUpdateItemSaleMutation();
const deleteSaleMut = useDeleteItemSaleMutation();
const updateOrcMut = useUpdateItemOrcamentoMutation();
const deleteOrcMut = useDeleteItemOrcamentoMutation();

const isUpdating = computed(() => props.isOrcamento ? updateOrcMut.isPending.value : updateSaleMut.isPending.value);
const isDeleting = computed(() => props.isOrcamento ? deleteOrcMut.isPending.value : deleteSaleMut.isPending.value);

const items = computed(() => props.sale?.produtos ?? []);

function getProductDescription(item: SaleOrOrcamento['produtos'][number]) {
  if (item.tipo_produto === 'AVULSO') {
    return 'Produto avulso';
  }

  return item.produto_id ? `SKU: #${item.sku}` : 'Produto cadastrado';
}

function mutateUpdate(entityId: number, productId: number, payload: { quantidade: number }) {
  if (props.isOrcamento) {
    updateOrcMut.mutate({ orcamentoId: entityId, productId, payload });
  } else {
    updateSaleMut.mutate({ saleId: entityId, productId, payload });
  }
}

function mutateDelete(entityId: number, productId: number) {
  if (props.isOrcamento) {
    deleteOrcMut.mutate({ orcamentoId: entityId, productId });
  } else {
    deleteSaleMut.mutate({ saleId: entityId, productId });
  }
}

function decreaseQuantity(item: SaleOrOrcamento['produtos'][number]) {
  if (props.readonly) return;
  if (!props.sale?.id) return;
  if (item.quantidade <= 1) return;

  mutateUpdate(props.sale.id, item.id, { quantidade: item.quantidade - 1 });
}

function increaseQuantity(item: SaleOrOrcamento['produtos'][number]) {
  if (props.readonly) return;
  if (!props.sale?.id) return;

  const estoque = item.estoque_disponivel;
  if (estoque !== null && estoque !== undefined) {
    const novaQtd = item.quantidade + 1;
    if (novaQtd > estoque) {
      pendingItem.value = item;
      avisoEstoqueOpen.value = true;
      return;
    }
  }

  mutateUpdate(props.sale.id, item.id, { quantidade: item.quantidade + 1 });
}

function confirmarIncremento() {
  if (!pendingItem.value || !props.sale?.id) return;
  mutateUpdate(props.sale.id, pendingItem.value.id, { quantidade: pendingItem.value.quantidade + 1 });
  avisoEstoqueOpen.value = false;
  pendingItem.value = null;
}

function removeItem(item: SaleOrOrcamento['produtos'][number]) {
  if (props.readonly) return;
  if (!props.sale?.id) return;

  mutateDelete(props.sale.id, item.id);
}
</script>

<template>
  <AvisoEstoqueNegativoModal
    :is-open="avisoEstoqueOpen"
    :nome-produto="pendingItem?.nome ?? ''"
    :estoque-atual="pendingItem?.estoque_disponivel ?? 0"
    :quantidade-desejada="pendingItem ? pendingItem.quantidade + 1 : 1"
    @confirmar="confirmarIncremento"
    @cancelar="avisoEstoqueOpen = false; pendingItem = null"
  />
  <section class="w-full h-full overflow-hidden rounded-xl border border-zinc-200 bg-white hover:border-brand-primary/30 transition-colors flex flex-col">
    <div class="flex-1 min-h-0 overflow-y-auto no-scrollbar">
      <table class="w-full border-collapse text-sm">
        <thead class="sticky top-0 z-10 bg-zinc-50">
          <tr
            class="h-12 border-b border-zinc-200 bg-zinc-50 text-left text-[11px] font-bold uppercase text-zinc-600"
          >
            <th class="px-5">Produto</th>
            <th class="w-16 px-2 text-center">Un.</th>
            <th class="w-32.5 px-4 text-center">Qtde.</th>
            <th class="w-37.5 px-4 text-center">Preço unit.</th>
            <th class="w-35 px-4 text-center">Desconto</th>
            <th class="w-35 px-4 text-right">Total</th>
            <th v-if="!readonly" class="w-18 px-4 text-center"></th>
          </tr>
        </thead>
        <tbody class="max-h-96 overflow-y-scroll">
          <tr v-if="items.length === 0">
            <td :colspan="readonly ? 6 : 7" class="px-6 py-8">
              <div class="mx-auto flex max-w-sm flex-col items-center justify-center text-center">
                <div class="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-brand-primary">
                  <PackagePlus class="h-5 w-5" />
                </div>
                <h3 class="text-sm font-bold text-zinc-800">Nenhum produto adicionado</h3>
                <p class="mt-1 text-xs leading-5 text-zinc-400">
                  Use a busca acima para localizar um produto pelo nome, SKU ou código de barras.
                </p>
              </div>
            </td>
          </tr>

          <tr
            v-for="item in items"
            :key="item.id"
            class="h-23 border-b border-zinc-100 last:border-b-0 hover:bg-zinc-50/70 hover:cursor-pointer"
            @click="openEditItemModal(item)"
          >
            <td class="px-5">
              <div class="flex items-center gap-4">
                <div
                  class="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-lg border border-zinc-200 bg-zinc-100"
                >
                  <img
                    v-if="'imagem_url' in item && item.imagem_url"
                    :src="`${getBackendBaseUrl()}/${item.imagem_url}`"
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

                </div>
              </div>
            </td>

            <td class="px-2 text-center">
              <span
                v-if="'unidade_medida' in item && item.unidade_medida"
                class="inline-block px-1.5 py-0.5 text-[10px] font-semibold rounded bg-zinc-100 text-zinc-500 uppercase"
              >
                {{ item.unidade_medida }}
              </span>
              <span v-else class="text-xs text-zinc-300">—</span>
            </td>

            <td class="px-4 text-center">
              <div
                class="mx-auto flex h-10 w-28 items-center justify-between rounded-lg border border-zinc-200 bg-white px-2 shadow-sm"
              >
                <button
                  type="button"
                  :disabled="readonly || item.quantidade <= 1 || isUpdating"
                  class="flex h-7 w-7 items-center justify-center rounded-md text-zinc-500 transition hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-40"
                  @click.stop="decreaseQuantity(item)"
                >
                  <Minus class="h-4 w-4" />
                </button>

                <span class="min-w-6 text-center text-sm font-semibold text-zinc-800 select-none z-99">
                  {{ item.quantidade }}
                </span>

                <button
                  type="button"
                  :disabled="readonly || isUpdating"
                  class="flex h-7 w-7 items-center justify-center rounded-md text-zinc-500 transition hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-40"
                  @click.stop="increaseQuantity(item)"
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

            <td class="px-4 text-right text-sm font-semibold text-zinc-800">
              {{ formatCurrency(item.total) }}
            </td>

            <td v-if="!readonly" class="px-4 text-center">
              <button
                type="button"
                :disabled="isDeleting"
                class="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-zinc-200 bg-white text-zinc-500 shadow-sm transition hover:border-red-200 hover:bg-red-50 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-50"
                @click.stop="removeItem(item)"
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
