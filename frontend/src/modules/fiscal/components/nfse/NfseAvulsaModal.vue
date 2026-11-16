<script setup lang="ts">
/**
 * @component NfseAvulsaModal
 * @description NFS-e de um serviço que não passou por OS (docs/nfse-fase2-plano.md,
 * G4). Mesmo ritmo do NfseEmitirModal: conferir (o que falta, ou a nota que vai
 * sair) e emitir. O tomador é opcional e digitado.
 */
import { computed, ref, watch } from 'vue';
import { AlertCircle, CheckCircle2, Loader2, Search, Send } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';
import MoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import { formatCurrency } from '@/shared/utils/finance';
import type { PendenciaFiscal } from '@/shared/types/fiscal.types';

import CodigoFiscalBuscaInput from '../shared/CodigoFiscalBuscaInput.vue';
import { fiscalService } from '../../services/fiscal.service';
import { nfseService } from '../../services/nfse.service';
import { useNbsSugeridos } from '../../composables/useNbsSugeridos';
import { CODIGO_NOTA_REPETIDA, codigoDoErro, useNfseEmitirAvulsaMutation } from '../../composables/useNfse';
import { formatarCodigoNacional, formatarNbs } from '../../utils/nfse.utils';
import type { NfseAvulsaRequest, NfsePreview } from '../../types/fiscal.types';

const props = defineProps<{ isOpen: boolean }>();
const emit = defineEmits<{ close: [] }>();

const codigoNacional = ref('');
const nbs = ref('');
const descricao = ref('');
/** MoneyInput trabalha em reais; a API, em centavos. */
const valorReais = ref<number | undefined>(undefined);
const descontoReais = ref<number | undefined>(undefined);
const tomadorDocumento = ref('');
const tomadorNome = ref('');
const tomadorEmail = ref('');

const conferindo = ref(false);
const pendencias = ref<PendenciaFiscal[]>([]);
const preview = ref<NfsePreview['dps'] | null>(null);
const avisoRepetida = ref<string | null>(null);

const nbsSugeridos = useNbsSugeridos(codigoNacional, true);
const emitirMutation = useNfseEmitirAvulsaMutation();

function limpar() {
  codigoNacional.value = '';
  nbs.value = '';
  descricao.value = '';
  valorReais.value = undefined;
  descontoReais.value = undefined;
  tomadorDocumento.value = '';
  tomadorNome.value = '';
  tomadorEmail.value = '';
  pendencias.value = [];
  preview.value = null;
  avisoRepetida.value = null;
}

watch(() => props.isOpen, (aberto) => !aberto && limpar());

const dados = computed<NfseAvulsaRequest>(() => ({
  codigo_tributacao_nacional: codigoNacional.value || null,
  codigo_nbs: nbs.value || null,
  descricao: descricao.value.trim(),
  valor: Math.round((valorReais.value ?? 0) * 100),
  desconto: Math.round((descontoReais.value ?? 0) * 100),
  tomador_documento: tomadorDocumento.value || null,
  tomador_nome: tomadorNome.value || null,
  tomador_email: tomadorEmail.value || null,
}));

// Mexeu no formulário: o que foi conferido não vale mais.
watch(dados, () => {
  preview.value = null;
  avisoRepetida.value = null;
});

const podeConferir = computed(() => dados.value.descricao.length >= 3 && dados.value.valor > 0);

async function conferir() {
  if (!podeConferir.value) return;
  conferindo.value = true;
  pendencias.value = [];
  try {
    preview.value = (await nfseService.previewAvulsa(dados.value)).dps;
  } catch (e: any) {
    pendencias.value = e?.response?.data?.detail?.pendencias ?? [
      { categoria: 'item', campo: 'erro', mensagem: e?.response?.data?.detail?.mensagem ?? 'Não foi possível conferir.' },
    ];
  } finally {
    conferindo.value = false;
  }
}

async function emitir(confirmar = false) {
  try {
    await emitirMutation.mutateAsync({ dados: dados.value, confirmar });
    emit('close');
  } catch (e: any) {
    if (codigoDoErro(e) === CODIGO_NOTA_REPETIDA) {
      avisoRepetida.value = e?.response?.data?.detail?.mensagem ?? 'Esta nota é igual a outra emitida há pouco.';
    }
  }
}

const buscarServicoNacional = async (termo: string) => (await fiscalService.buscarServicoNacional(termo)).resultados;
const buscarNbs = async (termo: string) => (await fiscalService.buscarNbs(termo)).resultados;
const emCentavos = (reais?: number) => Math.round((reais ?? 0) * 100);
</script>

