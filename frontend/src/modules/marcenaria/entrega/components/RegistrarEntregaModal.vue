<script setup lang="ts">
/**
 * @component RegistrarEntregaModal
 * @description Passar a limpo o termo que voltou assinado da obra (Spec 13B
 * D5, D6; 13A D4). Também corrige um registro feito antes (13A D5).
 *
 * Na ordem do papel: Conforme / Com ressalvas (botões grandes), a data,
 * quem montou (já marcados os do agendamento), quem recebeu, o checklist em
 * três estados (✓ / ✗ / em branco), observações, pendências (uma por linha,
 * obrigatória com ressalvas) e as fotos (termo assinado e montagem).
 *
 * Sem a foto do termo, PERGUNTA antes de enviar (D6): avisa sem travar.
 */
import { computed, ref, watch } from 'vue';
import { Check, X } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseConfirmModal from '@/shared/components/commons/BaseConfirmModal/BaseConfirmModal.vue';
import BaseDateInput from '@/shared/components/ui/BaseDateInput/BaseDateInput.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import { useConfirmacao } from '@/shared/composables/useConfirmacao';
import type { OpcaoFuncionario } from '@/modules/marcenaria/producao/utils/producao';
import { hojeIso } from '@/modules/marcenaria/terceirizados/utils/terceirizados';

import type { EntregaAmbiente, Marcacao } from '../schemas/entrega.schema';
import type { RegistroEntrega } from '../services/entrega.service';
import { registrada, type FotosDoRegistro } from '../utils/entrega';

const props = defineProps<{
  isOpen: boolean;
  entrega: EntregaAmbiente | null;
  funcionarios: OpcaoFuncionario[];
  gravando: boolean;
}>();
const emit = defineEmits<{ close: []; confirmar: [registro: RegistroEntrega, fotos: FotosDoRegistro] }>();

const situacao = ref<'CONFORME' | 'COM_RESSALVAS' | null>(null);
const data = ref('');
const montadores = ref<number[]>([]);
const recebidoPor = ref('');
const marcacoes = ref<Marcacao[]>([]);
const observacoes = ref('');
const pendencias = ref('');
const fotoTermo = ref<File | null>(null);
const fotosMontagem = ref<File[]>([]);
const tentou = ref(false);
const confirmacao = useConfirmacao();

const corrigindo = computed(() => (props.entrega ? registrada(props.entrega) : false));

// Abriu: o registro de antes (corrigir) ou o padrão (hoje, montadores do agendamento, tudo em branco).
watch(() => props.isOpen, (aberto) => {
  const e = props.entrega;
  if (!aberto || !e) return;
  const ja = registrada(e);
  situacao.value = ja ? (e.situacao as 'CONFORME' | 'COM_RESSALVAS') : null;
  data.value = e.data_entrega ?? hojeIso();
  // D5 (caso 06): pré-marcados os montadores do agendamento do ambiente.
  montadores.value = (ja ? e.montadores : e.agendamento?.montadores ?? []).map((m) => m.funcionario_id);
  recebidoPor.value = e.recebido_por ?? '';
  marcacoes.value = e.checklist.map((i) => (ja ? i.marcacao : null));
  observacoes.value = e.observacoes ?? '';
  pendencias.value = '';
  fotoTermo.value = null;
  fotosMontagem.value = [];
  tentou.value = false;
}, { immediate: true });

/** Quem já montou e saiu da empresa continua na lista (está no registro). */
const opcoesMontador = computed(() => {
  const lista = [...props.funcionarios];
  const conhecidos = [...(props.entrega?.montadores ?? []), ...(props.entrega?.agendamento?.montadores ?? [])];
  for (const m of conhecidos) {
    if (!lista.some((f) => f.id === m.funcionario_id)) lista.push({ id: m.funcionario_id, nome: m.nome });
  }
  return lista;
});

/** As pendências digitadas: uma por linha, sem as linhas em branco. */
const linhasDePendencia = computed(() => pendencias.value.split('\n').map((l) => l.trim()).filter(Boolean));

/** D4 (caso 04): com ressalvas, pelo menos uma pendência (as que já existem contam). */
const erroPendencias = computed(() =>
  (situacao.value === 'COM_RESSALVAS' && !linhasDePendencia.value.length && !props.entrega?.pendencias.length
    ? 'Com ressalvas, informe pelo menos uma pendência.'
    : ''));
