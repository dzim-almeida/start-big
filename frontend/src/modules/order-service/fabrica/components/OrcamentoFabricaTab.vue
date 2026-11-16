<script setup lang="ts">
/**
 * @fileoverview Aba "Orçamento" da OS da fábrica (docs/marcenaria-fabrica-plano.md, F2).
 *
 * Versões do orçamento: ambiente → móvel → material. Edita-se só o
 * RASCUNHO; enviar congela a proposta; aprovar escreve os itens na OS (um
 * por móvel, um por insumo em chapas inteiras) e troca os de uma aprovação
 * anterior. Mudou de ideia depois de enviar? Nova versão (copiando esta).
 *
 * Os custos na tela são prévia; o servidor recalcula tudo ao salvar e é ele
 * quem diz quantas chapas vão para a OS.
 */
import { computed, nextTick, ref, watch } from 'vue';
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';
import { storeToRefs } from 'pinia';
import { CheckCircle2, Copy, FilePlus2, Plus, Printer, Save, Send, Trash2, XCircle } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseConfirmModal from '@/shared/components/commons/BaseConfirmModal/BaseConfirmModal.vue';
import MotivoModal from '@/modules/compras/shared/components/MotivoModal.vue';
import { useConfirmacao } from '@/shared/composables/useConfirmacao';
import { useToast } from '@/shared/composables/useToast';
import { useConfiguracoesStore } from '@/shared/stores/configuracoes.store';
import type { ApiError } from '@/shared/types/axios.types';
import { getErrorMessage } from '@/shared/utils/error.utils';
import { formatCurrency } from '@/shared/utils/finance';
import { formatDataPura } from '@/shared/utils/date.utils';
import { imprimirComPagina } from '@/shared/utils/print.utils';

import { AMBIENTES, ROTULO_SITUACAO } from '../constants/orcamento';
import { fabricaKeys } from '../constants/queryKeys';
import {
  aprovarOrcamento,
  criarOrcamento,
  enviarOrcamento,
  getOrcamento,
  listarOrcamentos,
  recusarOrcamento,
  salvarOrcamento,
} from '../services/fabrica.service';
import type { MovelRead, OrcamentoRead } from '../types/fabrica.types';
import {
  editavelDe,
  escritaDe,
  novoAmbiente,
  novoMovel,
  problemasDe,
  totaisDe,
  type OrcamentoEdit,
} from '../utils/editor';
import { useAcessoFabrica } from '../composables/useAcessoFabrica';
import { useModulosStore } from '@/shared/stores/modulos.store';
import { MODULOS } from '@/shared/constants/modulos.constants';
import MargemFabrica from './MargemFabrica.vue';
import MovelCard from './MovelCard.vue';
import PedidoServicoModal from './PedidoServicoModal.vue';
import OrcamentoFabricaPrint from './OrcamentoFabricaPrint.vue';

const props = defineProps<{
  numeroOs: string;
  cliente: string;
  projeto: string;
  /** OS finalizada ou cancelada: só leitura. */
  travada: boolean;
}>();

/** Criar, enviar, aprovar e recusar mudam a OS (fase, itens, total). */
const emit = defineEmits<{ osAlterada: [] }>();

const toast = useToast();
const queryClient = useQueryClient();
const confirmacao = useConfirmacao();
const { margemLucroPadrao } = storeToRefs(useConfiguracoesStore());
// Linha "Fábrica" de Cargos: quem não gerencia só lê; quem não vê custo não vê margem.
const { podeGerenciar, podeVerCusto } = useAcessoFabrica();
/** Pode agir sobre as versões (criar, enviar, responder pelo cliente). */
const podeAgir = computed(() => !props.travada && podeGerenciar.value);

// F5: pedido à central de corte — só com o módulo Compras (é um pedido de compra).
const modulosStore = useModulosStore();
const podePedirServico = computed(
  () => podeAgir.value && orcamento.value?.situacao === 'APROVADO' && modulosStore.temModulo(MODULOS.COMPRAS),
);
const movelDoPedido = ref<MovelRead | null>(null);
function aoCriarPedido() {
  movelDoPedido.value = null;
  queryClient.invalidateQueries({ queryKey: fabricaKeys.orcamento(selecionadoId.value ?? 0) });
  queryClient.invalidateQueries({ queryKey: fabricaKeys.trilho(props.numeroOs) });
}
function lidoDe(i: number, j: number): MovelRead | null {
  if (orcamento.value?.situacao !== 'APROVADO') return null;
  return orcamento.value.ambientes[i]?.moveis[j] ?? null;
}

