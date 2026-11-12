<script setup lang="ts">
/**
 * @component AgendaTab
 * @description Agenda do lava-rápido (Spec 08B, SPEC-00 O11): a aba logo
 * depois do Pátio em Serviços.
 *
 * Em cima, a semana com quantos agendamentos há por dia; embaixo, os
 * horários do dia escolhido. Cada agendamento:
 *   Chegou   → abre a comanda já preenchida; a OS criada entra no pátio e o
 *              agendamento fica "Chegou" com o número dela;
 *   WhatsApp → mensagem de confirmação pronta;
 *   Não veio / Cancelar / Editar.
 */
import { computed, ref } from 'vue';
import { CalendarClock, CheckCircle2, ChevronLeft, ChevronRight, MessageCircle, Pencil, Plus, Trash2, UserX, XCircle } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseStatusPill, { type TomStatus } from '@/shared/components/ui/BaseStatusPill/BaseStatusPill.vue';

import OSClienteSearchModal from '@/modules/order-service/ordens/components/OSClienteSearchModal.vue';
import type { CustomerUnionReadSchemaDataType } from '@/modules/order-service/ordens/schemas/relationship/customer/customer.schema';
import type { ObjetoBuscaItemDataType } from '@/modules/order-service/ordens/schemas/relationship/objetoBusca.schema';
import { getCustomerByIdForOS } from '@/modules/order-service/ordens/services/relationship/osRelationshipGet.service';
import { useToast } from '@/shared/composables/useToast';

import { useEntradaLavagem } from '../../comanda/composables/useEntradaLavagem';
import type { Agendamento, AgendamentoEntrada, SituacaoAgenda } from '../../shared/schemas/agenda.schema';
import { horaLocal, linkWhatsApp, reais } from '../../shared/utils/lavaRapido';
import { diaISO, diasDaSemana, instanteDoBackend, useAgendaMutations, useAgendaSemana } from '../composables/useAgenda';
import AgendamentoModal from './AgendamentoModal.vue';

const diaAberto = ref(new Date());
const { data: agendamentos, isLoading, isError } = useAgendaSemana(diaAberto);
const { criar, atualizar, excluir } = useAgendaMutations();

const semana = computed(() => diasDaSemana(diaAberto.value));
const hojeISO = diaISO(new Date());
const NOMES_DIA = ['seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom'];

function doDia(dia: Date): Agendamento[] {
  const alvo = diaISO(dia);
  return (agendamentos.value ?? []).filter((a) => diaISO(instanteDoBackend(a.inicio)) === alvo);
}
/** Ativos (agendados) por dia, para a faixa da semana. */
const contagem = (dia: Date) => doDia(dia).filter((a) => a.situacao === 'AGENDADO').length;
const doDiaAberto = computed(() => doDia(diaAberto.value));

function mudarSemana(passo: number) {
  const d = new Date(diaAberto.value);
  d.setDate(d.getDate() + passo * 7);
  diaAberto.value = d;
}

const ROTULO: Record<SituacaoAgenda, { texto: string; tom: TomStatus }> = {
  AGENDADO: { texto: 'Agendado', tom: 'info' },
  CHEGOU: { texto: 'Chegou', tom: 'sucesso' },
  NAO_VEIO: { texto: 'Não veio', tom: 'alerta' },
  CANCELADO: { texto: 'Cancelado', tom: 'neutro' },
};

function mensagemConfirmacao(a: Agendamento): string {
  const quando = instanteDoBackend(a.inicio);
  const nome = a.cliente_nome.split(' ')[0];
  const dia = quando.toLocaleDateString('pt-BR', { weekday: 'long', day: '2-digit', month: '2-digit' });
  return `Olá, ${nome}! Confirmando sua lavagem ${dia} às ${horaLocal(a.inicio)}${a.veiculo ? ` (${a.veiculo})` : ''}. Até lá!`;
}

