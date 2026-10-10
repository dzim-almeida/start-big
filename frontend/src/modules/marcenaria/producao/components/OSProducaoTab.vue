<script setup lang="ts">
/**
 * @component OSProducaoTab
 * @description Aba "Produção" do modal de OS da marcenaria (Spec 12B D1-D14).
 *
 * Os móveis com as etapas, para marcar o que foi feito com o menor número de
 * cliques: um clique conclui, "Concluir em todos" faz o lote do dia, e o modo
 * seleção marca chips de vários móveis. Feita para o computador fixo da
 * fábrica (P3): botões grandes e nenhum preço (P4).
 *
 * Quando a produção começa ou termina, pergunta se move o status da OS
 * (D12). Não conhece o modal de OS: quem grava o status é a função
 * `aplicarStatus` que o pai passa (sem ela, a pergunta não aparece).
 */
import { computed, ref, toRef, watch } from 'vue';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseConfirmModal from '@/shared/components/commons/BaseConfirmModal/BaseConfirmModal.vue';
import { useConfirmacao } from '@/shared/composables/useConfirmacao';
import { useToast } from '@/shared/composables/useToast';
import { useRotulosStatusOS } from '@/modules/order-service/shared/segmento/useRotulosStatusOS';
import type { OsStatusEnumDataType } from '@/modules/order-service/ordens/schemas/enums/osEnums.schema';
import { mensagemDoErro, statusDoErro } from '@/modules/marcenaria/orcamentos/utils/erros';
import { escaparHtml } from '@/modules/marcenaria/orcamentos/utils/textoSeguro';

import { useFeitoPor } from '../composables/useFeitoPor';
import { useProducaoDaOS } from '../composables/useProducaoDaOS';
import type { Etapa, MovelProducao } from '../schemas/producao.schema';
import {
  diaMes, etapasParaConcluirEmTodos, prazoDaEntrega, proximaEtapa, type OpcaoFuncionario,
} from '../utils/producao';
import EditarEtapasModal from './EditarEtapasModal.vue';
import IniciarEtapasModal from './IniciarEtapasModal.vue';
import ImprimirEtiquetasModal from '@/modules/marcenaria/etiquetas/components/ImprimirEtiquetasModal.vue';
import type { DadosComunsEtiqueta } from '@/modules/marcenaria/etiquetas/utils/montarEtiquetas';
import MovelProducaoCard from './MovelProducaoCard.vue';
import SugestaoStatusModal from './SugestaoStatusModal.vue';

const props = withDefaults(defineProps<{
  numeroOs: string;
  /** Os funcionários ativos, para o "Feito por" (D6). Vazio: o select some. */
  funcionarios?: OpcaoFuncionario[];
  /** Grava só o status da OS (D13). Sem ela, a pergunta de status não aparece. */
  aplicarStatus?: ((status: string) => Promise<void>) | null;
  /** Spec 14: projeto, endereço da obra e cliente, para as etiquetas (da OS aberta no modal). */
  obra?: Omit<DadosComunsEtiqueta, 'os' | 'empresa'>;
}>(), { funcionarios: () => [], aplicarStatus: null, obra: () => ({ projeto: '', enderecoObra: '', cliente: '' }) });

const toast = useToast();

// --- Modais (enquanto um está aberto, a lista não recarrega) -----------------------
const editando = ref<MovelProducao | null>(null);
const iniciando = ref<{ ids: number[]; descricao: string } | null>(null);
const confirmacao = useConfirmacao();
/** Spec 14: o modal das etiquetas, com os móveis que já vêm marcados. */
const etiquetasPara = ref<number[] | null>(null);
const algumModalAberto = computed(() =>
  editando.value !== null || iniciando.value !== null || etiquetasPara.value !== null || confirmacao.isOpen.value);

const {
  data: producao, isLoading, error, gravando, sugestao,
  concluir, iniciar, reabrir, editarEtapas, aplicarPadrao, refetch,
} = useProducaoDaOS(toRef(props, 'numeroOs'), ref(true), algumModalAberto);

const semProducao = computed(() => statusDoErro(error.value) === 404);
const editavel = computed(() => producao.value?.os.editavel ?? false);

/** OS fechada: a frase com o status no texto do segmento (D10). */
const { rotuloStatus } = useRotulosStatusOS();
const fraseFechada = computed(() => {
  const status = producao.value?.os.status as OsStatusEnumDataType | undefined;
  return status ? `A OS está ${rotuloStatus(status).toLowerCase()}: a produção não pode mais ser alterada.` : '';
});

