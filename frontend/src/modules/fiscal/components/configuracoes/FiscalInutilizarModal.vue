<script setup lang="ts">
/**
 * Pede à SEFAZ a inutilização de uma faixa de numeração.
 *
 * Inutilização é evento que a SEFAZ REGISTRA E NÃO DESFAZ. Por isso o modal
 * mostra a faixa por extenso, exige a justificativa que a SEFAZ exige (15
 * caracteres) e nomeia o botão pelo efeito, não por "confirmar".
 */
import { computed, ref, watch } from 'vue';
import { Ban, X } from 'lucide-vue-next';

import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import { useFiscalInutilizarMutation } from '../../composables/useFiscalInutilizarMutation';
import type { GapNumeracao } from '../../types/fiscal.types';

const props = defineProps<{
  isOpen: boolean;
  gap: GapNumeracao | null;
}>();
const emit = defineEmits<{ (e: 'update:isOpen', value: boolean): void }>();

const MINIMO_JUSTIFICATIVA = 15;

const justificativa = ref('');
const inutilizar = useFiscalInutilizarMutation();

const faixaTexto = computed(() => {
  const g = props.gap;
  if (!g) return '';
  return g.numero_inicial === g.numero_final
    ? `nº ${g.numero_inicial}`
    : `nº ${g.numero_inicial} a ${g.numero_final}`;
});

const faltam = computed(() => Math.max(0, MINIMO_JUSTIFICATIVA - justificativa.value.trim().length));
const podeEnviar = computed(() => !!props.gap && faltam.value === 0 && !inutilizar.isPending.value);

// Abrir com outra faixa não pode herdar a justificativa da anterior.
watch(() => props.isOpen, (aberto) => { if (aberto) justificativa.value = ''; });

const fechar = () => emit('update:isOpen', false);

async function submeter() {
  if (!props.gap || !podeEnviar.value) return;
  await inutilizar.mutateAsync({
    serie: props.gap.serie,
    numero_inicial: props.gap.numero_inicial,
    numero_final: props.gap.numero_final,
    justificativa: justificativa.value.trim(),
  });
  fechar();
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0"
      leave-active-class="transition ease-in duration-150"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen && gap"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
        @click.self="fechar"
      >
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden flex flex-col">
          <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-200">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center text-amber-600">
                <LucideIcon :icon="Ban" />
              </div>
              <div>
                <h2 class="text-lg font-bold text-zinc-900">Inutilizar numeração</h2>
                <p class="text-xs text-zinc-500">Série {{ gap.serie }} · {{ faixaTexto }}</p>
              </div>
            </div>
            <button
              type="button"
              class="p-2 text-zinc-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
              @click="fechar"
            >
              <LucideIcon :icon="X" class="w-5 h-5" />
            </button>
          </div>

          <div class="px-6 py-5 flex flex-col gap-4">
            <div class="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
              A SEFAZ <strong>registra e não desfaz</strong> uma inutilização. Depois de
              homologada, {{ gap.quantidade === 1 ? 'este número' : 'estes números' }}
              nunca mais {{ gap.quantidade === 1 ? 'poderá' : 'poderão' }} ser
              {{ gap.quantidade === 1 ? 'usado' : 'usados' }} numa nota.
            </div>

            <label class="flex flex-col gap-1.5">
              <span class="text-sm font-medium text-zinc-700">Justificativa declarada à SEFAZ</span>
              <textarea
                v-model="justificativa"
                rows="3"
                maxlength="255"
                class="w-full rounded-xl border border-zinc-200 px-3 py-2 text-sm text-zinc-800 focus:border-brand-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/20"
                placeholder="Ex.: Números reservados por falha de transmissão e não utilizados"
              />
              <span class="text-xs" :class="faltam > 0 ? 'text-zinc-400' : 'text-emerald-600'">
                {{ faltam > 0 ? `Faltam ${faltam} caracteres (mínimo ${MINIMO_JUSTIFICATIVA})` : 'Justificativa válida' }}
              </span>
            </label>
          </div>

          <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-zinc-200 bg-zinc-50">
            <BaseButton variant="secondary" @click="fechar">Cancelar</BaseButton>
            <BaseButton
              variant="primary"
              :disabled="!podeEnviar"
              :is-loading="inutilizar.isPending.value"
              @click="submeter"
            >
              Inutilizar na SEFAZ
            </BaseButton>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
