<script setup lang="ts">
/**
 * @component OSSeparacaoTab
 * @description Aba "Separação" do modal de OS da marcenaria (Spec 10B).
 *
 * O que tirar do estoque para esta OS, na ordem das prateleiras, com
 * retirar, devolver, concluir e o LEITOR de código de barras. Feita para o
 * computador fixo da fábrica (P3): números grandes, poucos cliques, tudo pelo
 * teclado quando houver leitor. Nenhum preço (D9).
 *
 * No topo, a seção "Móveis da central" (Spec 11B), que só aparece quando a
 * OS tem móvel terceirizado.
 *
 * Não conhece o modal de OS: avisa o pai por evento ("ver nas Necessidades",
 * ou `navegar` para outra tela, como o pedido no Compras).
 */
import { computed, nextTick, onBeforeUnmount, onMounted, ref, toRef, watch } from 'vue';
import type { RouteLocationRaw } from 'vue-router';
import { PackageCheck, Printer, ScanBarcode } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseProgressBar from '@/shared/components/ui/BaseProgressBar/BaseProgressBar.vue';
import BaseStatusPill from '@/shared/components/ui/BaseStatusPill/BaseStatusPill.vue';
import BaseConfirmModal from '@/shared/components/commons/BaseConfirmModal/BaseConfirmModal.vue';
import { useConfirmacao } from '@/shared/composables/useConfirmacao';
import { unidadeEhFracionada } from '@/shared/utils/quantidade';
import { useAcessoCompras } from '@/modules/compras/shared/composables/useAcessoCompras';
import { useRotulosStatusOS } from '@/modules/order-service/shared/segmento/useRotulosStatusOS';
import type { OsStatusEnumDataType } from '@/modules/order-service/ordens/schemas/enums/osEnums.schema';
import { mensagemDoErro, statusDoErro } from '@/modules/marcenaria/orcamentos/utils/erros';
import { escaparHtml } from '@/modules/marcenaria/orcamentos/utils/textoSeguro';
import SecaoTerceirizados from '@/modules/marcenaria/terceirizados/components/SecaoTerceirizados.vue';
import type { SugestaoStatus, TerceirizadosDaOS } from '@/modules/marcenaria/terceirizados/schemas/terceirizado.schema';
import SugestaoStatusModal from '@/modules/marcenaria/producao/components/SugestaoStatusModal.vue';
import { useToast } from '@/shared/composables/useToast';

import { tocarSomDeErro, useLeitorCodigo } from '../composables/useLeitorCodigo';
import { useSeparacao } from '../composables/useSeparacao';
import type { LinhaSeparacao } from '../schemas/separacao.schema';
import { lerCodigo } from '../services/separacao.service';
import { quantidadeComUnidade, quantidadeSimples } from '../utils/quantidades';
import DevolverModal from './DevolverModal.vue';
import FaltasDaOS from './FaltasDaOS.vue';
import RetirarModal from './RetirarModal.vue';
import SeparacaoLinha from './SeparacaoLinha.vue';
import SeparacaoResumo from './SeparacaoResumo.vue';

const props = withDefaults(defineProps<{
  numeroOs: string;
  /** Grava só o status da OS (12B D13). Sem ela, a pergunta de status da 11B não aparece. */
  aplicarStatus?: ((status: string) => Promise<void>) | null;
}>(), { aplicarStatus: null });
const emit = defineEmits<{ verNecessidades: []; navegar: [destino: RouteLocationRaw] }>();

// --- Modais da aba (enquanto um está aberto, a lista não recarrega e o leitor dorme) ---
const retirarModal = ref<{ aberto: boolean; linha: LinhaSeparacao | null; quantidade: number | null }>({
  aberto: false, linha: null, quantidade: null,
});
const devolverModal = ref<{ aberto: boolean; linha: LinhaSeparacao | null }>({ aberto: false, linha: null });
const faltasAberto = ref(false);
const confirmacao = useConfirmacao();
/** A seção "Móveis da central" (11B) avisa quando está com um modal aberto. */
const terceirizadosOcupado = ref(false);
/** A pergunta de status da OS (12B D12), quando o conferir/voltar da 11B sugere uma. */
const sugestao = ref<SugestaoStatus>(null);
const algumModalAberto = computed(
  () => retirarModal.value.aberto || devolverModal.value.aberto || faltasAberto.value || confirmacao.isOpen.value
    || terceirizadosOcupado.value || sugestao.value !== null,
);

