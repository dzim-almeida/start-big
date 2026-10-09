<script setup lang="ts">
/**
 * @component PainelResumo
 * @description Resumo de valores da coluna lateral (Spec 06B §6.2): bruto,
 * desconto, total, sinal, saldo e instalação. Todos os números vêm prontos da
 * API (C8); aqui só se formata.
 */
import { computed } from 'vue';

import { formatCurrency } from '@/shared/utils/finance';

import { useEditor } from '../../composables/useEditorContexto';
import { formatarBp } from '../../utils/conversoes';

const { detalhe } = useEditor();

const calculo = computed(() => detalhe.value?.calculo);

/** "5%" no modo percentual; no modo valor, o % equivalente com "≈" (D18). */
function rotuloAjuste(tipo: 'desconto' | 'sinal'): string {
  const d = detalhe.value;
  if (!d) return '';
  const ajuste = d[tipo];
  const efetivo = tipo === 'desconto' ? d.calculo.desconto_bp_efetivo : d.calculo.sinal_bp_efetivo;
  return ajuste.modo === 'PERCENTUAL' ? formatarBp(ajuste.valor) : `≈ ${formatarBp(efetivo)}`;
}
</script>

<template>
  <section class="rounded-2xl border border-zinc-200 bg-white p-5" aria-labelledby="titulo-resumo" data-testid="painel-resumo">
    <h2 id="titulo-resumo" class="mb-3 text-sm font-bold text-zinc-800">Resumo</h2>

    <dl v-if="calculo" class="flex flex-col gap-1.5 text-sm">
      <div class="flex justify-between">
        <dt class="text-zinc-500">Bruto</dt>
        <dd class="tabular-nums text-zinc-800">{{ formatCurrency(calculo.bruto_centavos) }}</dd>
      </div>
      <div v-if="calculo.desconto_centavos" class="flex justify-between">
        <dt class="text-zinc-500">Desconto <span class="text-xs">{{ rotuloAjuste('desconto') }}</span></dt>
        <dd class="tabular-nums text-zinc-800">− {{ formatCurrency(calculo.desconto_centavos) }}</dd>
      </div>
      <div class="flex justify-between border-t border-zinc-100 pt-1.5 font-semibold">
        <dt class="text-zinc-700">Total</dt>
        <dd class="tabular-nums text-zinc-900" data-testid="total">{{ formatCurrency(calculo.total_centavos) }}</dd>
      </div>
      <div v-if="calculo.sinal_centavos" class="flex justify-between">
        <dt class="text-zinc-500">Sinal <span class="text-xs">{{ rotuloAjuste('sinal') }}</span></dt>
        <dd class="tabular-nums text-zinc-800">{{ formatCurrency(calculo.sinal_centavos) }}</dd>
      </div>
      <div v-if="calculo.sinal_centavos" class="flex justify-between">
        <dt class="text-zinc-500">Saldo</dt>
        <dd class="tabular-nums text-zinc-800">{{ formatCurrency(calculo.saldo_centavos) }}</dd>
      </div>
      <p v-if="calculo.instalacao" class="mt-1 text-xs text-zinc-500">
        Instalação incluída ({{ formatCurrency(calculo.instalacao.preco_centavos) }})
      </p>
    </dl>
    <p v-else class="text-sm text-zinc-400">Os valores aparecem quando o primeiro móvel for incluído.</p>
  </section>
</template>
