<script setup lang="ts">
/**
 * @component FaturamentoMoveisPanel
 * @description "Notas fiscais dos móveis", no topo da aba Entrega da OS da
 * marcenaria (docs/marcenaria-faturamento-plano.md, F3).
 *
 * - Só aparece com o faturamento dos móveis LIGADO (Configurações › Marcenaria).
 * - Cada móvel aprovado, por ambiente: "Em produção", "Pronto · no estoque"
 *   (dá para marcar) ou "NF-e 123" (já saiu numa nota).
 * - "Marcar este ambiente" escolhe os móveis prontos do ambiente que está sendo
 *   entregue; a nota é sempre pré-visualizada antes de emitir.
 * - Entrega futura (F4): primeiro a nota de simples faturamento (todos os
 *   móveis de uma vez); depois, a cada entrega, a nota de remessa.
 */
import { computed, ref, toRef } from 'vue';
import { useQuery, useQueryClient } from '@tanstack/vue-query';
import axios from 'axios';
import { FileText } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseStatusPill from '@/shared/components/ui/BaseStatusPill/BaseStatusPill.vue';
import { useToast } from '@/shared/composables/useToast';
import { formatCurrency } from '@/shared/utils/finance';
import { mensagemDoErro } from '@/modules/marcenaria/orcamentos/utils/erros';

import type { MovelFaturamento, PreviaNota } from '../schemas/faturamento.schema';
import {
  emitirNota,
  emitirSimplesFaturamento,
  getFaturamento,
  previaDaNota,
  previaDoSimplesFaturamento,
} from '../services/faturamento.service';

const props = defineProps<{ numeroOs: string }>();

const toast = useToast();
const queryClient = useQueryClient();
const numeroOs = toRef(props, 'numeroOs');
const chave = computed(() => ['marcenaria', 'faturamento', numeroOs.value]);

const { data } = useQuery({
  queryKey: chave,
  queryFn: () => getFaturamento(numeroOs.value),
  enabled: computed(() => !!numeroOs.value),
  retry: false,                                          // 404 (OS sem orçamento) não melhora repetindo
});

const ligado = computed(() => !!data.value && data.value.faturamento_modo !== 'DESLIGADO');
const entregaFutura = computed(() => data.value?.faturamento_modo === 'ENTREGA_FUTURA');

/** Os móveis agrupados por ambiente, na ordem da OS. */
const porAmbiente = computed(() => {
  const grupos = new Map<string, MovelFaturamento[]>();
  for (const movel of data.value?.moveis ?? []) {
    grupos.set(movel.ambiente, [...(grupos.get(movel.ambiente) ?? []), movel]);
  }
  return [...grupos.entries()].map(([ambiente, moveis]) => ({ ambiente, moveis }));
});

const marcados = ref<number[]>([]);
function alternar(movel: MovelFaturamento) {
  marcados.value = marcados.value.includes(movel.movel_id)
    ? marcados.value.filter((id) => id !== movel.movel_id)
    : [...marcados.value, movel.movel_id];
}
function marcarAmbiente(moveis: MovelFaturamento[]) {
  const prontos = moveis.filter((m) => m.pode_faturar).map((m) => m.movel_id);
  marcados.value = [...new Set([...marcados.value, ...prontos])];
}

function situacao(movel: MovelFaturamento): { texto: string; tom: 'neutro' | 'sucesso' | 'info' | 'alerta' } {
  if (movel.documento) {
    const numero = movel.documento.numero ? `NF-e ${movel.documento.numero}` : 'NF-e';
    if (movel.documento.status === 'AUTORIZADA') return { texto: numero, tom: 'sucesso' };
    return { texto: `${numero} · ${movel.documento.status.toLowerCase()}`, tom: 'alerta' };
  }
  if (movel.situacao === 'NO_ESTOQUE' && !movel.pode_faturar) {
    return { texto: 'Pronto · falta o simples faturamento', tom: 'alerta' };
  }
  if (movel.situacao === 'NO_ESTOQUE') return { texto: 'Pronto · no estoque', tom: 'info' };
  return { texto: movel.pronto ? 'Pronto' : 'Em produção', tom: 'neutro' };
}

/** As pendências do gate fiscal (422 com `detail.pendencias`), em texto. */
function pendenciasDoErro(erro: unknown): string[] {
  if (!axios.isAxiosError(erro)) return [];
  const detalhe = (erro.response?.data as { detail?: unknown } | undefined)?.detail as
    | { pendencias?: { mensagem: string; referencia_nome?: string | null }[] }
    | undefined;
  return (detalhe?.pendencias ?? []).map((p) => (p.referencia_nome ? `${p.referencia_nome}: ${p.mensagem}` : p.mensagem));
}

