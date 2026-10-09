<script setup lang="ts">
/**
 * @component OrcamentosTabela
 * @description Linhas da lista de orçamentos (Spec 06B D49). A linha inteira
 * é clicável. A coluna "Margem" só existe para quem vê custos (a API nem
 * manda o número para os outros, 06A D23).
 */
import { formatCurrency } from '@/shared/utils/finance';
import { tempoDecorrido } from '@/shared/utils/date.utils';

import type { ItemListaOrcamento } from '../../schemas/orcamentoDetalhe.schema';
import { formatarBp } from '../../utils/conversoes';
import { textoValidade, tomValidade } from '../../utils/validade';
import OrcamentoStatusBadge from './OrcamentoStatusBadge.vue';

defineProps<{
  itens: ItemListaOrcamento[];
  mostrarMargem: boolean;
}>();

const emit = defineEmits<{ abrir: [id: number] }>();

/** Validade só importa enquanto o cliente pode aceitar (enviado ou vencido). */
function validadeVisivel(item: ItemListaOrcamento): boolean {
  return !!item.data_validade && (item.status === 'ENVIADO' || item.status === 'VENCIDO');
}

/** "há 2 h" / "agora" (o "há" não combina com "agora"). */
function atualizadoHa(data: string | null): string {
  if (!data) return '—';
  const tempo = tempoDecorrido(data);
  return tempo === 'agora' ? 'agora' : `há ${tempo}`;
}

/** Cor do texto da validade: âmbar perto de vencer, vermelho vencido. */
function classeValidade(validade: string): string {
  const tom = tomValidade(validade);
  if (tom === 'vencido') return 'text-red-600 font-semibold';
  if (tom === 'atencao') return 'text-amber-700 font-semibold';
  return 'text-zinc-600';
}
</script>

<template>
  <table class="w-full min-w-220 text-sm">
    <thead>
      <tr class="border-b border-zinc-100 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
        <th class="px-5 py-3">Código</th>
        <th class="px-5 py-3">Cliente</th>
        <th class="px-5 py-3">Projeto</th>
        <th class="px-5 py-3">Vendedor</th>
        <th class="px-5 py-3 text-right">Móveis</th>
        <th class="px-5 py-3 text-right">Total</th>
        <th v-if="mostrarMargem" class="px-5 py-3 text-right" data-testid="coluna-margem">Margem</th>
        <th class="px-5 py-3">Validade</th>
        <th class="px-5 py-3">Status</th>
        <th class="px-5 py-3">Atualizado</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-zinc-100">
      <tr
        v-for="item in itens"
        :key="item.id"
        class="cursor-pointer hover:bg-zinc-50/60 focus:outline-none focus:bg-zinc-50"
        tabindex="0"
        :data-testid="`linha-orcamento-${item.id}`"
        @click="emit('abrir', item.id)"
        @keydown.enter="emit('abrir', item.id)"
      >
        <td class="px-5 py-3 whitespace-nowrap">
          <span class="font-semibold text-zinc-800">{{ item.codigo }}</span>
          <!-- A versão só aparece da v2 em diante (a v1 é o normal). -->
          <span v-if="item.versao > 1" class="ml-1.5 rounded bg-zinc-100 px-1.5 py-0.5 text-[10px] font-bold text-zinc-600">
            v{{ item.versao }}
          </span>
        </td>
        <td class="px-5 py-3 max-w-48 truncate text-zinc-700">{{ item.cliente_nome ?? '—' }}</td>
        <td class="px-5 py-3 max-w-56 truncate text-zinc-700">{{ item.projeto_nome ?? '—' }}</td>
        <td class="px-5 py-3 text-zinc-600">{{ item.vendedor_nome ?? '—' }}</td>
        <td class="px-5 py-3 text-right tabular-nums text-zinc-600">{{ item.resumo_qtd_moveis }}</td>
        <td class="px-5 py-3 text-right font-semibold tabular-nums text-zinc-800">
          {{ formatCurrency(item.resumo_total_centavos) }}
        </td>
        <td v-if="mostrarMargem" class="px-5 py-3 text-right tabular-nums text-zinc-600">
          {{ item.resumo_margem_bp != null ? formatarBp(item.resumo_margem_bp) : '—' }}
        </td>
        <td class="px-5 py-3 whitespace-nowrap">
          <span v-if="validadeVisivel(item)" :class="classeValidade(item.data_validade!)">
            {{ textoValidade(item.data_validade!) }}
          </span>
          <span v-else class="text-zinc-300">—</span>
        </td>
        <td class="px-5 py-3">
          <OrcamentoStatusBadge :status="item.status" />
          <!-- Aprovado: a OS que ele gerou (08A). -->
          <p v-if="item.os_numero" class="mt-0.5 text-[11px] text-zinc-400">OS {{ item.os_numero }}</p>
        </td>
        <td class="px-5 py-3 whitespace-nowrap text-xs text-zinc-400">
          {{ atualizadoHa(item.data_atualizacao) }}
        </td>
      </tr>
    </tbody>
  </table>
</template>
