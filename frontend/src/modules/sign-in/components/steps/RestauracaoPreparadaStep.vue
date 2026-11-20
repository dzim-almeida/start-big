<script setup lang="ts">
/**
 * @component RestauracaoPreparadaStep
 * @description "Restauração preparada" (LIC-03 §6.2, quadro 2).
 *
 * O backup já foi baixado e conferido; a troca do banco acontece quando o
 * servidor do StartBig liga de novo. Esta tela não tem "Voltar" nem "Sair":
 * sair no meio deixaria a restauração pela metade (spec §11).
 *
 * Divergência do quadro 2: não há botão "Reiniciar o sistema". O app não tem
 * comando que pare e religue o serviço do StartBig, então a tela orienta
 * reiniciar o computador (registrado na nota de revisão da spec).
 */

import { computed } from 'vue';
import { CheckCircle2, Info } from 'lucide-vue-next';
import { useSignIn } from '../../composables/useSignIn';

const { restauracaoPreparada } = useSignIn();

/** "17/11/2026" a partir do ciclo ISO. */
const semana = computed(() => {
  const [ano, mes, dia] = (restauracaoPreparada.value?.ciclo ?? '').split('-');
  return ano && mes && dia ? `${dia}/${mes}/${ano}` : '';
});
</script>

<template>
  <div class="flex flex-col items-center gap-4">
    <CheckCircle2 :size="48" class="text-emerald-500" aria-hidden="true" />
    <div class="flex flex-col items-center gap-1.5 text-center">
      <h2 class="text-2xl font-bold text-zinc-900">Restauração preparada</h2>
      <p class="text-sm text-zinc-600 leading-relaxed">
        O backup da semana de {{ semana }} foi baixado e conferido. Reinicie o computador para aplicá-lo.
      </p>
    </div>

    <div class="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-3.5 text-sm text-zinc-700">
      <p class="font-semibold mb-2">O que acontece agora</p>
      <ol class="list-decimal pl-5 flex flex-col gap-1.5">
        <li>Reinicie o computador.</li>
        <li>Na abertura, os dados do backup substituem o banco vazio deste computador.</li>
        <li>Depois, entre com o seu usuário do sistema, como sempre.</li>
      </ol>
    </div>

    <div class="w-full bg-blue-50 border border-blue-100 rounded-lg px-3 py-2.5 flex items-start gap-2" role="status">
      <Info :size="16" class="text-brand-primary shrink-0 mt-0.5" aria-hidden="true" />
      <p class="text-xs text-brand-primary leading-relaxed">
        Não use o sistema antes de reiniciar: a restauração só termina na próxima abertura.
      </p>
    </div>
  </div>
</template>
