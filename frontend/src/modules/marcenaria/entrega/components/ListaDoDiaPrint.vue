<script setup lang="ts">
/**
 * @component ListaDoDiaPrint
 * @description O roteiro do dia em A4 (Spec 13B D17): um bloco por
 * agendamento, com o endereço da obra, para a equipe sair de manhã com o papel
 * (P3). Preto e branco (o `check:print-bw` barra cor) e nenhum preço.
 */
import PrintCompanyHeader from '@/shared/components/print/a4/PrintCompanyHeader.vue';
import PrintFooter from '@/shared/components/print/a4/PrintFooter.vue';
import { formatTelefone } from '@/shared/utils/document.utils';
import { useCompanyPrintInfo } from '@/shared/utils/print.utils';

import type { Instalacao } from '../schemas/entrega.schema';
import { nomesDosMontadores, ROTULO_SITUACAO_ENTREGA } from '../utils/entrega';

defineProps<{ titulo: string; itens: Instalacao[] }>();

const { companyInfo } = useCompanyPrintInfo();
</script>

<template>
  <!-- Teleport: o print-a4.css esconde tudo o que não for filho direto do body. -->
  <Teleport to="body">
    <div class="print-container lista-do-dia hidden print:block bg-white text-black font-sans leading-snug" data-testid="lista-do-dia">
      <PrintCompanyHeader
        :company="companyInfo"
        document-label="INSTALAÇÕES DO DIA"
        :document-number="titulo"
        date-label="Agendamentos"
        :date-value="String(itens.length)"
      />
      <section v-for="item in itens" :key="item.id" class="instalacao mb-3 border border-neutral-400 p-3 text-sm">
        <p class="font-bold">
          {{ item.hora_inicio ?? 'Sem hora' }} · {{ item.numero_os }} · {{ item.cliente ?? '—' }}
          <template v-if="item.telefone"> · {{ formatTelefone(item.telefone) }}</template>
        </p>
        <p v-if="item.endereco_obra">Obra: {{ item.endereco_obra }}<template v-if="item.projeto"> — {{ item.projeto }}</template></p>
        <p>
          Ambientes:
          <template v-for="(ambiente, i) in item.ambientes" :key="ambiente.ambiente_id">
            {{ ambiente.nome }}<template v-if="ambiente.situacao && ambiente.situacao !== 'PENDENTE'"> ({{ ROTULO_SITUACAO_ENTREGA[ambiente.situacao] }})</template><template v-if="i < item.ambientes.length - 1">, </template>
          </template>
        </p>
        <p>Montadores: {{ nomesDosMontadores(item.montadores) }}</p>
        <p v-if="item.observacao">Observação: {{ item.observacao }}</p>
      </section>
      <PrintFooter />
    </div>
  </Teleport>
</template>

<style>
@media print {
  /* Um agendamento nunca dividido entre duas folhas. */
  .lista-do-dia .instalacao { break-inside: avoid; }
}
</style>
