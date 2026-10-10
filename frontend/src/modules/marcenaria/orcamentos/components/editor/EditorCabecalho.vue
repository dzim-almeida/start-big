<script setup lang="ts">
/**
 * @component EditorCabecalho
 * @description Topo do editor (Spec 06B §6.2, D9, D14, D36, D41-D43;
 * redesign 10/2026), fixo ao rolar:
 * - o NOME DO PROJETO como título (é como o vendedor lembra do orçamento), com
 *   "Orçamentos / código / versão" em cima, o status e o indicador de salvamento;
 * - Histórico, Mais › Excluir e fechar;
 * - embaixo, as seções do editor (EditorSecoesNav) e as etapas do orçamento.
 * As ações do orçamento (Aprovar, Enviar, Proposta, Visão do cliente) ficam no
 * resumo da coluna lateral (EditorAcoes).
 *
 * O indicador existe para o usuário CONFIAR no salvamento automático e não
 * procurar um botão "Salvar" que não existe.
 */
import { computed, ref } from 'vue';
import { onClickOutside } from '@vueuse/core';
import { AlertCircle, ArrowLeft, Check, History, Loader2, MoreHorizontal, X } from 'lucide-vue-next';

import type { EstadoSalvamento } from '../../composables/useSalvamentoAutomatico';
import type { OrcamentoDetalhe } from '../../schemas/orcamentoDetalhe.schema';
import { etapasDoOrcamento } from '../../utils/etapasOrcamento';
import OrcamentoStatusBadge from '../lista/OrcamentoStatusBadge.vue';
import VersoesMenu from '../modais/VersoesMenu.vue';
import EditorSecoesNav, { type SecaoEditor } from './EditorSecoesNav.vue';

const props = defineProps<{
  detalhe?: OrcamentoDetalhe;
  estado: EstadoSalvamento;
  salvoEm: Date | null;
  tentandoDeNovo: boolean;
  /** Escritas na fila (ambiente, móvel, transição) ainda em andamento. */
  gravandoAcao: boolean;
  /** O nome do projeto como está no formulário (muda enquanto o usuário digita). */
  projetoNome?: string | null;
  /** As seções do editor, para a navegação (some na Visão do cliente). */
  secoes?: SecaoEditor[];
}>();

const emit = defineEmits<{
  voltar: [];
  historico: [];
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

/** O título: o projeto; sem nome ainda, o que dá para dizer. */
const titulo = computed(() => props.projetoNome?.trim() || (props.detalhe ? 'Projeto sem nome' : 'Novo orçamento'));

const etapas = computed(() => etapasDoOrcamento(props.detalhe?.status, !!props.detalhe?.os));
</script>

<template>
  <header class="flex flex-col gap-1">
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div class="flex min-w-0 items-start gap-2">
        <button
          type="button"
          class="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-zinc-500 hover:bg-zinc-100 hover:text-zinc-800 cursor-pointer"
          aria-label="Voltar aos orçamentos"
          data-testid="voltar-lista"
          @click="emit('voltar')"
        >
          <ArrowLeft :size="18" />
        </button>

        <div class="min-w-0">
          <!-- Orçamentos / código / versão -->
          <div class="flex flex-wrap items-center gap-1.5 text-xs text-zinc-500">
            <button type="button" class="hover:text-zinc-800 hover:underline cursor-pointer" @click="emit('voltar')">Orçamentos</button>
            <span aria-hidden="true">/</span>
            <span class="tabular-nums" data-testid="codigo-orcamento">{{ detalhe?.codigo ?? 'Novo orçamento' }}</span>
            <VersoesMenu v-if="detalhe" :id="detalhe.id" :versao="detalhe.versao" @abrir="emit('abrirVersao', $event)" />
          </div>

          <div class="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-1">
            <h1 class="truncate text-xl font-bold tracking-tight text-zinc-900" data-testid="titulo-orcamento">{{ titulo }}</h1>
            <OrcamentoStatusBadge v-if="detalhe" :status="detalhe.status" />

            <!-- Indicador de salvamento (D9) -->
            <span
              v-if="indicador"
              class="inline-flex items-center gap-1 text-xs"
              :class="{ 'text-zinc-500': indicador.tom === 'neutro', 'text-emerald-700': indicador.tom === 'ok', 'text-red-600': indicador.tom === 'erro' }"
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
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-1">
        <template v-if="detalhe">
          <button
            type="button"
            class="inline-flex min-h-9 items-center gap-1.5 rounded-lg px-3 text-sm font-medium text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 cursor-pointer"
            data-testid="abrir-historico"
            @click="emit('historico')"
          >
            <History :size="16" /> Histórico
          </button>

          <!-- "Mais": excluir fica escondido de propósito (D41) -->
          <div v-if="acoes?.excluir" ref="menuRef" class="relative">
            <button
              type="button"
              class="flex h-9 w-9 items-center justify-center rounded-lg text-zinc-600 hover:bg-zinc-100 cursor-pointer"
              aria-label="Mais ações"
              aria-haspopup="menu"
              :aria-expanded="menuAberto"
              data-testid="menu-mais"
              @click="menuAberto = !menuAberto"
            >
              <MoreHorizontal :size="18" />
            </button>
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
          <span class="mx-1.5 h-6 w-px bg-zinc-200" aria-hidden="true" />
        </template>

        <!-- Tela cheia: o X devolve à lista (o mesmo que "voltar"). -->
        <button
          type="button"
          class="flex h-9 w-9 items-center justify-center rounded-lg text-zinc-500 hover:bg-zinc-100 hover:text-red-600 cursor-pointer"
          aria-label="Fechar orçamento"
          data-testid="fechar-editor"
          @click="emit('voltar')"
        >
          <X :size="20" />
        </button>
      </div>
    </div>

    <!-- Seções do editor e as etapas do orçamento -->
    <div class="flex flex-wrap items-end justify-between gap-x-6 gap-y-2 pl-11">
      <EditorSecoesNav v-if="secoes?.length" :secoes="secoes" />
      <span v-else />
      <ol class="flex items-center gap-2 pb-3" aria-label="Etapas do orçamento">
        <li v-for="(etapa, i) in etapas" :key="etapa.rotulo" class="flex items-center gap-2">
          <span v-if="i > 0" class="h-px w-5 bg-zinc-200" aria-hidden="true" />
          <span
            :class="[
              'flex items-center gap-1.5 text-xs',
              etapa.estado === 'atual' ? 'font-semibold text-brand-primary' : etapa.estado === 'concluida' ? 'text-zinc-700' : 'text-zinc-400',
            ]"
            :aria-current="etapa.estado === 'atual' ? 'step' : undefined"
          >
            <span
              :class="[
                'h-2 w-2 rounded-full',
                etapa.estado === 'atual' ? 'bg-brand-primary ring-4 ring-brand-primary-light' : etapa.estado === 'concluida' ? 'bg-emerald-600' : 'bg-zinc-300',
              ]"
              aria-hidden="true"
            />
            {{ etapa.rotulo }}
          </span>
        </li>
      </ol>
    </div>
  </header>
</template>
