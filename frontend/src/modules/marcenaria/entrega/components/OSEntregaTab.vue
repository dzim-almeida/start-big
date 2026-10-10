<script setup lang="ts">
/**
 * @component OSEntregaTab
 * @description Aba "Entrega" do modal de OS da marcenaria (Spec 13B D1-D11).
 *
 * No topo, o resumo ("1 de 3 ambientes entregues · 2 pendências abertas"), o
 * botão "Agendar instalação" e a lista de agendamentos. Abaixo, um cartão por
 * ambiente, com o termo para imprimir, o registro, as fotos e as pendências.
 *
 * Quando o último ambiente é entregue, pergunta se finaliza a OS (D9): quem
 * finaliza é o fluxo de sempre (pagamentos), que o pai abre (`finalizar`).
 * Não conhece o modal de OS: avisa por evento.
 */
import { computed, nextTick, ref, toRef } from 'vue';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseConfirmModal from '@/shared/components/commons/BaseConfirmModal/BaseConfirmModal.vue';
import { useConfirmacao } from '@/shared/composables/useConfirmacao';
import { useToast } from '@/shared/composables/useToast';
import { aguardarImagensDaImpressao, imprimirComPagina } from '@/shared/utils/print.utils';
import { useRotulosStatusOS } from '@/modules/order-service/shared/segmento/useRotulosStatusOS';
import type { OsStatusEnumDataType } from '@/modules/order-service/ordens/schemas/enums/osEnums.schema';
import { statusDoErro } from '@/modules/marcenaria/orcamentos/utils/erros';
import { escaparHtml } from '@/modules/marcenaria/orcamentos/utils/textoSeguro';
import type { OpcaoFuncionario } from '@/modules/marcenaria/producao/utils/producao';
import { diaMes } from '@/modules/marcenaria/producao/utils/producao';

import { useEntregaDaOS } from '../composables/useEntregaDaOS';
import type { Agendamento, EntregaAmbiente, EntregaDaOS, FotoEntrega, Pendencia } from '../schemas/entrega.schema';
import type { AgendamentoEnvio } from '../services/agenda.service';
import type { RegistroEntrega } from '../services/entrega.service';
import {
  nomeArquivoTermo, nomeArquivoTermos, nomesDosMontadores, textoDoResumo, type FotosDoRegistro,
} from '../utils/entrega';
import AgendarModal from './AgendarModal.vue';
import EditarChecklistModal from './EditarChecklistModal.vue';
import EntregaAmbienteCard from './EntregaAmbienteCard.vue';
import PendenciaModal from './PendenciaModal.vue';
import RegistrarEntregaModal from './RegistrarEntregaModal.vue';
import ResolverPendenciaModal from './ResolverPendenciaModal.vue';
import TermoEntregaPrint from './TermoEntregaPrint.vue';

const props = withDefaults(defineProps<{
  numeroOs: string;
  /** Os funcionários ativos (montadores) — os do select do modal de OS. */
  funcionarios?: OpcaoFuncionario[];
}>(), { funcionarios: () => [] });
const emit = defineEmits<{
  /** D9: "Finalizar a OS agora?" — o pai abre a finalização de sempre. */
  finalizar: [];
}>();

const toast = useToast();

// --- Modais (enquanto um está aberto, a aba não recarrega) ------------------------
const agendando = ref<{ aberto: boolean; agendamento: Agendamento | null }>({ aberto: false, agendamento: null });
const registrando = ref<EntregaAmbiente | null>(null);
const checklistDe = ref<EntregaAmbiente | null>(null);
const novaPendenciaDe = ref<EntregaAmbiente | null>(null);
const resolvendo = ref<{ entrega: EntregaAmbiente; pendencia: Pendencia } | null>(null);
const confirmacao = useConfirmacao();
const algumModalAberto = computed(() =>
  agendando.value.aberto || !!registrando.value || !!checklistDe.value || !!novaPendenciaDe.value
  || !!resolvendo.value || confirmacao.isOpen.value);