// --- Novo / editar ------------------------------------------------------------------
// Novo: primeiro o cliente, pela busca de sempre (como a Nova OS); depois o agendamento.
const modalAberto = ref(false);
const editando = ref<Agendamento | null>(null);
const buscandoCliente = ref(false);
const clienteDoNovo = ref<CustomerUnionReadSchemaDataType | null>(null);
const objetoDoNovo = ref<ObjetoBuscaItemDataType | null>(null);
const toast = useToast();
function novo() {
  editando.value = null;
  clienteDoNovo.value = null;
  objetoDoNovo.value = null;
  buscandoCliente.value = true;
}
function clienteEscolhido(c: CustomerUnionReadSchemaDataType) {
  clienteDoNovo.value = c;
  buscandoCliente.value = false;
  modalAberto.value = true;
}
async function veiculoEscolhido(o: ObjetoBuscaItemDataType) {
  try {
    clienteDoNovo.value = await getCustomerByIdForOS(o.cliente_id);
  } catch {
    toast.error('Não foi possível carregar o dono do veículo.');
    return;
  }
  objetoDoNovo.value = o;
  buscandoCliente.value = false;
  modalAberto.value = true;
}
function editar(a: Agendamento) { editando.value = a; modalAberto.value = true; }
function salvar(dados: AgendamentoEntrada) {
  const fechar = { onSuccess: () => { modalAberto.value = false; } };
  if (editando.value) atualizar.mutate({ id: editando.value.id, dados }, fechar);
  else criar.mutate(dados, fechar);
}

function situacao(a: Agendamento, nova: SituacaoAgenda) {
  atualizar.mutate({ id: a.id, dados: { situacao: nova } });
}

// --- Chegou: a comanda de sempre, preenchida com o combinado ------------------------------
const { chegouAgendado } = useEntradaLavagem();
function chegou(a: Agendamento) {
  void chegouAgendado(a, (numeroOs) =>
    atualizar.mutate({ id: a.id, dados: { situacao: 'CHEGOU', numero_os: numeroOs } }));
}
</script>

