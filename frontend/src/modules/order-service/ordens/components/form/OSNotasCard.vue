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
import { FileText, Package, Wrench, Send, Eye, Ban, MessageCircle } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import PendenciasFiscaisModal from '@/shared/components/commons/PendenciasFiscaisModal.vue';
import { useEmitirFiscal } from '@/shared/composables/useEmitirFiscal';
import { formatCurrency } from '@/shared/utils/finance';
import { STATUS_COLORS, STATUS_LABELS } from '@/modules/fiscal/constants/fiscal.constants';
import NfseEmitirModal from '@/modules/fiscal/components/nfse/NfseEmitirModal.vue';
import NfseDocumentoDrawer from '@/modules/fiscal/components/nfse/NfseDocumentoDrawer.vue';
import FiscalDocumentoDetailsDrawer from '@/modules/fiscal/components/detalhes/FiscalDocumentoDetailsDrawer.vue';
import ConferenciaNFeOSModal from '@/modules/fiscal/components/emitir/ConferenciaNFeOSModal.vue';
import FiscalCancelarModal from '@/modules/fiscal/components/detalhes/FiscalCancelarModal.vue';
import NfseCancelarModal from '@/modules/fiscal/components/nfse/NfseCancelarModal.vue';
import { formatDataHora } from '@/shared/utils/date.utils';
import { useToast } from '@/shared/composables/useToast';
import { abrirArquivo } from '@/modules/fiscal/utils/abrirArquivo';
import { useNfseConsultarMutation } from '@/modules/fiscal/composables/useNfse';
import { getMensagemDaNota, getNotasDaOs, type NotaDaOs } from '../../services/orderServiceFiscal.service';

const props = defineProps<{ osNumero: string }>();

const queryClient = useQueryClient();
const chave = computed(() => ['os-notas-fiscais', props.osNumero] as const);
const { data: notas } = useQuery({
  queryKey: chave,
  queryFn: () => getNotasDaOs(props.osNumero),
  staleTime: 15_000,
});
const recarregar = () => queryClient.invalidateQueries({ queryKey: chave.value });