// --- Prévia e emissão ---------------------------------------------------------------
const previa = ref<PreviaNota | null>(null);
/** De qual nota é a prévia aberta: a da entrega (venda ou remessa) ou o simples faturamento. */
const previaDe = ref<'entrega' | 'simples'>('entrega');
const pendencias = ref<string[]>([]);
const carregando = ref(false);
const emitindo = ref(false);

async function preVisualizar(de: 'entrega' | 'simples' = 'entrega') {
  carregando.value = true;
  pendencias.value = [];
  previaDe.value = de;
  try {
    previa.value = de === 'simples'
      ? await previaDoSimplesFaturamento(numeroOs.value)
      : await previaDaNota(numeroOs.value, marcados.value);
  } catch (erro) {
    pendencias.value = pendenciasDoErro(erro);
    if (!pendencias.value.length) toast.error(mensagemDoErro(erro, 'Não foi possível montar a prévia da nota.'));
  } finally {
    carregando.value = false;
  }
}

async function emitir() {
  emitindo.value = true;
  try {
    const resultado = previaDe.value === 'simples'
      ? await emitirSimplesFaturamento(numeroOs.value)
      : await emitirNota(numeroOs.value, marcados.value);
    if (resultado.status === 'AUTORIZADA') toast.success('NF-e autorizada.', resultado.mensagem);
    else if (resultado.status === 'PROCESSANDO') toast.success('NF-e enviada. A SEFAZ ainda está processando.');
    else toast.error(`NF-e ${resultado.status.toLowerCase()}.`, resultado.mensagem);
    previa.value = null;
    if (previaDe.value === 'entrega') marcados.value = [];
  } catch (erro) {
    toast.error(mensagemDoErro(erro, 'Não foi possível emitir a nota.'));
  } finally {
    emitindo.value = false;
    await queryClient.invalidateQueries({ queryKey: chave.value });
  }
}

const rotuloPagamento = (codigo: string) => {
  if (codigo === '99') return 'A receber';
  if (codigo === '90') return 'Sem pagamento (já está no simples faturamento)';
  return `Forma ${codigo}`;
};
const reais = (valor: number) => formatCurrency(Math.round(valor * 100));
</script>

