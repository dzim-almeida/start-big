<script setup lang="ts">
/**
 * @component NfseEmitirModal
 * @description Emitir a NFS-e da mão de obra de uma OS, em dois passos:
 * conferir (o que falta, ou a nota que vai sair) e emitir.
 *
 * Conferir ANTES é de propósito: a pendência aparece nomeada ("serviço sem
 * NBS") em vez de virar recusa do Sistema Nacional depois do envio.
 *
 * Escolher a OS (M3 de docs/nfse-melhorias-plano.md): a lista das OS
 * finalizadas sem NFS-e aparece ao abrir, e o mesmo campo procura pelo número
 * curto ("158") ou pelo cliente. Ninguém precisa lembrar "OS-2026-000158".
 */
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import { AlertCircle, CheckCircle2, ChevronRight, Loader2, Search, Send } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import { formatCurrency } from '@/shared/utils/finance';
import { formatCPF, formatCNPJ } from '@/shared/utils/document.utils';
import { formatData } from '@/shared/utils/date.utils';
import type { PendenciaFiscal } from '@/shared/types/fiscal.types';

import { nfseService } from '../../services/nfse.service';
import { CODIGO_NOTA_REPETIDA, codigoDoErro, useNfseEmitirMutation } from '../../composables/useNfse';
import { formatarCodigoNacional, formatarNbs } from '../../utils/nfse.utils';
import type { NfseOsParaEmitir, NfsePreview } from '../../types/fiscal.types';

const props = defineProps<{
  isOpen: boolean;
  /** Aberto a partir da OS ("Notas desta OS", M5): já confere esta OS. */
  numeroOsInicial?: string | null;
}>();
const emit = defineEmits<{ close: [] }>();

/** A OS escolhida (vazio = ainda escolhendo na lista). */
const numeroOs = ref('');
/** O que está digitado no campo: número curto, número inteiro ou cliente. */
const busca = ref('');
const opcoes = ref<NfseOsParaEmitir[]>([]);
const carregandoOpcoes = ref(false);
const conferindo = ref(false);
const erro = ref<string | null>(null);
const pendencias = ref<PendenciaFiscal[]>([]);
const preview = ref<NfsePreview | null>(null);
/** A plataforma achou uma nota igual há menos de 1 h: a mensagem dela, para o operador decidir. */
const avisoRepetida = ref<string | null>(null);

const emitirMutation = useNfseEmitirMutation();

let timer: ReturnType<typeof setTimeout> | undefined;
onBeforeUnmount(() => timer && clearTimeout(timer));

async function carregarOpcoes(termo = '') {
  carregandoOpcoes.value = true;
  try {
    opcoes.value = await nfseService.osParaEmitir(termo);
  } catch {
    opcoes.value = [];            // sem lista, o campo ainda aceita o número inteiro
  } finally {
    carregandoOpcoes.value = false;
  }
}

watch(() => props.isOpen, (aberto) => {
  if (aberto && props.numeroOsInicial) escolher(props.numeroOsInicial);
  else if (aberto) carregarOpcoes();
  if (!aberto) {
    numeroOs.value = '';
    busca.value = '';
    opcoes.value = [];
    erro.value = null;
    pendencias.value = [];
    preview.value = null;
    avisoRepetida.value = null;
  }
});

// Trocar a OS invalida o que foi conferido para a anterior.
watch(numeroOs, () => {
  pendencias.value = [];
  preview.value = null;
  erro.value = null;
  avisoRepetida.value = null;
});

// Digitar procura (300 ms de espera) e desfaz a OS escolhida.
watch(busca, (termo) => {
  if (numeroOs.value && termo === numeroOs.value) return;
  numeroOs.value = '';
  if (timer) clearTimeout(timer);
  timer = setTimeout(() => carregarOpcoes(termo.trim()), 300);
});

function escolher(numero: string) {
  numeroOs.value = numero;
  busca.value = numero;
  conferir();
}

/** Enter / Conferir: a OS da lista, se só sobrou uma; ou o número inteiro digitado. */
function conferirDigitado() {
  const termo = busca.value.trim();
  if (!termo) return;
  if (opcoes.value.length === 1) return escolher(opcoes.value[0].numero_os);
  if (/^os-/i.test(termo)) return escolher(termo.toUpperCase());
  erro.value = opcoes.value.length
    ? 'Mais de uma OS combina com a busca: escolha na lista.'
    : 'Nenhuma OS finalizada sem NFS-e combina com a busca.';
}

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

/**
 * Uma nota por código nacional (G3). Com um código só, uma entrada — e a tela
 * é a de sempre (o botão do rodapé). Com vários, cada nota tem o seu botão.
 */
const notas = computed(() =>
  preview.value?.notas ?? (preview.value ? [{ codigo: preview.value.dps.codigo_tributacao_nacional_iss, dps: preview.value.dps, ja_emitida: false }] : []),
);
const variasNotas = computed(() => notas.value.length > 1);
/** O código da nota que pediu "Emitir mesmo assim" (nota repetida). */
const codigoDoAviso = ref<string | undefined>(undefined);

