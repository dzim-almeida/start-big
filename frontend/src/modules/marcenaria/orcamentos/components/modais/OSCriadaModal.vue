<script setup lang="ts">
/**
 * @component OSCriadaModal
 * @description Confirmação depois de aprovar (Spec 08B D7): diz qual OS
 * nasceu e oferece os três próximos passos reais.
 */
import { computed } from 'vue';
import { CheckCircle2 } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';

import type { OrcamentoDetalhe } from '../../schemas/orcamentoDetalhe.schema';

const props = defineProps<{ isOpen: boolean; detalhe: OrcamentoDetalhe | undefined }>();
const emit = defineEmits<{ close: []; abrirOs: []; imprimirAprovada: [] }>();

/** "OS OS-2026-000512 criada com 3 móveis e a instalação." */
const frase = computed(() => {
  const d = props.detalhe;
  if (!d?.os) return '';
  const qtd = d.ambientes.reduce((soma, a) => soma + a.moveis.filter((m) => m.aprovado === true).length, 0);
  const moveis = qtd === 1 ? '1 móvel' : `${qtd} móveis`;
  const instalacao = d.aprovacao?.instalacao_aprovada ? ' e a instalação' : '';
  return `OS ${d.os.numero_os} criada com ${moveis}${instalacao}.`;
});
</script>

<template>
  <BaseModal :is-open="isOpen" title="Orçamento aprovado" size="sm" @close="emit('close')">
    <p class="flex items-start gap-2 text-sm text-zinc-700" data-testid="frase-os-criada">
      <CheckCircle2 :size="18" class="mt-0.5 shrink-0 text-emerald-600" /> {{ frase }}
    </p>
    <template #footer>
      <div class="flex flex-wrap justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">Ficar no orçamento</BaseButton>
        <BaseButton variant="secondary" data-testid="imprimir-aprovada" @click="emit('imprimirAprovada')">Imprimir proposta aprovada</BaseButton>
        <BaseButton variant="primary" data-testid="abrir-os" @click="emit('abrirOs')">Abrir OS</BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