<template>
  <BaseModal :is-open="isOpen" title="NFS-e avulsa" size="lg" @close="emit('close')">
    <div class="space-y-5">
      <p class="text-sm text-zinc-500">
        Para um serviço que <strong>não passou por OS</strong> (consultoria, aula, serviço avulso).
      </p>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <CodigoFiscalBuscaInput
          v-model="codigoNacional"
          label="Código de Tributação Nacional"
          placeholder="Ex: 01.07.01 ou suporte informática"
          :digitos="6"
          :formatar="formatarCodigoNacional"
          :buscar="buscarServicoNacional"
        />
        <CodigoFiscalBuscaInput
          v-model="nbs"
          label="NBS"
          placeholder="Ex: 1.1501.30.00"
          :digitos="9"
          :formatar="formatarNbs"
          :buscar="buscarNbs"
          :sugeridos="nbsSugeridos"
        />
      </div>

      <BaseTextarea v-model="descricao" label="Descrição do serviço" :rows="2" placeholder="O que foi prestado" required />

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <MoneyInput v-model="valorReais" label="Valor do serviço" required />
        <MoneyInput v-model="descontoReais" label="Desconto" />
      </div>

      <div class="pt-4 border-t border-zinc-200">
        <h4 class="text-sm font-semibold text-zinc-700 mb-1">Tomador (opcional)</h4>
        <p class="text-xs text-zinc-500 mb-3">Quem contratou o serviço. Sem CPF/CNPJ, a nota sai sem tomador identificado.</p>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <BaseInput v-model="tomadorDocumento" label="CPF ou CNPJ" inputmode="numeric" />
          <BaseInput v-model="tomadorNome" label="Nome / Razão social" />
          <BaseInput v-model="tomadorEmail" label="E-mail" type="email" />
        </div>
      </div>

      <div v-if="pendencias.length" class="p-4 rounded-xl bg-amber-50 border border-amber-200">
        <p class="text-sm font-semibold text-amber-800 mb-2">Antes de emitir, resolva:</p>
        <ul class="space-y-1.5" data-pendencias-avulsa>
          <li v-for="(p, i) in pendencias" :key="i" class="text-sm text-amber-800 flex items-start gap-2">
            <AlertCircle :size="14" class="mt-0.5 shrink-0" />
            <span>{{ p.mensagem }}</span>
          </li>
        </ul>
      </div>

      <div v-if="avisoRepetida" class="p-4 rounded-xl bg-amber-50 border border-amber-200 space-y-3">
        <p class="text-sm text-amber-800 flex items-start gap-2">
          <AlertCircle :size="16" class="mt-0.5 shrink-0" />
          <span>{{ avisoRepetida }} Se for mesmo outro serviço, confirme para emitir.</span>
        </p>
        <BaseButton type="button" variant="secondary" :is-loading="emitirMutation.isPending.value" @click="emitir(true)">
          Emitir mesmo assim
        </BaseButton>
      </div>

      <div v-if="preview" class="p-4 rounded-xl border border-zinc-200 bg-zinc-50/50 text-sm" data-preview-avulsa>
        <div class="flex items-center gap-2 text-emerald-700 font-semibold mb-2">
          <CheckCircle2 :size="16" /> Tudo certo para emitir
        </div>
        <p class="text-zinc-800">
          {{ formatarCodigoNacional(preview.codigo_tributacao_nacional_iss) }} ·
          {{ formatCurrency(emCentavos(preview.valor_servico)) }}
          <template v-if="preview.desconto_incondicionado">
            (desconto de {{ formatCurrency(emCentavos(preview.desconto_incondicionado)) }})
          </template>
        </p>
        <p class="text-xs text-zinc-500 mt-1">{{ preview.razao_social_tomador || 'Sem tomador identificado' }}</p>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-end gap-3 w-full">
        <BaseButton type="button" variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton v-if="!preview" type="button" variant="secondary" :disabled="!podeConferir || conferindo" @click="conferir">
          <Loader2 v-if="conferindo" :size="16" class="mr-1.5 animate-spin" />
          <Search v-else :size="16" class="mr-1.5" />
          Conferir
        </BaseButton>
        <BaseButton
          v-else
          type="button"
          variant="primary"
          :disabled="!!avisoRepetida || emitirMutation.isPending.value"
          :is-loading="emitirMutation.isPending.value"
          @click="emitir()"
        >
          <Send :size="16" class="mr-1.5" />
          Emitir NFS-e
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
