<script setup lang="ts">
/**
 * @component CartaoVeiculo
 * @description Um veículo no pátio (Spec 04B, SPEC-00 U3).
 *
 * Mostra o que o lavador e o atendente precisam sem abrir a OS: placa,
 * veículo, porte, serviços, lavadores, há quanto tempo está no pátio e a
 * previsão. A ação principal muda com a coluna:
 *   Aguardando → "Começar"   Lavando → "Pronto"   Pronto → WhatsApp + "Receber"
 * "Ver detalhes" abre a OS de sempre.
 */
import { computed } from 'vue';
import { AlertTriangle, ArrowLeft, Clock, MessageCircle, Users } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import type { CartaoPatio } from '../../shared/schemas/patio.schema';
import { horaLocal, linkWhatsApp, mensagemPronto, reais, soDia, tempoNoPatio } from '../../shared/utils/lavaRapido';

const props = defineProps<{
  cartao: CartaoPatio;
  /** Coluna em que o cartão está: decide a ação principal. */
  coluna: 'aguardando' | 'lavando' | 'pronto' | 'entregue';
  /** Relógio da tela (atualiza o "há X min" sem recarregar o pátio). */
  agora: Date;
  ocupado?: boolean;
}>();

const emit = defineEmits<{
  avancar: [numeroOs: string];
  voltar: [numeroOs: string];
  receber: [numeroOs: string];
  detalhes: [numeroOs: string];
  lavadores: [cartao: CartaoPatio];
}>();

const veiculo = computed(() =>
  [props.cartao.modelo, props.cartao.cor].filter(Boolean).join(' · ') || 'Veículo');

/** Placa gerada (VEI-...) não é placa de verdade: mostra mais discreta. */
const placaGerada = computed(() => (props.cartao.placa ?? '').startsWith('VEI-'));

/**
 * Previsão gravada só com o DIA (00:00, sem hora calculada): não é horário.
 * Lida como UTC ela virava "Pronto às 21:00" do dia anterior, em vermelho.
 */
const previsaoSoDia = computed(() => soDia(props.cartao.previsao));

/** Texto da previsão: a hora; ou, sem hora, o dia (e nada quando é hoje). */
const textoPrevisao = computed(() => {
  const p = props.cartao.previsao;
  if (!p) return '';
  if (!previsaoSoDia.value) return `Pronto às ${horaLocal(p)}`;
  const [ano, mes, dia] = p.slice(0, 10).split('-').map(Number);
  const data = new Date(ano, mes - 1, dia);
  if (data.toDateString() === props.agora.toDateString()) return '';
  return `Previsto p/ ${data.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}`;
});

const atrasado = computed(() => {
  const p = props.cartao.previsao;
  if (!p || props.coluna === 'entregue' || props.coluna === 'pronto') return false;
  if (previsaoSoDia.value) {
    // Só o dia: atrasa quando o dia inteiro já passou.
    const [ano, mes, dia] = p.slice(0, 10).split('-').map(Number);
    return new Date(ano, mes - 1, dia + 1).getTime() <= props.agora.getTime();
  }
  const iso = /[zZ]$/.test(p) ? p : `${p}Z`;
  return new Date(iso).getTime() < props.agora.getTime();
});

const whatsapp = computed(() =>
  linkWhatsApp(
    props.cartao.cliente_contato,
    mensagemPronto(props.cartao.cliente_nome, props.cartao.modelo, placaGerada.value ? null : props.cartao.placa),
  ));

const nomesLavadores = computed(() => props.cartao.lavadores.map((l) => l.nome.split(' ')[0]).join(' e '));
</script>

