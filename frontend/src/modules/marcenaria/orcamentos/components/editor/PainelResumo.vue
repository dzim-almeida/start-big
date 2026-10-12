<script setup lang="ts">
/**
 * @component PainelResumo
 * @description O resumo da proposta, no topo da coluna lateral (Spec 06B §6.2;
 * redesign 10/2026): o TOTAL uma vez só, em destaque; móveis, instalação e
 * desconto; a divisão sinal × saldo numa barra; e, embaixo (slot `acoes`), o
 * que se faz com o orçamento. Todos os números vêm prontos da API (C8).
 *
 * Aprovado (08B D14): quando o aprovado difere do proposto (móveis recusados,
 * desconto renegociado), mostra a tabela "Proposto × Aprovado": o vendedor vê
 * o que perdeu na negociação.
 */
import { computed } from 'vue';

import { formatDataPura } from '@/shared/utils/date.utils';
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
/** O que vale: o aprovado, quando existe; senão o proposto. */
const vigente = computed(() => aprovado.value ?? calculo.value ?? null);

/** "5%" no modo percentual; no modo valor, o % equivalente com "≈" (D18). */
function rotuloAjuste(tipo: 'desconto' | 'sinal'): string {
  const d = detalhe.value;
  if (!d) return '';
  const ajuste = d[tipo];
  const efetivo = tipo === 'desconto' ? d.calculo.desconto_bp_efetivo : d.calculo.sinal_bp_efetivo;
  return ajuste.modo === 'PERCENTUAL' ? formatarBp(ajuste.valor) : `≈ ${formatarBp(efetivo)}`;
}

/** As linhas da tabela "Proposto × Aprovado". */
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

/** Móveis = bruto sem a instalação (a API manda o preço da instalação à parte). */
const instalacaoCentavos = computed(() => vigente.value?.instalacao?.preco_centavos ?? 0);
const moveisCentavos = computed(() => (vigente.value ? vigente.value.bruto_centavos - instalacaoCentavos.value : 0));

/** "4 móveis · instalação incluída · válida até 25/10/2026". */
const subtitulo = computed(() => {
  const d = detalhe.value;
  if (!d) return '';
  const qtd = d.ambientes.reduce<number>((soma, a) => soma + a.moveis.length, 0);
  const partes = [`${qtd} ${qtd === 1 ? 'móvel' : 'móveis'}`];
  if (instalacaoCentavos.value) partes.push('instalação incluída');
  if (d.datas.validade) partes.push(`válida até ${formatDataPura(d.datas.validade.slice(0, 10))}`);
  return partes.join(' · ');
});

/** Parte do total que é sinal (a barra azul). */
const fracaoSinal = computed(() => {
  const v = vigente.value;
  return v && v.total_centavos > 0 ? Math.min(100, Math.round((v.sinal_centavos / v.total_centavos) * 100)) : 0;
});
</script>

<template>
  <section class="rounded-2xl border border-zinc-200 bg-white px-6 py-5" aria-labelledby="titulo-resumo" data-testid="painel-resumo">
    <h2 id="titulo-resumo" class="text-xs font-medium text-zinc-500">{{ duasColunas ? 'Total aprovado' : 'Total da proposta' }}</h2>

    <template v-if="calculo && vigente">
      <p class="mt-1 text-3xl font-bold leading-tight tracking-tight tabular-nums text-zinc-900" data-testid="total">
        {{ formatCurrency(vigente.total_centavos) }}
      </p>
      <p v-if="subtitulo" class="text-xs text-zinc-500">{{ subtitulo }}</p>

      <!-- Aprovado diferente do proposto: as duas colunas (D14) -->
      <table v-if="duasColunas" class="mt-4 w-full border-t border-zinc-100 text-sm">
        <thead>
          <tr class="text-xs text-zinc-500">
            <th class="pt-3 text-left font-medium"><span class="sr-only">Valor</span></th>
            <th class="pt-3 text-right font-medium">Proposto</th>
            <th class="pt-3 text-right font-medium">Aprovado</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="linha in linhas"
            :key="linha.chave"
            :class="linha.forte ? 'border-t border-zinc-100 font-semibold' : ''"
            :data-testid="`resumo-${linha.chave}`"
          >
            <td class="py-1 text-zinc-600" :class="linha.forte ? 'text-zinc-800' : ''">{{ linha.rotulo }}</td>
            <td class="py-1 text-right tabular-nums text-zinc-500">{{ linha.menos ? '− ' : '' }}{{ formatCurrency(linha.proposto) }}</td>
            <td class="py-1 text-right tabular-nums text-zinc-900">{{ linha.menos ? '− ' : '' }}{{ formatCurrency(linha.aprovado ?? 0) }}</td>
          </tr>
        </tbody>
      </table>

      <template v-else>
        <dl class="mt-4 flex flex-col gap-1.5 border-t border-zinc-100 pt-3 text-sm">
          <div class="flex justify-between gap-3" data-testid="resumo-moveis">
            <dt class="text-zinc-600">Móveis</dt>
            <dd class="tabular-nums text-zinc-800">{{ formatCurrency(moveisCentavos) }}</dd>
          </div>
          <div v-if="instalacaoCentavos" class="flex justify-between gap-3" data-testid="resumo-instalacao">
            <dt class="text-zinc-600">Instalação</dt>
            <dd class="tabular-nums text-zinc-800">{{ formatCurrency(instalacaoCentavos) }}</dd>
          </div>
          <div v-if="vigente.desconto_centavos" class="flex justify-between gap-3" data-testid="resumo-desconto">
            <dt class="text-zinc-600">Desconto {{ rotuloAjuste('desconto') }}</dt>
            <dd class="tabular-nums text-zinc-800">− {{ formatCurrency(vigente.desconto_centavos) }}</dd>
          </div>
        </dl>

        <!-- Sinal × saldo: a divisão do pagamento num olhar -->
        <div v-if="vigente.sinal_centavos" class="mt-4" data-testid="resumo-sinal">
          <div class="flex h-2 overflow-hidden rounded-full bg-brand-primary-light" aria-hidden="true">
            <span class="bg-brand-primary" :style="{ width: `${fracaoSinal}%` }" />
          </div>
          <div class="mt-2 flex justify-between gap-3 text-xs">
            <span class="text-zinc-600">
              <span class="mr-1.5 inline-block h-2 w-2 rounded-full bg-brand-primary" aria-hidden="true" />Sinal {{ rotuloAjuste('sinal') }}
              <strong class="tabular-nums text-zinc-900">{{ formatCurrency(vigente.sinal_centavos) }}</strong>
            </span>
            <span class="text-zinc-500">Saldo <strong class="tabular-nums text-zinc-800">{{ formatCurrency(vigente.saldo_centavos) }}</strong></span>
          </div>
        </div>
      </template>
    </template>
    <p v-else class="mt-2 text-sm text-zinc-500">Os valores aparecem quando o primeiro móvel for incluído.</p>

    <!-- O que se faz com o orçamento (EditorAcoes) -->
    <div v-if="$slots.acoes" class="mt-5">
      <slot name="acoes" />
    </div>
  </section>
</template>