const {
  data: dados, isLoading, error, gravando,
  agendar, editarAgendamento, excluirAgendamento, editarChecklist, registrar,
  criarPendencia, resolverPendencia, reabrirPendencia, enviarFoto, excluirFoto,
} = useEntregaDaOS(toRef(props, 'numeroOs'), ref(true), algumModalAberto);

const semEntrega = computed(() => statusDoErro(error.value) === 404);
const editavel = computed(() => dados.value?.os.editavel ?? false);

/** OS fechada: a frase com o status no texto do segmento (D10). */
const { rotuloStatus } = useRotulosStatusOS();
const fraseFechada = computed(() => {
  const status = dados.value?.os.status as OsStatusEnumDataType | undefined;
  return status
    ? `A OS está ${rotuloStatus(status).toLowerCase()}: só as pendências ainda podem ser anotadas e resolvidas.`
    : '';
});

/** Mostra os avisos que não travam (montador ocupado, sem foto do termo). */
function mostrarAvisos(resposta: EntregaDaOS | null) {
  for (const aviso of resposta?.avisos ?? []) toast.warning(aviso.mensagem);
}

// --- Agendamentos (D2) ------------------------------------------------------------------
async function confirmarAgendamento(envio: AgendamentoEnvio) {
  const atual = agendando.value.agendamento;
  const resposta = atual ? await editarAgendamento(atual.id, envio) : await agendar(envio);
  if (!resposta) return;                              // erro: o modal fica aberto
  agendando.value = { aberto: false, agendamento: null };
  mostrarAvisos(resposta);                            // 13A D11: montador ocupado (salvo mesmo assim)
}

async function pedirExclusao(agendamento: Agendamento) {
  const ok = await confirmacao.pedirConfirmacao({
    titulo: 'Desmarcar a instalação?',
    descricao: `Instalação de <strong>${diaMes(agendamento.data)}</strong> (${escaparHtml(agendamento.ambientes.join(', '))}).`,
    confirmLabel: 'Desmarcar',
    variant: 'danger',
  });
  if (ok) await excluirAgendamento(agendamento.id);
}

// --- Registro (D5, D6, D9) ---------------------------------------------------------------
async function confirmarRegistro(registro: RegistroEntrega, fotos: FotosDoRegistro) {
  const entrega = registrando.value;
  if (!entrega) return;
  const antesTodos = dados.value?.resumo.todos_entregues ?? false;
  // As fotos sobem ANTES: o registro sabe se já há a foto do termo (13A D8).
  if (fotos.termo && !(await enviarFoto(entrega.id, 'TERMO', fotos.termo))) return;
  for (const arquivo of fotos.montagem) {
    if (!(await enviarFoto(entrega.id, 'MONTAGEM', arquivo))) return;
  }
  const resposta = await registrar(entrega.id, registro);
  if (!resposta) return;
  registrando.value = null;
  // D9: o último ambiente acabou de ser entregue (a correção de um já entregue não pergunta de novo).
  if (resposta.resumo.todos_entregues && !antesTodos) {
    const ok = await confirmacao.pedirConfirmacao({
      titulo: 'Finalizar a OS agora?',
      descricao: 'Todos os ambientes foram entregues. A finalização segue o caminho de sempre, com os pagamentos.',
      confirmLabel: 'Finalizar a OS',
      variant: 'info',
    });
    if (ok) emit('finalizar');
  }
}

async function salvarChecklist(itens: string[]) {
  const entrega = checklistDe.value;
  if (entrega && (await editarChecklist(entrega.id, itens))) checklistDe.value = null;
}

async function confirmarPendencia(descricao: string) {
  const entrega = novaPendenciaDe.value;
  if (entrega && (await criarPendencia(entrega.id, descricao))) novaPendenciaDe.value = null;
}

async function confirmarResolucao(resolucao: string, data: string | null) {
  const alvo = resolvendo.value;
  if (alvo && (await resolverPendencia(alvo.entrega.id, alvo.pendencia.id, resolucao, data))) resolvendo.value = null;
}

