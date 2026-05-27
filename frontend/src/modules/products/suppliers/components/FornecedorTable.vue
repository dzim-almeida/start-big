// ============================================================================
// COMPONENTE: FornecedorTable (Sistema ERP Produto Motorista - Start Big)
// RESPONSABILIDADE: Listagem principal de fornecedores com suporte a busca,
//                   filtragem por status, paginação e ações rápidas.
// FUNCIONALIDADES: Formatação dinâmica de documentos (CPF/CNPJ), Badges de 
//                  tipo/status e estados de erro/vazio integrados.
// ============================================================================
<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { Ellipsis, Pencil, Power, Eye } from 'lucide-vue-next';
import BaseTableContainer from '@/shared/components/commons/BaseTableContainer/BaseTableContainer.vue';
import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';
import BaseFilter from '@/shared/components/ui/BaseFilter/BaseFilter.vue';
import { STATUS_FILTER_CONFIG } from '../constants/fornecedor.constants';
import type { StatusFilter } from '../types/fornecedor.types';
import type { FornecedorReadType } from '../schemas/fornecedor.schema';

function formatCnpj(cnpj: string): string {
  const digits = cnpj.replace(/\D/g, '');
  return digits.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
}

function formatCpf(cpf: string): string {
  const digits = cpf.replace(/\D/g, '');
  return digits.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, '$1.$2.$3-$4');
}

function getDocumento(fornecedor: FornecedorReadType): string {
  if (fornecedor.tipo === 'entregador' && fornecedor.cpf) {
    return formatCpf(fornecedor.cpf);
  }
  if (fornecedor.cnpj) return formatCnpj(fornecedor.cnpj);
  return '—';
}

const tipoBadgeConfig: Record<string, { label: string; class: string }> = {
  produto: { label: 'Produto', class: 'bg-zinc-100 text-zinc-700 border border-zinc-200' },
  transportadora: { label: 'Transportadora', class: 'bg-zinc-100 text-zinc-700 border border-zinc-200' },
  entregador: { label: 'Entregador', class: 'bg-zinc-100 text-zinc-700 border border-zinc-200' },
};

const ITEMS_PER_PAGE = 10;

interface Props {
  fornecedores: FornecedorReadType[];
  isLoading?: boolean;
  isError?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  isError: false,
});

const emit = defineEmits<{
  view: [fornecedor: FornecedorReadType];
  edit: [fornecedor: FornecedorReadType];
  'toggle-status': [fornecedor: FornecedorReadType];
}>();

const search = defineModel<string>('search', { default: '' });
const statusFilter = defineModel<StatusFilter | null>('statusFilter', { default: null });
const currentPage = ref(1);

watch([search, statusFilter], () => { currentPage.value = 1; });

const totalItems = computed(() => props.fornecedores.length);
const totalPages = computed(() => Math.max(1, Math.ceil(totalItems.value / ITEMS_PER_PAGE)));

const pagedFornecedores = computed(() => {
  const start = (currentPage.value - 1) * ITEMS_PER_PAGE;
  return props.fornecedores.slice(start, start + ITEMS_PER_PAGE);
});

const statusBadgeConfig = {
  true: { label: 'Ativo', class: 'bg-emerald-50 text-emerald-600 border border-emerald-200' },
  false: { label: 'Inativo', class: 'bg-red-50 text-red-600 border border-red-200' },
} as const;

</script>

