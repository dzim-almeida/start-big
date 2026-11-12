<script setup lang="ts">
/**
 * @component AgendamentoModal
 * @description Novo agendamento ou edição (Spec 08B, SPEC-00 O11).
 *
 * O mínimo para o balcão reconhecer quem vem e preparar o box: dia e hora,
 * cliente (cadastrado ou só nome e telefone), veículo, porte e serviços. A
 * duração sai da soma dos serviços do porte e pode ser mudada.
 */
import { computed, ref, watch } from 'vue';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import type { CustomerUnionReadSchemaDataType } from '@/modules/order-service/ordens/schemas/relationship/customer/customer.schema';
import OSClienteSearchModal from '@/modules/order-service/ordens/components/OSClienteSearchModal.vue';
import type { ObjetoBuscaItemDataType } from '@/modules/order-service/ordens/schemas/relationship/objetoBusca.schema';
import { getCustomerByIdForOS } from '@/modules/order-service/ordens/services/relationship/osRelationshipGet.service';
import { useTiposDeTrabalho } from '@/modules/order-service/shared/segmento/useTiposDeTrabalho';

import { usePortesQuery, useServicosDoPorteQuery } from '../../shared/composables/usePortes';
import type { Agendamento, AgendamentoEntrada } from '../../shared/schemas/agenda.schema';
import { normalizarPlaca, reais } from '../../shared/utils/lavaRapido';
import { nomeDoCliente } from '../../comanda/composables/useComanda';
import { diaISO, instanteDoBackend } from '../composables/useAgenda';

const props = defineProps<{
  isOpen: boolean;
  /** Editando este; `null` = novo. */
  agendamento: Agendamento | null;
  /** Novo: o cliente escolhido na busca de sempre, ANTES do modal (padrão da OS). */
  cliente?: CustomerUnionReadSchemaDataType | null;
  /** Novo: o veículo achado pela placa na busca. */
  objeto?: ObjetoBuscaItemDataType | null;
  /** Dia sugerido para um novo (o dia aberto na agenda). */
  diaSugerido: Date;
  salvando?: boolean;
}>();
const emit = defineEmits<{ close: []; salvar: [dados: AgendamentoEntrada] }>();

const { opcoes: tiposDeVeiculo } = useTiposDeTrabalho();
const { data: portes, ativosDoTipo } = usePortesQuery();

// --- Formulário ------------------------------------------------------------------
const dia = ref('');
const hora = ref('08:00');
const clienteId = ref<number | null>(null);
const clienteNome = ref('');
const clienteContato = ref('');
const placa = ref('');
const veiculo = ref('');
const tipo = ref('');
const porteId = ref<number | null>(null);
/** servico_id → valor combinado (centavos). */
const selecionados = ref<Record<number, { nome: string; valor: number }>>({});
const duracao = ref('');
const duracaoEditada = ref(false);
const observacao = ref('');

const { data: servicosDoPorte } = useServicosDoPorteQuery(porteId);
const portesDoTipo = computed(() => ativosDoTipo(tipo.value));

watch(() => props.isOpen, (aberto) => {
  if (!aberto) return;
  const a = props.agendamento;
  if (a) {
    const quando = instanteDoBackend(a.inicio);
    dia.value = diaISO(quando);
    hora.value = quando.toTimeString().slice(0, 5);
    clienteId.value = a.cliente_id;
    clienteNome.value = a.cliente_nome;
    clienteContato.value = a.cliente_contato ?? '';
    placa.value = a.placa ?? '';
    veiculo.value = a.veiculo ?? '';
    tipo.value = a.tipo_veiculo ?? tiposDeVeiculo.value[0]?.value ?? '';
    porteId.value = a.porte_id;
    selecionados.value = Object.fromEntries(
      a.servicos.filter((s) => s.servico_id).map((s) => [s.servico_id as number, { nome: s.nome, valor: s.valor }]));
    duracao.value = a.duracao_minutos ? String(a.duracao_minutos) : '';
    duracaoEditada.value = !!a.duracao_minutos;
    observacao.value = a.observacao ?? '';
  } else {
    dia.value = diaISO(props.diaSugerido);
    hora.value = '08:00';
    clienteId.value = null;
    clienteNome.value = '';
    clienteContato.value = '';
    placa.value = '';
    veiculo.value = '';
    tipo.value = tiposDeVeiculo.value[0]?.value ?? '';
    porteId.value = null;
    selecionados.value = {};
    duracao.value = '';
    duracaoEditada.value = false;
    observacao.value = '';
    if (props.cliente) aplicarCliente(props.cliente);
    if (props.objeto) aplicarVeiculo(props.objeto);
  }
});

