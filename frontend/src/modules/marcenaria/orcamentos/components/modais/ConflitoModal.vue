<script setup lang="ts">
/**
 * @component ConflitoModal
 * @description Conflito de revisão (Spec 06B D12): outro computador salvou
 * este orçamento antes. A fila PARA e este modal não fecha sozinho: lista o
 * que NÃO foi salvo ("Desconto, Observações da proposta") e oferece um botão
 * só, "Recarregar orçamento". A trava avisa, mas não junta (06A §8).
 */
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';

defineProps<{
  isOpen: boolean;
  /** Rótulos dos campos que ficaram sem salvar. */
  camposPerdidos: string[];
  recarregando: boolean;
}>();

const emit = defineEmits<{ recarregar: [] }>();
</script>

<template>
  <!-- Sem o "X" do cabeçalho: o único caminho é recarregar. -->
  <BaseModal :is-open="isOpen" title="Orçamento alterado em outro computador" size="sm" overlay @close="() => undefined">
    <template #header>
      <div class="border-b border-zinc-100 p-6">
        <h2 class="text-lg font-bold text-zinc-900">Orçamento alterado em outro computador</h2>
      </div>
    </template>

    <p class="text-sm text-zinc-700">Este orçamento foi alterado em outro computador.</p>
    <div v-if="camposPerdidos.length" class="mt-3" data-testid="campos-perdidos">
      <p class="text-sm text-zinc-600">Estas alterações não foram salvas e precisarão ser refeitas:</p>
      <p class="mt-1 text-sm font-semibold text-zinc-800">{{ camposPerdidos.join(', ') }}</p>
    </div>

    <template #footer>
      <div class="flex justify-end">
        <BaseButton variant="primary" :is-loading="recarregando" data-testid="recarregar-orcamento" @click="emit('recarregar')">
          Recarregar orçamento
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
