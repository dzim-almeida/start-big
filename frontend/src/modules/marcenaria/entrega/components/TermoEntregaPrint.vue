<script setup lang="ts">
/**
 * @component TermoEntregaPrint
 * @description O Termo de Entrega e Instalação de UM ambiente, em A4 (Spec
 * 13B D12, D13; I1). É o papel que o montador leva para a obra: o cliente
 * confere, marca o checklist à caneta, anota as pendências e assina.
 *
 * Preto e branco (o `check:print-bw` barra cor) e NENHUM preço (D11). O bloco
 * que se assina (checklist + pendências + declaração + assinaturas) nunca é
 * dividido entre páginas (`break-inside: avoid`), como o fechamento da
 * proposta (07 D13).
 */
import { computed } from 'vue';

import PrintCompanyHeader from '@/shared/components/print/a4/PrintCompanyHeader.vue';
import PrintSignatures from '@/shared/components/print/a4/PrintSignatures.vue';
import { formatTelefone } from '@/shared/utils/document.utils';
import { formatDataPura } from '@/shared/utils/date.utils';
import { useCompanyPrintInfo } from '@/shared/utils/print.utils';
import { formatarMedidasProposta } from '@/modules/marcenaria/orcamentos/utils/dadosProposta';

import type { EntregaAmbiente, EntregaDaOS } from '../schemas/entrega.schema';
import { nomesDosMontadores } from '../utils/entrega';

const props = defineProps<{
  /** O cabeçalho da obra: OS, projeto e cliente. */
  dados: Pick<EntregaDaOS, 'os' | 'projeto' | 'cliente'>;
  entrega: EntregaAmbiente;
  /** Do segundo termo em diante: começa numa página nova (D4). */
  quebraAntes?: boolean;
}>();

const { companyInfo } = useCompanyPrintInfo();

/** "Av. das Américas, 4200 — Residencial Alpha Ville - Apto 802". */
const obra = computed(() =>
  [props.dados.projeto.endereco_obra, props.dados.projeto.nome].filter(Boolean).join(' — '));
const telefone = computed(() => (props.dados.cliente.telefone ? formatTelefone(props.dados.cliente.telefone) : ''));
const agendamento = computed(() => props.entrega.agendamento);
/** As 6 linhas em branco para as pendências escritas à mão. */
const LINHAS = 6;
</script>

<template>
  <!-- Teleport: o print-a4.css esconde tudo o que não for filho direto do body. -->
  <Teleport to="body">
    <div
      class="print-container termo-entrega hidden print:block bg-white text-black font-sans leading-snug"
      :class="{ 'termo-nova-pagina': quebraAntes }"
      data-testid="termo-entrega"
    >
      <PrintCompanyHeader
        :company="companyInfo"
        document-label="TERMO DE ENTREGA E INSTALAÇÃO"
        :document-number="dados.os.numero_os"
        date-label="Projeto"
        :date-value="dados.projeto.codigo ?? '—'"
      />

      <!-- A obra -->
      <div class="mb-3 space-y-0.5 text-sm">
        <p>Cliente: <strong>{{ dados.cliente.nome ?? '—' }}</strong><template v-if="telefone"> · {{ telefone }}</template></p>
        <p v-if="obra">Obra: {{ obra }}</p>
        <p class="pt-1 text-base">
          Ambiente: <strong class="uppercase" data-testid="termo-ambiente">{{ entrega.ambiente }}</strong>
          <template v-if="agendamento">
            <span class="ml-4 text-sm">
              Instalação: {{ formatDataPura(agendamento.data) }}<template v-if="agendamento.hora_inicio"> às {{ agendamento.hora_inicio }}</template>
              <template v-if="agendamento.montadores.length"> · Montadores: {{ nomesDosMontadores(agendamento.montadores) }}</template>
            </span>
          </template>
        </p>
      </div>

      <!-- Os móveis do ambiente (nome, medidas, quantidade). Nenhum preço. -->
      <h2 class="mt-2 border-b-2 border-black pb-0.5 text-xs font-bold uppercase tracking-wider">Móveis</h2>
      <table class="mb-3 w-full border-collapse text-sm" data-testid="termo-moveis">
        <tbody>
          <tr v-for="(movel, i) in entrega.moveis" :key="i" class="border-b border-neutral-300">
            <td class="py-1 pr-2">{{ movel.nome }}</td>
            <td class="py-1 pr-2 text-right tabular-nums">
              {{ formatarMedidasProposta(movel.medidas.largura_mm, movel.medidas.altura_mm, movel.medidas.profundidade_mm) }}
            </td>
            <td class="w-16 py-1 text-right tabular-nums">{{ movel.quantidade }} un.</td>
          </tr>
        </tbody>
      </table>

      <!-- O que se assina fica junto (D13) -->
      <section class="termo-assinavel">
        <table class="w-full border-collapse text-sm" data-testid="termo-checklist">
          <thead>
            <tr class="border-b-2 border-black text-left">
              <th class="py-1 pr-2 text-xs uppercase tracking-wider">Vistoria</th>
              <th class="w-14 py-1 text-center text-xs uppercase">OK</th>
              <th class="w-14 py-1 text-center text-xs uppercase">Não OK</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, i) in entrega.checklist" :key="i" class="border-b border-neutral-300">
              <td class="py-1.5 pr-2">{{ item.texto }}</td>
              <td class="py-1.5 text-center"><span class="inline-block h-4 w-4 border border-black" /></td>
              <td class="py-1.5 text-center"><span class="inline-block h-4 w-4 border border-black" /></td>
            </tr>
          </tbody>
        </table>

        <h2 class="mt-4 text-xs font-bold uppercase tracking-wider">Pendências / observações</h2>
        <div v-for="n in LINHAS" :key="n" class="h-7 border-b border-neutral-400" data-testid="termo-linha" />

        <p class="mt-4 text-sm">
          Recebi os móveis acima, instalados e em condições de uso, ressalvadas as pendências anotadas.
        </p>
        <PrintSignatures left-label="Cliente / recebedor (nome e doc.)" right-label="Montador" />
        <p class="mt-4 text-sm">Data: ___/___/______</p>
      </section>
    </div>
  </Teleport>
</template>

<style>
@media print {
  /* D4: cada termo do agendamento começa numa folha nova. */
  .termo-entrega.termo-nova-pagina { break-before: page; }
  /* D13: o que se assina nunca fica numa folha diferente das assinaturas. */
  .termo-entrega .termo-assinavel { break-inside: avoid; }
}
</style>
