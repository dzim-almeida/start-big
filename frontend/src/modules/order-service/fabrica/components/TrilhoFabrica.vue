<script setup lang="ts">
/**
 * @fileoverview O trilho da OS da fábrica (docs/marcenaria-fabrica-plano.md, F3, §6).
 *
 * As 10 etapas, onde a OS está, o que falta para sair dela, o sinal, a data
 * de instalação e o histórico. O status de sempre da OS acompanha a etapa —
 * por isso o seletor de status fica travado nesta OS.
 *
 * Pendência: com "Travar etapas" ligado em Configurações, não avança; senão,
 * avança com motivo (fica no histórico).
 */
import { computed, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';
import { AlertTriangle, Check, ChevronRight, History, PackageCheck, RotateCcw, Unlock } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import MotivoModal from '@/modules/compras/shared/components/MotivoModal.vue';
import { useToast } from '@/shared/composables/useToast';
import type { ApiError } from '@/shared/types/axios.types';
import { getErrorMessage } from '@/shared/utils/error.utils';
import { formatCurrency } from '@/shared/utils/finance';

import { useAcessoFabrica } from '../composables/useAcessoFabrica';
import { fabricaKeys } from '../constants/queryKeys';
import { avancarEtapa, definirInstalacao, getTrilho, liberarCompra, voltarEtapa } from '../services/fabrica.service';
import type { TrilhoRead } from '../types/fabrica.types';

const props = defineProps<{
  numeroOs: string;
  /** Fase vinda da OS: quando o orçamento muda a fase, o trilho recarrega. */
  fase: string;
  /** Muda a cada gravação da OS (ex.: adiantamento): as travas recalculam. */
  atualizadoEm?: string;
}>();

const emit = defineEmits<{ osAlterada: [] }>();

const toast = useToast();
const queryClient = useQueryClient();
const { podeGerenciar } = useAcessoFabrica();

const { data: trilho, refetch } = useQuery({
  queryKey: computed(() => fabricaKeys.trilho(props.numeroOs)),
  queryFn: () => getTrilho(props.numeroOs),
});
watch(() => [props.fase, props.atualizadoEm], () => refetch());

const pendentes = computed(() => trilho.value?.travas.filter((t) => !t.ok) ?? []);

// F4: da "Separação e compra" em diante, o material se separa bipando.
const router = useRouter();
const ANTES_DA_SEPARACAO = ['MEDICAO', 'ELABORACAO', 'AGUARDANDO_APROVACAO', 'AGUARDANDO_SINAL'];
const podeSeparar = computed(
  () => !!trilho.value && trilho.value.aberta && !ANTES_DA_SEPARACAO.includes(trilho.value.fase),
);
function abrirSeparacao() {
  router.push({ name: 'fabrica-separacao', params: { numeroOs: props.numeroOs } });
}
const historicoAberto = ref(false);

const ROTULO_EVENTO: Record<string, string> = {
  AVANCO: 'Avançou',
  RETROCESSO: 'Voltou',
  APROVACAO: 'Orçamento aprovado',
  LIBERACAO_COMPRA: 'Compra liberada antes do sinal',
  AVISO_IGNORADO: 'Avançou com pendência',
  CANCELAMENTO: 'OS cancelada',
  REABERTURA: 'OS reaberta',
};

function rotuloDaFase(fase: string | null): string {
  return trilho.value?.etapas.find((e) => e.fase === fase)?.rotulo ?? fase ?? '';
}

function quando(iso: string): string {
  return new Date(iso.endsWith('Z') ? iso : `${iso}Z`).toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
  });
}

function aoGravar(novo: TrilhoRead, mensagem?: string) {
  queryClient.setQueryData(fabricaKeys.trilho(props.numeroOs), novo);
  if (mensagem) toast.success(mensagem);
  emit('osAlterada');
}

// --- Avançar ---------------------------------------------------------------------

interface DetalheTrava { codigo?: string; mensagem?: string; travas?: string[] }