/** Cliente do cadastro: nome e o contato para o WhatsApp de confirmação. */
function aplicarCliente(c: CustomerUnionReadSchemaDataType) {
  const x = c as unknown as { celular?: string | null; telefone?: string | null };
  clienteId.value = c.id;
  clienteNome.value = nomeDoCliente(c);
  clienteContato.value = x.celular ?? x.telefone ?? '';
}

/** Veículo achado pela placa: placa, modelo e o porte que ele já tem. */
function aplicarVeiculo(o: ObjetoBuscaItemDataType) {
  placa.value = o.numero_serie ?? '';
  veiculo.value = [o.modelo, o.cor].filter(Boolean).join(' ');
  const nomePorte = String((o.dados_adicionais ?? {}).porte ?? '').toLowerCase();
  const achado = (portes.value ?? []).find((p) => p.ativo && p.nome.toLowerCase() === nomePorte);
  if (achado) {
    tipo.value = achado.tipo_veiculo;
    porteId.value = achado.id;
  }
}

// "Trocar" cliente: a mesma busca de cliente/placa da OS.
const trocandoCliente = ref(false);
function clienteTrocado(c: CustomerUnionReadSchemaDataType) {
  aplicarCliente(c);
  trocandoCliente.value = false;
}
async function veiculoTrocado(o: ObjetoBuscaItemDataType) {
  trocandoCliente.value = false;
  try {
    aplicarCliente(await getCustomerByIdForOS(o.cliente_id));
    aplicarVeiculo(o);
  } catch {
    // sem o dono, segue com o cliente que já estava
  }
}

// Trocou o tipo: porte de outro tipo não vale.
watch(tipo, (novo, antigo) => {
  if (antigo && novo !== antigo && !portesDoTipo.value.some((p) => p.id === porteId.value)) porteId.value = null;
});

// Duração = soma dos serviços escolhidos, até alguém mexer à mão.
const duracaoCalculada = computed(() =>
  (servicosDoPorte.value ?? [])
    .filter((s) => s.servico_id in selecionados.value)
    .reduce((soma, s) => soma + (s.duracao_minutos ?? 0), 0));
watch(duracaoCalculada, (min) => { if (!duracaoEditada.value) duracao.value = min ? String(min) : ''; });

function alternarServico(servicoId: number, nome: string, valor: number) {
  const atual = { ...selecionados.value };
  if (servicoId in atual) delete atual[servicoId];
  else atual[servicoId] = { nome, valor };
  selecionados.value = atual;
}

const total = computed(() => Object.values(selecionados.value).reduce((s, x) => s + x.valor, 0));

const podeSalvar = computed(() => !!dia.value && !!hora.value && !!clienteNome.value.trim());

function salvar() {
  if (!podeSalvar.value) return;
  const [ano, mes, d] = dia.value.split('-').map(Number);
  const [h, m] = hora.value.split(':').map(Number);
  const inicio = new Date(ano, mes - 1, d, h, m);               // hora LOCAL da loja
  emit('salvar', {
    inicio: inicio.toISOString(),
    duracao_minutos: Number(duracao.value) || null,
    cliente_id: clienteId.value,
    cliente_nome: clienteNome.value.trim(),
    cliente_contato: clienteContato.value.replace(/\D/g, '') || null,
    placa: normalizarPlaca(placa.value) || null,
    veiculo: veiculo.value.trim() || null,
    tipo_veiculo: tipo.value || null,
    porte_id: porteId.value,
    servicos: Object.entries(selecionados.value).map(([id, s]) => ({ servico_id: Number(id), nome: s.nome, valor: s.valor })),
    observacao: observacao.value.trim() || null,
  });
}

