<script setup lang="ts">
/**
 * @component NfseDocumentoDrawer
 * @description O detalhe de uma NFS-e, aberto ao clicar na linha da aba — no
 * mesmo molde da gaveta da NF-e (FiscalDocumentoDetailsDrawer): abas Visão
 * Geral / Serviços / Histórico, cartões de valor e ambiente, tomador, origem,
 * chave com copiar e as ações da nota autorizada.
 *
 * Pedido do Alan em 29/10/2026: a linha mostrava o motivo da recusa cortado
 * ("Empresa não habilitada para emissão de NFSe no am…") e não havia onde ver
 * o resto nem o que fazer. Em 30/10: "não tá legal" perto do detalhe da NF-e —
 * daí o mesmo visual. As ações (consultar, cancelar) são as da tabela: a gaveta
 * só pede.
 */
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useQuery, useQueryClient } from '@tanstack/vue-query';
import {
  AlertTriangle, Ban, Check, CheckCircle, Clock, Copy, ExternalLink, FileCode, FileText, History, Info,
  Loader2, Maximize2, Minimize2, RefreshCw, RotateCcw, User, Wrench, X,
} from 'lucide-vue-next';

import { useToast } from '@/shared/composables/useToast';
import { formatCurrency } from '@/shared/utils/finance';
import { formatDataHora } from '@/shared/utils/date.utils';
import { formatCPF, formatCNPJ } from '@/shared/utils/document.utils';
import { nfseService } from '../../services/nfse.service';
import { fiscalKeys, STATUS_COLORS, STATUS_LABELS } from '../../constants/fiscal.constants';
import { formatarCodigoNacional } from '../../utils/nfse.utils';
import { abrirArquivo } from '../../utils/abrirArquivo';
import { ORIGEM_NFSE, salvarDocumentoFiscal } from '../../utils/salvarDocumentoFiscal';
import { useNfseTentarDeNovoMutation } from '../../composables/useNfse';
import { ehNotaRepetida, mensagemNotaRepetida } from '../../utils/notaRepetida';

const props = defineProps<{ documentoId: number | null }>();
const emit = defineEmits<{
  close: [];
  consultar: [id: number];
  cancelar: [id: number];
  /** A nova tentativa é outro documento: a gaveta passa a mostrá-lo. */
  trocar: [id: number];
}>();

const aberto = computed(() => props.documentoId != null);
const toast = useToast();
const isExpanded = ref(false);
const activeTab = ref<'geral' | 'servicos' | 'historico'>('geral');

const router = useRouter();
function abrirOs(numero: string) {
  emit('close');
  router.push({ name: 'services', query: { os: numero } });
}

const { data: doc, isLoading, isError } = useQuery({
  // Debaixo de `nfseDocumentos`: consultar e cancelar já invalidam a gaveta.
  queryKey: computed(() => [...fiscalKeys.nfseDocumentos(), 'detalhe', props.documentoId] as const),
  queryFn: () => nfseService.obterDocumento(props.documentoId!),
  enabled: aberto,
});

// DANFSe e XML pelo "Salvar como", como na NF-e. Depois de salvar, o arquivo
// pode ter sido guardado no disco agora: recarrega para o selo mudar.
const queryClient = useQueryClient();
const baixando = ref<'pdf' | 'xml' | null>(null);
async function salvar(extensao: 'pdf' | 'xml') {
  if (!doc.value) return;
  baixando.value = extensao;
  try {
    await salvarDocumentoFiscal(doc.value, extensao, ORIGEM_NFSE);
    queryClient.invalidateQueries({ queryKey: fiscalKeys.nfseDocumentos() });
  } finally {
    baixando.value = null;
  }
}

