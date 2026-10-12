<script setup lang="ts">
import { computed, ref } from 'vue';
import { storeToRefs } from 'pinia';
import { Plus, Trash2, Package, Wrench, ShoppingBag, Pencil, Lock, ChevronDown } from 'lucide-vue-next';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { useAuthStore } from '@/shared/stores/auth.store';
import { formatCurrency } from '@/shared/utils/finance';
import type { OsItemCreateSchemaDataType, OsItemReadSchemaDataType } from '../../schemas/relationship/osItem.schema';
import { useCapacidades } from '@/modules/order-service/shared/segmento/useCapacidades';
import { formatGarantiaItem } from '@/modules/order-service/shared/utils/formatters';

type OsItem = OsItemCreateSchemaDataType | OsItemReadSchemaDataType;

const { temAprovacaoItens, temGarantiaItens } = useCapacidades();

const STATUS_BADGE: Record<string, { label: string; cls: string }> = {
  APROVADO: { label: 'Aprovado', cls: 'bg-emerald-50 text-emerald-600' },
  PENDENTE: { label: 'Pendente', cls: 'bg-amber-50 text-amber-600' },
  REPROVADO: { label: 'Reprovado', cls: 'bg-red-50 text-red-600' },
};

function statusBadge(item: OsItem) {
  return STATUS_BADGE[item.status_aprovacao ?? 'APROVADO'] ?? STATUS_BADGE.APROVADO;
}

// Mesma função das vias impressas: tela e papel não podem divergir na garantia.
const garantiaLabel = formatGarantiaItem;

interface Props {
  itens: OsItem[];
  isLocked?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  isLocked: false,
});

const emit = defineEmits<{
  addItem: [];
  editItem: [index: number];
  removeItem: [index: number];
}>();

/**
 * Item gerado por um orçamento (fábrica antiga ou marcenaria, Spec 08B D24):
 * muda pelo orçamento, não aqui (F4a). Olha só os campos do item, nunca o
 * segmento. Itens de hoje (sem `origem` e sem `fabrica_orcamento_id`) e itens
 * novos ainda em memória (sem o campo) continuam editáveis.
 */
function veioDoOrcamento(item: OsItem): boolean {
  const daFabrica = 'fabrica_orcamento_id' in item && item.fabrica_orcamento_id != null;   // regra de antes
  const comOrigem = 'origem' in item && !!item.origem;                                      // 08A: coluna genérica
  return daFabrica || comOrigem;
}

/**
 * As linhas, com o índice ORIGINAL (editar/remover avisam o pai pelo índice
 * em `itens`). Peças embutidas que vieram do orçamento (itens de produto com
 * `origem`) vão para o grupo recolhido do fim (D24a): uma cozinha traz 20
 * linhas de chapa, fita e ferragem, que empurrariam os móveis para fora da tela.
 */
const linhas = computed(() => props.itens.map((item, indice) => ({ item, indice })));
const ehMaterialDoOrcamento = (item: OsItem) => 'origem' in item && !!item.origem && item.tipo === 'PRODUTO';
const linhasPrincipais = computed(() => linhas.value.filter(({ item }) => !ehMaterialDoOrcamento(item)));
const materialDoOrcamento = computed(() => linhas.value.filter(({ item }) => ehMaterialDoOrcamento(item)));
const materialAberto = ref(false);                        // recolhido por padrão

function getItemIcon(item: OsItem) {
  return item.tipo === 'SERVICO' ? Wrench : ShoppingBag;
}

function getItemIconClass(item: OsItem) {
  return item.tipo === 'SERVICO'
    ? 'bg-brand-primary-light text-brand-primary'
    : 'bg-brand-primary-light text-brand-primary';
}

function getItemTotal(item: OsItem): number {
  if ('valor_total' in item && item.valor_total !== undefined) return item.valor_total;
  return item.quantidade * item.valor_unitario;
}

