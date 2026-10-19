<script setup lang="ts">
/**
 * @component EditorAcoes
 * @description O que se faz com o orçamento, embaixo do resumo na coluna
 * lateral (redesign 10/2026): Aprovar e gerar OS (08B D1) em destaque, Enviar
 * ao cliente (D36), e a Proposta em PDF (Spec 07) e a Visão do cliente (D14).
 *
 * Fica no resumo, que acompanha a rolagem: as ações nunca somem de vista.
 */
import { computed } from 'vue';
import { CheckCheck, Eye, Printer, Send } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import type { OrcamentoDetalhe } from '../../schemas/orcamentoDetalhe.schema';

const props = defineProps<{
  detalhe?: OrcamentoDetalhe;
  visaoCliente: boolean;
  imprimindo: boolean;
}>();

const emit = defineEmits<{
  alternarVisaoCliente: [];
  enviar: [];
  /** Spec 08B D1: aprovar e gerar a OS. */
  aprovar: [];
  proposta: [];
}>();

const acoes = computed(() => props.detalhe?.acoes);
</script>

<template>
  <div v-if="detalhe" class="flex flex-col gap-2" data-testid="acoes-orcamento">
    <!-- Aprovar (08B D1): é o objetivo do orçamento, por isso é o botão principal. -->
    <BaseButton v-if="acoes?.aprovar" variant="primary" size="md" class="w-full" data-testid="acao-aprovar" @click="emit('aprovar')">
      <CheckCheck :size="16" class="mr-1.5" />
      <!-- Aditivo (remodelação item 20): não gera OS, soma na que já existe. -->
      {{ detalhe.aditivo_de ? 'Aprovar e somar na OS' : 'Aprovar e gerar OS' }}
    </BaseButton>
    <!-- Enviar fica sempre visível no rascunho: o modal explica o que falta (D36). -->
    <BaseButton v-if="acoes?.enviar" variant="ghost" size="md" class="w-full" data-testid="acao-enviar" @click="emit('enviar')">
      <Send :size="16" class="mr-1.5" /> Enviar ao cliente
    </BaseButton>
    <div class="grid grid-cols-2 gap-2">
      <!-- Spec 07: a proposta em qualquer status (com a faixa do status, D6) -->
      <BaseButton variant="secondary" size="sm" :is-loading="imprimindo" data-testid="imprimir-proposta" @click="emit('proposta')">
        <Printer :size="14" class="mr-1" /> Proposta PDF
      </BaseButton>
      <BaseButton variant="secondary" size="sm" data-testid="visao-cliente" @click="emit('alternarVisaoCliente')">
        <Eye :size="14" class="mr-1" /> {{ visaoCliente ? 'Voltar' : 'Visão do cliente' }}
      </BaseButton>
    </div>
  </div>
</template>