<template>
  <article
    class="flex flex-col gap-3 rounded-2xl border bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
    :class="atrasado ? 'border-red-200' : 'border-zinc-200'"
    :data-testid="`cartao-${cartao.numero_os}`"
  >
    <!-- Placa e tempo -->
    <header class="flex items-start justify-between gap-2">
      <div class="min-w-0">
        <p
          class="font-mono font-bold tracking-wider"
          :class="placaGerada ? 'text-sm text-zinc-400' : 'text-lg text-zinc-900'"
        >
          {{ cartao.placa || '—' }}
        </p>
        <p class="truncate text-sm font-medium text-zinc-700">{{ veiculo }}</p>
        <p v-if="cartao.porte" class="text-xs text-zinc-500">{{ cartao.porte }}</p>
      </div>
      <div class="shrink-0 text-right text-xs">
        <p v-if="coluna !== 'entregue'" class="flex items-center justify-end gap-1 text-zinc-500">
          <Clock :size="12" /> {{ tempoNoPatio(cartao.entrada, agora) }}
        </p>
        <p v-else class="text-zinc-500">às {{ horaLocal(cartao.finalizada_em) }}</p>
        <p
          v-if="textoPrevisao && coluna !== 'entregue'"
          class="mt-0.5 font-semibold"
          :class="atrasado ? 'text-red-600' : 'text-zinc-600'"
        >
          <AlertTriangle v-if="atrasado" :size="11" class="inline" />
          {{ textoPrevisao }}
        </p>
      </div>
    </header>

    <!-- Serviços e valor -->
    <div class="flex items-end justify-between gap-2 border-t border-zinc-100 pt-2">
      <p class="text-sm text-zinc-700">{{ cartao.servicos.join(', ') || 'Sem serviço lançado' }}</p>
      <p class="shrink-0 text-sm font-bold tabular-nums text-zinc-900">{{ reais(cartao.valor_total) }}</p>
    </div>

    <!-- Cliente, lavadores e avarias -->
    <div class="flex flex-col gap-1 text-xs text-zinc-500">
      <p v-if="cartao.cliente_nome" class="truncate">{{ cartao.cliente_nome }}</p>
      <button
        v-if="coluna !== 'entregue'"
        type="button"
        class="flex items-center gap-1 text-left hover:text-brand-primary"
        title="Trocar lavadores"
        @click="emit('lavadores', cartao)"
      >
        <Users :size="12" />
        {{ nomesLavadores || 'Escolher lavador' }}
      </button>
      <p v-else-if="nomesLavadores" class="flex items-center gap-1"><Users :size="12" /> {{ nomesLavadores }}</p>
      <p v-if="cartao.avarias.length" class="flex items-center gap-1 text-amber-700">
        <AlertTriangle :size="12" /> {{ cartao.avarias.length }} avaria(s): {{ cartao.avarias.join(', ') }}
      </p>
    </div>

    <!-- Ações -->
    <footer class="flex flex-wrap items-center gap-2 pt-1">
      <BaseButton
        v-if="coluna === 'aguardando'"
        size="sm"
        class="flex-1"
        :disabled="ocupado"
        @click="emit('avancar', cartao.numero_os)"
      >
        Começar a lavar
      </BaseButton>
      <BaseButton
        v-else-if="coluna === 'lavando'"
        size="sm"
        class="flex-1"
        :disabled="ocupado"
        @click="emit('avancar', cartao.numero_os)"
      >
        Pronto
      </BaseButton>
      <template v-else-if="coluna === 'pronto'">
        <a
          v-if="whatsapp"
          :href="whatsapp"
          target="_blank"
          rel="noopener"
          class="inline-flex min-h-9 items-center gap-1 rounded-lg border border-emerald-200 px-3 text-xs font-semibold text-emerald-700 hover:bg-emerald-50"
        >
          <MessageCircle :size="14" /> WhatsApp
        </a>
        <BaseButton size="sm" class="flex-1" :disabled="ocupado" @click="emit('receber', cartao.numero_os)">
          Receber
        </BaseButton>
      </template>

      <button
        v-if="coluna === 'lavando' || coluna === 'pronto'"
        type="button"
        class="rounded-lg p-2 text-zinc-400 hover:text-zinc-700"
        title="Voltar para a coluna anterior"
        :disabled="ocupado"
        @click="emit('voltar', cartao.numero_os)"
      >
        <ArrowLeft :size="14" />
      </button>
      <button
        type="button"
        class="ml-auto text-xs font-semibold text-brand-primary hover:underline"
        @click="emit('detalhes', cartao.numero_os)"
      >
        Ver detalhes
      </button>
    </footer>
  </article>
</template>
