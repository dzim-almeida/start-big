<script setup lang="ts">
/**
 * @component VisaoClienteView
 * @description Tela somente leitura para o vendedor virar para o cliente
 * (Spec 06B D14, §6.5; SPEC-00 T3a). Mesma ordem e mesmo conteúdo da proposta
 * impressa (Spec 07), porque os dois usam `montarDadosProposta`.
 *
 * Recebe SÓ `DadosProposta`: não há como mostrar custo, insumo, margem,
 * parâmetro ou preço por móvel aqui, nem por engano.
 */
import { ArrowLeft } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { formatCurrency } from '@/shared/utils/finance';

import type { DadosProposta } from '../../utils/dadosProposta';

defineProps<{ dados: DadosProposta }>();
const emit = defineEmits<{ voltar: [] }>();
</script>

<template>
  <div class="mx-auto max-w-3xl rounded-2xl border border-zinc-200 bg-white p-8 text-base text-zinc-800" data-testid="visao-cliente">
    <!-- Cabeçalho: cliente, projeto e endereço -->
    <header class="border-b border-zinc-100 pb-5">
      <p class="text-xs uppercase tracking-widest text-zinc-400">Proposta {{ dados.codigo }} · versão {{ dados.versao }}</p>
      <h2 class="mt-1 text-2xl font-bold text-zinc-900">{{ dados.projeto.nome || 'Projeto' }}</h2>
      <p v-if="dados.projeto.enderecoObra" class="text-sm text-zinc-500">{{ dados.projeto.enderecoObra }}</p>
      <p v-if="dados.cliente.nome" class="mt-3 text-sm">
        <span class="text-zinc-500">Cliente:</span> {{ dados.cliente.nome }}
      </p>
      <p v-if="dados.vendedor" class="text-sm">
        <span class="text-zinc-500">Consultor:</span> {{ dados.vendedor.nome }}<template v-if="dados.vendedor.telefone"> · {{ dados.vendedor.telefone }}</template>
      </p>
    </header>

    <!-- Ambientes com os móveis e o TOTAL do ambiente (sem preço por móvel, T5) -->
    <section v-if="dados.ambientes.length" class="mt-6 flex flex-col gap-6">
      <article v-for="ambiente in dados.ambientes" :key="ambiente.nome">
        <div class="flex items-baseline justify-between border-b border-zinc-200 pb-1">
          <h3 class="text-lg font-semibold uppercase tracking-wide">{{ ambiente.nome }}</h3>
          <span class="font-semibold tabular-nums">{{ formatCurrency(ambiente.totalCentavos) }}</span>
        </div>
        <ul class="mt-2 flex flex-col gap-3">
          <li v-for="(movel, indice) in ambiente.moveis" :key="indice">
            <p class="font-medium">
              {{ movel.nome }}
              <span v-if="movel.quantidade > 1" class="ml-2 text-sm font-semibold text-zinc-600">{{ movel.quantidade }} un.</span>
            </p>
            <p v-if="movel.descricao" class="text-sm text-zinc-600">{{ movel.descricao }}</p>
            <p v-if="movel.medidas" class="text-sm text-zinc-500">{{ movel.medidas }}</p>
          </li>
        </ul>
      </article>
    </section>
    <p v-else class="mt-6 text-zinc-500">Nenhum móvel incluído.</p>

    <!-- Valores -->
    <dl class="ml-auto mt-8 flex max-w-sm flex-col gap-1.5">
      <div v-if="dados.instalacaoCentavos != null" class="flex justify-between">
        <dt class="text-zinc-600">Instalação e montagem</dt>
        <dd class="tabular-nums">{{ formatCurrency(dados.instalacaoCentavos) }}</dd>
      </div>
      <div class="flex justify-between">
        <dt class="text-zinc-600">Subtotal</dt>
        <dd class="tabular-nums">{{ formatCurrency(dados.subtotalCentavos) }}</dd>
      </div>
      <div v-if="dados.desconto" class="flex justify-between">
        <dt class="text-zinc-600">Desconto<template v-if="dados.desconto.percentualTexto"> ({{ dados.desconto.percentualTexto }})</template></dt>
        <dd class="tabular-nums">− {{ formatCurrency(dados.desconto.centavos) }}</dd>
      </div>
      <div class="flex justify-between border-t border-zinc-200 pt-2 text-xl font-bold">
        <dt>Total</dt>
        <dd class="tabular-nums" data-testid="visao-total">{{ formatCurrency(dados.totalCentavos) }}</dd>
      </div>
    </dl>

    <!-- Condições -->
    <section class="mt-6 border-t border-zinc-100 pt-4 text-sm text-zinc-700">
      <p v-if="dados.sinal">
        Sinal na aprovação: {{ formatCurrency(dados.sinal.centavos) }}<template v-if="dados.sinal.percentualTexto"> ({{ dados.sinal.percentualTexto }})</template>
        · Saldo: {{ formatCurrency(dados.saldoCentavos) }}
      </p>
      <p v-else>Total a pagar: {{ formatCurrency(dados.totalCentavos) }}</p>
      <p>Prazo de entrega: {{ dados.prazoEntregaDias }} dias corridos após a aprovação</p>
      <p>Validade: {{ dados.validadeTexto }}</p>
      <p v-if="dados.observacoes" class="mt-3 whitespace-pre-line">{{ dados.observacoes }}</p>
    </section>

    <div class="sticky bottom-4 mt-8 flex justify-center">
      <BaseButton variant="primary" data-testid="voltar-orcamento" @click="emit('voltar')">
        <ArrowLeft :size="16" class="mr-1" /> Voltar ao orçamento
      </BaseButton>
    </div>
  </div>
</template>