const motivoAvancoAberto = ref(false);
const travasDoAviso = ref<string[]>([]);

const avancar = useMutation<TrilhoRead, AxiosError<ApiError>, string | undefined>({
  mutationFn: (motivo) => avancarEtapa(props.numeroOs, motivo),
  onSuccess: (novo) => {
    motivoAvancoAberto.value = false;
    aoGravar(novo, `Agora em: ${novo.rotulo}`);
  },
  onError: (erro) => {
    const detalhe = (erro.response?.data as { detail?: unknown } | undefined)?.detail as DetalheTrava | string | undefined;
    if (detalhe && typeof detalhe === 'object' && detalhe.codigo === 'MOTIVO_OBRIGATORIO') {
      travasDoAviso.value = detalhe.travas ?? [];
      motivoAvancoAberto.value = true;
      return;
    }
    if (detalhe && typeof detalhe === 'object' && detalhe.codigo === 'TRAVA_PENDENTE') {
      toast.error(detalhe.mensagem ?? 'Etapa com pendência', (detalhe.travas ?? []).join(' · '));
      return;
    }
    toast.error('Não foi possível avançar', getErrorMessage(erro, 'Tente de novo.') as string);
  },
});

// --- Voltar ----------------------------------------------------------------------

const voltarAberto = ref(false);
const destino = ref('');
const motivoVolta = ref('');
const anteriores = computed(() => trilho.value?.etapas.filter((e) => e.situacao === 'FEITA') ?? []);

function abrirVoltar() {
  destino.value = anteriores.value[anteriores.value.length - 1]?.fase ?? '';
  motivoVolta.value = '';
  voltarAberto.value = true;
}

const voltar = useMutation<TrilhoRead, AxiosError<ApiError>, void>({
  mutationFn: () => voltarEtapa(props.numeroOs, destino.value, motivoVolta.value.trim()),
  onSuccess: (novo) => {
    voltarAberto.value = false;
    aoGravar(novo, `Voltou para: ${novo.rotulo}`);
  },
  onError: (erro) => toast.error('Não foi possível voltar', getErrorMessage(erro, 'Tente de novo.') as string),
});

// --- Liberar compra e instalação ----------------------------------------------------

const liberarAberto = ref(false);
const liberar = useMutation<TrilhoRead, AxiosError<ApiError>, string>({
  mutationFn: (motivo) => liberarCompra(props.numeroOs, motivo),
  onSuccess: (novo) => {
    liberarAberto.value = false;
    aoGravar(novo, 'Compra liberada: o material já entra nas Necessidades');
  },
  onError: (erro) => toast.error('Não foi possível liberar', getErrorMessage(erro, 'Tente de novo.') as string),
});

const instalacao = ref<string | null>(null);
watch(trilho, (t) => (instalacao.value = t?.data_instalacao ?? null), { immediate: true });

const salvarInstalacao = useMutation<TrilhoRead, AxiosError<ApiError>, string | null>({
  mutationFn: (data) => definirInstalacao(props.numeroOs, data),
  onSuccess: (novo) => aoGravar(novo, novo.data_instalacao ? 'Instalação marcada' : 'Instalação desmarcada'),
  onError: (erro) => toast.error('Não foi possível marcar', getErrorMessage(erro, 'Tente de novo.') as string),
});

function aoMudarInstalacao() {
  if ((instalacao.value || null) !== (trilho.value?.data_instalacao ?? null)) {
    salvarInstalacao.mutate(instalacao.value || null);
  }
}
</script>