async function pedirExclusaoDeFoto(entrega: EntregaAmbiente, foto: FotoEntrega) {
  const ok = await confirmacao.pedirConfirmacao({
    titulo: 'Excluir a foto?',
    descricao: 'Ela sai também da galeria da OS.',
    confirmLabel: 'Excluir',
    variant: 'danger',
  });
  if (ok) await excluirFoto(entrega.id, foto.id);
}

// --- Impressão do termo (D4, D12-D14) -------------------------------------------------------
/** Rede de segurança: se o `afterprint` nunca vier, limpa depois de 2 minutos. */
const LIMPEZA_FORCADA_MS = 2 * 60 * 1000;
/** Os termos montados para imprimir (só existem durante a impressão). */
const termosParaImprimir = ref<EntregaAmbiente[]>([]);

/** Imprime um termo por ambiente, cada um começando numa folha nova. */
async function imprimirTermos(entregas: EntregaAmbiente[], tituloDoPdf: string) {
  if (!entregas.length || termosParaImprimir.value.length) return;
  termosParaImprimir.value = entregas;
  const tituloOriginal = document.title;
  document.title = tituloDoPdf;                        // D14: o nome sugerido do PDF
  await nextTick();                                    // os termos entram no DOM
  await aguardarImagensDaImpressao();                  // a logo da empresa
  let limpezaForcada: ReturnType<typeof setTimeout> | null = null;
  const restaurar = () => {
    document.title = tituloOriginal;
    termosParaImprimir.value = [];
    window.removeEventListener('afterprint', restaurar);
    if (limpezaForcada) clearTimeout(limpezaForcada);
  };
  window.addEventListener('afterprint', restaurar);
  limpezaForcada = setTimeout(restaurar, LIMPEZA_FORCADA_MS);
  imprimirComPagina('A4', { folha: 'A4' });
}

const imprimirTermo = (entrega: EntregaAmbiente) =>
  imprimirTermos([entrega], nomeArquivoTermo(props.numeroOs, entrega.ambiente));

/** D4: os termos de todos os ambientes do agendamento, um por página. */
function imprimirTermosDoAgendamento(agendamento: Agendamento) {
  const entregas = (dados.value?.entregas ?? []).filter((e) => agendamento.ambiente_ids.includes(e.ambiente_id));
  void imprimirTermos(entregas, nomeArquivoTermos(props.numeroOs, agendamento.data));
}
</script>

