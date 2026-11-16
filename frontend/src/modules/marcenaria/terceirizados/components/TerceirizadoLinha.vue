<script setup lang="ts">
/**
 * @component TerceirizadoLinha
 * @description Um móvel que vem pronto da central (Spec 11B D2, D5, D7, D8).
 *
 * Mostra o móvel, o ambiente, as medidas e a quantidade; a situação como
 * selo; o pedido com a previsão (quem liga para a central precisa do número
 * na frente); o atraso em vermelho. A caixa marca a linha para a barra de
 * ações da seção; o menu "⋯" tem o que é só desta linha.
 */
import { computed, ref } from 'vue';
import { onClickOutside } from '@vueuse/core';
import { AlertTriangle, ExternalLink, MoreHorizontal } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { formatCurrency } from '@/shared/utils/finance';

import type { MovelTerceirizado } from '../schemas/terceirizado.schema';
import { diasDeAtraso, seloDaSituacao, textoDasMedidas, textoDoPedido, voltaPara } from '../utils/terceirizados';

const props = defineProps<{
  movel: MovelTerceirizado;
  /** A OS ainda aceita mudanças (D9): sem caixa e sem menu quando fechada. */
  editavel: boolean;
  /** A caixa de seleção desta linha está marcada. */
  marcado: boolean;
  /** Mostrar "Ver no Compras" (há pedido do Compras e a pessoa pode ver o Compras, D5). */
  verNoCompras: boolean;
}>();

const emit = defineEmits<{
  'update:marcado': [valor: boolean];
  verNoCompras: [];
  problema: [];
  voltar: [];
}>();

const selo = computed(() => seloDaSituacao(props.movel));
const pedido = computed(() => textoDoPedido(props.movel));
const medidas = computed(() => textoDasMedidas(props.movel));
const atraso = computed(() => diasDeAtraso(props.movel));

// --- Menu "⋯" (D7) -------------------------------------------------------------------
const menuAberto = ref(false);
const menuRef = ref<HTMLElement | null>(null);
onClickOutside(menuRef, () => { menuAberto.value = false; });

/** Só o que faz sentido agora: problema em quem chegou; voltar quando há para onde. */
const opcoes = computed(() => {
  const lista: { id: 'problema' | 'voltar'; texto: string }[] = [];
  if (props.movel.situacao === 'RECEBIDO' || props.movel.situacao === 'CONFERIDO') {
    lista.push({ id: 'problema', texto: 'Registrar problema' });
  }
  if (voltaPara(props.movel)) lista.push({ id: 'voltar', texto: 'Voltar um passo' });
  return lista;
});

function escolher(id: 'problema' | 'voltar') {
  menuAberto.value = false;
  if (id === 'problema') emit('problema');
  else emit('voltar');
}
</script>

<template>
  <div
    class="flex flex-wrap items-start gap-x-4 gap-y-2 rounded-xl border px-4 py-3"
    :class="movel.situacao === 'CONFERIDO' ? 'border-zinc-100 bg-zinc-50' : 'border-zinc-200 bg-white'"
    :data-testid="`terceirizado-${movel.movel_id}`"
  >
    <!-- Caixa de seleção: a barra de ações age sobre os marcados (D3) -->
    <input
      v-if="editavel"
      type="checkbox"
      class="mt-1 h-4 w-4 shrink-0 accent-brand-primary"
      :checked="marcado"
      :aria-label="`Marcar ${movel.nome}`"
      :data-testid="`marcar-${movel.movel_id}`"
      @change="emit('update:marcado', ($event.target as HTMLInputElement).checked)"
    />

    <div class="min-w-0 flex-1">
      <p class="text-sm font-semibold text-zinc-900">
        {{ movel.nome }}
        <span class="ml-1 text-xs font-normal text-zinc-500">{{ movel.ambiente }}</span>
      </p>
      <p class="text-xs text-zinc-500">
        <template v-if="medidas">{{ medidas }} · </template>{{ movel.quantidade }}×
        <!-- D8: o valor orçado da central só vem para quem vê custos -->
        <span v-if="movel.valor_orcado_centavos != null" class="ml-1 text-zinc-400" data-testid="valor-orcado">
          · orçado {{ formatCurrency(movel.valor_orcado_centavos) }}
        </span>
      </p>

      <div class="mt-1.5 flex flex-wrap items-center gap-2">
        <span class="rounded-full border px-2 py-0.5 text-[11px] font-medium" :class="selo.classe" data-testid="selo">
          {{ selo.texto }}
        </span>
        <span v-if="pedido" class="text-xs text-zinc-600" data-testid="pedido">{{ pedido }}</span>
        <!-- O atraso em destaque: é o que se cobra da central (D2) -->
        <span
          v-if="atraso"
          class="inline-flex items-center gap-1 rounded-full border border-red-200 bg-red-50 px-2 py-0.5 text-[11px] font-semibold text-red-700"
          data-testid="atraso"
        >
          <AlertTriangle :size="12" />
          Atrasado {{ atraso }} {{ atraso === 1 ? 'dia' : 'dias' }}
        </span>
      </div>

      <p v-if="movel.problema" class="mt-1 text-xs text-red-700" data-testid="problema">Problema: {{ movel.problema }}</p>
    </div>

    <div class="flex shrink-0 items-center gap-2">
      <!-- D5: um clique até o pedido (ou o recebimento) no Compras -->
      <button
        v-if="verNoCompras"
        type="button"
        class="inline-flex items-center gap-1 text-xs font-medium text-brand-primary hover:underline cursor-pointer"
        data-testid="ver-no-compras"
        @click="emit('verNoCompras')"
      >
        Ver no Compras <ExternalLink :size="12" />
      </button>

      <div v-if="editavel && opcoes.length" ref="menuRef" class="relative">
        <BaseButton
          variant="secondary"
          size="sm"
          aria-haspopup="menu"
          :aria-expanded="menuAberto"
          aria-label="Mais ações"
          :data-testid="`menu-${movel.movel_id}`"
          @click="menuAberto = !menuAberto"
        >
          <MoreHorizontal :size="16" />
        </BaseButton>
        <div v-if="menuAberto" role="menu" class="absolute right-0 z-30 mt-1 w-48 overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-lg">
          <button
            v-for="opcao in opcoes"
            :key="opcao.id"
            type="button"
            role="menuitem"
            class="block w-full px-3 py-2 text-left text-sm text-zinc-700 hover:bg-zinc-50 cursor-pointer"
            :data-testid="`opcao-${opcao.id}`"
            @click="escolher(opcao.id)"
          >
            {{ opcao.texto }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
