<script setup lang="ts">
/**
 * @component FaltasDaOS
 * @description O que o estoque não cobre nesta OS (Spec 10B D18-D20): produto,
 * quanto falta, localização e o fornecedor principal (para ligar), com
 * "Imprimir" (A4) e, com o módulo Compras, "Ver nas Necessidades".
 *
 * A lista entre OS e o pedido de compra são do Compras (E5a); aqui é só a OS.
 */
import { computed, nextTick, ref, toRef } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import { Printer } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import { aguardarImagensDaImpressao, imprimirComPagina } from '@/shared/utils/print.utils';

import { getFaltas } from '../services/separacao.service';
import { quantidadeComUnidade } from '../utils/quantidades';
import FaltasPrint from './FaltasPrint.vue';

const props = defineProps<{
  isOpen: boolean;
  numeroOs: string;
  /** O módulo Compras está contratado e a pessoa pode ver (D19). */
  temCompras: boolean;
}>();

const emit = defineEmits<{ close: []; verNecessidades: [] }>();

const numeroOs = toRef(props, 'numeroOs');
const { data: faltas, isLoading, isError } = useQuery({
  queryKey: computed(() => ['marcenaria', 'separacao', numeroOs.value, 'faltas']),
  queryFn: () => getFaltas(numeroOs.value),
  enabled: computed(() => props.isOpen),            // só com o painel aberto
  staleTime: 0,                                       // abrir de novo = conta de agora
});

// --- Imprimir (o documento só existe enquanto imprime) ----------------------------
const imprimindo = ref(false);
async function imprimir() {
  if (!faltas.value || imprimindo.value) return;
  imprimindo.value = true;
  await nextTick();                                   // o documento entra no DOM
  await aguardarImagensDaImpressao();                 // a logo precisa ter carregado
  const terminar = () => {
    imprimindo.value = false;
    window.removeEventListener('afterprint', terminar);
  };
  window.addEventListener('afterprint', terminar);
  imprimirComPagina('A4', { folha: 'A4' });
}
</script>

<template>
  <BaseModal :is-open="isOpen" :title="`Faltas da ${numeroOs}`" :subtitle="faltas?.cliente ?? undefined" size="lg" overlay @close="emit('close')">
    <p v-if="isLoading" class="text-sm text-zinc-400">Calculando as faltas…</p>
    <p v-else-if="isError" class="text-sm text-red-600">Não foi possível calcular as faltas agora.</p>
    <p v-else-if="faltas && !faltas.itens.length" class="text-sm text-emerald-700" data-testid="sem-faltas">
      Nada a comprar: o estoque cobre esta OS.
    </p>
    <ul v-else-if="faltas" class="divide-y divide-zinc-100" data-testid="lista-faltas">
      <li v-for="item in faltas.itens" :key="item.produto_id" class="flex flex-wrap items-center gap-x-4 gap-y-1 py-2 text-sm">
        <span class="min-w-48 flex-1 font-medium text-zinc-800">{{ item.descricao }}</span>
        <span class="font-bold tabular-nums text-amber-700">faltam {{ quantidadeComUnidade(item.faltam_milesimos, item.unidade) }}</span>
        <span class="text-xs text-zinc-500">{{ item.localizacao || 'Sem localização' }}</span>
        <span class="w-full text-xs text-zinc-600 sm:w-auto">
          <template v-if="item.fornecedor">
            {{ item.fornecedor.nome }}<template v-if="item.fornecedor.telefone"> · {{ item.fornecedor.telefone }}</template>
          </template>
          <template v-else>Sem fornecedor principal no cadastro</template>
        </span>
      </li>
    </ul>

    <template #footer>
      <div class="flex flex-wrap justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">Fechar</BaseButton>
        <!-- D19: a lista entre OS e o pedido são do Compras; sem o módulo, nada aqui. -->
        <BaseButton v-if="temCompras" variant="secondary" data-testid="ver-necessidades" @click="emit('verNecessidades')">
          Ver nas Necessidades
        </BaseButton>
        <BaseButton :disabled="!faltas?.itens.length" :is-loading="imprimindo" data-testid="imprimir-faltas" @click="imprimir">
          <Printer :size="14" class="mr-1" /> Imprimir
        </BaseButton>
      </div>
    </template>
  </BaseModal>
  <FaltasPrint v-if="imprimindo && faltas" :faltas="faltas" />
</template>