<template>
  <div v-if="trilho" class="rounded-2xl border border-zinc-200 bg-white p-4 space-y-3">
    <!-- Etapas -->
    <ol class="flex items-center gap-1 overflow-x-auto pb-1 text-[11px]">
      <li
        v-for="(etapa, i) in trilho.etapas"
        :key="etapa.fase"
        class="flex items-center gap-1 shrink-0"
      >
        <span
          class="px-2 py-1 rounded-full border font-semibold whitespace-nowrap"
          :class="{
            'bg-emerald-50 text-emerald-700 border-emerald-200': etapa.situacao === 'FEITA',
            'bg-brand-primary text-white border-brand-primary': etapa.situacao === 'ATUAL',
            'bg-white text-zinc-400 border-zinc-200': etapa.situacao === 'A_FAZER',
          }"
        >
          <Check v-if="etapa.situacao === 'FEITA'" :size="10" class="inline -mt-0.5" />
          {{ etapa.rotulo }}
        </span>
        <ChevronRight v-if="i < trilho.etapas.length - 1" :size="12" class="text-zinc-300" />
      </li>
    </ol>

    <div class="grid grid-cols-1 md:grid-cols-12 gap-3 items-start">
      <!-- O que falta -->
      <div class="md:col-span-7 space-y-1.5">
        <p class="text-sm text-zinc-700">
          Etapa atual: <strong>{{ trilho.rotulo }}</strong>
          <span v-if="!trilho.aberta" class="text-zinc-400">(OS fechada)</span>
        </p>
        <ul v-if="trilho.travas.length" class="space-y-1">
          <li v-for="t in trilho.travas" :key="t.codigo" class="flex items-start gap-1.5 text-xs" :class="t.ok ? 'text-emerald-700' : 'text-amber-800'">
            <Check v-if="t.ok" :size="14" class="shrink-0 mt-px" />
            <AlertTriangle v-else :size="14" class="shrink-0 mt-px" />
            {{ t.texto }}
          </li>
        </ul>
        <p v-if="trilho.aberta && trilho.avanco_por_acao" class="text-xs text-zinc-500">{{ trilho.avanco_por_acao }}</p>
        <p v-if="trilho.sinal_exigido > 0" class="text-xs text-zinc-600">
          Sinal: {{ formatCurrency(trilho.recebido) }} recebido de {{ formatCurrency(trilho.sinal_exigido) }}
          <template v-if="trilho.compra_liberada_em">
            · compra liberada por {{ trilho.compra_liberada_por }} ({{ trilho.compra_liberada_motivo }})
          </template>
          <template v-else-if="!trilho.pode_comprar"> · o material só entra nas compras com o sinal pago</template>
        </p>
      </div>

      <!-- Instalação -->
      <label class="md:col-span-2 flex flex-col gap-1 text-xs font-medium text-zinc-600">
        Instalação
        <input
          v-model="instalacao"
          type="date"
          :disabled="!trilho.aberta"
          class="min-h-9 px-2 text-sm border border-zinc-200 rounded-lg bg-white outline-none focus:border-brand-primary disabled:bg-zinc-100"
          @change="aoMudarInstalacao"
        />
      </label>

      <!-- Ações -->
      <div v-if="trilho.aberta" class="md:col-span-3 flex flex-col gap-2">
        <BaseButton
          v-if="trilho.proxima && !trilho.avanco_por_acao"
          type="button"
          size="sm"
          class="flex items-center justify-center gap-1.5"
          :variant="pendentes.length ? 'secondary' : 'primary'"
          :is-loading="avancar.isPending.value"
          @click="avancar.mutate(undefined)"
        >
          Avançar: {{ trilho.proxima_rotulo }} <ChevronRight :size="14" />
        </BaseButton>
        <BaseButton
          v-if="podeSeparar"
          type="button" size="sm" variant="ghost" class="flex items-center justify-center gap-1.5"
          @click="abrirSeparacao"
        >
          <PackageCheck :size="14" /> Separação de material
        </BaseButton>
        <BaseButton
          v-if="!trilho.pode_comprar && podeGerenciar && trilho.sinal_exigido > 0"
          type="button" size="sm" variant="ghost" class="flex items-center justify-center gap-1.5"
          @click="liberarAberto = true"
        >
          <Unlock :size="14" /> Liberar compra antes do sinal
        </BaseButton>
        <BaseButton
          v-if="anteriores.length"
          type="button" size="sm" variant="ghost" class="flex items-center justify-center gap-1.5"
          @click="abrirVoltar"
        >
          <RotateCcw :size="14" /> Voltar etapa
        </BaseButton>
      </div>
    </div>

    <!-- Histórico -->
    <div v-if="trilho.log.length" class="border-t border-zinc-100 pt-2">
      <button
        type="button"
        class="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-700 cursor-pointer"
        @click="historicoAberto = !historicoAberto"
      >
        <History :size="13" /> Histórico ({{ trilho.log.length }})
      </button>
      <ul v-if="historicoAberto" class="mt-2 space-y-1 text-xs text-zinc-600">
        <li v-for="(l, i) in trilho.log" :key="i">
          <span class="text-zinc-400 tabular-nums">{{ quando(l.ocorrido_em) }}</span>
          · {{ ROTULO_EVENTO[l.evento] ?? l.evento }}
          <template v-if="l.fase_nova && l.fase_nova !== l.fase_anterior"> → {{ rotuloDaFase(l.fase_nova) }}</template>
          <template v-if="l.usuario"> · {{ l.usuario }}</template>
          <span v-if="l.motivo" class="block pl-4 text-zinc-500">{{ l.motivo }}</span>
        </li>
      </ul>
    </div>

    <!-- Avançar com pendência (modo aviso) -->
    <MotivoModal
      :aberto="motivoAvancoAberto"
      :titulo="`Avançar para ${trilho.proxima_rotulo ?? ''} com pendência?`"
      :descricao="`Pendente: ${travasDoAviso.join(' · ')}. O motivo fica no histórico da OS.`"
      confirm-label="Avançar mesmo assim"
      placeholder="Ex.: cliente paga o sinal amanhã, combinado com o dono"
      :carregando="avancar.isPending.value"
      @fechar="motivoAvancoAberto = false"
      @confirmar="avancar.mutate($event)"
    />

    <MotivoModal
      :aberto="liberarAberto"
      titulo="Liberar a compra antes do sinal"
      descricao="O material desta OS passa a entrar nas Necessidades de Compras mesmo sem o sinal pago. Fica registrado quem liberou e por quê."
      confirm-label="Liberar compra"
      placeholder="Ex.: cliente antigo, prazo de instalação curto"
      :carregando="liberar.isPending.value"
      @fechar="liberarAberto = false"
      @confirmar="liberar.mutate($event)"
    />

    <BaseModal :is-open="voltarAberto" title="Voltar etapa" size="sm" overlay @close="voltarAberto = false">
      <div class="flex flex-col gap-3 text-sm">
        <label class="flex flex-col gap-1">
          <span class="text-xs font-medium text-zinc-600">Para qual etapa</span>
          <select v-model="destino" class="min-h-10 px-2.5 border border-zinc-200 rounded-lg bg-white outline-none focus:border-brand-primary">
            <option v-for="e in anteriores" :key="e.fase" :value="e.fase">{{ e.rotulo }}</option>
          </select>
        </label>
        <label class="flex flex-col gap-1">
          <span class="text-xs font-medium text-zinc-600">Motivo</span>
          <textarea
            v-model="motivoVolta"
            rows="3"
            class="px-2.5 py-2 border border-zinc-200 rounded-lg outline-none focus:border-brand-primary"
            placeholder="Ex.: o cheque do sinal voltou"
          />
        </label>
      </div>
      <template #footer>
        <div class="flex w-full justify-end gap-2">
          <BaseButton variant="secondary" class="px-5" @click="voltarAberto = false">Cancelar</BaseButton>
          <BaseButton
            class="px-5"
            :disabled="!destino || motivoVolta.trim().length < 3"
            :is-loading="voltar.isPending.value"
            @click="voltar.mutate()"
          >
            Voltar
          </BaseButton>
        </div>
      </template>
    </BaseModal>
  </div>
</template>