/**
 * O CUSTO INTERNO NA LINHA DO ITEM.
 *
 * O campo "Custo para a loja" só existia dentro do modal de editar item, e a
 * aba trava quando a OS finaliza -- ou seja, depois de fechada NÃO HAVIA COMO
 * VER o custo declarado. O dono passou uma tarde conferindo R$ 846 de CMV no
 * papel sem ter onde abrir o número, e a diferença que ele procurava era
 * justamente um custo lançado num item avulso.
 *
 * ⚠️ AQUI E SÓ AQUI. Custo é tratamento INTERNO, por decisão explícita do dono
 * em 05/09/2026: não entra no resumo da OS, não entra no resumo de pagamento e
 * nunca sai em via impressa. Quem for mexer nisto depois, a regra é essa.
 *
 * Só o master vê. Não é permissão fina de propósito: é o mesmo critério que o
 * Relatório de faturamento já usa para os blocos de custo e margem.
 */
const authStore = useAuthStore();
const { userData } = storeToRefs(authStore);
const podeVerCusto = computed(() => userData.value?.is_master === true);

function custoDoItem(item: OsItem): number {
  return Math.round(item.quantidade * (item.custo_unitario ?? 0));
}

/** Nulo quando não há custo declarado — item sem custo não ganha linha nenhuma. */
function margemDoItem(item: OsItem): { custo: number; sobra: number } | null {
  const custo = custoDoItem(item);
  if (custo <= 0) return null;
  return { custo, sobra: getItemTotal(item) - custo };
}
</script>

