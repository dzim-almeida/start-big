<script setup lang="ts">
/**
 * @component PainelResumo
 * @description Resumo de valores da coluna lateral (Spec 06B §6.2): bruto,
 * desconto, total, sinal, saldo e instalação. Todos os números vêm prontos da
 * API (C8); aqui só se formata.
 *
 * Aprovado (08B D14): quando o aprovado difere do proposto (móveis recusados,
 * desconto renegociado), mostra as duas colunas, "Proposto" e "Aprovado":
 * o vendedor vê o que perdeu na negociação.
 */
import { computed } from 'vue';

import { formatCurrency } from '@/shared/utils/finance';

import { useEditor } from '../../composables/useEditorContexto';
import { formatarBp } from '../../utils/conversoes';

const { detalhe } = useEditor();

const calculo = computed(() => detalhe.value?.calculo);
/** O cálculo SÓ do que foi aprovado (08A §6.4); null fora de APROVADO. */
const aprovado = computed(() => detalhe.value?.aprovacao?.calculo ?? null);
/** Duas colunas só quando há diferença (iguais, uma basta). */
const duasColunas = computed(() =>
  !!aprovado.value && !!calculo.value
  && (aprovado.value.total_centavos !== calculo.value.total_centavos || aprovado.value.bruto_centavos !== calculo.value.bruto_centavos),
);

/** "5%" no modo percentual; no modo valor, o % equivalente com "≈" (D18). */
function rotuloAjuste(tipo: 'desconto' | 'sinal'): string {
  const d = detalhe.value;
  if (!d) return '';
  const ajuste = d[tipo];
  const efetivo = tipo === 'desconto' ? d.calculo.desconto_bp_efetivo : d.calculo.sinal_bp_efetivo;
  return ajuste.modo === 'PERCENTUAL' ? formatarBp(ajuste.valor) : `≈ ${formatarBp(efetivo)}`;
}

/** As linhas do resumo: rótulo e os valores proposto/aprovado. */
const linhas = computed(() => {
  const p = calculo.value;
  if (!p) return [];
  const a = aprovado.value;
  return [
    { chave: 'bruto', rotulo: 'Bruto', proposto: p.bruto_centavos, aprovado: a?.bruto_centavos, menos: false, forte: false },
    { chave: 'desconto', rotulo: `Desconto ${rotuloAjuste('desconto')}`, proposto: p.desconto_centavos, aprovado: a?.desconto_centavos, menos: true, forte: false },
    { chave: 'total', rotulo: 'Total', proposto: p.total_centavos, aprovado: a?.total_centavos, menos: false, forte: true },
    { chave: 'sinal', rotulo: `Sinal ${rotuloAjuste('sinal')}`, proposto: p.sinal_centavos, aprovado: a?.sinal_centavos, menos: false, forte: false },
    { chave: 'saldo', rotulo: 'Saldo', proposto: p.saldo_centavos, aprovado: a?.saldo_centavos, menos: false, forte: false },
  ].filter((linha) => linha.chave === 'bruto' || linha.chave === 'total' || linha.proposto || linha.aprovado);
});
</script>

<template>
  <section class="rounded-2xl border border-zinc-200 bg-white p-5" aria-labelledby="titulo-resumo" data-testid="painel-resumo">
    <h2 id="titulo-resumo" class="mb-3 text-sm font-bold text-zinc-800">Resumo</h2>

    <table v-if="calculo" class="w-full text-sm">
      <thead v-if="duasColunas">
        <tr class="text-[11px] uppercase tracking-wide text-zinc-400">
          <th class="text-left font-semibold"><span class="sr-only">Valor</span></th>
          <th class="text-right font-semibold">Proposto</th>
          <th class="text-right font-semibold">Aprovado</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="linha in linhas"
          :key="linha.chave"
          :class="linha.forte ? 'border-t border-zinc-100 font-semibold' : ''"
          :data-testid="`resumo-${linha.chave}`"
        >
          <td class="py-0.5 text-zinc-500" :class="linha.forte ? 'pt-1.5 text-zinc-700' : ''">{{ linha.rotulo }}</td>
          <td class="py-0.5 text-right tabular-nums" :class="[linha.forte ? 'pt-1.5 text-zinc-900' : 'text-zinc-800', duasColunas ? 'text-zinc-400' : '']">
            <span :data-testid="linha.chave === 'total' ? 'total' : undefined">{{ linha.menos ? '− ' : '' }}{{ formatCurrency(linha.proposto) }}</span>
          </td>
          <td v-if="duasColunas" class="py-0.5 text-right tabular-nums text-zinc-900" :class="linha.forte ? 'pt-1.5' : ''">
            {{ linha.menos ? '− ' : '' }}{{ formatCurrency(linha.aprovado ?? 0) }}
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="calculo?.instalacao" class="mt-1 text-xs text-zinc-500">
      Instalação incluída ({{ formatCurrency(calculo.instalacao.preco_centavos) }})
    </p>
    <p v-if="!calculo" class="text-sm text-zinc-400">Os valores aparecem quando o primeiro móvel for incluído.</p>
  </section>
</template>
