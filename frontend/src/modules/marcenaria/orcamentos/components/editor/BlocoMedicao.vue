<script setup lang="ts">
/**
 * @component BlocoMedicao
 * @description Medição do ambiente (Spec 06B D44; SPEC-00 O1): o texto
 * "Medidas e observações da medição" (salva sozinho) e os anexos.
 *
 * Na tela "novo" ainda não há orçamento para guardar arquivo: os anexos
 * aparecem depois do primeiro salvamento.
 */
import { computed } from 'vue';

import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';

import { useEditor } from '../../composables/useEditorContexto';
import AnexosOrcamento from './AnexosOrcamento.vue';

const { form, id, editavel } = useEditor();

/** Textarea devolve '' quando vazio; o backend guarda null. */
const observacoes = computed({
  get: () => form.medicao_observacoes ?? '',
  set: (texto: string | null) => { form.medicao_observacoes = texto && texto.trim() ? texto : null; },
});
</script>

<template>
  <div class="flex flex-col gap-3" aria-labelledby="titulo-medicao">
    <h3 id="titulo-medicao" class="text-sm font-semibold text-zinc-900">Medição</h3>

    <BaseTextarea
      v-model="observacoes"
      label="Medidas e observações"
      placeholder="Ex.: parede da pia 3,20 m; tomada a 1,10 m do piso; janela à esquerda."
      :rows="3"
      :disabled="!editavel"
    />

    <div>
      <p class="mb-1.5 text-xs font-medium text-zinc-600">Fotos e arquivos</p>
      <AnexosOrcamento v-if="id != null" />
      <p v-else class="text-xs text-zinc-500">
        Os anexos ficam disponíveis assim que o orçamento for criado (escolha o cliente ou dê um nome ao projeto).
      </p>
    </div>
  </div>
</template>
