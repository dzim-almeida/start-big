<script setup lang="ts">
/**
 * @component AgendarModal
 * @description Agendar (ou remarcar) a instalação (Spec 13B D2; 13A D9).
 *
 * Data (obrigatória), hora (opcional), os ambientes ainda não entregues e os
 * montadores (funcionários). Montador em outra obra no mesmo dia não trava:
 * o aviso vem na resposta e a aba mostra (13A D11).
 */
import { computed, ref, watch } from 'vue';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseDateInput from '@/shared/components/ui/BaseDateInput/BaseDateInput.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import type { OpcaoFuncionario } from '@/modules/marcenaria/producao/utils/producao';
import { hojeIso } from '@/modules/marcenaria/terceirizados/utils/terceirizados';

import type { Agendamento, EntregaAmbiente } from '../schemas/entrega.schema';
import type { AgendamentoEnvio } from '../services/agenda.service';
import { ambientesAgendaveis } from '../utils/entrega';

const props = defineProps<{
  isOpen: boolean;
  entregas: EntregaAmbiente[];
  funcionarios: OpcaoFuncionario[];
  /** Remarcando: o agendamento de antes. Novo: null. */
  agendamento: Agendamento | null;
  gravando: boolean;
}>();
const emit = defineEmits<{ close: []; confirmar: [dados: AgendamentoEnvio] }>();

const data = ref('');
const hora = ref('');
const ambientes = ref<number[]>([]);
const montadores = ref<number[]>([]);
const observacao = ref('');
const tentou = ref(false);                            // só mostra os erros depois do primeiro clique

/** Amanhã, no relógio da loja (o caso comum: agendar para o dia seguinte). */
function amanha(): string {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return hojeIso(d);
}

// Abriu: os dados do agendamento (remarcar) ou o padrão (novo).
watch(() => props.isOpen, (aberto) => {
  if (!aberto) return;
  const a = props.agendamento;
  data.value = a?.data ?? amanha();
  hora.value = a?.hora_inicio ?? '';
  ambientes.value = a ? [...a.ambiente_ids] : [];
  montadores.value = a ? a.montadores.map((m) => m.funcionario_id) : [];
  observacao.value = a?.observacao ?? '';
  tentou.value = false;
}, { immediate: true });

/** Os ambientes que dá para agendar: os pendentes (e os que o agendamento já tinha). */
const opcoesAmbiente = computed(() => ambientesAgendaveis(props.entregas, props.agendamento));

/** Os montadores do agendamento que já não estão na lista (saíram) continuam visíveis. */
const opcoesMontador = computed(() => {
  const lista = [...props.funcionarios];
  for (const m of props.agendamento?.montadores ?? []) {
    if (!lista.some((f) => f.id === m.funcionario_id)) lista.push({ id: m.funcionario_id, nome: m.nome });
  }
  return lista;
});

const erro = computed(() => {
  if (!data.value) return 'Informe a data da instalação.';
  if (!ambientes.value.length || !montadores.value.length) return 'Escolha pelo menos um ambiente e um montador.';
  return '';
});

/** Marca ou desmarca um id numa lista (ambientes e montadores). */
function alternar(lista: number[], id: number): number[] {
  return lista.includes(id) ? lista.filter((x) => x !== id) : [...lista, id];
}

function confirmar() {
  tentou.value = true;
  if (erro.value || props.gravando) return;
  emit('confirmar', {
    data: data.value,
    hora_inicio: hora.value || null,
    ambiente_ids: ambientes.value,
    montadores: montadores.value,
    observacao: observacao.value.trim() || null,
  });
}
</script>

<template>
  <BaseModal :is-open="isOpen" :title="agendamento ? 'Remarcar instalação' : 'Agendar instalação'" size="md" overlay @close="emit('close')">
    <div class="flex flex-col gap-4">
      <div class="grid grid-cols-2 gap-3">
        <BaseDateInput v-model="data" label="Data" required />
        <label class="flex flex-col gap-1 text-sm font-medium text-zinc-700">
          Hora (opcional)
          <input
            v-model="hora"
            type="time"
            class="rounded-lg border border-zinc-300 px-3 py-2 text-sm font-normal focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
            data-testid="hora-agendamento"
          />
        </label>
      </div>
      <p v-if="data && data < hojeIso()" class="-mt-2 text-xs text-amber-700">A data já passou: o agendamento já nasce atrasado.</p>

      <fieldset class="flex flex-col gap-1.5">
        <legend class="mb-1 text-sm font-medium text-zinc-700">Ambientes</legend>
        <label v-for="e in opcoesAmbiente" :key="e.ambiente_id" class="flex items-center gap-2 text-sm text-zinc-700">
          <input
            type="checkbox"
            class="h-4 w-4 accent-brand-primary"
            :checked="ambientes.includes(e.ambiente_id)"
            :data-testid="`ambiente-${e.ambiente_id}`"
            @change="ambientes = alternar(ambientes, e.ambiente_id)"
          />
          {{ e.ambiente }}
        </label>
        <p v-if="!opcoesAmbiente.length" class="text-sm text-zinc-500">Todos os ambientes já foram entregues.</p>
      </fieldset>

      <fieldset class="flex flex-col gap-1.5">
        <legend class="mb-1 text-sm font-medium text-zinc-700">Montadores</legend>
        <div class="grid grid-cols-2 gap-1.5">
          <label v-for="f in opcoesMontador" :key="f.id" class="flex items-center gap-2 text-sm text-zinc-700">
            <input
              type="checkbox"
              class="h-4 w-4 accent-brand-primary"
              :checked="montadores.includes(f.id)"
              :data-testid="`montador-${f.id}`"
              @change="montadores = alternar(montadores, f.id)"
            />
            {{ f.nome }}
          </label>
        </div>
        <p v-if="!opcoesMontador.length" class="text-sm text-zinc-500">Nenhum funcionário disponível.</p>
      </fieldset>

      <label class="flex flex-col gap-1 text-sm font-medium text-zinc-700">
        Observação
        <input
          v-model="observacao"
          type="text"
          maxlength="300"
          class="rounded-lg border border-zinc-300 px-3 py-2 text-sm font-normal focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
          placeholder="Ex.: levar o espelho"
        />
      </label>

      <p v-if="tentou && erro" class="text-xs text-red-600" data-testid="erro-agendar">{{ erro }}</p>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton :is-loading="gravando" data-testid="confirmar-agendar" @click="confirmar">
          {{ agendamento ? 'Salvar' : 'Agendar' }}
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
