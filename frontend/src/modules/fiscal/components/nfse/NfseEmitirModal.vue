<script setup lang="ts">
/**
 * @component NfseEmitirModal
 * @description Emitir a NFS-e da mão de obra de uma OS, em dois passos:
 * conferir (o que falta, ou a nota que vai sair) e emitir.
 *
 * Conferir ANTES é de propósito: a pendência aparece nomeada ("serviço sem
 * NBS") em vez de virar recusa do Sistema Nacional depois do envio.
 */
import { computed, ref, watch } from 'vue';
import { AlertCircle, CheckCircle2, Loader2, Search, Send } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import { formatCurrency } from '@/shared/utils/finance';
import { formatCPF, formatCNPJ } from '@/shared/utils/document.utils';
import type { PendenciaFiscal } from '@/shared/types/fiscal.types';

import { nfseService } from '../../services/nfse.service';
import { useNfseEmitirMutation } from '../../composables/useNfse';
import { formatarCodigoNacional, formatarNbs } from '../../utils/nfse.utils';
import type { NfsePreview } from '../../types/fiscal.types';

const props = defineProps<{ isOpen: boolean }>();
const emit = defineEmits<{ close: [] }>();

const numeroOs = ref('');
const conferindo = ref(false);
const erro = ref<string | null>(null);
const pendencias = ref<PendenciaFiscal[]>([]);
const preview = ref<NfsePreview | null>(null);

const emitirMutation = useNfseEmitirMutation();

watch(() => props.isOpen, (aberto) => {
  if (!aberto) {
    numeroOs.value = '';
    erro.value = null;
    pendencias.value = [];
    preview.value = null;
  }
});

// Trocar a OS invalida o que foi conferido para a anterior.
watch(numeroOs, () => {
  pendencias.value = [];
  preview.value = null;
  erro.value = null;
});

async function conferir() {
  const numero = numeroOs.value.trim();
  if (!numero) return;
  conferindo.value = true;
  erro.value = null;
  try {
    const verificacao = await nfseService.verificarOs(numero);
    pendencias.value = verificacao.pendencias;
    if (verificacao.completo) preview.value = await nfseService.previewOs(numero);
  } catch (e: any) {
    erro.value = e?.response?.status === 404
      ? 'Ordem de serviço não encontrada.'
      : e?.response?.data?.detail?.mensagem ?? 'Não foi possível conferir esta OS.';
  } finally {
    conferindo.value = false;
  }
}

async function emitir() {
  if (!preview.value) return;
  await emitirMutation.mutateAsync(preview.value.numero_os);
  emit('close');
}

const tomador = computed(() => {
  const dps = preview.value?.dps;
  if (!dps) return null;
  const documento = dps.cnpj_tomador ? formatCNPJ(dps.cnpj_tomador) : dps.cpf_tomador ? formatCPF(dps.cpf_tomador) : null;
  return { nome: dps.razao_social_tomador ?? 'Tomador não identificado', documento };
});

/** valor_servico vem em reais (formato da Focus); formatCurrency pede centavos. */
const emCentavos = (reais?: number) => Math.round((reais ?? 0) * 100);
</script>

<template>
  <BaseModal :is-open="isOpen" title="Emitir NFS-e" size="lg" @close="emit('close')">
    <div class="space-y-5">
      <p class="text-sm text-zinc-500">
        A NFS-e cobre a <strong>mão de obra</strong> da OS (os serviços aprovados). As peças continuam
        na NF-e.
      </p>

      <form class="flex items-end gap-2" @submit.prevent="conferir">
        <div class="flex-1">
          <BaseInput v-model="numeroOs" label="Número da OS" placeholder="Ex: OS-2026-000123" />
        </div>
        <BaseButton type="submit" variant="secondary" :disabled="!numeroOs.trim() || conferindo">
          <Loader2 v-if="conferindo" :size="16" class="mr-1.5 animate-spin" />
          <Search v-else :size="16" class="mr-1.5" />
          Conferir
        </BaseButton>
      </form>

      <div v-if="erro" class="flex items-start gap-2 p-3 rounded-xl bg-red-50 border border-red-200 text-sm text-red-700">
        <AlertCircle :size="16" class="mt-0.5 shrink-0" />
        <span>{{ erro }}</span>
      </div>

      <!-- O que falta, nomeado -->
      <div v-if="pendencias.length" class="p-4 rounded-xl bg-amber-50 border border-amber-200">
        <p class="text-sm font-semibold text-amber-800 mb-2">Antes de emitir, resolva:</p>
        <ul class="space-y-1.5" data-pendencias-nfse>
          <li v-for="(p, i) in pendencias" :key="i" class="text-sm text-amber-800 flex items-start gap-2">
            <AlertCircle :size="14" class="mt-0.5 shrink-0" />
            <span>
              <strong v-if="p.referencia_nome">{{ p.referencia_nome }}: </strong>{{ p.mensagem }}
            </span>
          </li>
        </ul>
      </div>

      <!-- A nota que vai sair -->
      <div v-if="preview" class="p-4 rounded-xl border border-zinc-200 bg-zinc-50/50 space-y-3" data-preview-nfse>
        <div class="flex items-center gap-2 text-emerald-700 text-sm font-semibold">
          <CheckCircle2 :size="16" /> Tudo certo para emitir
        </div>
        <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 text-sm">
          <div>
            <dt class="text-xs text-zinc-400">Tomador</dt>
            <dd class="text-zinc-800 font-medium">{{ tomador?.nome }}</dd>
            <dd v-if="tomador?.documento" class="text-xs text-zinc-500">{{ tomador.documento }}</dd>
          </div>
          <div>
            <dt class="text-xs text-zinc-400">Valor do serviço</dt>
            <dd class="text-zinc-800 font-semibold">{{ formatCurrency(emCentavos(preview.dps.valor_servico)) }}</dd>
            <dd v-if="preview.dps.desconto_incondicionado" class="text-xs text-zinc-500">
              desconto de {{ formatCurrency(emCentavos(preview.dps.desconto_incondicionado)) }}
            </dd>
          </div>
          <div>
            <dt class="text-xs text-zinc-400">Código de tributação nacional</dt>
            <dd class="text-zinc-800">{{ formatarCodigoNacional(preview.dps.codigo_tributacao_nacional_iss) }}</dd>
          </div>
          <div>
            <dt class="text-xs text-zinc-400">NBS</dt>
            <dd class="text-zinc-800">{{ formatarNbs(preview.dps.codigo_nbs) || '—' }}</dd>
          </div>
          <div class="sm:col-span-2">
            <dt class="text-xs text-zinc-400">Descrição</dt>
            <dd class="text-zinc-700">{{ preview.dps.descricao_servico }}</dd>
          </div>
        </dl>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-end gap-3 w-full">
        <BaseButton type="button" variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton
          type="button"
          variant="primary"
          :disabled="!preview || emitirMutation.isPending.value"
          :is-loading="emitirMutation.isPending.value"
          @click="emitir"
        >
          <Send :size="16" class="mr-1.5" />
          Emitir NFS-e
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