// --- Topo: progresso e previsão (D2) -----------------------------------------------------
const progresso = computed(() => producao.value?.progresso);
const percentual = computed(() => {
  const p = progresso.value;
  return p && p.etapas_total ? Math.round((p.etapas_concluidas / p.etapas_total) * 100) : 0;
});
const entrega = computed(() => {
  const previsao = producao.value?.os.previsao;
  if (!previsao) return null;
  const prazo = prazoDaEntrega(previsao);
  // Produção concluída não está "atrasada" (o que falta é entregar).
  return { data: diaMes(previsao), texto: prazo.texto, atrasada: prazo.atrasada && !producao.value?.producao_concluida };
});

// --- "Feito por" (D6) ---------------------------------------------------------------------
const { feitoPor } = useFeitoPor();
/** O <select> nativo guarda texto: '' = o usuário logado. */
const feitoPorTexto = computed({
  get: () => (feitoPor.value ? String(feitoPor.value) : ''),
  set: (valor: string) => { feitoPor.value = valor ? Number(valor) : null; },
});
/** O nome para a marcação otimista (o servidor confirma logo depois). */
const nomeDe = (id: number | null) => props.funcionarios.find((f) => f.id === id)?.nome ?? null;

// --- Filtro "Esconder prontos" (D9) e agrupamento por ambiente (D3) -----------------
const esconderProntos = ref(false);
const moveisVisiveis = computed(() =>
  (producao.value?.moveis ?? []).filter((m) => !esconderProntos.value || !m.pronto));
const escondidos = computed(() => (producao.value?.moveis.length ?? 0) - moveisVisiveis.value.length);
const ambientes = computed(() => {
  const grupos = new Map<string, MovelProducao[]>();
  for (const movel of moveisVisiveis.value) {
    if (!grupos.has(movel.ambiente)) grupos.set(movel.ambiente, []);
    grupos.get(movel.ambiente)!.push(movel);
  }
  return [...grupos.entries()].map(([nome, moveis]) => ({ nome, moveis }));
});

/** D2: "Concluir em todos: Corte (4)". */
const emLote = computed(() => etapasParaConcluirEmTodos(producao.value?.moveis ?? []));

// --- Modo seleção (D5) --------------------------------------------------------------------
const modoSelecao = ref(false);
const selecionadas = ref(new Set<number>());
watch(modoSelecao, () => { selecionadas.value = new Set(); });   // entrar ou sair começa do zero

function alternar(etapa: Etapa) {
  const nova = new Set(selecionadas.value);          // um Set novo: o Vue percebe a troca
  if (nova.has(etapa.id)) nova.delete(etapa.id);
  else nova.add(etapa.id);
  selecionadas.value = nova;
}

// --- Ações ---------------------------------------------------------------------------------
/** Conclui com o "Feito por" atual (ou o usuário logado). */
/**
 * Conclui com o "Feito por" atual (ou o usuário logado). Spec 14 D8: se algum
 * móvel ficou pronto agora (a última etapa), oferece as etiquetas dele.
 */
async function concluirIds(ids: number[]): Promise<boolean> {
  const prontosAntes = new Set((producao.value?.moveis ?? []).filter((m) => m.pronto).map((m) => m.movel_id));
  const ok = await concluir(ids, feitoPor.value, nomeDe(feitoPor.value));
  const novos = ok ? (producao.value?.moveis ?? []).filter((m) => m.pronto && !prontosAntes.has(m.movel_id)) : [];
  if (novos.length) {
    const quem = novos.length === 1 ? `${novos[0].nome} ficou pronto.` : `${novos.length} móveis ficaram prontos.`;
    toast.success(quem, 'A embalagem pede as etiquetas dos volumes.', {
      action: { label: 'Imprimir etiquetas', onClick: () => { etiquetasPara.value = novos.map((m) => m.movel_id); } },
    });
  }
  return ok;
}

/** D8: o botão do topo abre com os móveis prontos marcados. */
const abrirEtiquetas = () => {
  etiquetasPara.value = (producao.value?.moveis ?? []).filter((m) => m.pronto).map((m) => m.movel_id);
};

/**
 * D4: um clique conclui. Fora de ordem (não é a próxima do móvel), pergunta
 * antes — sem travar: às vezes a montagem anda antes da borda.
 */
async function concluirEtapa(movel: MovelProducao, etapa: Etapa) {
  const proxima = proximaEtapa(movel);
  if (proxima && proxima.id !== etapa.id) {
    const ok = await confirmacao.pedirConfirmacao({
      titulo: `Concluir ${etapa.nome} antes de ${proxima.nome}?`,
      descricao: `<strong>${escaparHtml(movel.nome)}</strong>: a etapa ${escaparHtml(proxima.nome)} ainda não foi concluída.`,
      confirmLabel: 'Concluir',
    });
    if (!ok) return;
  }
  await concluirIds([etapa.id]);
}

