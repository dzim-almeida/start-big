<script setup lang="ts">
/**
 * @component SecaoTerceirizados
 * @description "Móveis da central" no topo da aba Separação da OS (Spec 11B
 * D1-D9). Só aparece quando a OS tem móvel terceirizado.
 *
 * Os móveis vêm agrupados por central (com o telefone: quem cobra liga para
 * uma central de cada vez). Marca-se as linhas e a barra de ações age sobre
 * as marcadas; cada botão só habilita quando faz sentido para TODAS (D3).
 *
 * - Com o módulo Compras (e permissão de gerir compras): "Pedir à central"
 *   cria o pedido em rascunho NO Compras; enviar e receber são feitos lá (D4).
 * - Sem o Compras: "Enviar pedido" e "Receber" anotam à mão (D6).
 * - Nos dois: "Conferir"; no menu da linha, problema e voltar um passo (D7).
 *
 * Não conhece o modal de OS: para ir a outra tela, avisa o pai (`navegar`).
 */
import { computed, onBeforeUnmount, ref, toRef, watch } from 'vue';
import { useRouter, type RouteLocationRaw } from 'vue-router';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseConfirmModal from '@/shared/components/commons/BaseConfirmModal/BaseConfirmModal.vue';
import { useConfirmacao } from '@/shared/composables/useConfirmacao';
import { useToast } from '@/shared/composables/useToast';
import { formatTelefone } from '@/shared/utils/document.utils';
import { useAcessoCompras } from '@/modules/compras/shared/composables/useAcessoCompras';
import { statusDoErro } from '@/modules/marcenaria/orcamentos/utils/erros';
import { escaparHtml } from '@/modules/marcenaria/orcamentos/utils/textoSeguro';

import { useTerceirizadosDaOS } from '../composables/useTerceirizadosDaOS';
import type { MovelTerceirizado, TerceirizadosDaOS } from '../schemas/terceirizado.schema';
import { podeAplicar, ROTULO_SITUACAO, voltaPara, type AcaoEmLote } from '../utils/terceirizados';
import EnviarManualModal from './EnviarManualModal.vue';
import PedirCentralModal from './PedirCentralModal.vue';
import ProblemaModal from './ProblemaModal.vue';
import ReceberManualModal from './ReceberManualModal.vue';
import TerceirizadoLinha from './TerceirizadoLinha.vue';

const props = defineProps<{ numeroOs: string }>();
const emit = defineEmits<{
  /** Ir para outra tela (o pai fecha o modal de OS antes). */
  navegar: [destino: RouteLocationRaw];
  /** A resposta do conferir/voltar trouxe uma sugestão de status da OS (12A D16; usada na 12B). */
  sugestaoStatus: [secao: TerceirizadosDaOS];
}>();
/** Verdadeiro com um modal da seção aberto: a aba pausa o leitor de código (10B D17). */
const ocupado = defineModel<boolean>('ocupado', { default: false });

const {
  data: secao, error, gravando,
  pedir, enviarManual, receberManual, conferir, registrarProblema, voltar,
} = useTerceirizadosDaOS(toRef(props, 'numeroOs'), ref(true));

const toast = useToast();
const router = useRouter();
const acessoCompras = useAcessoCompras();

/** 404 = OS sem orçamento: a seção some sem aviso (a aba já explica). */
const erroDeVerdade = computed(() => !!error.value && statusDoErro(error.value) !== 404);
const moveis = computed(() => secao.value?.moveis ?? []);
const editavel = computed(() => secao.value?.os.editavel ?? false);
const modoCompras = computed(() => secao.value?.modo_compras === true);

/** §7.2: "Pedir à central" é ato do Compras: módulo e permissão de gerir compras (11A D10). */
const podePedirPeloCompras = computed(() => modoCompras.value && acessoCompras.podeGerenciar.value);
/**
 * "Receber" à mão: sem o Compras (D6) e também, com ele, para um pedido que
 * foi ANOTADO antes de a loja contratar o Compras (sem isso, esse móvel não
 * teria como andar).
 */
const mostraReceberManual = computed(() =>
  !modoCompras.value || moveis.value.some((m) => m.situacao === 'ENVIADO' && m.pedido?.origem === 'MANUAL'),
);

// --- Título com a contagem (D1) ---------------------------------------------------------
const atrasados = computed(() => moveis.value.filter((m) => m.atrasado).length);
const titulo = computed(() => {
  const base = `Móveis da central (${moveis.value.length})`;
  if (!atrasados.value) return base;
  return `${base} · ${atrasados.value} ${atrasados.value === 1 ? 'atrasado' : 'atrasados'}`;
});

