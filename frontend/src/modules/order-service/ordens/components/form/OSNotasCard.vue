<script setup lang="ts">
/**
 * @component OSNotasCard
 * @description "Notas desta OS": as peças vão em NF-e e o serviço em NFS-e,
 * cada uma com o seu valor, a sua situação e o seu botão.
 *
 * M5 de docs/nfse-melhorias-plano.md. Decisões do Alan (29/10/2026):
 * - nota só sai quando o cliente pede: "Não emitida" é cinza e neutra, sem
 *   cobrança — cor só depois que alguém emite;
 * - peça e serviço são notas diferentes (como Omie, GestãoClick e Olist);
 * - só aparece o lado que a OS tem.
 *
 * Até aqui a NF-e das peças de uma OS comum não tinha botão em tela nenhuma
 * (a seção que chamava `emitir-fiscal` nunca foi montada).
 */
import { computed, ref } from 'vue';
import { useQuery, useQueryClient } from '@tanstack/vue-query';
import { FileText, Package, Wrench, Send, Eye } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import PendenciasFiscaisModal from '@/shared/components/commons/PendenciasFiscaisModal.vue';
import { useEmitirFiscal } from '@/shared/composables/useEmitirFiscal';
import { formatCurrency } from '@/shared/utils/finance';
import { STATUS_COLORS, STATUS_LABELS } from '@/modules/fiscal/constants/fiscal.constants';
import NfseEmitirModal from '@/modules/fiscal/components/nfse/NfseEmitirModal.vue';
import NfseDocumentoDrawer from '@/modules/fiscal/components/nfse/NfseDocumentoDrawer.vue';
import FiscalDocumentoDetailsDrawer from '@/modules/fiscal/components/detalhes/FiscalDocumentoDetailsDrawer.vue';
import { useNfseConsultarMutation } from '@/modules/fiscal/composables/useNfse';
import { getNotasDaOs, type NotaDaOs } from '../../services/orderServiceFiscal.service';

const props = defineProps<{ osNumero: string }>();

const queryClient = useQueryClient();
const chave = computed(() => ['os-notas-fiscais', props.osNumero] as const);
const { data: notas } = useQuery({
  queryKey: chave,
  queryFn: () => getNotasDaOs(props.osNumero),
  staleTime: 15_000,
});
const recarregar = () => queryClient.invalidateQueries({ queryKey: chave.value });

// Peças → NF-e (o fluxo de sempre: confere, mostra pendências, emite)
const { pendencias, pendenciasModalOpen, isVerificando, emitirOS } = useEmitirFiscal();
async function emitirNfe() {
  await emitirOS(props.osNumero, 'nfe');
  recarregar();
}
const nfeAberta = ref<number | null>(null);

// Serviço → NFS-e (a conferência do Centro Fiscal, já na OS)
const emitindoNfse = ref(false);
function fecharNfse() {
  emitindoNfse.value = false;
  recarregar();
}
const nfseAberta = ref<number | null>(null);
const consultarNfse = useNfseConsultarMutation();

/** Status de quem já emitiu; sem documento é "Não emitida", cinza. */
function etiqueta(doc: NotaDaOs | null | undefined) {
  if (!doc) return { texto: 'Não emitida', classe: 'bg-zinc-100 text-zinc-500' };
  const c = STATUS_COLORS[doc.status];
  return { texto: STATUS_LABELS[doc.status] ?? doc.status, classe: c ? `${c.bg} ${c.text}` : 'bg-zinc-100 text-zinc-600' };
}

/** Pode emitir (de novo) quando não há nota viva. */
const VIVOS = ['AUTORIZADA', 'PROCESSANDO', 'INDETERMINADA', 'PENDENTE'];
const podeEmitirNfe = computed(() => {
  const doc = notas.value?.pecas.documento;
  return !doc || !VIVOS.includes(doc.status);
});
const podeEmitirNfse = computed(() => {
  const docs = notas.value?.servico.documentos ?? [];
  return !docs.length || docs.every((d) => !VIVOS.includes(d.status));
});

const somaBate = computed(() => {
  const n = notas.value;
  if (!n) return true;
  const soma = (n.pecas.tem ? n.pecas.valor : 0) + (n.servico.tem ? n.servico.valor : 0);
  return soma === n.total_os;
});
</script>