async function concluirSelecionadas() {
  const ids = [...selecionadas.value];
  if (!ids.length) return;
  if (await concluirIds(ids)) modoSelecao.value = false;
}

function abrirIniciar(ids: number[], descricao: string) {
  iniciando.value = { ids, descricao };
}

async function confirmarIniciar(responsavelId: number | null) {
  const alvo = iniciando.value;
  if (!alvo) return;
  const ok = await iniciar(alvo.ids, responsavelId, nomeDe(responsavelId));
  iniciando.value = null;
  if (ok && modoSelecao.value) modoSelecao.value = false;
}


async function salvarEtapas(etapas: { id: number | null; nome: string }[]) {
  const movel = editando.value;
  if (!movel) return;
  if (await editarEtapas(movel.movel_id, etapas)) editando.value = null;   // erro: o modal fica aberto
}

// --- Pergunta de status (D12-D14) ------------------------------------------------------------
const aplicandoStatus = ref(false);
/** A pergunta só aparece se o pai sabe gravar o status. */
const sugestaoVisivel = computed(() => (props.aplicarStatus ? sugestao.value : null));

async function moverStatus() {
  const alvo = sugestao.value;
  if (!alvo || !props.aplicarStatus) return;
  aplicandoStatus.value = true;
  try {
    await props.aplicarStatus(alvo.para);
    toast.success(`OS movida para ${alvo.rotulo}.`);
    sugestao.value = null;
    void refetch();                                   // o status da OS mudou: a aba relê
  } catch (erro) {
    toast.error('Não foi possível mudar o status da OS.', mensagemDoErro(erro));
  } finally {
    aplicandoStatus.value = false;
  }
}
</script>

