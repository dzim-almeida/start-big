<script setup lang="ts">
/**
 * @component EditorCabecalho
 * @description Topo do editor (Spec 06B §6.2, D9, D14, D36, D41-D43):
 * código, versão, status, indicador de salvamento e as ações
 * (Visão do cliente, Histórico, Mais › Excluir, Enviar ao cliente).
 *
 * O indicador existe para o usuário CONFIAR no salvamento automático e não
 * procurar um botão "Salvar" que não existe.
 */
import { computed, ref } from 'vue';
import { onClickOutside } from '@vueuse/core';
import { AlertCircle, ArrowLeft, Check, CheckCheck, Eye, History, Loader2, MoreHorizontal, Send } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import type { EstadoSalvamento } from '../../composables/useSalvamentoAutomatico';
import type { OrcamentoDetalhe } from '../../schemas/orcamentoDetalhe.schema';
import OrcamentoStatusBadge from '../lista/OrcamentoStatusBadge.vue';
import VersoesMenu from '../modais/VersoesMenu.vue';

const props = defineProps<{
  detalhe?: OrcamentoDetalhe;
  estado: EstadoSalvamento;
  salvoEm: Date | null;
  tentandoDeNovo: boolean;
  /** Escritas na fila (ambiente, móvel, transição) ainda em andamento. */
  gravandoAcao: boolean;
  visaoCliente: boolean;
}>();

const emit = defineEmits<{
  voltar: [];
  alternarVisaoCliente: [];
  historico: [];
  enviar: [];
  /** Spec 08B D1: aprovar e gerar a OS. */
  aprovar: [];
  excluir: [];
  tentarAgora: [];
  abrirVersao: [id: number];
}>();

const menuAberto = ref(false);
const menuRef = ref<HTMLElement | null>(null);
onClickOutside(menuRef, () => { menuAberto.value = false; });

/** O texto e o ícone do indicador (D9). */
const indicador = computed(() => {
  if (props.gravandoAcao || props.estado === 'salvando') return { texto: 'Salvando…', tom: 'neutro', icone: Loader2 };
  switch (props.estado) {
    case 'esperando':
      return { texto: 'Alterações não salvas', tom: 'neutro', icone: null };
    case 'erro':
      return props.tentandoDeNovo
        ? { texto: 'Não foi possível salvar — tentando de novo', tom: 'erro', icone: AlertCircle }
        : { texto: 'Não foi possível salvar', tom: 'erro', icone: AlertCircle };
    case 'invalido':
      return { texto: 'Corrija o campo destacado para salvar', tom: 'erro', icone: AlertCircle };
    default:
      return props.salvoEm
        ? { texto: `Salvo às ${props.salvoEm.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`, tom: 'ok', icone: Check }
        : props.detalhe ? { texto: 'Salvo', tom: 'ok', icone: Check } : null;
  }
});

/** "Tentar agora" depois das 3 tentativas automáticas (D9). */
const mostrarTentarAgora = computed(() => props.estado === 'erro' && !props.tentandoDeNovo);

const acoes = computed(() => props.detalhe?.acoes);
</script>

<template>
  <header class="flex flex-wrap items-center justify-between gap-3">
    <div class="flex flex-wrap items-center gap-3">
      <button
        type="button"
        class="inline-flex items-center gap-1 text-sm text-zinc-500 hover:text-zinc-800 cursor-pointer"
        data-testid="voltar-lista"
        @click="emit('voltar')"
      >
        <ArrowLeft :size="16" /> Orçamentos
      </button>

      <h1 class="text-lg font-bold text-zinc-900" data-testid="codigo-orcamento">
        {{ detalhe?.codigo ?? 'Novo orçamento' }}
      </h1>
      <VersoesMenu v-if="detalhe" :id="detalhe.id" :versao="detalhe.versao" @abrir="emit('abrirVersao', $event)" />
      <OrcamentoStatusBadge v-if="detalhe" :status="detalhe.status" />

      <!-- Indicador de salvamento (D9) -->
      <span
        v-if="indicador"
        class="inline-flex items-center gap-1 text-xs"
        :class="{ 'text-zinc-400': indicador.tom === 'neutro', 'text-emerald-700': indicador.tom === 'ok', 'text-red-600': indicador.tom === 'erro' }"
        role="status"
        aria-live="polite"
        data-testid="indicador-salvamento"
      >
        <component :is="indicador.icone" v-if="indicador.icone" :size="14" :class="indicador.icone === Loader2 ? 'animate-spin' : ''" />
        {{ indicador.texto }}
      </span>
      <button
        v-if="mostrarTentarAgora"
        type="button"
        class="text-xs font-semibold text-red-700 underline cursor-pointer"
        data-testid="tentar-agora"
        @click="emit('tentarAgora')"
      >
        Tentar agora
      </button>
    </div>

    <div v-if="detalhe" class="flex flex-wrap items-center gap-2">
      <!-- A Spec 07 coloca aqui o botão "Proposta". -->
      <slot name="acoes" />
      <BaseButton variant="secondary" size="sm" data-testid="visao-cliente" @click="emit('alternarVisaoCliente')">
        <Eye :size="14" class="mr-1" /> {{ visaoCliente ? 'Voltar ao orçamento' : 'Visão do cliente' }}
      </BaseButton>
      <BaseButton variant="secondary" size="sm" data-testid="abrir-historico" @click="emit('historico')">
        <History :size="14" class="mr-1" /> Histórico
      </BaseButton>

      <!-- "Mais": excluir fica escondido de propósito (D41) -->
      <div v-if="acoes?.excluir" ref="menuRef" class="relative">
        <BaseButton variant="secondary" size="sm" aria-haspopup="menu" :aria-expanded="menuAberto" data-testid="menu-mais" @click="menuAberto = !menuAberto">
          <MoreHorizontal :size="14" class="mr-1" /> Mais
        </BaseButton>
        <div v-if="menuAberto" role="menu" class="absolute right-0 z-30 mt-1 w-44 overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-lg">
          <button
            type="button"
            role="menuitem"
            class="block w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 cursor-pointer"
            data-testid="acao-excluir"
            @click="menuAberto = false; emit('excluir')"
          >
            Excluir orçamento
          </button>
        </div>
      </div>

      <!-- Aprovar (08B D1): é o objetivo do orçamento, não fica escondido no "Mais". -->
      <BaseButton v-if="acoes?.aprovar" variant="secondary" size="sm" data-testid="acao-aprovar" @click="emit('aprovar')">
        <CheckCheck :size="14" class="mr-1" /> Aprovar
      </BaseButton>
      <!-- Enviar fica sempre visível no rascunho: o modal explica o que falta (D36). -->
      <BaseButton v-if="acoes?.enviar" variant="primary" size="sm" data-testid="acao-enviar" @click="emit('enviar')">
        <Send :size="14" class="mr-1" /> Enviar ao cliente
      </BaseButton>
    </div>
  </header>
</template>