// Peças → NF-e: pendências primeiro; sem pendência, a conferência (com o
// CFOP desta nota, C2 de docs/nfe-cfop-e-notas-da-os-plano.md) e só então emite.
const { pendencias, pendenciasModalOpen, isVerificando, conferirOS } = useEmitirFiscal();
const conferindoNfe = ref(false);
async function emitirNfe() {
  if (await conferirOS(props.osNumero)) conferindoNfe.value = true;
}
function fecharConferencia() {
  conferindoNfe.value = false;
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

// Cancelar pela OS (O1 de docs/nfe-cfop-e-notas-da-os-plano.md). Quem diz se
// ainda dá é o backend (`pode_cancelar`); a tela só mostra o prazo.
const cancelandoNfe = ref<number | null>(null);
function fecharCancelarNfe() {
  cancelandoNfe.value = null;
  recarregar();
}
const cancelandoNfse = ref<{ id: number; numero: number | null; numero_os: string } | null>(null);
function cancelarNfse(id: number) {
  const doc = notas.value?.servico.documentos.find((d) => d.id === id);
  nfseAberta.value = null;
  cancelandoNfse.value = { id, numero: doc?.numero != null ? Number(doc.numero) : null, numero_os: props.osNumero };
}
function fecharCancelarNfse() {
  cancelandoNfse.value = null;
  recarregar();
}

// Mandar ao cliente (O2): o texto vem pronto do backend (número, valor, chave
// ou link público do DANFSe). Sem celular no cadastro, copia o texto.
const toast = useToast();
const enviando = ref<number | null>(null);
async function mandarWhatsapp(documentoId: number) {
  enviando.value = documentoId;
  try {
    const { texto, telefone } = await getMensagemDaNota(props.osNumero, documentoId);
    if (telefone) {
      await abrirArquivo(`https://wa.me/${telefone}?text=${encodeURIComponent(texto)}`);
      return;
    }
    let copiou = false;
    try {
      await navigator.clipboard.writeText(texto);
      copiou = true;
    } catch {
      copiou = false;
    }
    toast.warning(
      'Cliente sem celular cadastrado',
      copiou ? 'O texto da nota foi copiado: cole na conversa com ele.' : 'Cadastre o celular no cliente.',
    );
  } catch {
    toast.error('Não foi possível montar a mensagem da nota.');
  } finally {
    enviando.value = null;
  }
}

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
          <span v-if="notas.pecas.documento" class="flex items-center gap-3">
            <button
              v-if="notas.pecas.documento.status === 'AUTORIZADA'"
              type="button"
              class="text-xs font-semibold text-emerald-700 hover:underline flex items-center gap-1 disabled:opacity-50"
              :disabled="enviando === notas.pecas.documento.id"
              data-whatsapp-nfe
              @click="mandarWhatsapp(notas.pecas.documento!.id)"
            >
              <MessageCircle :size="12" /> WhatsApp
            </button>
            <button
              v-if="notas.pecas.documento.pode_cancelar"
              type="button"
              class="text-xs font-semibold text-red-600 hover:underline flex items-center gap-1"
              data-cancelar-nfe
              @click="cancelandoNfe = notas.pecas.documento!.id"
            >
              <Ban :size="12" /> Cancelar
            </button>
            <button
              type="button"
              class="text-xs font-semibold text-brand-primary hover:underline flex items-center gap-1"
              @click="nfeAberta = notas.pecas.documento!.id"
            >
              <Eye :size="12" /> Ver detalhes
            </button>
          </span>
        </div>
        <p v-if="notas.pecas.documento?.pode_cancelar && notas.pecas.documento.cancelar_ate" class="text-[11px] text-zinc-500">
          Dá para cancelar até {{ formatDataHora(notas.pecas.documento.cancelar_ate) }}. Depois, só com nota de devolução.
        </p>
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
          <span class="flex items-center gap-3">
            <button
              v-if="doc.status === 'AUTORIZADA'"
              type="button"
              class="text-xs font-semibold text-emerald-700 hover:underline flex items-center gap-1 disabled:opacity-50"
              :disabled="enviando === doc.id"
              data-whatsapp-nfse
              @click="mandarWhatsapp(doc.id)"
            >
              <MessageCircle :size="12" /> WhatsApp
            </button>
            <button
              v-if="doc.pode_cancelar"
              type="button"
              class="text-xs font-semibold text-red-600 hover:underline flex items-center gap-1"
              data-cancelar-nfse
              @click="cancelarNfse(doc.id)"
            >
              <Ban :size="12" /> Cancelar
            </button>
            <button type="button" class="text-xs font-semibold text-brand-primary hover:underline flex items-center gap-1" @click="nfseAberta = doc.id">
              <Eye :size="12" /> Ver detalhes
            </button>
          </span>
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
    <ConferenciaNFeOSModal
      v-if="conferindoNfe"
      :is-open="conferindoNfe"
      :numero-os="osNumero"
      @close="fecharConferencia"
      @emitida="fecharConferencia"
    />
    <NfseDocumentoDrawer
      :documento-id="nfseAberta"
      @close="nfseAberta = null; recarregar()"
      @consultar="consultarNfse.mutate($event)"
      @cancelar="cancelarNfse($event)"
      @trocar="nfseAberta = $event; recarregar()"
    />
    <FiscalCancelarModal
      v-if="notas.pecas.modulo"
      :is-open="cancelandoNfe !== null"
      :documento-ids="cancelandoNfe !== null ? [cancelandoNfe] : []"
      @close="fecharCancelarNfe"
    />
    <NfseCancelarModal :documento="cancelandoNfse" @close="fecharCancelarNfse" />
    <FiscalDocumentoDetailsDrawer
      v-if="notas.pecas.modulo"
      :documento-id="nfeAberta"
      :is-open="nfeAberta !== null"
      @update:is-open="(v: boolean) => { if (!v) { nfeAberta = null; recarregar(); } }"
    />
  </div>
</template>