<template>
  <div class="space-y-4 animate-fadeIn">
    <div class="flex items-center justify-between border-b border-slate-200 pb-3">
      <div class="flex items-center gap-3">
        <div class="bg-brand-primary-light p-2 rounded-lg text-brand-primary">
          <Package :size="20" />
        </div>
        <div>
          <h5 class="text-sm font-bold text-slate-700">Itens da OS</h5>
          <p class="text-xs text-slate-500">Serviços e Peças adicionados</p>
        </div>
      </div>

      <BaseButton v-if="!isLocked" variant="primary" size="sm" @click="emit('addItem')">
        <Plus :size="16" class="mr-2" />
        ADICIONAR ITEM
      </BaseButton>
    </div>

    <fieldset :disabled="isLocked" class="contents">
      <div
        v-if="itens.length === 0"
        class="flex flex-col items-center justify-center py-12 text-slate-400 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50/50"
      >
        <div class="w-14 h-14 bg-slate-100 rounded-full flex items-center justify-center mb-3">
          <Package :size="28" stroke-width="1.5" class="text-slate-300" />
        </div>
        <p class="text-sm font-semibold text-slate-500">Nenhum item adicionado</p>
        <p class="text-xs text-slate-400 mt-1">Clique em "Adicionar Item" para incluir serviços ou peças.</p>
      </div>

      <div v-else class="space-y-2">
        <div
          v-for="{ item, indice: index } in linhasPrincipais"
          :key="'id' in item && item.id ? item.id : `new-${index}`"
          class="flex items-center justify-between p-3 bg-white border border-slate-200 rounded-lg hover:border-brand-primary/20 transition-colors group"
        >
          <div class="flex items-center gap-3 overflow-hidden">
            <div class="w-10 h-10 rounded-lg flex items-center justify-center shrink-0" :class="getItemIconClass(item)">
              <component :is="getItemIcon(item)" :size="18" />
            </div>
            <div class="min-w-0">
              <div class="flex items-center gap-2 min-w-0">
                <p class="text-sm font-bold text-slate-700 truncate">{{ item.nome }}</p>
                <span
                  v-if="temAprovacaoItens"
                  class="text-[10px] font-bold px-1.5 py-0.5 rounded-full shrink-0"
                  :class="statusBadge(item).cls"
                >
                  {{ statusBadge(item).label }}
                </span>
              </div>
              <p class="text-xs text-slate-500 truncate">
                {{ item.unidade_medida }}
                <span v-if="temGarantiaItens && garantiaLabel(item)"> · Garantia {{ garantiaLabel(item) }}</span>
              </p>
              <!-- Custo interno: só master, nunca em via impressa nem em resumo. -->
              <p
                v-if="podeVerCusto && margemDoItem(item)"
                class="mt-0.5 flex items-center gap-1 text-[11px] text-slate-400"
              >
                <Lock :size="10" class="shrink-0" />
                <span>
                  Custo {{ formatCurrency(margemDoItem(item)!.custo) }} · sobra
                  <strong :class="margemDoItem(item)!.sobra >= 0 ? 'text-emerald-600' : 'text-red-600'">
                    {{ formatCurrency(margemDoItem(item)!.sobra) }}
                  </strong>
                </span>
              </p>
            </div>
          </div>

          <div class="flex items-center gap-6 shrink-0">
            <div class="text-right hidden sm:block">
              <p class="text-xs text-slate-400 font-medium uppercase">Qtd</p>
              <p class="text-sm font-bold text-slate-600">{{ item.quantidade }}</p>
            </div>
            <div class="text-right hidden sm:block">
              <p class="text-xs text-slate-400 font-medium uppercase">Unitário</p>
              <p class="text-sm font-bold text-slate-600">{{ formatCurrency(item.valor_unitario) }}</p>
            </div>
            <div class="text-right w-24">
              <p class="text-xs text-slate-400 font-medium uppercase">Total</p>
              <p class="text-sm font-black text-slate-800">{{ formatCurrency(getItemTotal(item)) }}</p>
            </div>

            <div
              v-if="!isLocked && veioDoOrcamento(item)"
              class="flex items-center gap-1 pl-2 border-l border-slate-100 text-slate-300"
              title="Veio do orçamento aprovado. Para mudar, desfaça a aprovação ou crie uma nova versão do orçamento."
            >
              <Lock :size="14" />
            </div>
            <div v-else-if="!isLocked" class="flex items-center gap-1 pl-2 border-l border-slate-100">
              <BaseButton variant="ghost" size="sm" class="p-1.5 text-slate-400 hover:text-brand-primary hover:bg-brand-primary-light" @click="emit('editItem', index)">
                <Pencil :size="14" />
              </BaseButton>
              <BaseButton variant="ghost" size="sm" class="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50" @click="emit('removeItem', index)">
                <Trash2 :size="14" />
              </BaseButton>
            </div>
          </div>
        </div>

        <!-- Material do orçamento (D24a): recolhido, abre com um clique. Só itens com `origem`. -->
        <div v-if="materialDoOrcamento.length" class="rounded-lg border border-slate-200 bg-slate-50/50" data-testid="material-orcamento">
          <button
            type="button"
            class="flex w-full items-center justify-between px-3 py-2 text-xs font-bold text-slate-600 cursor-pointer"
            :aria-expanded="materialAberto"
            @click="materialAberto = !materialAberto"
          >
            <span>Material do orçamento ({{ materialDoOrcamento.length }} {{ materialDoOrcamento.length === 1 ? 'item' : 'itens' }})</span>
            <ChevronDown :size="14" class="transition-transform" :class="materialAberto ? 'rotate-180' : ''" />
          </button>
          <ul v-if="materialAberto" class="divide-y divide-slate-100 border-t border-slate-200 text-xs">
            <li v-for="{ item, indice } in materialDoOrcamento" :key="'id' in item && item.id ? item.id : `mat-${indice}`" class="flex items-center justify-between px-3 py-1.5">
              <span class="truncate text-slate-700">{{ item.nome }}</span>
              <span class="flex shrink-0 items-center gap-3 text-slate-500">
                {{ item.quantidade }} {{ item.unidade_medida }}
                <span class="tabular-nums">{{ formatCurrency(getItemTotal(item)) }}</span>
                <Lock :size="12" class="text-slate-300" />
              </span>
            </li>
          </ul>
        </div>
      </div>

    </fieldset>
  </div>
</template>

<style scoped>
.animate-fadeIn {
  animation: fadeIn 0.3s ease-in-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
