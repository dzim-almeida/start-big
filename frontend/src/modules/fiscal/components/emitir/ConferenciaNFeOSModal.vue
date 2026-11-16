<script setup lang="ts">
/**
 * @component ConferenciaNFeOSModal
 * @description Conferência da NF-e das peças de uma OS antes de transmitir,
 * com o campo "CFOP desta nota".
 *
 * C2 de docs/nfe-cfop-e-notas-da-os-plano.md. Até aqui o botão "Emitir NF-e
 * das peças" do cartão da OS transmitia direto, sem mostrar o que ia na nota —
 * e sem conferência não há onde trocar o CFOP. Quem abre já passou pelas
 * pendências (`useEmitirFiscal().conferirOS`).
 */
import { ref, watch } from 'vue';
import { Loader2, Package } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { formatCurrency } from '@/shared/utils/finance';

import CfopDaNotaCampo from './CfopDaNotaCampo.vue';
import { useFiscalPreviewMutation } from '../../composables/useFiscalPreviewMutation';
import { useFiscalEmitirNfeMutation } from '../../composables/useFiscalEmitirNfeMutation';
import type { EmissaoNFeRequest, EmissaoPreviewResponse } from '../../types/fiscal.types';

const props = defineProps<{ isOpen: boolean; numeroOs: string }>();
const emit = defineEmits<{ (e: 'close'): void; (e: 'emitida'): void }>();

const previewMutation = useFiscalPreviewMutation();
const emitirMutation = useFiscalEmitirNfeMutation();

const previa = ref<EmissaoPreviewResponse | null>(null);
const trocas = ref<Record<string, string>>({});
const comoPadrao = ref(false);
let trocasDaPrevia: Record<string, string> = {};

function corpo(): EmissaoNFeRequest {
  const t = Object.keys(trocas.value).length ? trocas.value : undefined;
  return { numero_os: props.numeroOs, trocar_cfop: t, cfop_como_padrao: t ? comoPadrao.value : undefined };
}

async function carregar() {
  try {
    previa.value = await previewMutation.mutateAsync(corpo());
    trocasDaPrevia = { ...trocas.value };
  } catch {
    // A recusa já virou toast. Sem prévia nenhuma não há o que conferir.
    trocas.value = { ...trocasDaPrevia };
    if (!previa.value) emit('close');
  }
}

watch(
  () => props.isOpen,
  (aberto) => {
    if (!aberto) return;
    previa.value = null;
    trocas.value = {};
    trocasDaPrevia = {};
    comoPadrao.value = false;
    carregar();
  },
  { immediate: true },
);

function confirmar() {
  emitirMutation.mutate(corpo(), {
    onSuccess: () => emit('emitida'),
  });
}

function fechar() {
  if (emitirMutation.isPending.value) return;
  emit('close');
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Conferir NF-e das peças"
    :subtitle="`${numeroOs} · confira antes de transmitir para a SEFAZ.`"
    size="lg"
    @close="fechar"
  >
    <div v-if="!previa" class="flex flex-col items-center justify-center p-8 text-zinc-400">
      <Loader2 class="w-8 h-8 animate-spin mb-2" />
      <p class="text-sm">Montando a nota...</p>
    </div>

    <div v-else class="space-y-4" data-conferencia-os>
      <div class="rounded-xl border border-zinc-200 bg-white overflow-hidden">
        <div class="flex items-center gap-2 px-4 py-2.5 bg-zinc-50 border-b border-zinc-100">
          <Package :size="14" class="text-zinc-400" />
          <h4 class="text-xs font-semibold uppercase tracking-wider text-zinc-500">Peças</h4>
          <span class="ml-auto text-xs text-zinc-500 truncate">{{ previa.destinatario.nome }}</span>
        </div>
        <div class="max-h-48 overflow-y-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-zinc-50/80 border-b border-zinc-100 sticky top-0">
              <tr>
                <th class="px-4 py-2 font-semibold text-zinc-500">Descrição</th>
                <th class="px-4 py-2 font-semibold text-zinc-500 text-center">Qtd</th>
                <th class="px-4 py-2 font-semibold text-zinc-500 text-center">CFOP</th>
                <th class="px-4 py-2 font-semibold text-zinc-500 text-center">CST/CSOSN</th>
                <th class="px-4 py-2 font-semibold text-zinc-500 text-right">Total</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-zinc-50">
              <tr v-for="item in previa.itens" :key="item.numero_item">
                <td class="px-4 py-2 text-zinc-800 font-medium truncate max-w-48" :title="item.nome">{{ item.nome }}</td>
                <td class="px-4 py-2 text-zinc-600 text-center">{{ item.quantidade }}</td>
                <td class="px-4 py-2 text-center font-mono text-zinc-600">{{ item.cfop }}</td>
                <td class="px-4 py-2 text-center font-mono text-zinc-600">{{ item.cst_csosn || '—' }}</td>
                <td class="px-4 py-2 text-right font-mono font-semibold text-zinc-800">{{ formatCurrency(item.valor_total) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="flex justify-between items-center px-4 py-2.5 border-t border-zinc-100">
          <span class="text-sm font-semibold text-zinc-700">Valor da nota</span>
          <span class="text-base font-bold text-brand-primary font-mono">{{ formatCurrency(previa.totais.valor_nota) }}</span>
        </div>
      </div>

      <CfopDaNotaCampo
        v-model:trocas="trocas"
        v-model:como-padrao="comoPadrao"
        :grupos="previa.grupos_cfop ?? []"
        :disabled="previewMutation.isPending.value || emitirMutation.isPending.value"
        @alterou="carregar"
      />
    </div>

    <div class="mt-6 flex justify-end gap-3 pt-4 border-t border-zinc-100">
      <BaseButton variant="secondary" :disabled="emitirMutation.isPending.value" @click="fechar">Voltar</BaseButton>
      <BaseButton
        variant="primary"
        :disabled="!previa || previewMutation.isPending.value || emitirMutation.isPending.value"
        :is-loading="emitirMutation.isPending.value"
        @click="confirmar"
      >
        Confirmar emissão
      </BaseButton>
    </div>
  </BaseModal>
</template>
