<script setup lang="ts">
/**
 * @component NfseSubstituirModal
 * @description Substituir uma NFS-e autorizada (O4 de
 * docs/nfe-cfop-e-notas-da-os-plano.md). A NFS-e Nacional não tem carta de
 * correção: a nota errada se substitui por uma nova, que sai com os dados
 * ATUAIS da OS e do cadastro, o motivo (tabela da NFS-e Nacional) e o porquê.
 * A antiga só é cancelada quando a nova é autorizada.
 */
import { computed, ref, watch } from 'vue';
import { RefreshCcw } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';
import { useToast } from '@/shared/composables/useToast';

import { useNfseSubstituirMutation } from '../../composables/useNfse';
import { ehNotaRepetida, mensagemNotaRepetida } from '../../utils/notaRepetida';

const props = defineProps<{ documento: { id: number; numero: number | null } | null }>();
const emit = defineEmits<{ close: []; substituida: [novoId: number] }>();

/** Os códigos do `cMotivo` da DPS (campos da Focus). */
const MOTIVOS = [
  { value: '99', label: '99 – Outros (erro de valor, descrição, tomador…)' },
  { value: '05', label: '05 – Rejeição da nota pelo tomador' },
  { value: '01', label: '01 – Desenquadramento do Simples Nacional' },
  { value: '02', label: '02 – Enquadramento no Simples Nacional' },
  { value: '03', label: '03 – Inclusão retroativa de imunidade/isenção' },
  { value: '04', label: '04 – Exclusão retroativa de imunidade/isenção' },
];
const MIN_CHARS = 15;
const MAX_CHARS = 255;

const motivo = ref<string | number>('99');
const descricao = ref('');
const toast = useToast();
const substituirMutation = useNfseSubstituirMutation();

watch(() => props.documento, () => {
  motivo.value = '99';
  descricao.value = '';
});

const valida = computed(() => {
  const n = descricao.value.trim().length;
  return !!motivo.value && n >= MIN_CHARS && n <= MAX_CHARS;
});

async function substituir(confirmar = false) {
  if (!props.documento || !valida.value) return;
  try {
    const r = await substituirMutation.mutateAsync({
      id: props.documento.id,
      motivo: String(motivo.value),
      descricao: descricao.value.trim(),
      confirmar,
    });
    emit('substituida', r.documento_id);
  } catch (e) {
    if (ehNotaRepetida(e)) {
      toast.warning('Nota igual a outra emitida há pouco', mensagemNotaRepetida(e), {
        action: { label: 'Substituir mesmo assim', onClick: () => substituir(true) },
      });
    }
  }
}
</script>

<template>
  <BaseModal :is-open="!!documento" title="Substituir NFS-e" size="md" @close="emit('close')">
    <div class="space-y-4" data-substituir-nfse>
      <p class="text-sm text-zinc-600">
        Sai uma NFS-e nova no lugar da nº <strong>{{ documento?.numero ?? '—' }}</strong>, com os dados
        <strong>atuais</strong> da OS e do cadastro — corrija antes o que estava errado.
        A nota antiga é cancelada quando a nova for autorizada.
      </p>
      <BaseSelect v-model="motivo" :options="MOTIVOS" label="Motivo" />
      <BaseTextarea
        v-model="descricao"
        label="O que mudou"
        :rows="3"
        placeholder="Ex: valor do serviço lançado errado na OS"
        required
      />
      <p class="text-xs" :class="valida ? 'text-zinc-400' : 'text-amber-600'">
        {{ descricao.trim().length }}/{{ MIN_CHARS }} caracteres no mínimo (até {{ MAX_CHARS }})
      </p>
    </div>

    <template #footer>
      <div class="flex items-center justify-end gap-3 w-full">
        <BaseButton type="button" variant="secondary" @click="emit('close')">Voltar</BaseButton>
        <BaseButton
          type="button"
          :disabled="!valida || substituirMutation.isPending.value"
          :is-loading="substituirMutation.isPending.value"
          data-testid="confirmar-substituicao"
          @click="substituir()"
        >
          <RefreshCcw :size="16" class="mr-1.5" />
          Substituir NFS-e
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