<template>
  <section v-if="ligado && data" class="rounded-2xl border border-zinc-200 bg-white p-4" data-testid="faturamento-moveis">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div class="flex items-center gap-2">
        <FileText :size="18" class="text-zinc-500" />
        <div>
          <h3 class="text-base font-semibold text-zinc-900">Notas fiscais dos móveis</h3>
          <p class="text-xs text-zinc-500">
            {{ entregaFutura ? 'Venda para entrega futura: uma nota de remessa a cada entrega.' : 'Uma NF-e a cada entrega, com os móveis que saíram.' }}
            {{ data.instalacao_modo === 'EMBUTIDA' ? 'A instalação entra no preço dos móveis.' : 'A instalação fica fora da NF-e.' }}
          </p>
        </div>
      </div>
      <BaseButton
        size="sm"
        :disabled="!marcados.length"
        :is-loading="carregando"
        data-testid="previa-nota"
        @click="preVisualizar('entrega')"
      >
        Emitir NF-e ({{ marcados.length }})
      </BaseButton>
    </div>

    <!-- Entrega futura (F4): a nota de simples faturamento vem antes de qualquer remessa. -->
    <div
      v-if="entregaFutura && data.falta_simples_faturamento"
      class="mt-3 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-sky-200 bg-sky-50 px-3 py-2 text-xs text-sky-900"
      data-testid="falta-simples-faturamento"
    >
      <span>Falta a nota de simples faturamento destes móveis. Ela vem antes das notas de remessa.</span>
      <BaseButton size="sm" variant="secondary" :is-loading="carregando && previaDe === 'simples'" data-testid="previa-simples" @click="preVisualizar('simples')">
        Emitir simples faturamento
      </BaseButton>
    </div>

    <div
      v-if="pendencias.length"
      class="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800"
      data-testid="pendencias-nota"
    >
      <p class="font-medium">Falta acertar antes de emitir:</p>
      <ul class="mt-1 list-disc pl-4">
        <li v-for="p in pendencias" :key="p">{{ p }}</li>
      </ul>
    </div>

    <div v-for="grupo in porAmbiente" :key="grupo.ambiente" class="mt-4">
      <div class="flex items-center justify-between">
        <p class="text-xs font-semibold uppercase tracking-wide text-zinc-500">{{ grupo.ambiente }}</p>
        <button
          v-if="grupo.moveis.some((m) => m.pode_faturar)"
          type="button"
          class="text-xs font-medium text-brand-primary hover:underline"
          @click="marcarAmbiente(grupo.moveis)"
        >
          Marcar este ambiente
        </button>
      </div>
      <ul class="mt-1 divide-y divide-zinc-100">
        <li v-for="movel in grupo.moveis" :key="movel.movel_id" class="flex items-center gap-3 py-2">
          <input
            type="checkbox"
            class="h-4 w-4 accent-brand-primary"
            :checked="marcados.includes(movel.movel_id)"
            :disabled="!movel.pode_faturar"
            :data-testid="`marcar-${movel.movel_id}`"
            @change="alternar(movel)"
          />
          <span class="flex-1 text-sm text-zinc-800">{{ movel.nome }} <span class="text-xs text-zinc-400">{{ movel.quantidade }}×</span></span>
          <BaseStatusPill :tom="situacao(movel).tom">{{ situacao(movel).texto }}</BaseStatusPill>
        </li>
      </ul>
    </div>

    <div v-if="data.notas.length" class="mt-4 border-t border-zinc-100 pt-3">
      <p class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Notas desta OS</p>
      <ul class="mt-1 text-sm text-zinc-700">
        <li v-for="nota in data.notas" :key="nota.id" class="flex justify-between py-1">
          <span>
            NF-e {{ nota.numero ?? '—' }} · {{ nota.status.toLowerCase() }}
            <span v-if="nota.papel === 'SIMPLES_FATURAMENTO'" class="text-xs text-zinc-400">· simples faturamento</span>
            <span v-else-if="nota.papel === 'REMESSA_ENTREGA_FUTURA'" class="text-xs text-zinc-400">· remessa</span>
          </span>
          <span class="tabular-nums">{{ nota.valor_total != null ? formatCurrency(nota.valor_total) : '' }}</span>
        </li>
      </ul>
      <p class="mt-1 text-[11px] text-zinc-400">A DANFE e o XML ficam no Centro Fiscal.</p>
    </div>

    <BaseModal :is-open="previa !== null" title="Conferir a NF-e" subtitle="Nada foi enviado ainda." size="lg" overlay @close="previa = null">
      <div v-if="previa" class="flex flex-col gap-4 text-sm" data-testid="previa">
        <p v-if="previa.natureza_operacao" class="text-xs text-zinc-500">{{ previa.natureza_operacao }}</p>
        <table class="w-full">
          <thead class="text-left text-xs text-zinc-500">
            <tr><th class="py-1">Item</th><th>CFOP</th><th>NCM</th><th class="text-right">Valor</th></tr>
          </thead>
          <tbody>
            <tr v-for="(item, i) in previa.itens" :key="i" class="border-t border-zinc-100">
              <td class="py-1">{{ item.quantidade_comercial }}× {{ item.descricao }}</td>
              <td>{{ item.cfop }}</td>
              <td>{{ item.ncm }}</td>
              <td class="text-right tabular-nums">{{ reais(item.valor_bruto) }}</td>
            </tr>
          </tbody>
        </table>
        <div class="flex justify-between border-t border-zinc-200 pt-2 font-semibold">
          <span>Total da nota</span><span class="tabular-nums">{{ reais(previa.totais.valor_total) }}</span>
        </div>
        <div>
          <p class="text-xs text-zinc-500">Pagamento</p>
          <p v-for="(p, i) in previa.formas_pagamento" :key="i" class="flex justify-between">
            <span>{{ rotuloPagamento(p.forma_pagamento) }}</span><span class="tabular-nums">{{ reais(p.valor_pagamento) }}</span>
          </p>
        </div>
        <ul v-if="previa.avisos.length" class="list-disc pl-4 text-xs text-amber-700">
          <li v-for="aviso in previa.avisos" :key="aviso">{{ aviso }}</li>
        </ul>
      </div>
      <template #footer>
        <div class="flex justify-end gap-2">
          <BaseButton variant="secondary" @click="previa = null">Voltar</BaseButton>
          <BaseButton :is-loading="emitindo" data-testid="emitir-nota" @click="emitir">Emitir NF-e</BaseButton>
        </div>
      </template>
    </BaseModal>
  </section>
</template>
