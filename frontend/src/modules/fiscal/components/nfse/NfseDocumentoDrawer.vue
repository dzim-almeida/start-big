<script setup lang="ts">
/**
 * @component NfseDocumentoDrawer
 * @description O detalhe de uma NFS-e, aberto ao clicar na linha da aba — no
 * mesmo visual da gaveta da NF-e.
 *
 * Pedido do Alan em 29/10/2026: a linha mostrava o motivo da recusa cortado
 * ("Empresa não habilitada para emissão de NFSe no am…") e não havia onde ver
 * o resto nem o que fazer. Aqui vão o motivo inteiro, a dica, os dados da nota,
 * os serviços e as tentativas anteriores. As ações (consultar, cancelar) são as
 * da tabela: a gaveta só pede.
 */
import { computed } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import {
  AlertTriangle, Ban, CheckCircle, Clock, ExternalLink, FileText, History, Lightbulb, Loader2, RefreshCw, X,
} from 'lucide-vue-next';

import { formatCurrency } from '@/shared/utils/finance';
import { formatDataHora } from '@/shared/utils/date.utils';
import { formatCPF, formatCNPJ } from '@/shared/utils/document.utils';
import { nfseService } from '../../services/nfse.service';
import { fiscalKeys, STATUS_COLORS, STATUS_LABELS } from '../../constants/fiscal.constants';
import { formatarCodigoNacional } from '../../utils/nfse.utils';
import { abrirArquivo } from '../../utils/abrirArquivo';

const props = defineProps<{ documentoId: number | null }>();
const emit = defineEmits<{ close: []; consultar: [id: number]; cancelar: [id: number] }>();

const aberto = computed(() => props.documentoId != null);

const { data: doc, isLoading, isError } = useQuery({
  // Debaixo de `nfseDocumentos`: consultar e cancelar já invalidam a gaveta.
  queryKey: computed(() => [...fiscalKeys.nfseDocumentos(), 'detalhe', props.documentoId] as const),
  queryFn: () => nfseService.obterDocumento(props.documentoId!),
  enabled: aberto,
});

const cores = computed(() => {
  const c = doc.value ? STATUS_COLORS[doc.value.status] : undefined;
  return c ? `${c.bg} ${c.text}` : 'bg-zinc-100 text-zinc-600';
});

const icone = computed(() => {
  switch (doc.value?.status) {
    case 'AUTORIZADA': return CheckCircle;
    case 'CANCELADA': return Ban;
    case 'PROCESSANDO':
    case 'INDETERMINADA': return Clock;
    default: return AlertTriangle;
  }
});

const recusada = computed(() => ['REJEITADA', 'NAO_TRANSMITIDA', 'ERRO', 'DENEGADA'].includes(doc.value?.status ?? ''));
const podeConsultar = computed(() => ['PROCESSANDO', 'INDETERMINADA'].includes(doc.value?.status ?? ''));