// --- Versões --------------------------------------------------------------------

const { data: versoes, isLoading: carregandoVersoes } = useQuery({
  queryKey: computed(() => fabricaKeys.orcamentos(props.numeroOs)),
  queryFn: () => listarOrcamentos(props.numeroOs),
});

const selecionadoId = ref<number | null>(null);
watch(versoes, (lista) => {
  if (!lista?.length) return;
  if (!lista.some((v) => v.id === selecionadoId.value)) selecionadoId.value = lista[0]!.id;
}, { immediate: true });

const { data: orcamento } = useQuery({
  queryKey: computed(() => fabricaKeys.orcamento(selecionadoId.value ?? 0)),
  queryFn: () => getOrcamento(selecionadoId.value as number),
  enabled: computed(() => selecionadoId.value != null),
});

// --- Edição -----------------------------------------------------------------------

const edit = ref<OrcamentoEdit | null>(null);
const assinatura = ref('');

function carregar(orc: OrcamentoRead | undefined) {
  if (!orc) return;
  edit.value = editavelDe(orc);
  assinatura.value = JSON.stringify(escritaDe(edit.value));
}
watch(orcamento, carregar, { immediate: true });

const editavel = computed(() => podeAgir.value && !!orcamento.value?.editavel);
const alterado = computed(() => !!edit.value && JSON.stringify(escritaDe(edit.value)) !== assinatura.value);
const totais = computed(() => (edit.value ? totaisDe(edit.value) : null));
const problemas = computed(() => (edit.value ? problemasDe(edit.value) : []));

function adicionarAmbiente() {
  const usados = new Set(edit.value?.ambientes.map((a) => a.nome));
  edit.value?.ambientes.push(novoAmbiente(AMBIENTES.find((a) => !usados.has(a)) ?? ''));
}

function margem(bp: number | null): string {
  if (bp == null) return '—';
  return `${(bp / 100).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`;
}

// --- Ações ---------------------------------------------------------------------------

function aoGravar(orc: OrcamentoRead, mensagem: string, mexeuNaOs = true) {
  queryClient.setQueryData(fabricaKeys.orcamento(orc.id), orc);
  queryClient.invalidateQueries({ queryKey: fabricaKeys.orcamentos(props.numeroOs) });
  selecionadoId.value = orc.id;
  carregar(orc);
  toast.success(mensagem);
  if (mexeuNaOs) emit('osAlterada');
}

function aoFalhar(titulo: string) {
  return (erro: AxiosError<ApiError>) =>
    toast.error(titulo, getErrorMessage(erro, 'Tente de novo.') as string);
}

const criar = useMutation<OrcamentoRead, AxiosError<ApiError>, number | undefined>({
  mutationFn: (copiarDe) => criarOrcamento(props.numeroOs, copiarDe),
  onSuccess: (orc) => aoGravar(orc, `Versão ${orc.versao} criada`),
  onError: aoFalhar('Não foi possível criar a versão'),
});

const salvar = useMutation<OrcamentoRead, AxiosError<ApiError>, void>({
  mutationFn: () => salvarOrcamento(selecionadoId.value as number, escritaDe(edit.value as OrcamentoEdit)),
  onSuccess: (orc) => aoGravar(orc, 'Orçamento salvo', false),
  onError: aoFalhar('Não foi possível salvar o orçamento'),
});

const enviar = useMutation<OrcamentoRead, AxiosError<ApiError>, void>({
  mutationFn: () => enviarOrcamento(selecionadoId.value as number),
  onSuccess: (orc) => aoGravar(orc, 'Proposta enviada ao cliente'),
  onError: aoFalhar('Não foi possível enviar'),
});

const aprovar = useMutation<OrcamentoRead, AxiosError<ApiError>, void>({
  mutationFn: () => aprovarOrcamento(selecionadoId.value as number),
  onSuccess: (orc) => aoGravar(orc, 'Aprovado: os itens já estão na OS'),
  onError: aoFalhar('Não foi possível aprovar'),
});

const recusaAberta = ref(false);
const recusar = useMutation<OrcamentoRead, AxiosError<ApiError>, string>({
  mutationFn: (motivo) => recusarOrcamento(selecionadoId.value as number, motivo),
  onSuccess: (orc) => {
    recusaAberta.value = false;
    aoGravar(orc, 'Versão recusada');
  },
  onError: aoFalhar('Não foi possível recusar'),
});