<template>
  <div class="space-y-4" data-testid="aba-entrega">
    <p v-if="isLoading" class="text-sm text-zinc-400">Carregando a entrega…</p>
    <p v-else-if="semEntrega" class="text-sm text-zinc-500" data-testid="sem-entrega">Esta OS não tem entrega por ambiente.</p>
    <p v-else-if="error" class="text-sm text-red-600">Não foi possível carregar a entrega agora.</p>

    <template v-else-if="dados">
      <!-- Topo: resumo e "Agendar instalação" (D2) -->
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="flex flex-wrap items-center gap-3">
          <h3 class="text-base font-bold text-zinc-800">Entrega</h3>
          <span class="text-sm text-zinc-600" data-testid="resumo-entrega">{{ textoDoResumo(dados.resumo) }}</span>
        </div>
        <BaseButton v-if="editavel" size="sm" data-testid="agendar" @click="agendando = { aberto: true, agendamento: null }">
          Agendar instalação
        </BaseButton>
      </div>

      <!-- OS fechada: só pendências (D10) -->
      <p v-if="!editavel" class="rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm text-zinc-600" data-testid="entrega-fechada">
        {{ fraseFechada }}
      </p>

      <!-- Agendamentos da OS (D2, D4) -->
      <div v-if="dados.agendamentos.length" class="rounded-xl border border-zinc-200 bg-zinc-50/60 p-3">
        <p class="mb-1 text-xs font-bold uppercase tracking-wide text-zinc-500">Agendamentos</p>
        <ul class="flex flex-col gap-1.5">
          <li
            v-for="a in dados.agendamentos"
            :key="a.id"
            class="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm"
            :data-testid="`agendamento-${a.id}`"
          >
            <span class="w-24 font-semibold tabular-nums" :class="a.atrasado ? 'text-red-700' : 'text-zinc-800'">
              {{ diaMes(a.data) }} {{ a.hora_inicio ?? '—' }}
            </span>
            <span class="min-w-40 flex-1 text-zinc-700">{{ a.ambientes.join(', ') }}</span>
            <span class="text-zinc-600">{{ nomesDosMontadores(a.montadores) }}</span>
            <span v-if="a.atrasado" class="rounded-full border border-red-200 bg-red-50 px-2 py-0.5 text-[11px] font-semibold text-red-700" data-testid="atrasado">
              Atrasado
            </span>
            <span v-if="a.observacao" class="w-full pl-27 text-xs text-zinc-500">{{ a.observacao }}</span>
            <span class="flex gap-2">
              <button type="button" class="text-xs font-medium text-brand-primary hover:underline cursor-pointer" :data-testid="`imprimir-termos-${a.id}`" @click="imprimirTermosDoAgendamento(a)">
                Imprimir termos
              </button>
              <template v-if="a.editavel">
                <button type="button" class="text-xs font-medium text-brand-primary hover:underline cursor-pointer" :data-testid="`editar-agendamento-${a.id}`" @click="agendando = { aberto: true, agendamento: a }">
                  Editar
                </button>
                <button type="button" class="text-xs font-medium text-red-600 hover:underline cursor-pointer" :data-testid="`excluir-agendamento-${a.id}`" @click="pedirExclusao(a)">
                  Excluir
                </button>
              </template>
            </span>
          </li>
        </ul>
      </div>

      <!-- Um cartão por ambiente (D3) -->
      <EntregaAmbienteCard
        v-for="entrega in dados.entregas"
        :key="entrega.id"
        :entrega="entrega"
        :editavel="editavel"
        @imprimir-termo="imprimirTermo(entrega)"
        @registrar="registrando = entrega"
        @editar-checklist="checklistDe = entrega"
        @nova-pendencia="novaPendenciaDe = entrega"
        @resolver-pendencia="resolvendo = { entrega, pendencia: $event }"
        @reabrir-pendencia="reabrirPendencia(entrega.id, $event.id)"
        @enviar-foto="(tipo, arquivo) => enviarFoto(entrega.id, tipo, arquivo)"
        @excluir-foto="pedirExclusaoDeFoto(entrega, $event)"
      />
      <p v-if="!dados.entregas.length" class="text-sm text-zinc-500">Esta OS não tem ambientes a entregar.</p>
    </template>

    <!-- Modais (overlay: abrem por cima do modal de OS) -->
    <AgendarModal
      :is-open="agendando.aberto"
      :entregas="dados?.entregas ?? []"
      :funcionarios="funcionarios"
      :agendamento="agendando.agendamento"
      :gravando="gravando"
      @close="agendando = { aberto: false, agendamento: null }"
      @confirmar="confirmarAgendamento"
    />
    <RegistrarEntregaModal
      :is-open="registrando !== null"
      :entrega="registrando"
      :funcionarios="funcionarios"
      :gravando="gravando"
      @close="registrando = null"
      @confirmar="confirmarRegistro"
    />
    <EditarChecklistModal :is-open="checklistDe !== null" :entrega="checklistDe" :gravando="gravando" @close="checklistDe = null" @salvar="salvarChecklist" />
    <PendenciaModal :is-open="novaPendenciaDe !== null" :ambiente="novaPendenciaDe?.ambiente ?? ''" :gravando="gravando" @close="novaPendenciaDe = null" @confirmar="confirmarPendencia" />
    <ResolverPendenciaModal :is-open="resolvendo !== null" :pendencia="resolvendo?.pendencia ?? null" :gravando="gravando" @close="resolvendo = null" @confirmar="confirmarResolucao" />
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

    <!-- Os termos (só durante a impressão), cada um numa página (D4) -->
    <template v-if="dados">
      <TermoEntregaPrint
        v-for="(entrega, i) in termosParaImprimir"
        :key="entrega.id"
        :dados="dados"
        :entrega="entrega"
        :quebra-antes="i > 0"
      />
    </template>
  </div>
</template>
