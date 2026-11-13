<script setup lang="ts">
/**
 * @component AgendaTab
 * @description Agenda do lava-rápido (Spec 08B, SPEC-00 O11): a aba logo
 * depois do Pátio em Serviços.
 *
 * À esquerda, o calendário do mês com quantos agendamentos há por dia
 * (clicar no dia abre a lista); à direita, os horários do dia escolhido.
 * Cada agendamento:
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
import { diaISO, diasDoMes, instanteDoBackend, useAgendaMes, useAgendaMutations } from '../composables/useAgenda';
import AgendamentoModal from './AgendamentoModal.vue';

const diaAberto = ref(new Date());
/** O mês mostrado no calendário (pode ser outro que o do dia aberto). */
const mesVisivel = ref(new Date());
const { data: agendamentos, isLoading, isError } = useAgendaMes(mesVisivel);
const { criar, atualizar, excluir } = useAgendaMutations();

const grade = computed(() => diasDoMes(mesVisivel.value));
const hojeISO = diaISO(new Date());
const NOMES_DIA = ['S', 'T', 'Q', 'Q', 'S', 'S', 'D'];
const tituloMes = computed(() =>
  mesVisivel.value.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' }));

/** Agendamentos por dia ("AAAA-MM-DD"), já em ordem de horário. */
const porDia = computed(() => {
  const mapa = new Map<string, Agendamento[]>();
  for (const a of agendamentos.value ?? []) {
    const chave = diaISO(instanteDoBackend(a.inicio));
    mapa.set(chave, [...(mapa.get(chave) ?? []), a]);
  }
  return mapa;
});
/** Ativos (ainda "Agendado") no dia: é o número que aparece no calendário. */
const contagem = (dia: Date) => (porDia.value.get(diaISO(dia)) ?? []).filter((a) => a.situacao === 'AGENDADO').length;
const doDiaAberto = computed(() => porDia.value.get(diaISO(diaAberto.value)) ?? []);
const doMes = (dia: Date) => dia.getMonth() === mesVisivel.value.getMonth();

function mudarMes(passo: number) {
  mesVisivel.value = new Date(mesVisivel.value.getFullYear(), mesVisivel.value.getMonth() + passo, 1);
}
function escolherDia(dia: Date) {
  diaAberto.value = dia;
  if (!doMes(dia)) mesVisivel.value = new Date(dia.getFullYear(), dia.getMonth(), 1);
}
function irParaHoje() {
  diaAberto.value = new Date();
  mesVisivel.value = new Date();
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
  <div class="grid grid-cols-1 items-start gap-6 lg:grid-cols-[300px_1fr]" data-testid="agenda">
    <!-- Calendário do mês -->
    <aside class="space-y-3">
      <section class="rounded-3xl border border-zinc-200 bg-white p-4">
        <header class="mb-3 flex items-center gap-1">
          <button type="button" class="rounded-lg p-1.5 text-zinc-500 hover:bg-zinc-100 hover:text-brand-primary" title="Mês anterior" @click="mudarMes(-1)">
            <ChevronLeft :size="16" />
          </button>
          <h3 class="flex-1 text-center text-sm font-semibold capitalize text-zinc-800">{{ tituloMes }}</h3>
          <button type="button" class="rounded-lg p-1.5 text-zinc-500 hover:bg-zinc-100 hover:text-brand-primary" title="Próximo mês" @click="mudarMes(1)">
            <ChevronRight :size="16" />
          </button>
        </header>

        <div class="grid grid-cols-7 gap-1 text-center">
          <span v-for="(n, i) in NOMES_DIA" :key="i" class="pb-1 text-[11px] font-semibold text-zinc-400">{{ n }}</span>
          <button
            v-for="dia in grade"
            :key="diaISO(dia)"
            type="button"
            class="relative flex aspect-square flex-col items-center justify-center rounded-lg text-sm transition-colors"
            :class="[
              diaISO(dia) === diaISO(diaAberto)
                ? 'bg-brand-primary font-bold text-white'
                : diaISO(dia) === hojeISO
                  ? 'font-bold text-brand-primary ring-1 ring-brand-primary'
                  : doMes(dia) ? 'text-zinc-700 hover:bg-zinc-100' : 'text-zinc-300 hover:bg-zinc-50',
            ]"
            :title="contagem(dia) ? `${contagem(dia)} agendamento(s)` : undefined"
            :data-testid="`agenda-dia-${diaISO(dia)}`"
            @click="escolherDia(dia)"
          >
            <span class="leading-none">{{ dia.getDate() }}</span>
            <span
              v-if="contagem(dia)"
              class="mt-0.5 min-w-4 rounded-full px-1 text-[10px] font-bold leading-4"
              :class="diaISO(dia) === diaISO(diaAberto) ? 'bg-white text-brand-primary' : 'bg-brand-primary text-white'"
            >{{ contagem(dia) }}</span>
          </button>
        </div>
      </section>

      <BaseButton variant="secondary" size="sm" class="w-full" @click="irParaHoje">Hoje</BaseButton>
    </aside>

    <!-- Dia -->
    <section class="rounded-3xl border border-zinc-200 bg-white">
      <header class="flex flex-wrap items-center gap-2 border-b border-zinc-100 px-5 py-4">
        <CalendarClock :size="18" class="text-brand-primary" />
        <h3 class="text-sm font-semibold capitalize text-zinc-800">
          {{ diaAberto.toLocaleDateString('pt-BR', { weekday: 'long', day: '2-digit', month: 'long' }) }}
        </h3>
        <span class="text-xs text-zinc-500">· {{ doDiaAberto.length }} agendamento(s)</span>
        <BaseButton size="md" class="ml-auto flex gap-1" data-testid="novo-agendamento" @click="novo">
          <Plus :size="18" /> Novo agendamento
        </BaseButton>
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
