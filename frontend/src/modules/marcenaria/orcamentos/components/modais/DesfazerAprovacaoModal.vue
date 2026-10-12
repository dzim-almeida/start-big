<script setup lang="ts">
/**
 * @component DesfazerAprovacaoModal
 * @description Desfazer a aprovação (Spec 08B D16; SPEC-00 O8, O8a).
 *
 * É uma ação de perigo: cancela a OS e devolve o orçamento para Enviado.
 * Motivo obrigatório. Com sinal recebido, pergunta o destino do dinheiro:
 * vira crédito do cliente (usado na próxima aprovação) ou foi devolvido.
 * O PIN do gerente, quando a loja exige, é pedido pelo editor (D17).
 */
import { computed, ref, watch } from 'vue';
import { AlertTriangle } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';
import { formatCurrency } from '@/shared/utils/finance';

import type { DesfazerEntrada } from '../../schemas/aprovacao.schema';

const props = defineProps<{
  isOpen: boolean;
  numeroOs: string;
  /** Sinal que já entrou na OS (adiantamento). Zero: a pergunta do destino some. */
  sinalRecebidoCentavos: number;
  gravando: boolean;
}>();

const emit = defineEmits<{ close: []; confirmar: [entrada: DesfazerEntrada] }>();

const LIMITE_MOTIVO = 300;
const motivo = ref<string | null>('');
const destino = ref<DesfazerEntrada['destino_sinal']>('CREDITO');

// Cada abertura começa limpa.
watch(() => props.isOpen, (aberto) => {
  if (!aberto) return;
  motivo.value = '';
  destino.value = 'CREDITO';
}, { immediate: true });

const texto = computed(() => (motivo.value ?? '').trim());
const erroMotivo = computed(() => (texto.value.length > LIMITE_MOTIVO ? `O motivo pode ter até ${LIMITE_MOTIVO} caracteres.` : ''));
const podeConfirmar = computed(() => !!texto.value && !erroMotivo.value && !props.gravando);
</script>

<template>
  <BaseModal :is-open="isOpen" title="Desfazer a aprovação" size="md" @close="emit('close')">
    <p class="mb-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800" data-testid="aviso-desfazer">
      <AlertTriangle :size="16" class="mt-0.5 shrink-0" />
      <span>Desfazer a aprovação vai <strong>cancelar a OS {{ numeroOs }}</strong> e devolver o orçamento para Enviado.</span>
    </p>

    <BaseTextarea v-model="motivo" label="Motivo" required :rows="3" :error="erroMotivo" placeholder="Ex.: aprovado por engano; o cliente mudou de ideia" />

    <!-- O8a: o sinal que já entrou precisa de um destino -->
    <fieldset v-if="sinalRecebidoCentavos > 0" class="mt-4 text-sm" data-testid="destino-sinal">
      <legend class="mb-2 text-zinc-700">O que fazer com o sinal de {{ formatCurrency(sinalRecebidoCentavos) }}?</legend>
      <label class="flex items-center gap-2"><input v-model="destino" type="radio" value="CREDITO" class="accent-brand-primary" /> Vira crédito do cliente (usado na próxima aprovação)</label>
      <label class="mt-1 flex items-center gap-2"><input v-model="destino" type="radio" value="DEVOLVIDO" class="accent-brand-primary" /> Foi devolvido ao cliente</label>
    </fieldset>

    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">Voltar</BaseButton>
        <BaseButton
          variant="danger"
          :disabled="!podeConfirmar"
          :is-loading="gravando"
          data-testid="confirmar-desfazer"
          @click="emit('confirmar', { motivo: texto, destino_sinal: destino })"
        >
          Desfazer e cancelar a OS
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
