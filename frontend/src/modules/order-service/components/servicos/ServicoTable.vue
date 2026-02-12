<script setup lang="ts">
import { Ellipsis, Pencil, Power } from 'lucide-vue-next';
import BaseTableContainer from '@/shared/components/commons/BaseTableContainer/BaseTableContainer.vue';
import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';
import BaseFilter from '@/shared/components/ui/BaseFilter/BaseFilter.vue';
import { STATUS_FILTER_CONFIG } from '../../constants/servicos.constants';
import { formatCentavosToBRL } from '../../utils/servicos.utils';
import type { StatusFilter } from '../../types/servicos.types';
import type { ServiceReadZod } from '../../schemas/servicos.schema';

interface Props {
  servicos: ServiceReadZod[];
  isLoading?: boolean;
  isError?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  isError: false,
});

const emit = defineEmits<{
  view: [servico: ServiceReadZod];
  edit: [servico: ServiceReadZod];
  toggleStatus: [servico: ServiceReadZod];
}>();

const search = defineModel<string>('search', { default: '' });
const statusFilter = defineModel<StatusFilter | null>('statusFilter', { default: null });

const statusBadgeConfig = {
  true: {
    label: 'Ativo',
    class: 'bg-emerald-50 text-emerald-600 border border-emerald-200',
  },
  false: {
    label: 'Inativo',
    class: 'bg-red-50 text-red-600 border border-red-200',
  },
} as const;
</script>

<template>
  <BaseTableContainer
    :is-loading="isLoading"
    :is-error="isError"
    :is-empty="servicos.length === 0"
    :current-page="1"
    :total-pages="1"
    :total-items="servicos.length"
    item-label="serviço"
    empty-title="Nenhum serviço encontrado"
    :empty-description="servicos.length > 0 ? 'Tente ajustar os filtros de busca.' : 'Cadastre seu primeiro serviço.'"
    error-title="Erro ao carregar serviços"
    error-description="Verifique sua conexão e tente novamente."
  >
    <template #toolbar>
      <BaseSearchInput
        v-model="search"
        placeholder="Buscar por descrição..."
      />

      <BaseFilter
        v-model="statusFilter"
        :filter-config="STATUS_FILTER_CONFIG"
        button-label="Status"
      />
    </template>

    <div class="overflow-x-auto">
      <table class="w-full text-left min-w-120">
        <thead>
          <tr class="bg-zinc-50/50 text-[10px] uppercase tracking-wider text-zinc-500 font-bold border-b border-zinc-100">
            <th class="px-4 md:px-6 py-3 md:py-4">Descrição</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Valor</th>
            <th class="px-4 md:px-6 py-3 md:py-4">Status</th>
            <th class="px-4 md:px-6 py-3 md:py-4 text-right min-w-40">Ações Rápidas</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-100">
          <tr
            v-for="servico in servicos"
            :key="servico.id"
            class="hover:bg-zinc-50/50 transition-colors group cursor-pointer"
            @click="emit('view', servico)"
          >
            <td class="px-4 md:px-6 py-3 md:py-4">
              <span class="text-sm font-medium text-zinc-900 group-hover:text-brand-primary transition-colors">
                {{ servico.descricao }}
              </span>
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4">
              <span class="text-sm font-semibold text-zinc-600 group-hover:text-brand-primary transition-colors">
                {{ formatCentavosToBRL(servico.valor) }}
              </span>
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4">
              <span
                :class="[
                  'px-2 md:px-3 py-1 rounded-full text-[10px] md:text-[11px] font-bold whitespace-nowrap transition-colors',
                  statusBadgeConfig[String(servico.ativo) as 'true' | 'false'].class,
                ]"
              >
                {{ statusBadgeConfig[String(servico.ativo) as 'true' | 'false'].label }}
              </span>
            </td>

            <td class="px-4 md:px-6 py-3 md:py-4">
              <div class="flex items-center justify-end h-full">
                <div class="hidden group-hover:flex items-center justify-end gap-2">
                  <button
                    type="button"
                    class="p-2 rounded-lg text-zinc-400 hover:text-brand-primary hover:bg-brand-primary/10 transition-colors cursor-pointer"
                    title="Editar serviço"
                    @click.stop="emit('edit', servico)"
                  >
                    <Pencil :size="18" />
                  </button>

                  <button
                    type="button"
                    :class="[
                      'p-2 rounded-lg transition-colors cursor-pointer',
                      servico.ativo
                        ? 'text-zinc-400 hover:text-red-500 hover:bg-red-50'
                        : 'text-zinc-400 hover:text-emerald-500 hover:bg-emerald-50',
                    ]"
                    :title="servico.ativo ? 'Desativar serviço' : 'Ativar serviço'"
                    @click.stop="emit('toggleStatus', servico)"
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
