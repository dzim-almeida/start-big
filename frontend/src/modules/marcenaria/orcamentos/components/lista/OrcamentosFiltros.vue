<script setup lang="ts">
/**
 * @component OrcamentosFiltros
 * @description Chips de status com contagem, busca, vendedor e "Mostrar
 * versões antigas" (Spec 06B D48, §6.1).
 *
 * "Vence em 3 dias" é a pergunta que o vendedor faz toda manhã: por isso ele
 * tem um chip próprio, que filtra por `vence_em_dias=3` em vez de status.
 */
import { computed } from 'vue';

import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';
import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';
import BaseSelect, { type SelectOption } from '@/shared/components/ui/BaseSelect/BaseSelect.vue';

import type { ContagensOrcamento } from '../../schemas/orcamentoDetalhe.schema';

/** Os chips, na ordem da tela. `VENCE_3` não é status: é o filtro de validade. */
export type ChipFiltro = 'TODOS' | 'RASCUNHO' | 'ENVIADO' | 'VENCE_3' | 'VENCIDO' | 'RECUSADO' | 'APROVADO';

const props = defineProps<{
  contagens?: ContagensOrcamento;
  /** Funcionários para o filtro "Vendedor" (vazio esconde o filtro). */
  vendedores: SelectOption[];
}>();

// Cada filtro é um v-model: quem guarda o estado (e a URL) é a tela.
const chip = defineModel<ChipFiltro>('chip', { required: true });
const busca = defineModel<string>('busca', { required: true });
const vendedorId = defineModel<number | null>('vendedorId', { required: true });
const versoesAntigas = defineModel<boolean>('versoesAntigas', { required: true });

/** Rótulo e contagem de cada chip (a contagem vem pronta da API, D48). */
const chips = computed(() => {
  const c = props.contagens;
  return [
    { id: 'TODOS' as const, rotulo: 'Todos', total: c?.total },
    { id: 'RASCUNHO' as const, rotulo: 'Rascunho', total: c?.RASCUNHO },
    { id: 'ENVIADO' as const, rotulo: 'Enviado', total: c?.ENVIADO },
    { id: 'VENCE_3' as const, rotulo: 'Vence em 3 dias', total: c?.vence_em_3_dias },
    { id: 'VENCIDO' as const, rotulo: 'Vencido', total: c?.VENCIDO },
    { id: 'RECUSADO' as const, rotulo: 'Recusado', total: c?.RECUSADO },
    { id: 'APROVADO' as const, rotulo: 'Aprovado', total: c?.APROVADO },
  ];
});

/** O BaseSelect trabalha com string|number; "todos" vira null. */
const vendedorSelecionado = computed({
  get: () => vendedorId.value ?? '',
  set: (valor: string | number | undefined) => {
    vendedorId.value = valor === '' || valor == null ? null : Number(valor);
  },
});
const opcoesVendedor = computed<SelectOption[]>(() => [{ value: '', label: 'Todos os vendedores' }, ...props.vendedores]);
</script>

<template>
  <div class="flex w-full flex-col gap-3">
    <!-- Chips: um clique troca o filtro de status (role="tablist" para leitor de tela). -->
    <div class="flex flex-wrap gap-2" role="tablist" aria-label="Filtrar por status">
      <button
        v-for="item in chips"
        :key="item.id"
        type="button"
        role="tab"
        :aria-selected="chip === item.id"
        class="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors cursor-pointer"
        :class="chip === item.id
          ? 'border-brand-primary bg-brand-primary text-white'
          : 'border-zinc-200 bg-white text-zinc-600 hover:bg-zinc-50'"
        :data-testid="`chip-${item.id}`"
        @click="chip = item.id"
      >
        {{ item.rotulo }}
        <!-- Contagem só quando já chegou (sem "undefined" piscando). -->
        <span v-if="item.total != null" class="tabular-nums opacity-80">{{ item.total }}</span>
      </button>
    </div>

    <div class="flex flex-wrap items-center gap-3">
      <div class="min-w-60 flex-1">
        <BaseSearchInput v-model="busca" placeholder="Código, projeto ou cliente…" />
      </div>
      <div v-if="vendedores.length" class="w-56">
        <BaseSelect v-model="vendedorSelecionado" :options="opcoesVendedor" placeholder="Vendedor" />
      </div>
      <BaseCheckbox v-model="versoesAntigas" label="Mostrar versões antigas" />
    </div>
  </div>
</template>
