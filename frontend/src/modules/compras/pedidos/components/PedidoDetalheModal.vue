<script setup lang="ts">
/**
 * Tudo sobre um pedido de compra, e as ações de cada situação.
 *
 *   RASCUNHO  editar · WhatsApp · imprimir · marcar como enviado · cancelar
 *   ENVIADO   WhatsApp · imprimir · mudar previsão · voltar a rascunho · cancelar
 *             · receber
 *   PARCIAL   receber o resto · encerrar saldo · imprimir
 *   RECEBIDO / CANCELADO  só leitura (com os recebimentos / o motivo)
 *
 * "Marcar como enviado" é separado do WhatsApp de propósito: mandar a mensagem
 * não prova que o fornecedor recebeu, e o lojista pode mandar por outro canal
 * (ligação, e-mail, vendedor na loja). Quem diz que foi é ele.
 */
import { computed, nextTick, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import {
  MessageCircle, Printer, Send, Undo2, XCircle, Pencil, Copy, CalendarClock, PackageCheck, CircleSlash,
} from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import { useToast } from '@/shared/composables/useToast';
import { formatData, formatDataPura } from '@/shared/utils/date.utils';
import { formatCurrency } from '@/shared/utils/finance';
import { imprimirComPagina } from '@/shared/utils/print.utils';

import MotivoModal from '../../shared/components/MotivoModal.vue';
import SituacaoPedidoBadge from '../../shared/components/SituacaoPedidoBadge.vue';
import { useAcessoCompras } from '../../shared/composables/useAcessoCompras';
import {
  useAtualizarDadosPedido,
  useCancelarPedido,
  useEncerrarSaldo,
  useEnviarPedido,
  usePedidoQuery,
  useVoltarRascunho,
} from '../../shared/composables/useCompras';
import { ROTULO_ACAO } from '../../shared/constants/situacoes';
import { getMensagemPedido } from '../../shared/services/compras.service';
import type { PedidoRead } from '../../shared/types/compras.types';
import PedidoCompraPrint from './PedidoCompraPrint.vue';

const props = defineProps<{ pedidoId: number | null }>();
const emit = defineEmits<{ fechar: []; editar: [pedido: PedidoRead] }>();

const toast = useToast();
const router = useRouter();
const { podeGerenciar, podeCancelar, podeVerCusto, podeReceber } = useAcessoCompras();
const idRef = computed(() => props.pedidoId);
const { data: pedido, isLoading } = usePedidoQuery(idRef);

const enviar = useEnviarPedido();
const voltar = useVoltarRascunho();
const cancelar = useCancelarPedido();
const encerrar = useEncerrarSaldo();
const atualizarDados = useAtualizarDadosPedido();

const situacao = computed(() => pedido.value?.situacao);
const aberto = computed(() => situacao.value === 'RASCUNHO' || situacao.value === 'ENVIADO');
/** Enviado ou recebido em parte: ainda chega mercadoria. */
const aReceber = computed(() => situacao.value === 'ENVIADO' || situacao.value === 'PARCIAL');
const algoRecebido = computed(() => (pedido.value?.itens ?? []).some((i) => i.quantidade_recebida > 0));

function irParaRecebimento() {
  if (!pedido.value) return;
  const id = pedido.value.id;
  emit('fechar');
  router.push({ name: 'purchases-receiving', query: { pedido: String(id) } });
}

// --- previsão de entrega (rascunho ou enviado) -------------------------------------
const editandoPrevisao = ref(false);
const novaPrevisao = ref('');
watch(() => props.pedidoId, () => { editandoPrevisao.value = false; });

function abrirPrevisao() {
  novaPrevisao.value = pedido.value?.previsao_entrega ?? '';
  editandoPrevisao.value = true;
}

function salvarPrevisao() {
  if (!pedido.value) return;
  atualizarDados.mutate(
    { id: pedido.value.id, previsao_entrega: novaPrevisao.value || null, observacao: pedido.value.observacao },
    { onSuccess: () => { editandoPrevisao.value = false; } },
  );
}

// --- motivo (voltar / cancelar) -----------------------------------------------------
type AcaoMotivo = 'voltar' | 'cancelar' | 'encerrar' | null;
const acaoMotivo = ref<AcaoMotivo>(null);

const TEXTOS_MOTIVO: Record<Exclude<AcaoMotivo, null>, { titulo: string; descricao: string; botao: string }> = {
  cancelar: {
    titulo: 'Cancelar o pedido?',
    descricao:
      'O pedido sai do que está a caminho e volta a aparecer nas Necessidades. Fica no histórico como cancelado; nada é apagado.',
    botao: 'Cancelar pedido',
  },
  voltar: {
    titulo: 'Voltar a rascunho?',
    descricao: 'O pedido volta a ser editável. Avise o fornecedor da mudança — o motivo fica no histórico.',
    botao: 'Voltar a rascunho',
  },
  encerrar: {
    titulo: 'Encerrar o saldo?',
    descricao:
      'O que ainda não chegou deixa de ser esperado e o pedido fica recebido. O que já entrou no estoque e nas contas não muda.',
    botao: 'Encerrar saldo',
  },
};

function confirmarMotivo(motivo: string) {
  if (!pedido.value) return;
  const id = pedido.value.id;
  const fechar = { onSuccess: () => { acaoMotivo.value = null; } };
  if (acaoMotivo.value === 'voltar') voltar.mutate({ id, motivo }, fechar);
  if (acaoMotivo.value === 'cancelar') cancelar.mutate({ id, motivo }, fechar);
  if (acaoMotivo.value === 'encerrar') encerrar.mutate({ id, motivo }, fechar);
}

// --- WhatsApp ----------------------------------------------------------------------
const montandoMensagem = ref(false);

async function abrirUrl(url: string) {
  try {
    const { openUrl } = await import('@tauri-apps/plugin-opener');
    await openUrl(url);
  } catch {
    window.open(url, '_blank');
  }
}

async function copiar(texto: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(texto);
    return true;
  } catch {
    return false;
  }
}