const erroData = computed(() => (data.value && data.value > hojeIso() ? 'A data da entrega não pode ser no futuro.' : ''));
const erroSituacao = computed(() => (situacao.value ? '' : 'Escolha Conforme ou Com ressalvas.'));
const temErro = computed(() => !!(erroSituacao.value || erroPendencias.value || erroData.value));

/** Clique no item do checklist: em branco → ✓ → ✗ → em branco. */
function proximaMarcacao(indice: number) {
  const atual = marcacoes.value[indice];
  const proxima: Marcacao = atual === null ? 'ok' : atual === 'ok' ? 'nao_ok' : null;
  marcacoes.value = marcacoes.value.map((m, i) => (i === indice ? proxima : m));
}

function alternarMontador(id: number) {
  montadores.value = montadores.value.includes(id) ? montadores.value.filter((x) => x !== id) : [...montadores.value, id];
}

function escolherTermo(evento: Event) {
  fotoTermo.value = (evento.target as HTMLInputElement).files?.[0] ?? null;
}
function escolherMontagem(evento: Event) {
  fotosMontagem.value = [...((evento.target as HTMLInputElement).files ?? [])];
}

/** Já tem foto do termo (de antes ou escolhida agora)? */
const temFotoDoTermo = computed(() =>
  !!fotoTermo.value || !!props.entrega?.fotos.some((f) => f.tipo === 'TERMO'));