const documentoTomador = computed(() => {
  const d = (doc.value?.tomador_documento ?? '').replace(/\D/g, '');
  if (d.length === 14) return formatCNPJ(d);
  if (d.length === 11) return formatCPF(d);
  return null;
});
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="aberto" class="fixed inset-0 z-50 overflow-hidden" data-nfse-detalhe>
        <div class="absolute inset-0 bg-black/30 backdrop-blur-sm" @click="emit('close')" />

        <div class="absolute inset-y-0 right-0 flex max-w-full pl-6">
          <div class="w-screen max-w-2xl">
            <div class="flex h-full flex-col bg-white shadow-2xl">
              <!-- Cabeçalho -->
              <div class="flex items-center justify-between border-b border-zinc-200 bg-zinc-50/80 px-6 py-4">
                <div class="flex items-center gap-3">
                  <div v-if="doc" :class="['flex h-10 w-10 items-center justify-center rounded-xl', cores]">
                    <component :is="icone" class="h-5 w-5" />
                  </div>
                  <div>
                    <div class="flex items-center gap-2.5">
                      <h2 class="text-lg font-bold text-zinc-900">Detalhes da NFS-e</h2>
                      <span v-if="doc" :class="['rounded-full px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wider', cores]">
                        {{ STATUS_LABELS[doc.status] ?? doc.status }}
                      </span>
                    </div>
                    <p v-if="doc" class="text-xs text-zinc-500 mt-0.5">
                      Nº {{ doc.numero ?? '-' }}
                      <template v-if="doc.numero_os"> · {{ doc.numero_os }}</template>
                      <template v-else> · Avulsa</template>
                      · {{ doc.ambiente === 1 ? 'Produção' : 'Homologação (teste)' }}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  class="rounded-lg p-2 text-zinc-400 transition-colors hover:bg-zinc-200 hover:text-zinc-700 cursor-pointer"
                  @click="emit('close')"
                >
                  <X class="h-5 w-5" />
                </button>
              </div>

              <div v-if="isLoading" class="flex flex-1 items-center justify-center">
                <Loader2 class="h-8 w-8 animate-spin text-brand-primary" />
              </div>
              <div v-else-if="isError || !doc" class="flex flex-1 items-center justify-center text-sm text-zinc-500">
                Não foi possível carregar esta NFS-e.
              </div>

              <div v-else class="flex-1 overflow-y-auto px-6 py-5 space-y-5">
                <!-- O motivo inteiro e o que fazer -->
                <div v-if="doc.motivo && (recusada || podeConsultar)" class="rounded-xl border border-red-200 bg-red-50 p-4" data-motivo>
                  <p class="text-xs font-semibold uppercase tracking-wide text-red-700 mb-1">
                    {{ podeConsultar ? 'Situação' : 'Por que não saiu' }}
                  </p>
                  <p class="text-sm text-red-800 whitespace-pre-line">{{ doc.motivo }}</p>
                  <p v-if="doc.codigo_status" class="text-xs text-red-600 mt-1">Código: {{ doc.codigo_status }}</p>
                </div>
                <div v-if="doc.dica" class="rounded-xl border border-amber-200 bg-amber-50 p-4 flex items-start gap-2" data-dica>
                  <Lightbulb :size="16" class="mt-0.5 shrink-0 text-amber-600" />
                  <p class="text-sm text-amber-800">{{ doc.dica }}</p>
                </div>

                <!-- Ações -->
                <div class="flex flex-wrap gap-2">
                  <button
                    v-if="podeConsultar"
                    type="button"
                    class="inline-flex items-center gap-1.5 rounded-lg border border-zinc-200 px-3 py-2 text-sm font-semibold text-zinc-700 hover:bg-zinc-50"
                    @click="emit('consultar', doc.id)"
                  >
                    <RefreshCw :size="14" /> Consultar o resultado
                  </button>
                  <button
                    v-if="doc.url_pdf"
                    type="button"
                    class="inline-flex items-center gap-1.5 rounded-lg border border-zinc-200 px-3 py-2 text-sm font-semibold text-zinc-700 hover:bg-zinc-50"
                    @click="abrirArquivo(doc.url_pdf)"
                  >
                    <FileText :size="14" /> DANFSe (PDF)
                  </button>
                  <button
                    v-if="doc.url_consulta"
                    type="button"
                    class="inline-flex items-center gap-1.5 rounded-lg border border-zinc-200 px-3 py-2 text-sm font-semibold text-zinc-700 hover:bg-zinc-50"
                    @click="abrirArquivo(doc.url_consulta)"
                  >
                    <ExternalLink :size="14" /> Ver no portal da NFS-e
                  </button>
                  <button
                    v-if="doc.status === 'AUTORIZADA'"
                    type="button"
                    class="inline-flex items-center gap-1.5 rounded-lg border border-red-200 px-3 py-2 text-sm font-semibold text-red-700 hover:bg-red-50"
                    @click="emit('cancelar', doc.id)"
                  >
                    <Ban :size="14" /> Cancelar NFS-e
                  </button>
                </div>

                <!-- A nota -->
                <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 text-sm rounded-xl border border-zinc-200 p-4">
                  <div>
                    <dt class="text-xs text-zinc-400">Tomador</dt>
                    <dd class="font-medium text-zinc-800">{{ doc.tomador || 'Não identificado' }}</dd>
                    <dd v-if="documentoTomador" class="text-xs text-zinc-500">{{ documentoTomador }}</dd>
                  </div>
                  <div>
                    <dt class="text-xs text-zinc-400">Valor</dt>
                    <dd class="font-semibold text-zinc-800">{{ doc.valor_total != null ? formatCurrency(doc.valor_total) : '-' }}</dd>
                  </div>
                  <div>
                    <dt class="text-xs text-zinc-400">Enviada em</dt>
                    <dd class="text-zinc-700">{{ formatDataHora(doc.data_emissao) }}</dd>
                  </div>
                  <div v-if="doc.data_autorizacao">
                    <dt class="text-xs text-zinc-400">Autorizada em</dt>
                    <dd class="text-zinc-700">{{ formatDataHora(doc.data_autorizacao) }}</dd>
                  </div>
                  <div v-if="doc.codigo_verificacao">
                    <dt class="text-xs text-zinc-400">Código de verificação</dt>
                    <dd class="font-mono text-zinc-800">{{ doc.codigo_verificacao }}</dd>
                  </div>
                  <div v-if="doc.chave_acesso" class="sm:col-span-2">
                    <dt class="text-xs text-zinc-400">Chave de acesso</dt>
                    <dd class="font-mono text-xs text-zinc-700 break-all">{{ doc.chave_acesso }}</dd>
                  </div>
                  <div>
                    <dt class="text-xs text-zinc-400">Referência na emissora</dt>
                    <dd class="font-mono text-xs text-zinc-600">{{ doc.ref ?? '-' }}</dd>
                  </div>
                </dl>

                <!-- Serviços -->
                <div v-if="doc.itens.length">
                  <p class="text-xs font-semibold uppercase tracking-wide text-zinc-500 mb-2">Serviços</p>
                  <ul class="divide-y divide-zinc-100 rounded-xl border border-zinc-200">
                    <li v-for="(item, i) in doc.itens" :key="i" class="flex items-center justify-between gap-3 px-4 py-2.5 text-sm">
                      <span class="min-w-0">
                        <span class="block text-zinc-800 truncate">{{ item.descricao }}</span>
                        <span v-if="item.codigo" class="block text-xs text-zinc-400">Código {{ formatarCodigoNacional(item.codigo) }}</span>
                      </span>
                      <span class="shrink-0 font-medium text-zinc-700">{{ formatCurrency(item.valor) }}</span>
                    </li>
                  </ul>
                </div>

                <!-- Tentativas anteriores -->
                <div v-if="doc.tentativas_anteriores.length">
                  <p class="text-xs font-semibold uppercase tracking-wide text-zinc-500 mb-2 flex items-center gap-1">
                    <History :size="12" /> Tentativas anteriores
                  </p>
                  <ul class="space-y-2">
                    <li v-for="t in doc.tentativas_anteriores" :key="t.id" class="rounded-lg bg-zinc-50 px-3 py-2 text-xs">
                      <span class="font-semibold text-zinc-700">{{ STATUS_LABELS[t.status] ?? t.status }}</span>
                      <span class="text-zinc-400"> · {{ formatDataHora(t.data) }}</span>
                      <p v-if="t.motivo" class="text-zinc-600 mt-0.5">{{ t.motivo }}</p>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