const {
  data: separacao, isLoading, error, gravando,
  retirarLinha, devolverLinha, concluirLinha, reabrirLinha,
} = useSeparacao(toRef(props, 'numeroOs'), ref(true), algumModalAberto);

const semSeparacao = computed(() => statusDoErro(error.value) === 404);
// D19: "Ver nas Necessidades" só com o módulo Compras e a permissão de ver.
const { podeVer: comprasDisponivel } = useAcessoCompras();
const editavel = computed(() => separacao.value?.os.editavel ?? false);

// --- Filtros e progresso (D2) -------------------------------------------------------
const soPendentes = ref(true);
const cadaLeituraRetira = ref(false);
const linhasVisiveis = computed(() =>
  (separacao.value?.linhas ?? []).filter((linha) => !soPendentes.value || !linha.concluida),
);
const progresso = computed(() => {
  const resumo = separacao.value?.resumo;
  if (!resumo || !resumo.linhas) return 0;
  return Math.round((resumo.concluidas / resumo.linhas) * 100);
});

/** OS fechada: a frase com o status no texto do segmento (D10). */
const { rotuloStatus } = useRotulosStatusOS();
const fraseFechada = computed(() => {
  const status = separacao.value?.os.status as OsStatusEnumDataType | undefined;
  return status ? `A OS está ${rotuloStatus(status).toLowerCase()}: a separação não pode mais ser alterada.` : '';
});

// --- Leitor de código (D14-D17) ---------------------------------------------------------
const campoCodigo = ref<HTMLInputElement | null>(null);
const codigoDigitado = ref('');
const mensagemLeitor = ref<{ texto: string; tom: 'ok' | 'atencao' | 'erro' } | null>(null);
const destacada = ref<number | null>(null);
let tempoDestaque: ReturnType<typeof setTimeout> | null = null;

function focarCampo() {
  void nextTick(() => campoCodigo.value?.focus());
}

/** Rola até a linha e a destaca por 2 s (D14). */
function destacar(itemId: number) {
  destacada.value = itemId;
  if (tempoDestaque) clearTimeout(tempoDestaque);
  tempoDestaque = setTimeout(() => { destacada.value = null; }, 2000);
  void nextTick(() => document.getElementById(`separacao-linha-${itemId}`)?.scrollIntoView?.({ block: 'center', behavior: 'smooth' }));
}

async function aoLer(lido: string) {
  const codigo = lido.trim();
  codigoDigitado.value = '';                           // o campo fica limpo e focado (D15)
  focarCampo();
  if (!codigo) return;
  try {
    const { linha, fator } = await lerCodigo(props.numeroOs, codigo);
    destacar(linha.item_id);
    if (linha.concluida) {
      mensagemLeitor.value = { texto: 'Este item já foi separado.', tom: 'atencao' };
      return;
    }
    mensagemLeitor.value = null;
    // D16: "cada leitura retira" o FATOR lido (1 o produto; 10 a caixa de 10).
    // Metro e quilo sempre pelo modal: "1 metro por bipe" não corresponde a nada real.
    if (cadaLeituraRetira.value && !unidadeEhFracionada(linha.unidade)) {
      const nova = await retirarLinha(linha, fator * 1000);
      const atual = nova?.linhas.find((l) => l.item_id === linha.item_id);
      if (atual) {
        const q = (m: number) => quantidadeComUnidade(m, atual.unidade);
        mensagemLeitor.value = { texto: `${atual.descricao}: ${q(atual.separada_milesimos)} de ${q(atual.quantidade_milesimos)}`, tom: 'ok' };
      }
    } else {
      abrirRetirar(linha);
    }
  } catch (erro) {
    if (statusDoErro(erro) === 404) {
      tocarSomDeErro();                                 // D15: o marceneiro olha para a chapa
      mensagemLeitor.value = { texto: 'Este produto não faz parte desta OS.', tom: 'erro' };
    } else {
      mensagemLeitor.value = { texto: mensagemDoErro(erro), tom: 'erro' };
    }
  }
}