<template>
  <div class="space-y-6" data-testid="agenda">
    <!-- Semana -->
    <div class="flex flex-wrap items-center gap-3">
      <button type="button" class="rounded-lg border border-zinc-200 p-2 text-zinc-500 hover:text-brand-primary" title="Semana anterior" @click="mudarSemana(-1)">
        <ChevronLeft :size="16" />
      </button>
      <div class="grid flex-1 grid-cols-7 gap-2">
        <button
          v-for="(dia, i) in semana"
          :key="diaISO(dia)"
          type="button"
          class="flex flex-col items-center rounded-2xl border px-2 py-2 transition-colors"
          :class="diaISO(dia) === diaISO(diaAberto)
            ? 'border-brand-primary bg-brand-primary text-white'
            : diaISO(dia) === hojeISO
              ? 'border-brand-primary bg-white text-brand-primary'
              : 'border-zinc-200 bg-white text-zinc-700 hover:border-brand-primary'"
          @click="diaAberto = dia"
        >
          <span class="text-[11px] uppercase">{{ NOMES_DIA[i] }}</span>
          <span class="text-lg font-bold leading-tight">{{ dia.getDate() }}</span>
          <span class="text-[11px]" :class="contagem(dia) ? '' : 'opacity-50'">{{ contagem(dia) || '—' }}</span>
        </button>
      </div>
      <button type="button" class="rounded-lg border border-zinc-200 p-2 text-zinc-500 hover:text-brand-primary" title="Próxima semana" @click="mudarSemana(1)">
        <ChevronRight :size="16" />
      </button>
      <BaseButton variant="secondary" size="sm" @click="diaAberto = new Date()">Hoje</BaseButton>
      <BaseButton size="md" class="flex gap-1" data-testid="novo-agendamento" @click="novo">
        <Plus :size="18" /> Novo agendamento
      </BaseButton>
    </div>

    <!-- Dia -->
    <section class="rounded-3xl border border-zinc-200 bg-white">
      <header class="flex items-center gap-2 border-b border-zinc-100 px-5 py-4">
        <CalendarClock :size="18" class="text-brand-primary" />
        <h3 class="text-sm font-semibold capitalize text-zinc-800">
          {{ diaAberto.toLocaleDateString('pt-BR', { weekday: 'long', day: '2-digit', month: 'long' }) }}
        </h3>
        <span class="ml-auto text-xs text-zinc-500">{{ doDiaAberto.length }} agendamento(s)</span>
      </header>

      <p v-if="isLoading" class="p-6 text-sm text-zinc-400">Carregando…</p>
      <p v-else-if="isError" class="p-6 text-sm text-red-600">Não foi possível carregar a agenda.</p>
      <p v-else-if="!doDiaAberto.length" class="p-10 text-center text-sm text-zinc-400">Nenhum agendamento neste dia.</p>

      <ul v-else class="divide-y divide-zinc-100">
        <li
          v-for="a in doDiaAberto"
          :key="a.id"
          class="flex flex-wrap items-center gap-4 px-5 py-4"
          :class="a.situacao === 'CANCELADO' || a.situacao === 'NAO_VEIO' ? 'opacity-60' : ''"
        >
          <div class="w-16 shrink-0 text-center">
            <p class="text-lg font-bold tabular-nums text-zinc-900">{{ horaLocal(a.inicio) }}</p>
            <p v-if="a.duracao_minutos" class="text-[11px] text-zinc-400">{{ a.duracao_minutos }} min</p>
          </div>

          <div class="min-w-48 flex-1">
            <p class="text-sm font-semibold text-zinc-800">{{ a.cliente_nome }}</p>
            <p class="text-xs text-zinc-500">
              <span v-if="a.placa" class="font-mono font-semibold">{{ a.placa }}</span>
              <span v-if="a.veiculo"> · {{ a.veiculo }}</span>
            </p>
            <p v-if="a.servicos.length" class="mt-0.5 text-xs text-zinc-600">
              {{ a.servicos.map((s) => s.nome).join(', ') }} · {{ reais(a.servicos.reduce((t, s) => t + s.valor, 0)) }}
            </p>
            <p v-if="a.observacao" class="mt-0.5 text-xs italic text-zinc-400">{{ a.observacao }}</p>
          </div>

          <BaseStatusPill :tom="ROTULO[a.situacao].tom">
            {{ ROTULO[a.situacao].texto }}<template v-if="a.numero_os"> · {{ a.numero_os }}</template>
          </BaseStatusPill>

          <div v-if="a.situacao === 'AGENDADO'" class="flex flex-wrap items-center gap-1.5">
            <BaseButton size="sm" @click="chegou(a)">
              <CheckCircle2 :size="14" class="mr-1" /> Chegou
            </BaseButton>
            <a
              v-if="linkWhatsApp(a.cliente_contato, mensagemConfirmacao(a))"
              :href="linkWhatsApp(a.cliente_contato, mensagemConfirmacao(a)) ?? undefined"
              target="_blank"
              rel="noopener"
              class="inline-flex min-h-9 items-center gap-1 rounded-lg border border-emerald-200 px-2.5 text-xs font-semibold text-emerald-700 hover:bg-emerald-50"
              title="Confirmar pelo WhatsApp"
            >
              <MessageCircle :size="14" />
            </a>
            <button type="button" class="rounded-lg p-2 text-zinc-400 hover:text-zinc-700" title="Editar" @click="editar(a)">
              <Pencil :size="14" />
            </button>
            <button type="button" class="rounded-lg p-2 text-zinc-400 hover:text-amber-600" title="Não veio" @click="situacao(a, 'NAO_VEIO')">
              <UserX :size="14" />
            </button>
            <button type="button" class="rounded-lg p-2 text-zinc-400 hover:text-red-600" title="Cancelar" @click="situacao(a, 'CANCELADO')">
              <XCircle :size="14" />
            </button>
          </div>
          <div v-else-if="a.situacao !== 'CHEGOU'" class="flex items-center gap-1.5">
            <button type="button" class="text-xs font-semibold text-brand-primary hover:underline" @click="situacao(a, 'AGENDADO')">
              Reagendar
            </button>
            <button
              v-if="a.situacao === 'CANCELADO'"
              type="button"
              class="rounded-lg p-2 text-zinc-400 hover:text-red-600"
              title="Excluir"
              @click="excluir.mutate(a.id)"
            >
              <Trash2 :size="14" />
            </button>
          </div>
        </li>
      </ul>
    </section>

    <OSClienteSearchModal
      :is-open="buscandoCliente"
      @close="buscandoCliente = false"
      @select-cliente="clienteEscolhido"
      @select-objeto="veiculoEscolhido"
    />

    <AgendamentoModal
      :is-open="modalAberto"
      :agendamento="editando"
      :cliente="clienteDoNovo"
      :objeto="objetoDoNovo"
      :dia-sugerido="diaAberto"
      :salvando="criar.isPending.value || atualizar.isPending.value"
      @close="modalAberto = false"
      @salvar="salvar"
    />
  </div>
</template>