async function confirmarAprovacao() {
  const ok = await confirmacao.pedirConfirmacao({
    titulo: `Aprovar a versão ${orcamento.value?.versao}?`,
    descricao:
      'Os móveis e os insumos (em chapas inteiras, com a perda) passam a ser os itens da OS, ' +
      'e a OS fica aguardando o sinal. Se outra versão já estava aprovada, os itens dela saem.',
    confirmLabel: 'Aprovar',
    variant: 'info',
  });
  if (ok) aprovar.mutate();
}

// --- Impressão -----------------------------------------------------------------------

const mostrarFolha = ref(false);
async function imprimir() {
  if (!orcamento.value) return;
  mostrarFolha.value = true;
  await nextTick();
  let reserva: ReturnType<typeof setTimeout>;
  const limpar = () => {
    mostrarFolha.value = false;
    window.removeEventListener('afterprint', limpar);
    clearTimeout(reserva);
  };
  window.addEventListener('afterprint', limpar);
  reserva = setTimeout(limpar, 60000);
  imprimirComPagina('A4');
}
</script>

<template>
  <div class="space-y-4">
    <!-- Sem versão ainda -->
    <div
      v-if="!carregandoVersoes && !versoes?.length"
      class="rounded-xl border border-dashed border-zinc-300 p-8 text-center space-y-3"
    >
      <p class="text-sm text-zinc-600">
        Ainda não há orçamento. Monte por ambiente e móvel, com a lista de material — o sistema calcula as
        chapas e, quando o cliente aprovar, escreve tudo na OS.
      </p>
      <BaseButton
        v-if="podeAgir"
        type="button"
        class="inline-flex items-center gap-2"
        :is-loading="criar.isPending.value"
        @click="criar.mutate(undefined)"
      >
        <FilePlus2 :size="16" /> Criar orçamento
      </BaseButton>
    </div>

    <template v-else-if="orcamento && edit">
      <!-- Barra de versões -->
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <select
            v-model="selecionadoId"
            class="min-h-9 px-2.5 text-sm border border-zinc-200 rounded-lg bg-white outline-none focus:border-brand-primary"
          >
            <option v-for="v in versoes" :key="v.id" :value="v.id">
              Versão {{ v.versao }} · {{ ROTULO_SITUACAO[v.situacao].rotulo }} · {{ formatCurrency(v.total) }}
            </option>
          </select>
          <span
            class="px-2 py-0.5 rounded-full text-[11px] font-bold border"
            :class="ROTULO_SITUACAO[orcamento.situacao].classe"
          >
            {{ ROTULO_SITUACAO[orcamento.situacao].rotulo }}
          </span>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <BaseButton type="button" variant="ghost" size="sm" class="flex items-center gap-1.5" :disabled="alterado" @click="imprimir">
            <Printer :size="15" /> Imprimir proposta
          </BaseButton>
          <template v-if="podeAgir">
            <BaseButton
              type="button" variant="ghost" size="sm" class="flex items-center gap-1.5"
              :is-loading="criar.isPending.value" @click="criar.mutate(orcamento.id)"
            >
              <Copy :size="15" /> Nova versão a partir desta
            </BaseButton>
            <BaseButton
              type="button" variant="ghost" size="sm" class="flex items-center gap-1.5"
              :is-loading="criar.isPending.value" @click="criar.mutate(undefined)"
            >
              <FilePlus2 :size="15" /> Versão em branco
            </BaseButton>
          </template>
        </div>
      </div>

      <p v-if="orcamento.situacao === 'RECUSADO' && orcamento.recusado_motivo" class="text-xs text-red-700 bg-red-50 border border-red-200 rounded-xl p-3">
        Recusada: {{ orcamento.recusado_motivo }}
      </p>
      <p v-else-if="orcamento.situacao === 'APROVADO'" class="text-xs text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-xl p-3">
        Aprovada<template v-if="orcamento.aprovado_por"> por {{ orcamento.aprovado_por }}</template>.
        Os itens desta versão estão na aba Serviços e Peças.
      </p>
      <p v-else-if="orcamento.situacao === 'VENCIDO'" class="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-xl p-3">
        A validade passou ({{ orcamento.validade ? formatDataPura(orcamento.validade) : '' }}). Para aprovar,
        faça uma nova versão a partir desta com a validade nova.
      </p>

      <!-- Parâmetros -->
      <div class="grid grid-cols-2 md:grid-cols-12 gap-3 items-end">
        <label class="campo md:col-span-2">
          <span>Perda no corte (%)</span>
          <input v-model.number="edit.perdaPercentual" :disabled="!editavel" type="number" min="0" max="50" step="0.5" />
        </label>
        <label class="campo md:col-span-2">
          <span>Sinal (%)</span>
          <input v-model.number="edit.sinalPercentual" :disabled="!editavel" type="number" min="0" max="100" step="5" />
        </label>
        <label class="campo md:col-span-3">
          <span>Válida até</span>
          <input v-model="edit.validade" :disabled="!editavel" type="date" />
        </label>
        <label class="campo col-span-2 md:col-span-5">
          <span>Observação (sai na proposta)</span>
          <input v-model="edit.observacao" :disabled="!editavel" maxlength="2000" placeholder="Prazo de entrega, condições…" />
        </label>
      </div>

      <!-- Ambientes -->
      <datalist id="fabrica-ambientes">
        <option v-for="a in AMBIENTES" :key="a" :value="a" />
      </datalist>
      <div v-for="(amb, i) in edit.ambientes" :key="amb.chave" class="rounded-2xl bg-zinc-50 border border-zinc-200 p-4 space-y-3">
        <div class="flex items-center gap-2">
          <input
            v-model="amb.nome"
            :disabled="!editavel"
            list="fabrica-ambientes"
            maxlength="60"
            placeholder="Ambiente"
            class="flex-1 min-h-10 px-3 text-base font-bold border border-transparent rounded-lg bg-transparent outline-none focus:border-brand-primary focus:bg-white disabled:text-zinc-700"
          />
          <button
            v-if="editavel"
            type="button"
            class="p-2 rounded-lg text-zinc-400 hover:text-red-600 hover:bg-red-50 cursor-pointer"
            title="Tirar este ambiente"
            @click="edit.ambientes.splice(i, 1)"
          >
            <Trash2 :size="16" />
          </button>
        </div>
        <MovelCard
          v-for="(mov, j) in amb.moveis"
          :key="mov.chave"
          v-model="amb.moveis[j]!"
          :perda-percentual="edit.perdaPercentual"
          :margem-padrao="margemLucroPadrao"
          :editavel="editavel"
          :mostrar-custo="podeVerCusto"
          :lido="lidoDe(i, j)"
          :pode-pedir-servico="podePedirServico"
          @pedir-servico="movelDoPedido = $event"
          @remover="amb.moveis.splice(j, 1)"
        />
        <BaseButton v-if="editavel" type="button" variant="ghost" size="sm" class="flex items-center gap-1.5" @click="amb.moveis.push(novoMovel())">
          <Plus :size="15" /> Móvel
        </BaseButton>
      </div>
      <BaseButton v-if="editavel" type="button" variant="ghost" class="flex items-center gap-2" @click="adicionarAmbiente">
        <Plus :size="16" /> Ambiente
      </BaseButton>

      <!-- Totais -->
      <div v-if="totais" class="grid gap-3" :class="podeVerCusto ? 'grid-cols-2 md:grid-cols-4' : 'grid-cols-2'">
        <div class="rounded-xl border border-zinc-200 p-3">
          <p class="text-[11px] uppercase font-bold text-zinc-400">Total</p>
          <p class="text-lg font-black tabular-nums">{{ formatCurrency(totais.total) }}</p>
        </div>
        <div v-if="podeVerCusto" class="rounded-xl border border-zinc-200 p-3">
          <p class="text-[11px] uppercase font-bold text-zinc-400">Custo</p>
          <p class="text-lg font-bold tabular-nums text-zinc-700">{{ formatCurrency(totais.custo) }}</p>
        </div>
        <div v-if="podeVerCusto" class="rounded-xl border border-zinc-200 p-3">
          <p class="text-[11px] uppercase font-bold text-zinc-400">Margem</p>
          <p class="text-lg font-bold tabular-nums" :class="(totais.margemBp ?? 0) < 0 ? 'text-red-600' : 'text-emerald-700'">
            {{ margem(totais.margemBp) }}
          </p>
        </div>
        <div class="rounded-xl border border-zinc-200 p-3">
          <p class="text-[11px] uppercase font-bold text-zinc-400">Sinal</p>
          <p class="text-lg font-bold tabular-nums text-zinc-700">{{ formatCurrency(totais.sinal) }}</p>
        </div>
      </div>

      <!-- O que vai para a OS -->
      <div v-if="orcamento.insumos.length" class="rounded-xl border border-zinc-200 p-4">
        <p class="text-xs font-bold uppercase tracking-wider text-zinc-500 mb-2">
          Material que vai para a OS ao aprovar
          <span v-if="alterado" class="normal-case font-normal text-amber-700">— salve para atualizar</span>
        </p>
        <ul class="text-sm divide-y divide-zinc-100">
          <li v-for="ins in orcamento.insumos" :key="ins.produto_id" class="flex justify-between py-1.5">
            <span>{{ ins.descricao }}</span>
            <span class="font-bold tabular-nums">{{ ins.quantidade }} {{ ins.unidade_medida || 'UN' }}</span>
          </li>
        </ul>
      </div>

      <MargemFabrica v-if="orcamento.situacao === 'APROVADO' && podeVerCusto" :numero-os="numeroOs" />

      <ul v-if="editavel && problemas.length" class="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-xl p-3 space-y-1">
        <li v-for="p in problemas" :key="p">{{ p }}</li>
      </ul>

      <!-- Ações da versão -->
      <div v-if="podeAgir" class="flex flex-wrap justify-end gap-2 pt-2 border-t border-zinc-100">
        <template v-if="orcamento.situacao === 'RASCUNHO'">
          <BaseButton
            type="button" variant="secondary" class="flex items-center gap-2"
            :disabled="!alterado || problemas.length > 0" :is-loading="salvar.isPending.value"
            @click="salvar.mutate()"
          >
            <Save :size="16" /> Salvar
          </BaseButton>
          <BaseButton
            type="button" class="flex items-center gap-2"
            :disabled="alterado" :is-loading="enviar.isPending.value"
            :title="alterado ? 'Salve antes de enviar' : ''"
            @click="enviar.mutate()"
          >
            <Send :size="16" /> Enviar ao cliente
          </BaseButton>
        </template>
        <template v-else-if="orcamento.situacao === 'ENVIADO' || orcamento.situacao === 'VENCIDO'">
          <BaseButton type="button" variant="secondary" class="flex items-center gap-2" @click="recusaAberta = true">
            <XCircle :size="16" /> Cliente recusou
          </BaseButton>
          <BaseButton
            v-if="orcamento.situacao === 'ENVIADO'"
            type="button" class="flex items-center gap-2"
            :is-loading="aprovar.isPending.value" @click="confirmarAprovacao"
          >
            <CheckCircle2 :size="16" /> Cliente aprovou
          </BaseButton>
        </template>
      </div>

      <OrcamentoFabricaPrint v-if="mostrarFolha" :orcamento="orcamento" :cliente="cliente" :projeto="projeto" />
    </template>

    <p v-else class="text-sm text-zinc-400 text-center py-8">Carregando orçamento…</p>

    <PedidoServicoModal :movel="movelDoPedido" @fechar="movelDoPedido = null" @criado="aoCriarPedido" />
    <MotivoModal
      :aberto="recusaAberta"
      titulo="O cliente recusou"
      descricao="O motivo fica na versão — ajuda a acertar a próxima."
      confirm-label="Recusar versão"
      placeholder="Ex.: achou caro, vai pensar"
      :carregando="recusar.isPending.value"
      perigo
      @fechar="recusaAberta = false"
      @confirmar="recusar.mutate($event)"
    />
    <BaseConfirmModal
      :is-open="confirmacao.isOpen.value"
      :title="confirmacao.opcoes.value.titulo"
      :description="confirmacao.opcoes.value.descricao"
      :confirm-label="confirmacao.opcoes.value.confirmLabel"
      :cancel-label="confirmacao.opcoes.value.cancelLabel"
      :variant="confirmacao.opcoes.value.variant"
      overlay
      @confirm="confirmacao.confirmar"
      @close="confirmacao.cancelar"
    />
  </div>
</template>

<style scoped>
.campo {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
}
.campo > span {
  font-size: 0.75rem;
  font-weight: 500;
  color: #374151;
}
.campo input {
  width: 100%;
  min-width: 0;
  min-height: 2.5rem;
  padding: 0.5rem 0.625rem;
  font-size: 0.875rem;
  border: 1px solid #e4e4e7;
  border-radius: 0.5rem;
  background: #fff;
  outline: none;
}
.campo input:focus {
  border-color: var(--color-brand-primary);
}
.campo input:disabled {
  background: #f4f4f5;
  color: #71717a;
}
</style>