<template>
  <div class="space-y-4" data-testid="aba-producao">
    <p v-if="isLoading" class="text-sm text-zinc-400">Carregando a produção…</p>
    <p v-else-if="semProducao" class="text-sm text-zinc-500" data-testid="sem-producao">Esta OS não tem produção.</p>
    <p v-else-if="error" class="text-sm text-red-600">Não foi possível carregar a produção agora.</p>

    <template v-else-if="producao && progresso">
      <!-- Topo: progresso e previsão (D2) -->
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="flex flex-wrap items-center gap-3">
          <h3 class="text-base font-bold text-zinc-800">Produção</h3>
          <div class="h-2.5 w-40 overflow-hidden rounded-full bg-zinc-100" aria-hidden="true">
            <div class="h-full bg-emerald-500 transition-all" :style="{ width: `${percentual}%` }" />
          </div>
          <span class="text-sm text-zinc-600" data-testid="progresso">
            {{ progresso.etapas_concluidas }} de {{ progresso.etapas_total }} etapas ·
            {{ progresso.moveis_prontos }} de {{ progresso.moveis_total }} móveis prontos
          </span>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <span
            v-if="entrega"
            class="text-sm"
            :class="entrega.atrasada ? 'font-semibold text-red-700' : 'text-zinc-600'"
            data-testid="previsao-entrega"
          >
            Entrega prevista {{ entrega.data }} · {{ entrega.texto }}
          </span>
          <!-- Spec 14 D8: as etiquetas dos volumes (os prontos já vêm marcados) -->
          <BaseButton v-if="producao.moveis.length" variant="secondary" size="sm" data-testid="abrir-etiquetas" @click="abrirEtiquetas">
            Etiquetas
          </BaseButton>
        </div>
      </div>

      <!-- OS fechada: só leitura (D10) -->
      <p v-if="!editavel" class="rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm text-zinc-600" data-testid="producao-fechada">
        {{ fraseFechada }}
      </p>

      <template v-else>
        <!-- Feito por, seleção e filtro (D5, D6, D9) -->
        <div class="flex flex-wrap items-center justify-between gap-3">
          <label v-if="funcionarios.length" class="flex items-center gap-2 text-sm text-zinc-700">
            Feito por:
            <select
              v-model="feitoPorTexto"
              class="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-base text-zinc-800 focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
              data-testid="feito-por"
            >
              <option value="">Eu (usuário logado)</option>
              <option v-for="f in funcionarios" :key="f.id" :value="String(f.id)">{{ f.nome }}</option>
            </select>
          </label>
          <span v-else />
          <div class="flex flex-wrap items-center gap-3">
            <BaseButton :variant="modoSelecao ? 'primary' : 'secondary'" size="sm" data-testid="modo-selecao" @click="modoSelecao = !modoSelecao">
              {{ modoSelecao ? 'Sair da seleção' : 'Selecionar' }}
            </BaseButton>
            <label class="flex items-center gap-2 text-sm text-zinc-700">
              <input v-model="esconderProntos" type="checkbox" class="accent-brand-primary" data-testid="esconder-prontos" />
              Esconder móveis prontos
            </label>
          </div>
        </div>

        <!-- D2: o lote do dia, um botão por etapa com pendência -->
        <div v-if="emLote.length && !modoSelecao" class="flex flex-wrap items-center gap-2" data-testid="concluir-em-todos">
          <span class="text-sm font-medium text-zinc-600">Concluir em todos:</span>
          <BaseButton
            v-for="grupo in emLote"
            :key="grupo.nome"
            size="md"
            variant="secondary"
            :disabled="gravando"
            :data-testid="`lote-${grupo.nome}`"
            @click="concluirIds(grupo.etapaIds)"
          >
            {{ grupo.nome }} ({{ grupo.etapaIds.length }})
          </BaseButton>
        </div>

        <!-- D5: a barra do modo seleção -->
        <div v-if="modoSelecao" class="flex flex-wrap items-center gap-2 rounded-lg border border-brand-primary/30 bg-brand-primary/5 px-3 py-2" data-testid="barra-selecao">
          <span class="text-sm text-zinc-700">{{ selecionadas.size }} {{ selecionadas.size === 1 ? 'etapa marcada' : 'etapas marcadas' }}</span>
          <BaseButton size="sm" :disabled="!selecionadas.size || gravando" data-testid="concluir-selecionadas" @click="concluirSelecionadas">
            Concluir selecionadas
          </BaseButton>
          <BaseButton
            size="sm"
            variant="secondary"
            :disabled="!selecionadas.size || gravando"
            data-testid="iniciar-selecionadas"
            @click="abrirIniciar([...selecionadas], `${selecionadas.size} ${selecionadas.size === 1 ? 'etapa' : 'etapas'}`)"
          >
            Iniciar selecionadas
          </BaseButton>
        </div>
      </template>

      <!-- Os móveis, agrupados por ambiente (D3) -->
      <section v-for="ambiente in ambientes" :key="ambiente.nome" class="space-y-2">
        <p class="text-xs font-bold uppercase tracking-wide text-zinc-500">{{ ambiente.nome }}</p>
        <MovelProducaoCard
          v-for="movel in ambiente.moveis"
          :key="movel.movel_id"
          :movel="movel"
          :editavel="editavel"
          :modo-selecao="modoSelecao"
          :selecionadas="selecionadas"
          @concluir="concluirEtapa(movel, $event)"
          @iniciar="abrirIniciar([$event.id], `${$event.nome} — ${movel.nome}`)"
          @reabrir="reabrir($event.id)"
          @alternar="alternar"
          @editar-etapas="editando = movel"
          @imprimir-etiquetas="etiquetasPara = [movel.movel_id]"
          @aplicar-padrao="aplicarPadrao(movel.movel_id)"
        />
      </section>
      <p v-if="!producao.moveis.length" class="text-sm text-zinc-500">Esta OS não tem móveis.</p>
      <p v-if="escondidos" class="text-sm text-emerald-700" data-testid="prontos-escondidos">
        {{ escondidos }} {{ escondidos === 1 ? 'móvel pronto escondido' : 'móveis prontos escondidos' }}.
      </p>
    </template>

    <!-- Modais (overlay: abrem por cima do modal de OS) -->
    <EditarEtapasModal :is-open="editando !== null" :movel="editando" :gravando="gravando" @close="editando = null" @salvar="salvarEtapas" />
    <ImprimirEtiquetasModal
      v-if="producao"
      :is-open="etiquetasPara !== null"
      :numero-os="producao.os.numero_os"
      :moveis="producao.moveis"
      :marcados="etiquetasPara ?? []"
      :obra="obra"
      @close="etiquetasPara = null"
    />
    <IniciarEtapasModal
      :is-open="iniciando !== null"
      :descricao="iniciando?.descricao ?? ''"
      :funcionarios="funcionarios"
      :responsavel-inicial="feitoPor"
      :gravando="gravando"
      @close="iniciando = null"
      @confirmar="confirmarIniciar"
    />
    <SugestaoStatusModal :sugestao="sugestaoVisivel" :aplicando="aplicandoStatus" @mover="moverStatus" @agora-nao="sugestao = null" />
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
  </div>
</template>
