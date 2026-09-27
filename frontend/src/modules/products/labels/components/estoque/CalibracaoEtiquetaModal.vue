<script setup lang="ts">
/**
 * @fileoverview Calibração da impressão de etiquetas NESTE terminal.
 *
 * Cada impressora puxa o papel com a sua folga: a mesma folha Pimaco sai
 * alinhada numa HP e 2 mm para baixo numa Epson. Por isso o deslocamento fica
 * no `impressao.store` (localStorage, por máquina), e não no modelo, que é da loja.
 */
import { ref, watch } from 'vue';
import { Ruler } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import { useImpressaoStore } from '@/shared/stores/impressao.store';
import { useToast } from '@/shared/composables/useToast';

const LIMITE_MM = 20;

const props = defineProps<{ isOpen: boolean }>();

const emit = defineEmits<{
  close: [];
  /** Imprime a página de teste com o deslocamento em edição (ainda não salvo). */
  testar: [deslocamentoX: number, deslocamentoY: number];
}>();

const impressaoStore = useImpressaoStore();
const toast = useToast();

const x = ref(0);
const y = ref(0);

watch(
  () => props.isOpen,
  (aberto) => {
    if (!aberto) return;
    x.value = impressaoStore.config.etiqueta_deslocamento_x_mm;
    y.value = impressaoStore.config.etiqueta_deslocamento_y_mm;
  },
);

function limitar(valor: unknown): number {
  const n = Number(valor);
  if (!Number.isFinite(n)) return 0;
  return Math.max(-LIMITE_MM, Math.min(LIMITE_MM, n));
}

function salvar() {
  impressaoStore.salvar({
    ...impressaoStore.config,
    etiqueta_deslocamento_x_mm: limitar(x.value),
    etiqueta_deslocamento_y_mm: limitar(y.value),
  });
  toast.success('Calibração salva', 'Vale só para este computador.');
  emit('close');
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Calibrar impressão"
    subtitle="Ajuste fino deste computador — não muda o modelo da loja"
    size="md"
    @close="emit('close')"
  >
    <div class="space-y-4">
      <ol class="list-decimal pl-5 space-y-1 text-sm text-zinc-600">
        <li>Imprima a página de teste: ela desenha o contorno de cada etiqueta e uma cruz no centro.</li>
        <li>Se o contorno sair deslocado, meça com a régua de quanto e para qual lado.</li>
        <li>Informe abaixo e imprima o teste de novo até o contorno bater com a etiqueta.</li>
      </ol>

      <div class="grid grid-cols-2 gap-4">
        <BaseInput
          v-model.number="x"
          type="number"
          step="0.5"
          :min="-LIMITE_MM"
          :max="LIMITE_MM"
          label="Horizontal (mm)"
          ajuda="Positivo empurra para a direita; negativo, para a esquerda."
        />
        <BaseInput
          v-model.number="y"
          type="number"
          step="0.5"
          :min="-LIMITE_MM"
          :max="LIMITE_MM"
          label="Vertical (mm)"
          ajuda="Positivo empurra para baixo; negativo, para cima."
        />
      </div>

      <p class="text-xs text-zinc-500">
        Etiqueta cortada ou fora de escala costuma ser o <strong>papel no driver</strong> da impressora: ele precisa ter o
        tamanho do rolo (ou a folha certa) e a opção de ajustar à página desligada.
      </p>
    </div>

    <template #footer>
      <div class="flex justify-between gap-2">
        <BaseButton variant="ghost" class="flex items-center gap-2" @click="emit('testar', limitar(x), limitar(y))">
          <Ruler :size="16" />
          Imprimir teste
        </BaseButton>
        <BaseButton @click="salvar">Salvar calibração</BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