// "Tentar de novo" (30/10): como o "Reemitir" da NF-e. Relê a OS e o cadastro,
// então o que o lojista corrigiu depois da recusa vai junto.
const tentarMutation = useNfseTentarDeNovoMutation();
/** A plataforma achou nota igual (409): a mensagem dela, e o lojista confirma ou desiste. */
const confirmarRepetida = ref<string | null>(null);
async function tentarDeNovo(confirmar = false) {
  if (!doc.value) return;
  try {
    const r = await tentarMutation.mutateAsync({ id: doc.value.id, confirmar });
    confirmarRepetida.value = null;
    activeTab.value = 'geral';
    emit('trocar', r.documento_id);
  } catch (e) {
    confirmarRepetida.value = ehNotaRepetida(e) ? mensagemNotaRepetida(e) : null;
  }
}

function coresDe(status: string) {
  return STATUS_COLORS[status] ?? { bg: 'bg-zinc-100', text: 'text-zinc-600', border: 'border-zinc-200' };
}

const icone = computed(() => {
  switch (doc.value?.status) {
    case 'AUTORIZADA': return CheckCircle;
    case 'CANCELADA':
    case 'NAO_TRANSMITIDA': return Ban;
    case 'PENDENTE':
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

const nomeAmbiente = computed(() => (doc.value?.ambiente === 1 ? 'Produção' : 'Homologação (teste)'));

/** A atual primeiro, depois as que ela substituiu — como o histórico da NF-e. */
const linhaDoTempo = computed(() => {
  if (!doc.value) return [];
  return [
    { id: doc.value.id, status: doc.value.status, motivo: doc.value.motivo, data: doc.value.data_emissao },
    ...doc.value.tentativas_anteriores,
  ];
});

// --- Copiar ---
const copiado = ref<'chave' | 'codigo' | 'diagnostico' | null>(null);
async function copiar(texto: string | null | undefined, qual: 'chave' | 'codigo' | 'diagnostico', aviso: string) {
  if (!texto) return;
  try {
    await navigator.clipboard.writeText(texto);
    copiado.value = qual;
    toast.success(aviso);
    setTimeout(() => { copiado.value = null; }, 2000);
  } catch {
    toast.error('Falha ao copiar');
  }
}

/** O que o suporte precisa ver, num bloco só. */
const textoDiagnostico = computed(() => {
  const d = doc.value;
  if (!d) return '';
  return [
    `NFS-e #${d.id} — ${STATUS_LABELS[d.status] ?? d.status}`,
    d.numero_os ? `OS: ${d.numero_os}` : 'Avulsa',
    `Ambiente: ${nomeAmbiente.value}`,
    d.ref ? `Referência: ${d.ref}` : null,
    d.codigo_status ? `Código: ${d.codigo_status}` : null,
    d.motivo ? `Motivo: ${d.motivo}` : null,
    d.dica ? `Como resolver: ${d.dica}` : null,
  ].filter(Boolean).join('\n');
});
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="aberto" class="fixed inset-0 z-50 overflow-hidden" data-nfse-detalhe>
        <div class="absolute inset-0 bg-black/30 backdrop-blur-sm transition-opacity" @click="emit('close')" />

        <div class="absolute inset-y-0 right-0 flex max-w-full pl-6">
          <div :class="['w-screen transition-all duration-300 ease-in-out', isExpanded ? 'max-w-4xl' : 'max-w-2xl']">
            <div class="flex h-full flex-col bg-white shadow-2xl">
              <!-- Cabeçalho -->
              <div class="flex items-center justify-between border-b border-zinc-200 bg-zinc-50/80 px-6 py-4">
                <div class="flex items-center gap-3">
                  <div
                    v-if="doc"
                    :class="[
                      'flex h-10 w-10 items-center justify-center rounded-xl border shadow-2xs',
                      coresDe(doc.status).bg, coresDe(doc.status).text, coresDe(doc.status).border,
                    ]"
                  >
                    <component :is="icone" class="h-5 w-5" :class="{ 'animate-spin': doc.status === 'PROCESSANDO' }" />
                  </div>
                  <div>
                    <div class="flex items-center gap-2.5">
                      <h2 class="text-lg font-bold text-zinc-900">Detalhes da NFS-e</h2>
                      <span
                        v-if="doc"
                        :class="['rounded-full px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wider', coresDe(doc.status).bg, coresDe(doc.status).text]"
                      >
                        {{ STATUS_LABELS[doc.status] ?? doc.status }}
                      </span>
                    </div>
                    <p v-if="doc" class="text-xs text-zinc-500 mt-0.5">
                      Nº {{ doc.numero ?? '-' }}
                      <template v-if="doc.numero_os"> · {{ doc.numero_os }}</template>
                      <template v-else> · Avulsa</template>
                    </p>
                  </div>
                </div>

                <div class="flex items-center gap-1.5">
                  <button
                    type="button"
                    class="rounded-lg p-2 text-zinc-400 transition-colors hover:bg-zinc-200 hover:text-zinc-700 cursor-pointer"
                    :title="isExpanded ? 'Reduzir painel' : 'Expandir painel'"
                    @click="isExpanded = !isExpanded"
                  >
                    <component :is="isExpanded ? Minimize2 : Maximize2" class="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    class="rounded-lg p-2 text-zinc-400 transition-colors hover:bg-zinc-200 hover:text-zinc-700 cursor-pointer"
                    @click="emit('close')"
                  >
                    <X class="h-5 w-5" />
                  </button>
                </div>
              </div>

              <div v-if="isLoading" class="flex flex-1 items-center justify-center">
                <div class="text-center">
                  <Loader2 class="mx-auto h-8 w-8 animate-spin text-brand-primary" />
                  <p class="mt-2 text-sm text-zinc-500 font-medium">Carregando detalhes da NFS-e...</p>
                </div>
              </div>
              <div v-else-if="isError || !doc" class="flex flex-1 items-center justify-center text-sm text-zinc-500">
                Não foi possível carregar esta NFS-e.
              </div>

              <div v-else class="flex flex-1 flex-col overflow-hidden">
                <!-- Abas -->
                <div class="px-6 pt-4 pb-4 border-b border-zinc-200/80 bg-white">
                  <div class="flex items-center gap-1.5 bg-zinc-100/90 p-1.5 rounded-xl border border-zinc-200/80">
                    <button
                      v-for="aba in [
                        { id: 'geral', rotulo: 'Visão Geral', icone: Info, total: 0 },
                        { id: 'servicos', rotulo: 'Serviços', icone: Wrench, total: doc.itens.length },
                        { id: 'historico', rotulo: 'Histórico', icone: History, total: linhaDoTempo.length },
                      ] as const"
                      :key="aba.id"
                      type="button"
                      class="flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer"
                      :class="activeTab === aba.id ? 'bg-white text-zinc-900 shadow-sm font-bold' : 'text-zinc-500 hover:text-zinc-900 hover:bg-white/60'"
                      @click="activeTab = aba.id"
                    >
                      <component :is="aba.icone" class="h-4 w-4" />
                      <span>{{ aba.rotulo }}</span>
                      <span v-if="aba.total" class="rounded-full bg-zinc-200 px-1.5 text-[10px] text-zinc-700 font-bold">
                        {{ aba.total }}
                      </span>
                    </button>
                  </div>
                </div>

                <div class="flex-1 overflow-y-auto p-6 space-y-6">
                  <!-- ABA 1: VISÃO GERAL -->
                  <div v-show="activeTab === 'geral'" class="space-y-5">
                    <!-- Sem retorno ainda -->
                    <div v-if="podeConsultar" class="rounded-2xl border border-blue-200 bg-blue-50/70 p-4.5 shadow-sm space-y-3">
                      <div class="flex items-center justify-between gap-3">
                        <div class="flex items-center gap-2.5">
                          <Clock class="h-5 w-5 text-blue-600 animate-pulse" />
                          <h4 class="text-sm font-bold text-blue-950">Aguardando o retorno da prefeitura</h4>
                        </div>
                        <span class="rounded-md bg-blue-100 border border-blue-200 px-2 py-0.5 text-[11px] font-bold text-blue-800 uppercase tracking-wider">
                          Em processamento
                        </span>
                      </div>
                      <p v-if="doc.motivo" class="text-xs text-blue-900 leading-relaxed whitespace-pre-line" data-motivo>{{ doc.motivo }}</p>
                      <p v-else class="text-xs text-blue-900 leading-relaxed">
                        A nota foi enviada e ainda não voltou autorizada. Consulte para ver se já foi processada.
                      </p>
                      <button
                        type="button"
                        class="flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white shadow-sm hover:bg-blue-700 transition-colors cursor-pointer"
                        @click="emit('consultar', doc.id)"
                      >
                        <RefreshCw class="h-4 w-4" /> Consultar o resultado
                      </button>
                    </div>

                    <!-- Recusa: o motivo inteiro e o que fazer -->
                    <div
                      v-if="recusada"
                      class="relative overflow-hidden rounded-2xl border border-rose-200/90 bg-linear-to-b from-rose-50/40 via-white to-rose-50/20 p-5 shadow-xs"
                    >
                      <div class="absolute top-0 left-0 right-0 h-1.5 bg-rose-500" />
                      <div class="flex items-center justify-between gap-3 mb-3 pt-1">
                        <div class="flex items-center gap-2.5">
                          <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-100 text-rose-600 shadow-2xs">
                            <AlertTriangle class="h-4.5 w-4.5" />
                          </div>
                          <span class="inline-block rounded-md bg-rose-50 border border-rose-200 px-2.5 py-0.5 text-[10px] font-bold text-rose-700 uppercase tracking-wider">
                            {{ STATUS_LABELS[doc.status] ?? doc.status }}
                          </span>
                        </div>
                        <button
                          type="button"
                          class="inline-flex items-center gap-1.5 rounded-lg border border-zinc-200 bg-white px-2.5 py-1 text-xs font-semibold text-zinc-600 shadow-2xs transition-colors hover:bg-zinc-50 hover:text-zinc-900 cursor-pointer"
                          @click="copiar(textoDiagnostico, 'diagnostico', 'Diagnóstico copiado para a área de transferência!')"
                        >
                          <Check v-if="copiado === 'diagnostico'" class="h-3.5 w-3.5 text-emerald-600" />
                          <Copy v-else class="h-3.5 w-3.5 text-zinc-400" />
                          <span>{{ copiado === 'diagnostico' ? 'Copiado!' : 'Copiar Diagnóstico' }}</span>
                        </button>
                      </div>

                      <h4 class="text-sm font-bold text-zinc-900 tracking-tight">A NFS-e não saiu</h4>

                      <div
                        v-if="doc.motivo"
                        class="mt-3.5 rounded-xl bg-zinc-50 border border-zinc-200/70 p-3 text-xs leading-relaxed font-mono text-zinc-700 whitespace-pre-line"
                        data-motivo
                      >
                        <span class="text-[10px] uppercase font-bold text-zinc-400 block mb-1 font-sans tracking-wider">
                          Retorno da emissora<template v-if="doc.codigo_status"> · código {{ doc.codigo_status }}</template>
                        </span>
                        {{ doc.motivo }}
                      </div>

                      <div v-if="doc.dica" class="mt-3.5 rounded-xl bg-amber-50/60 border border-amber-200/70 p-3.5 flex items-start gap-2.5" data-dica>
                        <div class="h-5 w-5 rounded-full bg-amber-100 flex items-center justify-center shrink-0 text-amber-700 text-xs font-bold mt-0.5">
                          💡
                        </div>
                        <p class="text-xs text-amber-950 leading-relaxed">
                          <strong class="font-bold text-amber-900">Como resolver:</strong>
                          {{ doc.dica }}
                        </p>
                      </div>

                      <!-- A plataforma achou nota igual: confirmar antes de enviar -->
                      <div
                        v-if="confirmarRepetida"
                        class="mt-3.5 rounded-xl border border-amber-300 bg-amber-50 p-3.5 space-y-2.5"
                        data-confirmar-repetida
                      >
                        <p class="text-xs text-amber-950 leading-relaxed">
                          {{ confirmarRepetida }} Nada foi enviado. Se é outro serviço, envie mesmo assim;
                          se é a mesma nota, confira na lista antes.
                        </p>
                        <div class="flex gap-2">
                          <button
                            type="button"
                            class="rounded-lg bg-amber-600 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-amber-700 disabled:opacity-50 cursor-pointer"
                            :disabled="tentarMutation.isPending.value"
                            @click="tentarDeNovo(true)"
                          >
                            Enviar mesmo assim
                          </button>
                          <button
                            type="button"
                            class="rounded-lg px-3 py-1.5 text-xs text-zinc-600 hover:bg-zinc-100 cursor-pointer"
                            @click="confirmarRepetida = null"
                          >
                            Desistir
                          </button>
                        </div>
                      </div>

                      <div class="mt-4 flex flex-wrap items-center gap-2.5 pt-1">
                        <button
                          v-if="doc.pode_tentar_de_novo"
                          type="button"
                          data-testid="btn-tentar-de-novo"
                          :disabled="tentarMutation.isPending.value"
                          class="inline-flex items-center gap-2 rounded-xl bg-brand-primary px-4 py-2 text-xs font-bold text-white shadow-xs hover:opacity-90 transition-all cursor-pointer disabled:opacity-50"
                          @click="tentarDeNovo()"
                        >
                          <RotateCcw class="h-3.5 w-3.5" :class="{ 'animate-spin': tentarMutation.isPending.value }" />
                          <span>{{ tentarMutation.isPending.value ? 'Enviando à prefeitura...' : 'Tentar de novo' }}</span>
                        </button>
                        <p v-else-if="!doc.numero_os" class="text-xs text-zinc-500">
                          NFS-e avulsa: corrija e emita uma nova em “Emitir NFS-e avulsa”.
                        </p>
                        <p v-else class="text-xs text-zinc-500">
                          Esta tentativa já foi substituída por outra mais nova — veja a aba Histórico ou a lista.
                        </p>
                      </div>
                    </div>

                    <!-- Valor e ambiente -->
                    <div class="grid grid-cols-2 gap-3">
                      <div class="rounded-xl border border-zinc-200 bg-white p-4 shadow-2xs">
                        <span class="text-[10px] font-bold uppercase tracking-wider text-zinc-400 block">Valor Total da Nota</span>
                        <p class="mt-1 text-xl font-bold text-emerald-600">
                          {{ doc.valor_total != null ? formatCurrency(doc.valor_total) : 'R$ 0,00' }}
                        </p>
                      </div>
                      <div class="rounded-xl border border-zinc-200 bg-white p-4 shadow-2xs">
                        <span class="text-[10px] font-bold uppercase tracking-wider text-zinc-400 block">Ambiente de Emissão</span>
                        <div class="mt-1 flex items-center gap-2">
                          <span :class="['inline-flex h-2.5 w-2.5 rounded-full', doc.ambiente === 1 ? 'bg-emerald-500' : 'bg-amber-500']" />
                          <p class="text-base font-bold text-zinc-800">{{ nomeAmbiente }}</p>
                        </div>
                      </div>
                    </div>

                    <!-- Tomador -->
                    <div class="rounded-xl border border-zinc-200 bg-white p-4 shadow-2xs space-y-3">
                      <div class="flex items-center gap-2">
                        <User class="h-4 w-4 text-zinc-500" />
                        <span class="text-xs font-bold uppercase tracking-wider text-zinc-500">Tomador do Serviço</span>
                      </div>
                      <div class="rounded-lg bg-zinc-50 p-3">
                        <p class="text-sm font-bold text-zinc-900">{{ doc.tomador || 'Tomador não identificado' }}</p>
                        <p class="text-xs text-zinc-600 mt-0.5">
                          Documento:
                          <span class="font-mono font-medium">{{ documentoTomador || 'Sem CPF/CNPJ' }}</span>
                        </p>
                      </div>
                    </div>

                    <!-- Origem -->
                    <div class="rounded-xl border border-zinc-200 bg-white p-4 shadow-2xs space-y-3">
                      <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2">
                          <FileText class="h-4 w-4 text-zinc-500" />
                          <span class="text-xs font-bold uppercase tracking-wider text-zinc-500">Origem da Emissão</span>
                        </div>
                        <button
                          v-if="doc.numero_os"
                          type="button"
                          class="flex items-center gap-1 text-xs font-semibold text-brand-primary hover:underline cursor-pointer"
                          @click="abrirOs(doc.numero_os)"
                        >
                          <ExternalLink class="h-3.5 w-3.5" /> Abrir a OS
                        </button>
                      </div>
                      <div class="grid grid-cols-2 gap-2 text-xs text-zinc-600">
                        <div class="rounded-lg bg-zinc-50 p-2.5">
                          <span class="text-zinc-400 block text-[10px] uppercase font-semibold">Documento de Origem</span>
                          <span class="font-bold text-zinc-800 text-sm">{{ doc.numero_os ?? 'NFS-e avulsa' }}</span>
                        </div>
                        <div class="rounded-lg bg-zinc-50 p-2.5">
                          <span class="text-zinc-400 block text-[10px] uppercase font-semibold">Enviada em</span>
                          <span class="font-medium text-zinc-800">{{ doc.data_emissao ? formatDataHora(doc.data_emissao) : '-' }}</span>
                        </div>
                        <div v-if="doc.data_autorizacao" class="rounded-lg bg-zinc-50 p-2.5 col-span-2">
                          <span class="text-zinc-400 block text-[10px] uppercase font-semibold">Autorizada em</span>
                          <span class="font-medium text-zinc-800">{{ formatDataHora(doc.data_autorizacao) }}</span>
                        </div>
                      </div>
                    </div>

                    <!-- Chave, código de verificação e referência -->
                    <div class="rounded-xl border border-zinc-200 bg-white p-4 shadow-2xs space-y-3">
                      <div class="flex items-center justify-between">
                        <span class="text-xs font-bold uppercase tracking-wider text-zinc-500">Chave de Acesso</span>
                        <button
                          v-if="doc.chave_acesso"
                          type="button"
                          class="flex items-center gap-1 rounded px-2 py-1 text-xs text-zinc-600 hover:bg-zinc-100 transition-colors cursor-pointer"
                          @click="copiar(doc.chave_acesso, 'chave', 'Chave de acesso copiada!')"
                        >
                          <Check v-if="copiado === 'chave'" class="h-3.5 w-3.5 text-emerald-600" />
                          <Copy v-else class="h-3.5 w-3.5" />
                          <span>{{ copiado === 'chave' ? 'Copiado!' : 'Copiar Chave' }}</span>
                        </button>
                      </div>
                      <p class="break-all rounded-lg bg-zinc-50 p-3 font-mono text-xs text-zinc-800 leading-relaxed border border-zinc-100">
                        {{ doc.chave_acesso || 'Chave não gerada para esta tentativa.' }}
                      </p>

                      <div class="border-t border-zinc-100 pt-3 flex items-center justify-between text-xs">
                        <span class="font-semibold text-zinc-400 uppercase tracking-wider text-[10px]">Código de Verificação</span>
                        <span class="flex items-center gap-1.5">
                          <span class="font-mono font-medium text-zinc-800">{{ doc.codigo_verificacao || '-' }}</span>
                          <button
                            v-if="doc.codigo_verificacao"
                            type="button"
                            class="rounded p-1 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-700 cursor-pointer"
                            title="Copiar código de verificação"
                            @click="copiar(doc.codigo_verificacao, 'codigo', 'Código de verificação copiado!')"
                          >
                            <Check v-if="copiado === 'codigo'" class="h-3.5 w-3.5 text-emerald-600" />
                            <Copy v-else class="h-3.5 w-3.5" />
                          </button>
                        </span>
                      </div>
                      <div class="flex items-center justify-between text-xs">
                        <span class="font-semibold text-zinc-400 uppercase tracking-wider text-[10px]">Referência na Emissora</span>
                        <span class="font-mono text-zinc-600">{{ doc.ref ?? '-' }}</span>
                      </div>
                    </div>

                    <!-- Ações da nota autorizada -->
                    <div v-if="doc.status === 'AUTORIZADA'" class="space-y-2" data-arquivos>
                      <span class="text-xs font-bold uppercase tracking-wider text-zinc-400 block">Ações do Documento Autorizado</span>
                      <div class="grid grid-cols-2 gap-2">
                        <button
                          type="button"
                          data-testid="btn-baixar-pdf"
                          :disabled="baixando !== null || (!doc.url_pdf && !doc.pdf_local)"
                          class="flex items-center justify-center gap-2 rounded-xl border border-zinc-200 bg-white p-3 text-sm font-semibold text-zinc-700 shadow-2xs hover:bg-zinc-50 transition-colors disabled:opacity-40 cursor-pointer"
                          @click="salvar('pdf')"
                        >
                          <FileText class="h-4 w-4 text-rose-500" />
                          {{ baixando === 'pdf' ? 'Salvando…' : 'DANFSe (PDF)' }}
                        </button>
                        <button
                          type="button"
                          data-testid="btn-baixar-xml"
                          :disabled="baixando !== null || (!doc.url_xml && !doc.xml_local)"
                          class="flex items-center justify-center gap-2 rounded-xl border border-zinc-200 bg-white p-3 text-sm font-semibold text-zinc-700 shadow-2xs hover:bg-zinc-50 transition-colors disabled:opacity-40 cursor-pointer"
                          @click="salvar('xml')"
                        >
                          <FileCode class="h-4 w-4 text-blue-500" />
                          {{ baixando === 'xml' ? 'Salvando…' : 'XML' }}
                        </button>
                        <p
                          class="col-span-2 flex items-center gap-1.5 text-[11px]"
                          :class="doc.xml_local ? 'text-emerald-600' : 'text-zinc-400'"
                        >
                          <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="doc.xml_local ? 'bg-emerald-500' : 'bg-zinc-300'" />
                          {{
                            doc.xml_local
                              ? (doc.pdf_local
                                  ? 'XML e DANFSe guardados neste computador — abrem sem internet. O XML entra no backup.'
                                  : 'XML guardado neste computador — abre sem internet e entra no backup.')
                              : 'Arquivos ainda não guardados aqui; serão buscados na emissora.'
                          }}
                        </p>
                        <button
                          v-if="doc.url_consulta"
                          type="button"
                          class="flex items-center justify-center gap-2 rounded-xl border border-zinc-200 bg-white p-2.5 text-xs font-semibold text-zinc-700 hover:bg-zinc-50 transition-colors cursor-pointer"
                          @click="abrirArquivo(doc.url_consulta)"
                        >
                          <ExternalLink class="h-4 w-4" /> Ver no portal da NFS-e
                        </button>
                        <button
                          type="button"
                          data-testid="btn-cancelar"
                          :class="[
                            'flex items-center justify-center gap-2 rounded-xl border border-rose-200 bg-rose-50/50 p-2.5 text-xs font-semibold text-rose-700 hover:bg-rose-100 transition-colors cursor-pointer',
                            doc.url_consulta ? '' : 'col-span-2',
                          ]"
                          @click="emit('cancelar', doc.id)"
                        >
                          <Ban class="h-4 w-4" /> Cancelar NFS-e
                        </button>
                      </div>
                    </div>

                    <!-- Portal também para quem não está autorizada (ex.: cancelada) -->
                    <button
                      v-else-if="doc.url_consulta"
                      type="button"
                      class="inline-flex items-center gap-1.5 rounded-xl border border-zinc-200 px-3 py-2 text-xs font-semibold text-zinc-700 hover:bg-zinc-50 cursor-pointer"
                      @click="abrirArquivo(doc.url_consulta)"
                    >
                      <ExternalLink class="h-4 w-4" /> Ver no portal da NFS-e
                    </button>
                  </div>

                  <!-- ABA 2: SERVIÇOS -->
                  <div v-show="activeTab === 'servicos'" class="space-y-4">
                    <div>
                      <h4 class="text-xs font-bold uppercase tracking-wider text-zinc-500">Serviços da Nota</h4>
                      <p class="text-[11px] text-zinc-400 mt-0.5">O que foi declarado à prefeitura, com o código nacional de cada serviço.</p>
                    </div>
                    <div v-if="doc.itens.length" class="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-2xs">
                      <table class="w-full text-left text-xs">
                        <thead class="bg-zinc-50 text-[10px] font-bold uppercase text-zinc-400 border-b border-zinc-100">
                          <tr>
                            <th class="py-2.5 px-3">Serviço</th>
                            <th class="py-2.5 px-2">Código</th>
                            <th class="py-2.5 px-2 text-right">Desconto</th>
                            <th class="py-2.5 px-3 text-right">Valor</th>
                          </tr>
                        </thead>
                        <tbody class="divide-y divide-zinc-100">
                          <tr v-for="(item, i) in doc.itens" :key="i">
                            <td class="py-2.5 px-3 font-medium text-zinc-900">{{ item.descricao }}</td>
                            <td class="py-2.5 px-2 font-mono">
                              <span v-if="item.codigo" class="rounded bg-zinc-100 px-1.5 py-0.5 text-[11px] text-zinc-700">
                                {{ formatarCodigoNacional(item.codigo) }}
                              </span>
                              <span v-else class="text-zinc-400">-</span>
                            </td>
                            <td class="py-2.5 px-2 text-right text-zinc-600">{{ item.desconto ? formatCurrency(item.desconto) : '-' }}</td>
                            <td class="py-2.5 px-3 text-right font-bold text-zinc-900">{{ formatCurrency(item.valor) }}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <div v-else class="rounded-xl border border-zinc-200 bg-zinc-50/50 p-8 text-center">
                      <Wrench class="mx-auto h-8 w-8 text-zinc-400" />
                      <p class="mt-2 text-xs font-medium text-zinc-500">Nenhum serviço detalhado disponível para esta nota.</p>
                    </div>
                  </div>

                  <!-- ABA 3: HISTÓRICO -->
                  <div v-show="activeTab === 'historico'" class="space-y-4">
                    <h4 class="text-xs font-bold uppercase tracking-wider text-zinc-500">Linha do Tempo de Emissão</h4>
                    <div class="relative space-y-0">
                      <div v-for="(t, index) in linhaDoTempo" :key="t.id" class="relative flex gap-3.5 pb-5 last:pb-0">
                        <div v-if="index !== linhaDoTempo.length - 1" class="absolute left-2.75 top-6 bottom-0 w-px bg-zinc-200" />
                        <div
                          class="relative z-10 mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 bg-white"
                          :class="coresDe(t.status).border"
                        >
                          <div
                            class="h-2 w-2 rounded-full"
                            :class="{
                              'bg-emerald-500': t.status === 'AUTORIZADA',
                              'bg-rose-500': ['REJEITADA', 'DENEGADA', 'NAO_TRANSMITIDA', 'ERRO'].includes(t.status),
                              'bg-zinc-400': t.status === 'CANCELADA',
                              'bg-blue-500': ['PROCESSANDO', 'PENDENTE', 'INDETERMINADA'].includes(t.status),
                            }"
                          />
                        </div>
                        <div class="min-w-0 flex-1 rounded-xl border border-zinc-200 bg-white p-3 shadow-2xs">
                          <div class="flex items-center justify-between gap-2">
                            <span :class="['rounded-full px-2 py-0.5 text-[10px] font-bold uppercase', coresDe(t.status).bg, coresDe(t.status).text]">
                              {{ STATUS_LABELS[t.status] ?? t.status }}<template v-if="index === 0"> · atual</template>
                            </span>
                            <span class="text-[11px] text-zinc-400">{{ t.data ? formatDataHora(t.data) : '-' }}</span>
                          </div>
                          <p
                            v-if="t.motivo"
                            class="mt-2 rounded-lg bg-zinc-50 p-2.5 text-xs leading-relaxed text-zinc-700 font-mono border border-zinc-100"
                          >
                            {{ t.motivo }}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.2s ease;
}
.drawer-enter-active > div:last-child,
.drawer-leave-active > div:last-child {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}
.drawer-enter-from > div:last-child,
.drawer-leave-to > div:last-child {
  transform: translateX(100%);
}
</style>