function chip(ativo: boolean): string {
  return ativo
    ? 'border-brand-primary bg-brand-primary text-white'
    : 'border-zinc-200 bg-white text-zinc-700 hover:border-brand-primary hover:text-brand-primary';
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    :title="agendamento ? 'Editar agendamento' : 'Novo agendamento'"
    subtitle="O cliente chega, e a lavagem entra no pátio pela comanda"
    size="2xl"
    @close="emit('close')"
  >
    <div class="space-y-5">
      <div class="grid grid-cols-12 gap-3">
        <div class="col-span-6 sm:col-span-4">
          <label class="mb-1 block text-xs font-medium text-zinc-600">Dia</label>
          <input v-model="dia" type="date" class="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm" />
        </div>
        <div class="col-span-6 sm:col-span-3">
          <label class="mb-1 block text-xs font-medium text-zinc-600">Hora</label>
          <input v-model="hora" type="time" step="900" class="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm" />
        </div>
        <div class="col-span-12 sm:col-span-5">
          <BaseInput
            v-model="duracao"
            label="Duração (min)"
            type="text"
            inputmode="numeric"
            placeholder="Soma dos serviços"
            @update:model-value="duracaoEditada = true"
          />
        </div>
      </div>

      <!-- Cliente: escolhido na busca de sempre, antes do modal -->
      <section class="flex items-center justify-between rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-3">
        <div>
          <p class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Cliente</p>
          <p class="text-sm font-semibold text-zinc-800">{{ clienteNome || 'Nenhum cliente selecionado' }}</p>
          <p v-if="clienteContato" class="text-xs text-zinc-500">{{ clienteContato }}</p>
        </div>
        <button type="button" class="text-xs font-semibold text-brand-primary hover:underline" @click="trocandoCliente = true">
          {{ clienteNome ? 'Trocar' : 'Selecionar' }}
        </button>
      </section>

      <!-- Veículo -->
      <section class="space-y-2">
        <p class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Veículo</p>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="t in tiposDeVeiculo"
            :key="t.value"
            type="button"
            class="rounded-full border px-3 py-1 text-sm font-semibold"
            :class="chip(tipo === t.value)"
            @click="tipo = t.value"
          >
            {{ t.label }}
          </button>
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="p in portesDoTipo"
            :key="p.id"
            type="button"
            class="rounded-lg border px-3 py-1 text-sm"
            :class="chip(porteId === p.id)"
            @click="porteId = p.id"
          >
            {{ p.nome }}
          </button>
        </div>
        <div class="grid grid-cols-12 gap-3">
          <div class="col-span-5"><BaseInput v-model="placa" label="Placa" placeholder="ABC1D23" /></div>
          <div class="col-span-7"><BaseInput v-model="veiculo" label="Veículo" placeholder="Ex: Gol prata" /></div>
        </div>
      </section>

      <!-- Serviços -->
      <section class="space-y-2">
        <p class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Serviços</p>
        <p v-if="!porteId" class="text-sm text-zinc-400">Escolha o porte para ver os serviços e os preços.</p>
        <p v-else-if="!(servicosDoPorte ?? []).length" class="rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-800">
          Nenhum serviço cadastrado. Cadastre suas lavagens na aba <strong>Cadastro de Serviços</strong>.
        </p>
        <div v-else class="grid grid-cols-1 gap-2 sm:grid-cols-2">
          <button
            v-for="s in servicosDoPorte ?? []"
            :key="s.servico_id"
            type="button"
            class="flex items-center justify-between rounded-xl border px-3 py-2 text-left"
            :class="chip(s.servico_id in selecionados)"
            @click="alternarServico(s.servico_id, s.descricao, s.valor)"
          >
            <span class="text-sm">{{ s.descricao }}</span>
            <span class="text-sm font-bold tabular-nums">{{ reais(s.valor) }}</span>
          </button>
        </div>
        <p v-if="total" class="text-right text-sm font-semibold text-zinc-800">Total combinado: {{ reais(total) }}</p>
      </section>

      <BaseInput v-model="observacao" label="Observação" placeholder="Ex: busca no trabalho, cliente prefere cera" />
    </div>

    <template #footer>
      <div class="flex w-full justify-end gap-3">
        <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton :is-loading="salvando" :disabled="!podeSalvar" @click="salvar">
          {{ agendamento ? 'Salvar' : 'Agendar' }}
        </BaseButton>
      </div>
    </template>
  </BaseModal>

  <OSClienteSearchModal
    :is-open="trocandoCliente"
    @close="trocandoCliente = false"
    @select-cliente="clienteTrocado"
    @select-objeto="veiculoTrocado"
  />
</template>