// --- Agrupados por central, na ordem em que aparecem (D2) -------------------------------
const grupos = computed(() => {
  const mapa = new Map<string, { chave: string; nome: string; telefone: string | null; moveis: MovelTerceirizado[] }>();
  for (const movel of moveis.value) {
    const chave = movel.central ? String(movel.central.id) : 'sem';
    if (!mapa.has(chave)) {
      mapa.set(chave, {
        chave,
        nome: movel.central?.nome ?? 'Sem central no orçamento',
        telefone: movel.central?.telefone ? formatTelefone(movel.central.telefone) : null,
        moveis: [],
      });
    }
    mapa.get(chave)!.moveis.push(movel);
  }
  return [...mapa.values()];
});

// --- Seleção (D3) -----------------------------------------------------------------------
const selecionados = ref(new Set<number>());
const marcados = computed(() => moveis.value.filter((m) => selecionados.value.has(m.movel_id)));

function marcar(movelId: number, valor: boolean) {
  const novo = new Set(selecionados.value);          // um Set novo: o Vue percebe a troca
  if (valor) novo.add(movelId);
  else novo.delete(movelId);
  selecionados.value = novo;
}

// Recarregou (outra pessoa mexeu): tira da seleção o que sumiu da lista.
watch(moveis, (lista) => {
  const ids = new Set(lista.map((m) => m.movel_id));
  if ([...selecionados.value].some((id) => !ids.has(id))) {
    selecionados.value = new Set([...selecionados.value].filter((id) => ids.has(id)));
  }
});

/** O botão habilita? E, se não, por quê (vai no `title`). */
const regra = (acao: AcaoEmLote) => podeAplicar(acao, marcados.value);

// --- Modais da seção --------------------------------------------------------------------
type Modal = 'pedir' | 'enviar' | 'receber' | null;
const modal = ref<Modal>(null);
const problemaDe = ref<MovelTerceirizado | null>(null);
const confirmacao = useConfirmacao();
// Avisa a aba: com modal aberto, o leitor de código não pode capturar a digitação.
watch(
  () => modal.value !== null || problemaDe.value !== null || confirmacao.isOpen.value,
  (aberto) => { ocupado.value = aberto; },
  { immediate: true },
);
/** Os móveis que o modal aberto recebe (cópia: a seleção pode mudar por baixo). */
const moveisDoModal = ref<MovelTerceirizado[]>([]);

function abrir(qual: Exclude<Modal, null>) {
  moveisDoModal.value = [...marcados.value];
  modal.value = qual;
}

/** Depois de cada ação que deu certo: limpa a seleção e fecha o modal (§7.3). */
function terminou(ok: unknown) {
  if (!ok) return;                                    // erro: o modal fica aberto para tentar de novo
  selecionados.value = new Set();
  modal.value = null;
}

// --- Navegação --------------------------------------------------------------------------
let montado = true;
onBeforeUnmount(() => { montado = false; });
/**
 * Pede ao pai para navegar. O toast do pedido pode ser clicado DEPOIS de a
 * aba fechar: aí não há mais pai para avisar, e o próprio roteador leva.
 */
function navegar(destino: RouteLocationRaw) {
  if (montado) emit('navegar', destino);
  else void router.push(destino);
}

/** D5: "Pedido enviado" vai receber; nos outros, a lista de pedidos já filtrada na situação. */
function verNoCompras(movel: MovelTerceirizado) {
  if (movel.pedido?.origem !== 'COMPRAS') return;
  if (movel.situacao === 'ENVIADO') {
    navegar({ name: 'purchases-receiving', query: { pedido: String(movel.pedido.id) } });
  } else {
    navegar({ name: 'purchases-orders', query: { situacao: movel.pedido.situacao } });
  }
}

// --- Ações ------------------------------------------------------------------------------
async function confirmarPedir(previsao: string | null, observacao: string | null) {
  const resposta = await pedir(moveisDoModal.value.map((m) => m.movel_id), previsao, observacao);
  terminou(resposta);
  if (!resposta) return;
  const codigo = resposta.pedido.codigo;
  // D4: o atalho para o pedido recém-criado (a lista abre nos rascunhos).
  toast.success(`Pedido ${codigo} criado no Compras.`, 'Envie e receba o pedido por lá.', {
    action: {
      label: `Abrir pedido ${codigo}`,
      onClick: () => navegar({ name: 'purchases-orders', query: { situacao: 'RASCUNHO' } }),
    },
  });
}

async function confirmarEnviar(pedido: string | null, previsao: string | null) {
  terminou(await enviarManual(moveisDoModal.value.map((m) => m.movel_id), pedido, previsao));
}

async function confirmarReceber(data: string | null) {
  terminou(await receberManual(moveisDoModal.value.map((m) => m.movel_id), data));
}

/** Só o botão "Conferir" mostra "carregando" enquanto confere (não o de outra ação). */
const conferindo = ref(false);

async function conferirMarcados() {
  conferindo.value = true;
  const resposta = await conferir(marcados.value.map((m) => m.movel_id));
  conferindo.value = false;
  terminou(resposta);
  if (resposta?.sugestao_status) emit('sugestaoStatus', resposta);
}

async function confirmarProblema(texto: string) {
  const movel = problemaDe.value;
  if (!movel) return;
  const resposta = await registrarProblema(movel.movel_id, texto);
  if (resposta) problemaDe.value = null;
}