async function emitir(confirmar = false, codigo?: string) {
  if (!preview.value) return;
  try {
    await emitirMutation.mutateAsync({ numeroOs: preview.value.numero_os, confirmar, codigo });
    avisoRepetida.value = null;
    // Com várias notas, fica aberto para a próxima: a conferência marca a emitida.
    if (variasNotas.value) await conferir();
    else emit('close');
  } catch (e: any) {
    if (codigoDoErro(e) === CODIGO_NOTA_REPETIDA) {
      codigoDoAviso.value = codigo;
      avisoRepetida.value = e?.response?.data?.detail?.mensagem ?? 'Esta nota é igual a outra emitida há pouco.';
    }
  }
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

      <form class="flex items-end gap-2" @submit.prevent="conferirDigitado">
        <div class="flex-1">
          <BaseInput v-model="busca" label="OS" placeholder="Número (ex: 158) ou nome do cliente" />
        </div>
        <BaseButton type="submit" variant="secondary" :disabled="!busca.trim() || conferindo">
          <Loader2 v-if="conferindo" :size="16" class="mr-1.5 animate-spin" />
          <Search v-else :size="16" class="mr-1.5" />
          Conferir
        </BaseButton>
      </form>

      <!-- As OS prontas para a nota: um clique escolhe (M3) -->
      <div v-if="!numeroOs" class="rounded-xl border border-zinc-200 overflow-hidden" data-os-para-emitir>
        <p class="px-4 py-2 text-[11px] font-semibold uppercase tracking-wide text-zinc-500 bg-zinc-50 border-b border-zinc-100">
          Escolha a OS
        </p>
        <p v-if="carregandoOpcoes" class="px-4 py-3 text-sm text-zinc-400 flex items-center gap-2">
          <Loader2 :size="14" class="animate-spin" /> procurando…
        </p>
        <p v-else-if="!opcoes.length" class="px-4 py-3 text-sm text-zinc-500">
          {{ busca.trim() ? 'Nenhuma OS finalizada sem NFS-e combina com a busca.' : 'Nenhuma OS finalizada esperando a nota.' }}
        </p>
        <ul v-else class="max-h-64 overflow-y-auto divide-y divide-zinc-100">
          <li v-for="os in opcoes" :key="os.numero_os">
            <button
              type="button"
              class="w-full px-4 py-2.5 flex items-center justify-between gap-3 text-left hover:bg-zinc-50 transition-colors"
              @click="escolher(os.numero_os)"
            >
              <span class="min-w-0">
                <span class="block text-sm font-semibold text-zinc-800 truncate">{{ os.cliente || 'Cliente não identificado' }}</span>
                <span class="block text-xs text-zinc-500">
                  {{ os.numero_os }}<template v-if="os.data"> · {{ formatData(os.data) }}</template>
                  <template v-if="os.nfse_parcial"> · falta um código</template>
                </span>
              </span>
              <span class="flex items-center gap-2 shrink-0 text-sm font-semibold text-zinc-700">
                {{ formatCurrency(os.valor_servicos) }}
                <ChevronRight :size="16" class="text-zinc-400" />
              </span>
            </button>
          </li>
        </ul>
      </div>

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

      <!-- Nota repetida: a plataforma não emitiu e pede a confirmação do operador -->
      <div v-if="avisoRepetida" class="p-4 rounded-xl bg-amber-50 border border-amber-200 space-y-3" data-aviso-repetida>
        <p class="text-sm text-amber-800 flex items-start gap-2">
          <AlertCircle :size="16" class="mt-0.5 shrink-0" />
          <span>{{ avisoRepetida }} Se for mesmo outro serviço, confirme para emitir.</span>
        </p>
        <BaseButton type="button" variant="secondary" :is-loading="emitirMutation.isPending.value" @click="emitir(true, codigoDoAviso)">
          Emitir mesmo assim
        </BaseButton>
      </div>

      <!-- Uma nota por código (G3): cada uma com o seu botão -->
      <div v-if="variasNotas" class="space-y-3" data-varias-notas>
        <p class="text-sm text-zinc-600">
          Esta OS tem serviços de <strong>{{ notas.length }} códigos</strong> diferentes: sai uma NFS-e para cada.
        </p>
        <div
          v-for="nota in notas"
          :key="nota.codigo"
          class="p-4 rounded-xl border border-zinc-200 bg-zinc-50/50 flex items-center justify-between gap-4"
        >
          <div class="text-sm">
            <p class="font-semibold text-zinc-800">
              {{ formatarCodigoNacional(nota.codigo) }} · {{ formatCurrency(emCentavos(nota.dps.valor_servico)) }}
            </p>
            <p class="text-xs text-zinc-500 truncate max-w-md">{{ nota.dps.descricao_servico }}</p>
          </div>
          <span v-if="nota.ja_emitida" class="text-xs font-semibold text-emerald-700 flex items-center gap-1 shrink-0">
            <CheckCircle2 :size="14" /> Emitida
          </span>
          <BaseButton
            v-else
            type="button"
            variant="primary"
            class="text-sm shrink-0"
            :disabled="!!avisoRepetida || emitirMutation.isPending.value"
            @click="emitir(false, nota.codigo)"
          >
            <Send :size="14" class="mr-1.5" /> Emitir esta
          </BaseButton>
        </div>
      </div>

      <!-- A nota que vai sair -->
      <div v-if="preview && !variasNotas" class="p-4 rounded-xl border border-zinc-200 bg-zinc-50/50 space-y-3" data-preview-nfse>
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
          v-if="!variasNotas"
          type="button"
          variant="primary"
          :disabled="!preview || !!avisoRepetida || emitirMutation.isPending.value"
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