// O ouvinte global só com a lista editável e nenhum modal aberto (D17).
useLeitorCodigo(aoLer, computed(() => editavel.value && !algumModalAberto.value), campoCodigo);

onMounted(focarCampo);                                  // D2: sempre focado ao abrir a aba
watch(() => separacao.value != null, (carregou) => { if (carregou) focarCampo(); });
onBeforeUnmount(() => { if (tempoDestaque) clearTimeout(tempoDestaque); });

// --- Pergunta de status da OS (12B D12): conferir o último terceirizado pode terminar a produção ---
const toast = useToast();
const aplicandoStatus = ref(false);
function aoSugerirStatus(secao: TerceirizadosDaOS) {
  if (props.aplicarStatus) sugestao.value = secao.sugestao_status ?? null;
}
async function moverStatus() {
  const alvo = sugestao.value;
  if (!alvo || !props.aplicarStatus) return;
  aplicandoStatus.value = true;
  try {
    await props.aplicarStatus(alvo.para);
    toast.success(`OS movida para ${alvo.rotulo}.`);
    sugestao.value = null;
  } catch (erro) {
    toast.error('Não foi possível mudar o status da OS.', mensagemDoErro(erro));
  } finally {
    aplicandoStatus.value = false;
  }
}

// --- Ações ------------------------------------------------------------------------------
async function abrirRetirar(linha: LinhaSeparacao) {
  let alvo = linha;
  // Linha "Não usado" (devolveu tudo ou marcou que não usa): o backend só deixa retirar
  // depois de reabrir (Spec 10A D11/D12). Em vez de obrigar o usuário a achar o "Reabrir"
  // no menu, o "Retirar" reabre sozinho e segue (remodelação item 13).
  if (linha.nao_usado) {
    const nova = await reabrirLinha(linha);
    const reaberta = nova?.linhas.find((l) => l.item_id === linha.item_id);
    if (!reaberta) return;                               // não reabriu (o erro já virou aviso)
    alvo = reaberta;                                     // a linha nova, com o retirado de agora
  }
  retirarModal.value = { aberto: true, linha: alvo, quantidade: null };
}

async function confirmarRetirar(quantidade: number) {
  const linha = retirarModal.value.linha;
  if (!linha) return;
  const nova = await retirarLinha(linha, quantidade);
  fecharRetirar();
  if (nova) mensagemLeitor.value = null;
}
function fecharRetirar() {
  retirarModal.value = { aberto: false, linha: null, quantidade: null };
  focarCampo();
}

async function confirmarDevolver(quantidade: number) {
  const linha = devolverModal.value.linha;
  if (!linha) return;
  await devolverLinha(linha, quantidade);
  devolverModal.value = { aberto: false, linha: null };
  focarCampo();
}

/** D6: concluir explica o efeito no estoque antes de gravar. */
async function concluir(linha: LinhaSeparacao, naoUsado: boolean) {
  const nome = escaparHtml(linha.descricao);
  const retirado = quantidadeComUnidade(linha.separada_milesimos, linha.unidade);
  const ok = await confirmacao.pedirConfirmacao(naoUsado
    ? {
      titulo: 'Não usado nesta OS',
      descricao: `<strong>${nome}</strong>: este produto não será usado nesta OS.`,
      confirmLabel: 'Marcar como não usado',
    }
    : {
      titulo: 'Concluir a separação',
      descricao: `<strong>${nome}</strong>: a OS passa a consumir ${retirado} (o que foi retirado). `
        + 'A finalização não baixará mais nada deste produto.',
      confirmLabel: 'Concluir',
    });
  if (ok) await concluirLinha(linha);
  focarCampo();
}
</script>

