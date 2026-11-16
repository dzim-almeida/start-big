<script setup lang="ts">
/**
 * @component NfseDocumentosTable
 * @description As NFS-e emitidas, no mesmo visual da tabela de NF-e.
 *
 * Mostra o CÓDIGO DE VERIFICAÇÃO ao lado do número: é o que o tomador usa para
 * conferir a nota no portal, e o que o lojista passa por telefone.
 */
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { AlertCircle, Ban, ExternalLink, FileText, RefreshCw } from 'lucide-vue-next';

import BaseTableContainer from '@/shared/components/commons/BaseTableContainer/BaseTableContainer.vue';
import { formatCurrency } from '@/shared/utils/finance';
import { formatDataHora } from '@/shared/utils/date.utils';

import { useNfseConsultarMutation, useNfseDocumentosQuery } from '../../composables/useNfse';
import { STATUS_COLORS, STATUS_LABELS } from '../../constants/fiscal.constants';
import { abrirArquivo } from '../../utils/abrirArquivo';
import NfseCancelarModal from './NfseCancelarModal.vue';
import NfseDocumentoDrawer from './NfseDocumentoDrawer.vue';
import type { DocumentoFiscalStatus, NfseDocumento } from '../../types/fiscal.types';

const props = defineProps<{
  /** O card clicado na aba (M4): os mesmos grupos dos contadores do resumo. */
  statusFiltro?: DocumentoFiscalStatus | null;
}>();

/** Cada card soma mais de um status (como `obter_resumo` no backend). */
const GRUPOS_DO_CARD: Partial<Record<DocumentoFiscalStatus, string[]>> = {
  PENDENTE: ['PENDENTE', 'PROCESSANDO'],
  CANCELADA: ['CANCELADA', 'DENEGADA'],
};

const { documentos: todos, isLoading, isError } = useNfseDocumentosQuery();
const documentos = computed(() => {
  if (!props.statusFiltro) return todos.value;
  const aceitos = GRUPOS_DO_CARD[props.statusFiltro] ?? [props.statusFiltro];
  return todos.value.filter((d) => aceitos.includes(d.status));
});
const consultarMutation = useNfseConsultarMutation();
const paraCancelar = ref<NfseDocumento | null>(null);
/** A NFS-e aberta na gaveta de detalhes (clique na linha, como na NF-e). */
const detalheId = ref<number | null>(null);

/** O número da OS leva à própria OS (vínculo nos dois sentidos, M5). */
const router = useRouter();
const abrirOs = (numero: string) => router.push({ name: 'services', query: { os: numero } });

function cancelarPelaGaveta(id: number) {
  paraCancelar.value = todos.value.find((d) => d.id === id) ?? null;
  detalheId.value = null;
}

/** Sem resposta definitiva: só a consulta resolve (nunca reemitir por cima). */
const podeConsultar = (status: string) => ['PROCESSANDO', 'INDETERMINADA'].includes(status);

function corDoStatus(status: string) {
  const c = STATUS_COLORS[status];
  return c ? `${c.bg} ${c.text}` : 'bg-zinc-100 text-zinc-600';
}
</script>

