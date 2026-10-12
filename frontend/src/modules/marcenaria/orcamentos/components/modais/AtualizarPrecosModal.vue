<script setup lang="ts">
/**
 * @component AtualizarPrecosModal
 * @description Preços dos insumos que mudaram no cadastro (Spec 06B D39, D40;
 * SPEC-00 O3): nunca mudar preço sem avisar.
 *
 * Tabela com o custo no orçamento e o de hoje, uma caixa por linha (todas
 * marcadas) e o efeito no total. O vendedor decide sabendo quanto o total
 * muda: "Manter preços do orçamento" ou "Atualizar selecionados".
 */
import { computed, ref, watch } from 'vue';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import { formatCurrency } from '@/shared/utils/finance';

import type { PrecosDesatualizados } from '../../schemas/orcamentoDetalhe.schema';
import { ROTULO_ORIGEM } from '../../utils/custoProduto';

const props = defineProps<{
  isOpen: boolean;
  precos: PrecosDesatualizados | null;
  gravando: boolean;
}>();

const emit = defineEmits<{ close: []; atualizar: [insumoIds: number[]] }>();

// Todas as linhas começam marcadas; reabrir com outra lista remarca tudo.
const marcados = ref<Set<number>>(new Set());
watch(() => props.precos, (precos) => {
  marcados.value = new Set(precos?.itens.map((item) => item.insumo_id) ?? []);
}, { immediate: true });

function alternar(insumoId: number) {
  const novo = new Set(marcados.value);              // novo Set: o Vue percebe a troca
  if (novo.has(insumoId)) novo.delete(insumoId);
  else novo.add(insumoId);
  marcados.value = novo;
}

const itens = computed(() => props.precos?.itens ?? []);

/** "+R$ 73,15" / "−R$ 10,00": sinal explícito para ler a direção de relance. */
function comSinal(centavos: number): string {
  if (centavos === 0) return formatCurrency(0);
  return `${centavos > 0 ? '+' : '−'}${formatCurrency(Math.abs(centavos))}`;
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="Atualizar preços dos insumos" subtitle="Estes insumos têm hoje um custo diferente do que está no orçamento." size="xl" @close="emit('close')">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-zinc-100 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
          <th class="w-8 py-2"><span class="sr-only">Atualizar</span></th>
          <th class="py-2">Móvel</th>
          <th class="py-2">Insumo</th>
          <th class="py-2 text-right">No orçamento</th>
          <th class="py-2 text-right">Hoje</th>
          <th class="py-2 text-right">Diferença</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-zinc-100">
        <tr v-for="item in itens" :key="item.insumo_id" :data-testid="`preco-${item.insumo_id}`">
          <td class="py-2">
            <input
              type="checkbox"
              class="accent-brand-primary"
              :checked="marcados.has(item.insumo_id)"
              :aria-label="`Atualizar ${item.descricao} de ${item.movel}`"
              @change="alternar(item.insumo_id)"
            />
          </td>
          <td class="py-2 text-zinc-600">{{ item.movel }}</td>
          <td class="py-2 text-zinc-800">
            {{ item.descricao }}
            <span
              v-if="item.sofre_perda_orcamento !== item.sofre_perda_hoje"
              class="ml-1 rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-semibold text-amber-800"
            >perda mudou</span>
          </td>
          <td class="py-2 text-right tabular-nums text-zinc-600">{{ formatCurrency(item.custo_atual_orcamento) }}</td>
          <td class="py-2 text-right tabular-nums text-zinc-800">
            {{ formatCurrency(item.custo_produto_hoje) }}
            <span class="block text-[10px] text-zinc-400">{{ ROTULO_ORIGEM[item.origem_hoje] ?? item.origem_hoje }}</span>
          </td>
          <td class="py-2 text-right tabular-nums" :class="item.custo_produto_hoje > item.custo_atual_orcamento ? 'text-red-600' : 'text-emerald-700'">
            {{ comSinal(item.custo_produto_hoje - item.custo_atual_orcamento) }}
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Efeito no total (com todos os preços novos), calculado pela API. -->
    <p v-if="precos" class="mt-4 text-sm text-zinc-700" data-testid="efeito-total">
      Total: {{ formatCurrency(precos.total_atual_centavos) }} → {{ formatCurrency(precos.total_com_precos_novos_centavos) }}
      <span class="font-semibold">({{ comSinal(precos.diferenca_centavos) }})</span>
      <span class="block text-[11px] text-zinc-400">Com todos os preços da lista atualizados.</span>
    </p>

    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" data-testid="manter-precos" @click="emit('close')">Manter preços do orçamento</BaseButton>
        <BaseButton
          variant="primary"
          :disabled="!marcados.size"
          :is-loading="gravando"
          data-testid="atualizar-selecionados"
          @click="emit('atualizar', [...marcados])"
        >
          Atualizar selecionados
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