async function confirmar() {
  tentou.value = true;
  if (temErro.value || props.gravando || !situacao.value) return;
  // D6: sem a foto do termo, pergunta (o papel assinado é a prova).
  if (!temFotoDoTermo.value) {
    const ok = await confirmacao.pedirConfirmacao({
      titulo: 'Registrar sem a foto do termo assinado?',
      descricao: 'O termo assinado é a prova da entrega. Dá para enviar a foto depois, pelo cartão do ambiente.',
      confirmLabel: 'Registrar sem a foto',
    });
    if (!ok) return;
  }
  emit('confirmar', {
    situacao: situacao.value,
    data_entrega: data.value || null,
    montadores: montadores.value,
    recebido_por: recebidoPor.value.trim() || null,
    checklist: marcacoes.value,
    observacoes: observacoes.value.trim() || null,
    pendencias: linhasDePendencia.value,
  }, { termo: fotoTermo.value, montagem: fotosMontagem.value });
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    :title="corrigindo ? 'Corrigir registro da entrega' : 'Registrar entrega'"
    :subtitle="entrega?.ambiente"
    size="lg"
    overlay
    @close="emit('close')"
  >
    <div v-if="entrega" class="flex flex-col gap-4">
      <!-- A situação: botões grandes (o que o montador marcou no papel) -->
      <div class="grid grid-cols-2 gap-3">
        <button
          type="button"
          class="rounded-xl border-2 px-4 py-3 text-base font-bold transition-colors cursor-pointer"
          :class="situacao === 'CONFORME' ? 'border-emerald-500 bg-emerald-50 text-emerald-800' : 'border-zinc-200 text-zinc-600 hover:bg-zinc-50'"
          data-testid="situacao-conforme"
          @click="situacao = 'CONFORME'"
        >
          Conforme
        </button>
        <button
          type="button"
          class="rounded-xl border-2 px-4 py-3 text-base font-bold transition-colors cursor-pointer"
          :class="situacao === 'COM_RESSALVAS' ? 'border-amber-500 bg-amber-50 text-amber-800' : 'border-zinc-200 text-zinc-600 hover:bg-zinc-50'"
          data-testid="situacao-ressalvas"
          @click="situacao = 'COM_RESSALVAS'"
        >
          Com ressalvas
        </button>
      </div>
      <p v-if="tentou && erroSituacao" class="-mt-2 text-xs text-red-600">{{ erroSituacao }}</p>

      <div class="grid grid-cols-2 gap-3">
        <BaseDateInput v-model="data" label="Data da entrega" :error="erroData" />
        <label class="flex flex-col gap-1 text-sm font-medium text-zinc-700">
          Recebido por
          <input
            v-model="recebidoPor"
            type="text"
            maxlength="150"
            placeholder="Quem assinou na obra"
            class="rounded-lg border border-zinc-300 px-3 py-2 text-sm font-normal focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
            data-testid="recebido-por"
          />
        </label>
      </div>

      <fieldset>
        <legend class="mb-1 text-sm font-medium text-zinc-700">Montadores</legend>
        <div class="grid grid-cols-2 gap-1.5">
          <label v-for="f in opcoesMontador" :key="f.id" class="flex items-center gap-2 text-sm text-zinc-700">
            <input
              type="checkbox"
              class="h-4 w-4 accent-brand-primary"
              :checked="montadores.includes(f.id)"
              :data-testid="`registro-montador-${f.id}`"
              @change="alternarMontador(f.id)"
            />
            {{ f.nome }}
          </label>
        </div>
      </fieldset>

      <!-- O checklist em três estados, na ordem do papel (D5) -->
      <fieldset v-if="entrega.checklist.length">
        <legend class="mb-1 text-sm font-medium text-zinc-700">Checklist (clique: ✓ → ✗ → em branco)</legend>
        <ul class="flex flex-col gap-1">
          <li v-for="(item, i) in entrega.checklist" :key="i">
            <button
              type="button"
              class="flex w-full items-center gap-2 rounded-lg border px-3 py-1.5 text-left text-sm cursor-pointer"
              :class="marcacoes[i] === 'ok' ? 'border-emerald-200 bg-emerald-50' : marcacoes[i] === 'nao_ok' ? 'border-red-200 bg-red-50' : 'border-zinc-200'"
              :data-testid="`marcacao-${i}`"
              :data-marcacao="marcacoes[i] ?? ''"
              @click="proximaMarcacao(i)"
            >
              <span class="flex h-5 w-5 shrink-0 items-center justify-center rounded border border-zinc-300 bg-white">
                <Check v-if="marcacoes[i] === 'ok'" :size="14" class="text-emerald-700" />
                <X v-else-if="marcacoes[i] === 'nao_ok'" :size="14" class="text-red-700" />
              </span>
              {{ item.texto }}
            </button>
          </li>
        </ul>
      </fieldset>

      <label class="flex flex-col gap-1 text-sm font-medium text-zinc-700">
        Pendências (uma por linha)
        <textarea
          v-model="pendencias"
          rows="3"
          class="rounded-lg border px-3 py-2 text-sm font-normal focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
          :class="tentou && erroPendencias ? 'border-red-400' : 'border-zinc-300'"
          placeholder="Ex.: porta do aéreo 2 desalinhada"
          data-testid="pendencias"
        />
      </label>
      <p v-if="tentou && erroPendencias" class="-mt-3 text-xs text-red-600" data-testid="erro-pendencias">{{ erroPendencias }}</p>
      <p v-else-if="entrega.pendencias.length" class="-mt-3 text-xs text-zinc-500">
        Este ambiente já tem {{ entrega.pendencias.length }} pendência(s); as novas se somam a elas.
      </p>

      <label class="flex flex-col gap-1 text-sm font-medium text-zinc-700">
        Observações
        <textarea v-model="observacoes" rows="2" maxlength="1000" class="rounded-lg border border-zinc-300 px-3 py-2 text-sm font-normal focus:outline-none focus:ring-2 focus:ring-brand-primary/30" />
      </label>

      <!-- As fotos: sobem para a galeria da OS antes do registro (13A D7) -->
      <div class="grid grid-cols-2 gap-3">
        <label class="flex flex-col gap-1 text-sm font-medium text-zinc-700">
          Foto do termo assinado
          <input type="file" accept="image/*" class="text-xs font-normal" data-testid="foto-termo" @change="escolherTermo" />
          <span v-if="entrega.fotos.some((f) => f.tipo === 'TERMO')" class="text-xs font-normal text-emerald-700">Já há foto do termo.</span>
        </label>
        <label class="flex flex-col gap-1 text-sm font-medium text-zinc-700">
          Fotos da montagem
          <input type="file" accept="image/*" multiple class="text-xs font-normal" data-testid="fotos-montagem" @change="escolherMontagem" />
        </label>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton :is-loading="gravando" data-testid="confirmar-registro" @click="confirmar">
          {{ corrigindo ? 'Salvar correção' : 'Registrar' }}
        </BaseButton>
      </div>
    </template>
  </BaseModal>

  <BaseConfirmModal
    :is-open="confirmacao.isOpen.value"
    :title="confirmacao.opcoes.value.titulo"
    :description="confirmacao.opcoes.value.descricao"
    :confirm-label="confirmacao.opcoes.value.confirmLabel"
    :cancel-label="confirmacao.opcoes.value.cancelLabel"
    :variant="confirmacao.opcoes.value.variant"
    overlay
    @close="confirmacao.cancelar"
    @confirm="confirmacao.confirmar"
  />
</template>