<template>
  <div v-if="notas && (notas.pecas.tem || notas.servico.tem)" class="bg-white rounded-2xl border border-zinc-200 p-4 space-y-3" data-os-notas>
    <div class="flex items-center gap-2">
      <FileText :size="16" class="text-brand-primary" />
      <h4 class="text-sm font-semibold text-zinc-800">Notas desta OS</h4>
    </div>
    <p class="text-xs text-zinc-500">Emita só a que o cliente pedir.</p>

    <!-- Peças → NF-e -->
    <div v-if="notas.pecas.tem" class="rounded-xl border border-zinc-200 p-3 space-y-2" data-nota-pecas>
      <div class="flex items-center justify-between gap-2">
        <span class="flex items-center gap-1.5 text-sm font-semibold text-zinc-700">
          <Package :size="14" /> Peças · NF-e
        </span>
        <span class="text-sm font-semibold text-zinc-800">{{ formatCurrency(notas.pecas.valor) }}</span>
      </div>
      <template v-if="notas.pecas.modulo">
        <div class="flex items-center justify-between gap-2">
          <span :class="['px-2 py-0.5 text-[11px] font-semibold rounded-full', etiqueta(notas.pecas.documento).classe]">
            {{ etiqueta(notas.pecas.documento).texto }}<template v-if="notas.pecas.documento?.numero"> · nº {{ notas.pecas.documento.numero }}</template>
          </span>
          <button
            v-if="notas.pecas.documento"
            type="button"
            class="text-xs font-semibold text-brand-primary hover:underline flex items-center gap-1"
            @click="nfeAberta = notas.pecas.documento!.id"
          >
            <Eye :size="12" /> Ver detalhes
          </button>
        </div>
        <BaseButton v-if="podeEmitirNfe" variant="secondary" size="sm" class="w-full" :is-loading="isVerificando" @click="emitirNfe">
          <Send :size="14" class="mr-1.5" /> Emitir NF-e das peças
        </BaseButton>
      </template>
      <p v-else class="text-xs text-zinc-500">
        A sua empresa não emite NF-e por este sistema. Se o cliente pedir nota das peças, fale com o seu contador.
      </p>
    </div>

    <!-- Serviço → NFS-e -->
    <div v-if="notas.servico.tem" class="rounded-xl border border-zinc-200 p-3 space-y-2" data-nota-servico>
      <div class="flex items-center justify-between gap-2">
        <span class="flex items-center gap-1.5 text-sm font-semibold text-zinc-700">
          <Wrench :size="14" /> Serviço · NFS-e
        </span>
        <span class="text-sm font-semibold text-zinc-800">{{ formatCurrency(notas.servico.valor) }}</span>
      </div>
      <template v-if="notas.servico.modulo">
        <div v-if="!notas.servico.documentos.length" class="flex">
          <span :class="['px-2 py-0.5 text-[11px] font-semibold rounded-full', etiqueta(null).classe]">Não emitida</span>
        </div>
        <div v-for="doc in notas.servico.documentos" :key="doc.id" class="flex items-center justify-between gap-2">
          <span :class="['px-2 py-0.5 text-[11px] font-semibold rounded-full', etiqueta(doc).classe]">
            {{ etiqueta(doc).texto }}<template v-if="doc.numero"> · nº {{ doc.numero }}</template>
          </span>
          <button type="button" class="text-xs font-semibold text-brand-primary hover:underline flex items-center gap-1" @click="nfseAberta = doc.id">
            <Eye :size="12" /> Ver detalhes
          </button>
        </div>
        <BaseButton v-if="podeEmitirNfse" variant="secondary" size="sm" class="w-full" @click="emitindoNfse = true">
          <Send :size="14" class="mr-1.5" /> Emitir NFS-e do serviço
        </BaseButton>
      </template>
      <p v-else class="text-xs text-zinc-500">
        A nota de serviço (NFS-e) não está contratada. Fale com a StartBig para liberar.
      </p>
    </div>

    <p v-if="notas.pecas.tem && notas.servico.tem" class="text-[11px] text-zinc-500">
      Peças + serviço = {{ formatCurrency((notas.pecas.valor || 0) + (notas.servico.valor || 0)) }}
      <template v-if="!somaBate"> (o total da OS, {{ formatCurrency(notas.total_os) }}, inclui entrega ou acréscimo)</template>
    </p>

    <PendenciasFiscaisModal
      :is-open="pendenciasModalOpen"
      :pendencias="pendencias"
      titulo="Pendências Fiscais — OS"
      @close="pendenciasModalOpen = false"
    />
    <NfseEmitirModal :is-open="emitindoNfse" :numero-os-inicial="osNumero" @close="fecharNfse" />
    <NfseDocumentoDrawer
      :documento-id="nfseAberta"
      @close="nfseAberta = null; recarregar()"
      @consultar="consultarNfse.mutate($event)"
      @cancelar="nfseAberta = null"
    />
    <FiscalDocumentoDetailsDrawer
      v-if="notas.pecas.modulo"
      :documento-id="nfeAberta"
      :is-open="nfeAberta !== null"
      @update:is-open="(v: boolean) => { if (!v) { nfeAberta = null; recarregar(); } }"
    />
  </div>
</template>