/** D7: voltar um passo, sempre com confirmação dizendo para onde. */
async function pedirVoltar(movel: MovelTerceirizado) {
  const destino = voltaPara(movel);
  if (!destino) return;
  const de = ROTULO_SITUACAO[movel.situacao];
  const para = ROTULO_SITUACAO[destino];
  // Voltar a "A pedir" apaga o pedido anotado: é bom dizer antes.
  const aviso = destino === 'A_PEDIR' ? ' O número do pedido e a previsão anotados serão apagados.' : '';
  const ok = await confirmacao.pedirConfirmacao({
    titulo: `Voltar para ${para}?`,
    descricao: `<strong>${escaparHtml(movel.nome)}</strong> volta de "${de}" para "${para}".${aviso}`,
    confirmLabel: 'Voltar',
  });
  if (!ok) return;
  const resposta = await voltar(movel.movel_id);
  if (resposta) selecionados.value = new Set();
  if (resposta?.sugestao_status) emit('sugestaoStatus', resposta);
}
</script>

<template>
  <section v-if="erroDeVerdade" class="text-sm text-red-600">Não foi possível carregar os móveis da central agora.</section>

  <!-- D1: só quando a OS tem móvel terceirizado -->
  <section v-else-if="moveis.length" class="space-y-3 rounded-2xl border border-zinc-200 bg-zinc-50/60 p-4" data-testid="secao-terceirizados">
    <h3 class="text-base font-bold text-zinc-800" :class="{ 'text-red-700': atrasados }" data-testid="titulo-terceirizados">
      {{ titulo }}
    </h3>

    <!-- D2: um bloco por central, com o telefone -->
    <div v-for="grupo in grupos" :key="grupo.chave" class="space-y-2" :data-testid="`central-${grupo.chave}`">
      <p class="text-sm font-semibold text-zinc-700">
        {{ grupo.nome }}<span v-if="grupo.telefone" class="font-normal text-zinc-500"> · {{ grupo.telefone }}</span>
      </p>
      <TerceirizadoLinha
        v-for="movel in grupo.moveis"
        :key="movel.movel_id"
        :movel="movel"
        :editavel="editavel"
        :marcado="selecionados.has(movel.movel_id)"
        :ver-no-compras="movel.pedido?.origem === 'COMPRAS' && acessoCompras.podeVer.value"
        @update:marcado="marcar(movel.movel_id, $event)"
        @ver-no-compras="verNoCompras(movel)"
        @problema="problemaDe = movel"
        @voltar="pedirVoltar(movel)"
      />
    </div>

    <!-- D3: a barra age sobre os marcados; o `title` do invólucro explica o botão apagado -->
    <div v-if="editavel" class="flex flex-wrap justify-end gap-2" data-testid="barra-terceirizados">
      <span v-if="podePedirPeloCompras" :title="regra('pedir').motivo">
        <BaseButton size="sm" :disabled="!regra('pedir').ok" data-testid="acao-pedir" @click="abrir('pedir')">Pedir à central</BaseButton>
      </span>
      <span v-if="!modoCompras" :title="regra('enviar').motivo">
        <BaseButton size="sm" variant="secondary" :disabled="!regra('enviar').ok" data-testid="acao-enviar" @click="abrir('enviar')">
          Enviar pedido
        </BaseButton>
      </span>
      <span v-if="mostraReceberManual" :title="regra('receber').motivo">
        <BaseButton size="sm" variant="secondary" :disabled="!regra('receber').ok" data-testid="acao-receber" @click="abrir('receber')">
          Receber
        </BaseButton>
      </span>
      <span :title="regra('conferir').motivo">
        <BaseButton size="sm" :disabled="!regra('conferir').ok" :is-loading="conferindo" data-testid="acao-conferir" @click="conferirMarcados">
          Conferir
        </BaseButton>
      </span>
    </div>

    <!-- D6: sem o Compras, a conta da central é lançada à mão -->
    <p v-if="!modoCompras" class="text-xs text-zinc-500" data-testid="dica-conta">
      Lance a conta da central em Contas a Pagar, numa categoria de despesa.
    </p>

    <!-- Modais (overlay: abrem por cima do modal de OS) -->
    <PedirCentralModal :is-open="modal === 'pedir'" :moveis="moveisDoModal" :gravando="gravando" @close="modal = null" @confirmar="confirmarPedir" />
    <EnviarManualModal :is-open="modal === 'enviar'" :moveis="moveisDoModal" :gravando="gravando" @close="modal = null" @confirmar="confirmarEnviar" />
    <ReceberManualModal :is-open="modal === 'receber'" :moveis="moveisDoModal" :gravando="gravando" @close="modal = null" @confirmar="confirmarReceber" />
    <ProblemaModal :is-open="problemaDe !== null" :movel="problemaDe" :gravando="gravando" @close="problemaDe = null" @confirmar="confirmarProblema" />
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
  </section>
</template>