<template>
  <BaseTableContainer
    :is-loading="isLoading"
    :is-error="isError"
    :is-empty="fornecedores.length === 0"
    :current-page="currentPage"
    :total-pages="totalPages"
    :total-items="totalItems"
    item-label="fornecedor"
    empty-title="Nenhum fornecedor encontrado"
    empty-description="Cadastre seu primeiro fornecedor."
    error-title="Erro ao carregar fornecedores"
    error-description="Verifique sua conexão e tente novamente."
    @update:current-page="currentPage = $event"
  >
    <template #toolbar>
      <BaseSearchInput v-model="search" placeholder="Buscar por nome ou CNPJ..." />
      <BaseFilter v-model="statusFilter" :filter-config="STATUS_FILTER_CONFIG" button-label="Filtro" />
    </template>

    <div class="overflow-x-auto">
      <table class="w-full text-left min-w-120">
        <thead>
          <tr
            class="bg-zinc-50/50 text-[10px] uppercase tracking-wider text-zinc-500 font-bold border-b border-zinc-100"
          >
            <th class="px-4 md:px-6 py-3 md:py-4">Razão Social / Nome Fantasia</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Tipo</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Documento</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Contato</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Status</th>
            <th class="px-4 md:px-6 py-3 md:py-4 text-right min-w-40">Ações</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-100">
          <tr
            v-for="fornecedor in pagedFornecedores"
            :key="fornecedor.id"
            class="hover:bg-zinc-50/50 transition-colors group cursor-pointer"
            @click="emit('view', fornecedor)"
          >
            <td class="px-4 md:px-6 py-3 md:py-4">
              <div class="flex flex-col">
                <span class="text-sm font-medium text-zinc-900 group-hover:text-brand-primary transition-colors">
                  {{ fornecedor.nome }}
                </span>
                <span v-if="fornecedor.nome_fantasia" class="text-xs text-zinc-400">
                  {{ fornecedor.nome_fantasia }}
                </span>
              </div>
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4">
              <span
                v-if="fornecedor.tipo && tipoBadgeConfig[fornecedor.tipo]"
                :class="[
                  'px-2 py-1 rounded-full text-[10px] font-bold whitespace-nowrap',
                  tipoBadgeConfig[fornecedor.tipo].class,
                ]"
              >
                {{ tipoBadgeConfig[fornecedor.tipo].label }}
              </span>
              <span v-else class="text-xs text-zinc-400">—</span>
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4">
              <span class="text-sm text-zinc-600 font-mono">{{ getDocumento(fornecedor) }}</span>
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4">
              <div class="flex flex-col gap-0.5">
                <span v-if="fornecedor.email" class="text-xs text-zinc-600">{{ fornecedor.email }}</span>
                <span v-if="fornecedor.telefone || fornecedor.celular" class="text-xs text-zinc-500">
                  {{ fornecedor.celular || fornecedor.telefone }}
                </span>
                <span v-if="!fornecedor.email && !fornecedor.telefone && !fornecedor.celular" class="text-xs text-zinc-400">—</span>
              </div>
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4">
              <span
                :class="[
                  'px-2 md:px-3 py-1 rounded-full text-[10px] md:text-[11px] font-bold whitespace-nowrap transition-colors',
                  statusBadgeConfig[String(fornecedor.ativo) as 'true' | 'false'].class,
                ]"
              >
                {{ statusBadgeConfig[String(fornecedor.ativo) as 'true' | 'false'].label }}
              </span>
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4">
              <div class="flex items-center justify-end h-full">
                <div class="hidden group-hover:flex items-center justify-end gap-2">
                  <button
                    type="button"
                    class="p-2 rounded-lg text-zinc-400 hover:text-brand-primary hover:bg-brand-primary/10 transition-colors cursor-pointer"
                    title="Ver detalhes"
                    @click.stop="emit('view', fornecedor)"
                  >
                    <Eye :size="18" />
                  </button>
                  <button
                    type="button"
                    class="p-2 rounded-lg text-zinc-400 hover:text-brand-primary hover:bg-brand-primary/10 transition-colors cursor-pointer"
                    title="Editar fornecedor"
                    @click.stop="emit('edit', fornecedor)"
                  >
                    <Pencil :size="18" />
                  </button>
                  <button
                    type="button"
                    :class="[
                      'p-2 rounded-lg transition-colors cursor-pointer',
                      fornecedor.ativo
                        ? 'text-zinc-400 hover:text-red-500 hover:bg-red-50'
                        : 'text-zinc-400 hover:text-emerald-500 hover:bg-emerald-50',
                    ]"
                    :title="fornecedor.ativo ? 'Desativar fornecedor' : 'Ativar fornecedor'"
                    @click.stop="emit('toggle-status', fornecedor)"
                  >
                    <Power :size="18" />
                  </button>
                </div>
                <div class="p-2 text-zinc-400 group-hover:hidden cursor-pointer">
                  <Ellipsis :size="20" />
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </BaseTableContainer>
</template>