<template>
  <BaseTableContainer
    :is-loading="isLoading"
    :is-error="isError"
    :is-empty="!documentos.length"
    item-label="nota"
    empty-title="Nenhuma NFS-e emitida ainda"
    empty-description="Use “Emitir NFS-e” para a mão de obra de uma OS finalizada."
  >
    <table class="w-full text-left">
      <thead class="bg-zinc-50/80 text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
        <tr>
          <th class="px-4 md:px-6 py-3 md:py-4">Nº</th>
          <th class="px-4 md:px-6 py-3 md:py-4">Tomador</th>
          <th class="px-4 md:px-6 py-3 md:py-4 text-right">Valor</th>
          <th class="px-4 md:px-6 py-3 md:py-4">Status</th>
          <th class="px-4 md:px-6 py-3 md:py-4">Data</th>
          <th class="px-4 md:px-6 py-3 md:py-4 text-right min-w-36">Ações</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-zinc-100">
        <tr
          v-for="doc in documentos"
          :key="doc.id"
          class="hover:bg-zinc-50/50 transition-colors group cursor-pointer"
          data-nfse-linha
          title="Ver detalhes"
          @click="detalheId = doc.id"
        >
          <td class="px-4 md:px-6 py-3 md:py-4">
            <div class="w-12 h-10 bg-brand-primary/10 rounded-xl flex flex-col items-center justify-center text-brand-primary">
              <span class="text-[7px] opacity-70 font-bold leading-none">NFS-E</span>
              <span class="text-sm font-black leading-none mt-0.5">{{ doc.numero ?? '-' }}</span>
            </div>
          </td>
          <td class="px-4 md:px-6 py-3 md:py-4">
            <div class="flex flex-col">
              <span class="text-sm font-semibold text-zinc-900 truncate max-w-xs">{{ doc.tomador || 'Tomador não identificado' }}</span>
              <span class="text-[10px] text-zinc-400 mt-0.5">
                <button
                  v-if="doc.numero_os"
                  type="button"
                  class="text-brand-primary hover:underline"
                  title="Abrir a OS"
                  @click.stop="abrirOs(doc.numero_os)"
                >{{ doc.numero_os }}</button>
                <template v-else>Avulsa</template>
                <template v-if="doc.codigo_verificacao"> · verificação {{ doc.codigo_verificacao }}</template>
              </span>
              <div
                v-if="['REJEITADA', 'INDETERMINADA', 'NAO_TRANSMITIDA'].includes(doc.status) && doc.mensagem"
                class="flex items-center gap-1 mt-1 text-[11px] text-red-600 truncate max-w-xs"
                :title="doc.mensagem"
              >
                <AlertCircle :size="12" class="shrink-0 text-red-500" />
                <span class="truncate">{{ doc.mensagem }}</span>
              </div>
            </div>
          </td>
          <td class="px-4 md:px-6 py-3 md:py-4 text-xs md:text-sm font-medium text-zinc-600 text-right whitespace-nowrap">
            {{ doc.valor_total != null ? formatCurrency(doc.valor_total) : '-' }}
          </td>
          <td class="px-4 md:px-6 py-3 md:py-4">
            <span :class="['px-2 md:px-3 py-1 rounded-full text-[10px] md:text-[11px] font-bold whitespace-nowrap inline-block', corDoStatus(doc.status)]">
              {{ STATUS_LABELS[doc.status] ?? doc.status }}
            </span>
          </td>
          <td class="px-4 md:px-6 py-3 md:py-4 text-xs md:text-sm font-medium text-zinc-600 whitespace-nowrap">
            {{ formatDataHora(doc.data_autorizacao ?? doc.data_emissao) }}
          </td>
          <td class="px-4 md:px-6 py-3 md:py-4 text-right">
            <div class="flex items-center justify-end gap-1">
              <button
                v-if="doc.url_consulta"
                type="button"
                class="p-2 rounded-lg text-zinc-400 hover:text-brand-primary hover:bg-brand-primary/10 transition-colors cursor-pointer"
                title="Abrir a nota no portal da NFS-e"
                @click.stop="abrirArquivo(doc.url_consulta)"
              >
                <ExternalLink :size="18" />
              </button>
              <button
                v-if="doc.url_pdf"
                type="button"
                class="p-2 rounded-lg text-zinc-400 hover:text-brand-primary hover:bg-brand-primary/10 transition-colors cursor-pointer"
                title="DANFSe (PDF)"
                @click.stop="abrirArquivo(doc.url_pdf)"
              >
                <FileText :size="18" />
              </button>
              <button
                v-if="podeConsultar(doc.status)"
                type="button"
                class="p-2 rounded-lg text-zinc-400 hover:text-blue-600 hover:bg-blue-50 transition-colors cursor-pointer disabled:opacity-50"
                title="Consultar o resultado"
                :disabled="consultarMutation.isPending.value"
                @click.stop="consultarMutation.mutate(doc.id)"
              >
                <RefreshCw :size="18" />
              </button>
              <button
                v-if="doc.status === 'AUTORIZADA'"
                type="button"
                class="p-2 rounded-lg text-zinc-400 hover:text-red-600 hover:bg-red-50 transition-colors cursor-pointer"
                title="Cancelar NFS-e"
                @click.stop="paraCancelar = doc"
              >
                <Ban :size="18" />
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </BaseTableContainer>

  <NfseCancelarModal :documento="paraCancelar" @close="paraCancelar = null" />
  <NfseDocumentoDrawer
    :documento-id="detalheId"
    @close="detalheId = null"
    @consultar="consultarMutation.mutate($event)"
    @cancelar="cancelarPelaGaveta"
    @trocar="detalheId = $event"
  />
</template>