async function mandarWhatsapp() {
  if (!pedido.value) return;
  montandoMensagem.value = true;
  try {
    const { texto, telefone } = await getMensagemPedido(pedido.value.id);
    if (telefone) {
      await abrirUrl(`https://wa.me/${telefone}?text=${encodeURIComponent(texto)}`);
    } else {
      const ok = await copiar(texto);
      toast.error(
        'Fornecedor sem celular cadastrado',
        ok ? 'O texto do pedido foi copiado: cole na conversa com ele.' : 'Cadastre o celular no fornecedor.',
      );
    }
  } catch {
    toast.error('Não foi possível montar a mensagem');
  } finally {
    montandoMensagem.value = false;
  }
}

async function copiarTexto() {
  if (!pedido.value) return;
  try {
    const { texto } = await getMensagemPedido(pedido.value.id);
    if (await copiar(texto)) toast.success('Texto do pedido copiado');
  } catch {
    toast.error('Não foi possível copiar o texto');
  }
}

// --- impressão ---------------------------------------------------------------------
const imprimindo = ref(false);

async function imprimir() {
  if (!pedido.value || imprimindo.value) return;
  imprimindo.value = true;
  await nextTick();
  let fallback: ReturnType<typeof setTimeout>;
  const limpar = () => {
    imprimindo.value = false;
    window.removeEventListener('afterprint', limpar);
    clearTimeout(fallback);
  };
  window.addEventListener('afterprint', limpar);
  fallback = setTimeout(limpar, 60000);
  imprimirComPagina('A4');
}

function qtd(n: number): string {
  return n.toLocaleString('pt-BR');
}
</script>

