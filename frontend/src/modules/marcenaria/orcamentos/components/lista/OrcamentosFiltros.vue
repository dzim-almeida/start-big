<script setup lang="ts">
/**
 * @component OrcamentosFiltros
 * @description Barra de filtros da lista de orçamentos (Spec 06B D48, §6.1),
 * no padrão das outras listas do sistema: busca + BaseFilter (Status e
 * Vendedor) + "Mostrar versões antigas".
 *
 * "Vence em 3 dias" é a pergunta que o vendedor faz toda manhã: por isso ele é
 * uma opção do filtro de Status, que filtra por `vence_em_dias=3` em vez de status.
 * A contagem de cada status vai no rótulo da opção (vem pronta da API, D48).
 */
import { computed } from 'vue';

import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';
import BaseFilter from '@/shared/components/ui/BaseFilter/BaseFilter.vue';
import BaseSearchInput from '@/shared/components/ui/BaseSearchInput/BaseSearchInput.vue';
import type { SelectOption } from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import type { FilterOption } from '@/shared/types/filter.types';

import type { ContagensOrcamento } from '../../schemas/orcamentoDetalhe.schema';

/** As opções de status, na ordem da tela. `VENCE_3` não é status: é o filtro de validade. */
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

/** "Rascunho · 3" — a contagem só aparece quando já chegou (sem "undefined" piscando). */
const comTotal = (rotulo: string, total?: number) => (total != null ? `${rotulo} · ${total}` : rotulo);

const opcoesStatus = computed<Record<string, FilterOption>>(() => {
  const c = props.contagens;
  return {
    RASCUNHO: { label: comTotal('Rascunho', c?.RASCUNHO), class: '', color: 'bg-zinc-400' },
    ENVIADO: { label: comTotal('Enviado', c?.ENVIADO), class: '', color: 'bg-blue-500' },
    VENCE_3: { label: comTotal('Vence em 3 dias', c?.vence_em_3_dias), class: '', color: 'bg-amber-500' },
    VENCIDO: { label: comTotal('Vencido', c?.VENCIDO), class: '', color: 'bg-amber-700' },
    APROVADO: { label: comTotal('Aprovado', c?.APROVADO), class: '', color: 'bg-emerald-500' },
    RECUSADO: { label: comTotal('Recusado', c?.RECUSADO), class: '', color: 'bg-red-500' },
  };
});

/** O BaseFilter fala `null` para "Todos"; a tela fala 'TODOS'. */
const statusSelecionado = computed<string | null>({
  get: () => (chip.value === 'TODOS' ? null : chip.value),
  set: (valor) => { chip.value = (valor ?? 'TODOS') as ChipFiltro; },
});

const opcoesVendedor = computed<Record<string, FilterOption>>(() =>
  Object.fromEntries(props.vendedores.map((v) => [String(v.value), { label: v.label, class: '', color: 'bg-brand-primary' }])),
);

const vendedorSelecionado = computed<string | null>({
  get: () => (vendedorId.value == null ? null : String(vendedorId.value)),
  set: (valor) => { vendedorId.value = valor == null ? null : Number(valor); },
});
</script>

<template>
  <!-- `contents`: os filtros viram itens da barra do BaseTableContainer, como nas outras listas. -->
  <div class="contents">
    <div class="min-w-56 flex-1">
      <BaseSearchInput v-model="busca" placeholder="Buscar orçamento…" />
    </div>
    <div data-testid="filtro-status">
      <BaseFilter
        v-model="statusSelecionado"
        :filter-config="opcoesStatus"
        title="Status do orçamento"
        button-label="Status"
      />
    </div>
    <BaseFilter
      v-if="vendedores.length"
      v-model="vendedorSelecionado"
      :filter-config="opcoesVendedor"
      title="Vendedor"
      button-label="Vendedor"
    />
    <div class="shrink-0">
      <BaseCheckbox v-model="versoesAntigas" label="Versões antigas" />
    </div>
  </div>
</template>