<template>
  <div class="flex flex-col gap-6" data-testid="aba-separacao">
    <!-- 11B D1: os móveis da central vêm primeiro (o atraso deles atrasa a obra inteira) -->
    <SecaoTerceirizados
      v-model:ocupado="terceirizadosOcupado"
      :numero-os="numeroOs"
      @navegar="emit('navegar', $event)"
      @sugestao-status="aoSugerirStatus"
    />

    <p v-if="isLoading" class="text-sm text-zinc-500">Carregando a separação…</p>
    <p v-else-if="semSeparacao" class="text-sm text-zinc-500" data-testid="sem-separacao">Esta OS não tem separação de material.</p>
    <p v-else-if="error" class="text-sm text-red-600">Não foi possível carregar a separação agora.</p>

    <template v-else-if="separacao">
      <!-- Topo: título, progresso e faltas (D2, D18) -->
      <section class="flex flex-wrap items-center justify-between gap-6 rounded-2xl border border-zinc-200 bg-white px-6 py-5">
        <div class="flex items-center gap-3.5">
          <span class="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-primary text-white" aria-hidden="true">
            <PackageCheck :size="22" />
          </span>
          <div>
            <h3 class="text-base font-semibold text-zinc-900">Separação de almoxarifado</h3>
            <p class="text-xs text-zinc-500">Os insumos dos móveis desta OS, somados por item do estoque.</p>
          </div>
        </div>
        <div class="flex flex-wrap items-center gap-6">
          <div class="w-64" data-testid="progresso">
            <BaseProgressBar
              :valor="progresso"
              rotulo="Progresso"
              :detalhe="`${separacao.resumo.concluidas} de ${separacao.resumo.linhas} separados`"
              :tom="progresso >= 100 ? 'sucesso' : 'primario'"
            />
          </div>
          <BaseButton
            variant="secondary"
            size="sm"
            :disabled="!separacao.resumo.com_falta"
            data-testid="abrir-faltas"
            @click="faltasAberto = true"
          >
            <Printer :size="14" class="mr-1" />
            Faltas desta OS<template v-if="separacao.resumo.com_falta"> ({{ separacao.resumo.com_falta }})</template>
          </BaseButton>
        </div>
      </section>

      <!-- OS fechada: só leitura (D10) -->
      <p v-if="!editavel" class="rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm text-zinc-600" data-testid="separacao-fechada">
        {{ fraseFechada }}
      </p>

      <!-- Leitor (D2, D14-D17) -->
      <section v-else class="flex flex-wrap items-end gap-x-6 gap-y-3 rounded-2xl border border-zinc-200 bg-white px-6 py-4">
        <div>
          <label for="campo-codigo-separacao" class="mb-1 block text-xs font-medium text-gray-700">Ler código</label>
          <div class="relative">
            <ScanBarcode :size="18" class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
            <!-- Nativo de propósito: o leitor precisa do foco e do Enter direto no campo (D14). -->
            <input
              id="campo-codigo-separacao"
              ref="campoCodigo"
              v-model="codigoDigitado"
              type="text"
              autocomplete="off"
              class="w-72 rounded-md border border-gray-300 py-2 pl-10 pr-3 text-sm text-gray-700 outline-none transition-colors placeholder:text-gray-400 focus:border-brand-primary focus:ring-1 focus:ring-brand-primary"
              placeholder="Bipe ou digite e tecle Enter"
              data-testid="campo-codigo"
              @keydown.enter.prevent="aoLer(codigoDigitado)"
            />
          </div>
        </div>
        <label class="flex min-h-11 items-center gap-2 text-sm text-zinc-700">
          <input v-model="cadaLeituraRetira" type="checkbox" class="h-4 w-4 accent-brand-primary" data-testid="cada-leitura-retira" />
          Cada leitura retira
        </label>
        <label class="flex min-h-11 items-center gap-2 text-sm text-zinc-700">
          <input v-model="soPendentes" type="checkbox" class="h-4 w-4 accent-brand-primary" data-testid="so-pendentes" />
          Mostrar só pendentes
        </label>
        <p
          v-if="mensagemLeitor"
          role="status"
          class="basis-full text-sm font-medium"
          :class="{ 'text-red-600': mensagemLeitor.tom === 'erro', 'text-amber-700': mensagemLeitor.tom === 'atencao', 'text-emerald-700': mensagemLeitor.tom === 'ok' }"
          data-testid="mensagem-leitor"
        >
          {{ mensagemLeitor.texto }}
        </p>
      </section>

      <!-- As linhas, na ordem do depósito (D3) -->
      <section class="overflow-hidden rounded-2xl border border-zinc-200 bg-white">
        <div
          v-if="linhasVisiveis.length"
          class="hidden gap-x-4 border-b border-zinc-200 bg-zinc-50 px-5 py-3 text-xs font-semibold uppercase tracking-wide text-zinc-500 md:grid md:grid-cols-[minmax(0,2fr)_minmax(0,1.6fr)_minmax(0,1fr)_minmax(0,1fr)_auto]"
          aria-hidden="true"
        >
          <span>Insumo · usado em</span><span>Quantidades</span><span>Local no estoque</span><span>Situação</span><span class="w-28" />
        </div>
        <div class="divide-y divide-zinc-100">
          <SeparacaoLinha
            v-for="linha in linhasVisiveis"
            :key="linha.item_id"
            :linha="linha"
            :editavel="editavel"
            :destacada="destacada === linha.item_id"
            @retirar="abrirRetirar(linha)"
            @devolver="devolverModal = { aberto: true, linha }"
            @concluir="concluir(linha, false)"
            @nao-usado="concluir(linha, true)"
            @reabrir="reabrirLinha(linha)"
          />
        </div>
        <p v-if="!separacao.linhas.length" class="px-5 py-6 text-center text-sm text-zinc-500">Esta OS não tem material a separar.</p>
        <p v-else-if="!linhasVisiveis.length" class="px-5 py-6 text-center text-sm text-emerald-700" data-testid="tudo-separado">
          Tudo separado. Desmarque "Mostrar só pendentes" para ver o que saiu.
        </p>
      </section>

      <!-- Produto excluído do cadastro: só informa (D8; 10A D3) -->
      <div v-if="separacao.sem_cadastro.length" class="rounded-2xl border border-zinc-200 bg-white px-6 py-4" data-testid="sem-cadastro">
        <p class="flex items-center gap-2 text-sm font-semibold text-zinc-800">
          Produto excluído do cadastro: não baixa estoque
          <BaseStatusPill tom="neutro">{{ separacao.sem_cadastro.length }}</BaseStatusPill>
        </p>
        <ul class="mt-1 text-sm text-zinc-600">
          <li v-for="item in separacao.sem_cadastro" :key="item.descricao">{{ item.descricao }} · {{ quantidadeSimples(item.planejado_milesimos) }}</li>
        </ul>
      </div>

      <SeparacaoResumo :linhas="separacao.linhas" />
    </template>

    <!-- Modais -->
    <RetirarModal
      :is-open="retirarModal.aberto"
      :linha="retirarModal.linha"
      :quantidade-inicial="retirarModal.quantidade"
      :gravando="gravando"
      @close="fecharRetirar"
      @confirmar="confirmarRetirar"
    />
    <DevolverModal
      :is-open="devolverModal.aberto"
      :linha="devolverModal.linha"
      :gravando="gravando"
      @close="devolverModal = { aberto: false, linha: null }; focarCampo()"
      @confirmar="confirmarDevolver"
    />
    <FaltasDaOS
      :is-open="faltasAberto"
      :numero-os="numeroOs"
      :tem-compras="comprasDisponivel"
      @close="faltasAberto = false; focarCampo()"
      @ver-necessidades="faltasAberto = false; emit('verNecessidades')"
    />
    <SugestaoStatusModal :sugestao="sugestao" :aplicando="aplicandoStatus" @mover="moverStatus" @agora-nao="sugestao = null" />
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