<template>
  <BaseModal
    :is-open="!!pedidoId"
    :title="pedido ? `Pedido ${pedido.codigo}` : 'Pedido de compra'"
    size="3xl"
    overlay
    @close="emit('fechar')"
  >
    <p v-if="isLoading" class="py-8 text-center text-sm text-zinc-400">Carregando o pedido…</p>

    <div v-else-if="pedido" class="flex flex-col gap-5">
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p class="text-lg font-semibold text-zinc-800">{{ pedido.fornecedor_nome }}</p>
          <p class="mt-0.5 text-xs text-zinc-500">
            Criado em {{ formatData(pedido.criado_em) }}
            <template v-if="pedido.criado_por_nome"> por {{ pedido.criado_por_nome }}</template>
            <template v-if="pedido.enviado_em"> · enviado em {{ formatData(pedido.enviado_em) }}</template>
          </p>
        </div>
        <SituacaoPedidoBadge :situacao="pedido.situacao" :atrasado="pedido.atrasado" />
      </div>

      <p
        v-if="pedido.situacao === 'CANCELADO' && pedido.motivo_cancelamento"
        class="rounded-xl border border-zinc-200 bg-zinc-50 px-3.5 py-2.5 text-sm text-zinc-600"
      >
        <strong>Cancelado:</strong> {{ pedido.motivo_cancelamento }}
      </p>

      <dl class="grid gap-3 rounded-xl bg-zinc-50 px-4 py-3 text-sm sm:grid-cols-3">
        <div>
          <dt class="text-xs text-zinc-500">Entrega até</dt>
          <dd v-if="!editandoPrevisao" class="flex items-center gap-2 font-medium text-zinc-800">
            {{ formatDataPura(pedido.previsao_entrega, 'A combinar') }}
            <button
              v-if="aberto && podeGerenciar"
              type="button"
              class="text-brand-primary cursor-pointer"
              title="Mudar a previsão (o fornecedor avisou que atrasa, por exemplo)"
              @click="abrirPrevisao"
            >
              <CalendarClock :size="14" />
            </button>
          </dd>
          <dd v-else class="mt-1 flex items-end gap-2">
            <BaseInput v-model="novaPrevisao" type="date" />
            <BaseButton :is-loading="atualizarDados.isPending.value" @click="salvarPrevisao">Salvar</BaseButton>
            <BaseButton variant="ghost" @click="editandoPrevisao = false">Voltar</BaseButton>
          </dd>
        </div>
        <div>
          <dt class="text-xs text-zinc-500">Pagamento</dt>
          <dd class="font-medium text-zinc-800">{{ pedido.condicao_pagamento || 'A combinar' }}</dd>
        </div>
        <div v-if="podeVerCusto">
          <dt class="text-xs text-zinc-500">Total</dt>
          <dd class="font-semibold text-zinc-900 tabular-nums">{{ formatCurrency(pedido.valor_total ?? 0) }}</dd>
        </div>
      </dl>

      <div class="overflow-x-auto rounded-xl border border-zinc-200">
        <table class="w-full min-w-160 text-sm">
          <thead>
            <tr class="border-b border-zinc-100 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
              <th class="px-4 py-2.5">Produto</th>
              <th class="px-3 py-2.5 text-right">Qtd.</th>
              <th class="px-3 py-2.5">Un.</th>
              <th v-if="algoRecebido" class="px-3 py-2.5 text-right">Chegou</th>
              <th v-if="podeVerCusto" class="px-3 py-2.5 text-right">Preço</th>
              <th v-if="podeVerCusto" class="px-4 py-2.5 text-right">Subtotal</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-100">
            <tr v-for="item in pedido.itens" :key="item.id">
              <td class="px-4 py-2.5">
                <p class="text-zinc-800">{{ item.descricao }}</p>
                <p v-if="item.codigo_fornecedor" class="text-[11px] text-zinc-400">cód. {{ item.codigo_fornecedor }}</p>
              </td>
              <td class="px-3 py-2.5 text-right font-semibold tabular-nums">{{ qtd(item.quantidade) }}</td>
              <td class="px-3 py-2.5 text-zinc-600">
                {{ item.unidade_compra }}<span v-if="item.fator > 1" class="text-zinc-400"> c/ {{ item.fator }}</span>
              </td>
              <td v-if="algoRecebido" class="px-3 py-2.5 text-right tabular-nums">
                <span :class="item.pendente ? 'text-amber-700' : 'text-emerald-700'">{{ qtd(item.quantidade_recebida) }}</span>
                <span v-if="item.quantidade_cancelada" class="block text-[11px] text-zinc-400">
                  {{ qtd(item.quantidade_cancelada) }} encerrado
                </span>
              </td>
              <td v-if="podeVerCusto" class="px-3 py-2.5 text-right tabular-nums">{{ formatCurrency(item.custo_unitario ?? 0) }}</td>
              <td v-if="podeVerCusto" class="px-4 py-2.5 text-right tabular-nums">{{ formatCurrency(item.subtotal ?? 0) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="podeVerCusto" class="grid gap-4 sm:grid-cols-2">
        <div v-if="pedido.parcelas.length" class="text-sm">
          <p class="mb-1 text-xs font-semibold uppercase tracking-wide text-zinc-500">Parcelas combinadas</p>
          <p class="text-xs text-zinc-500 mb-1.5">Viram contas a pagar só quando a mercadoria chegar.</p>
          <ul class="flex flex-col gap-1">
            <li v-for="p in pedido.parcelas" :key="p.numero" class="flex justify-between text-zinc-700">
              <span>{{ p.numero }}ª — {{ p.dias === 0 ? 'à vista' : `${p.dias} dias` }}</span>
              <span class="tabular-nums">{{ formatCurrency(p.valor ?? 0) }}</span>
            </li>
          </ul>
        </div>
        <dl class="flex flex-col gap-1 text-sm sm:ml-auto sm:w-56">
          <div class="flex justify-between"><dt class="text-zinc-500">Itens</dt><dd class="tabular-nums">{{ formatCurrency(pedido.valor_itens ?? 0) }}</dd></div>
          <div v-if="pedido.frete" class="flex justify-between"><dt class="text-zinc-500">Frete</dt><dd class="tabular-nums">{{ formatCurrency(pedido.frete) }}</dd></div>
          <div v-if="pedido.desconto" class="flex justify-between"><dt class="text-zinc-500">Desconto</dt><dd class="tabular-nums">− {{ formatCurrency(pedido.desconto) }}</dd></div>
          <div class="flex justify-between border-t border-zinc-200 pt-1 font-semibold">
            <dt>Total</dt><dd class="tabular-nums">{{ formatCurrency(pedido.valor_total ?? 0) }}</dd>
          </div>
        </dl>
      </div>

      <div v-if="pedido.observacao" class="rounded-xl border border-zinc-100 px-3.5 py-2.5 text-xs text-zinc-600">
        {{ pedido.observacao }}
      </div>

      <!-- Cada chegada de mercadoria: o que entrou e quanto virou conta. -->
      <div v-if="pedido.recebimentos.length">
        <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">Recebimentos</p>
        <ul class="flex flex-col gap-2">
          <li v-for="r in pedido.recebimentos" :key="r.id" class="rounded-xl border border-zinc-100 px-3.5 py-2.5 text-sm">
            <p class="flex flex-wrap justify-between gap-2 text-zinc-800">
              <span>
                <strong>{{ formatData(r.recebido_em) }}</strong>
                <template v-if="r.recebido_por_nome"> · {{ r.recebido_por_nome }}</template>
                <template v-if="r.numero_nota"> · NF {{ r.numero_nota }}</template>
              </span>
              <span v-if="podeVerCusto && r.valor_total != null" class="tabular-nums font-semibold">
                {{ formatCurrency(r.valor_total) }}
              </span>
            </p>
            <p class="text-xs text-zinc-500">
              <span v-for="(i, n) in r.itens" :key="n">
                {{ qtd(i.quantidade) }} {{ i.unidade_compra }} {{ i.descricao }}<template v-if="n < r.itens.length - 1">; </template>
              </span>
            </p>
            <p v-if="r.contas_pagar_lancadas" class="text-[11px] text-zinc-400">
              {{ r.contas_pagar_lancadas }} {{ r.contas_pagar_lancadas === 1 ? 'conta lançada' : 'contas lançadas' }} no contas a pagar
            </p>
          </li>
        </ul>
      </div>

      <!-- Histórico: quem fez o quê, quando e por quê. Nunca se apaga. -->
      <div>
        <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">Histórico</p>
        <ol class="flex flex-col gap-2 border-l border-zinc-200 pl-4">
          <li v-for="(h, i) in pedido.historico" :key="i" class="text-sm">
            <p class="text-zinc-800">
              <strong>{{ ROTULO_ACAO[h.acao] ?? h.acao }}</strong>
              <span class="text-zinc-500"> · {{ formatData(h.ocorrido_em) }}<template v-if="h.usuario_nome"> · {{ h.usuario_nome }}</template></span>
            </p>
            <p v-if="h.motivo" class="text-xs text-zinc-500">{{ h.motivo }}</p>
          </li>
        </ol>
      </div>

      <PedidoCompraPrint v-if="imprimindo" :pedido="pedido" />
    </div>

    <template #footer>
      <div v-if="pedido" class="flex w-full flex-wrap items-center justify-between gap-2">
        <div class="flex flex-wrap gap-2">
          <template v-if="aberto">
            <BaseButton variant="secondary" :is-loading="montandoMensagem" @click="mandarWhatsapp">
              <MessageCircle :size="15" class="mr-1.5" /> WhatsApp
            </BaseButton>
            <BaseButton variant="ghost" @click="copiarTexto">
              <Copy :size="15" class="mr-1.5" /> Copiar texto
            </BaseButton>
          </template>
          <BaseButton variant="ghost" @click="imprimir">
            <Printer :size="15" class="mr-1.5" /> Imprimir / PDF
          </BaseButton>
        </div>
        <div class="flex flex-wrap gap-2">
          <BaseButton
            v-if="aberto && podeCancelar"
            variant="ghost-danger"
            @click="acaoMotivo = 'cancelar'"
          >
            <XCircle :size="15" class="mr-1.5" /> Cancelar pedido
          </BaseButton>
          <template v-if="pedido.situacao === 'RASCUNHO' && podeGerenciar">
            <BaseButton variant="secondary" @click="emit('editar', pedido)">
              <Pencil :size="15" class="mr-1.5" /> Editar
            </BaseButton>
            <BaseButton :is-loading="enviar.isPending.value" @click="enviar.mutate(pedido.id)">
              <Send :size="15" class="mr-1.5" /> Marcar como enviado
            </BaseButton>
          </template>
          <BaseButton
            v-if="pedido.situacao === 'ENVIADO' && podeGerenciar && !algoRecebido"
            variant="secondary"
            @click="acaoMotivo = 'voltar'"
          >
            <Undo2 :size="15" class="mr-1.5" /> Voltar a rascunho
          </BaseButton>
          <BaseButton
            v-if="pedido.situacao === 'PARCIAL' && podeReceber"
            variant="secondary"
            @click="acaoMotivo = 'encerrar'"
          >
            <CircleSlash :size="15" class="mr-1.5" /> Encerrar saldo
          </BaseButton>
          <BaseButton v-if="aReceber && podeReceber" @click="irParaRecebimento">
            <PackageCheck :size="15" class="mr-1.5" />
            {{ pedido.situacao === 'PARCIAL' ? 'Receber o resto' : 'Receber' }}
          </BaseButton>
        </div>
      </div>
    </template>
  </BaseModal>

  <MotivoModal
    :aberto="acaoMotivo !== null"
    :titulo="acaoMotivo ? TEXTOS_MOTIVO[acaoMotivo].titulo : ''"
    :descricao="acaoMotivo ? TEXTOS_MOTIVO[acaoMotivo].descricao : ''"
    :confirm-label="acaoMotivo ? TEXTOS_MOTIVO[acaoMotivo].botao : ''"
    :perigo="acaoMotivo === 'cancelar'"
    :carregando="cancelar.isPending.value || voltar.isPending.value || encerrar.isPending.value"
    @fechar="acaoMotivo = null"
    @confirmar="confirmarMotivo"
  />
</template>
