<script setup lang="ts">
import type { Component } from 'vue';

/**
 * Card de seção: o bloco branco com cabeçalho (ícone + título + ações) que
 * organiza telas de formulário e de detalhe. Rodapé opcional em cinza, para
 * subtotais e avisos.
 *
 * `semPadding` deixa o corpo encostar nas bordas — para tabela dentro do card.
 */
withDefaults(
  defineProps<{
    titulo?: string;
    descricao?: string;
    icone?: Component;
    semPadding?: boolean;
  }>(),
  { semPadding: false },
);
</script>

<template>
  <section class="overflow-hidden rounded-2xl border border-zinc-200 bg-white">
    <header
      v-if="titulo || $slots.cabecalho || $slots.acoes"
      class="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-100 px-6 py-4"
    >
      <slot name="cabecalho">
        <div class="flex min-w-0 items-center gap-3">
          <span
            v-if="icone"
            class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-primary-light text-brand-primary"
          >
            <component :is="icone" :size="16" />
          </span>
          <div class="min-w-0">
            <h2 class="text-base font-semibold text-zinc-900">{{ titulo }}</h2>
            <p v-if="descricao" class="text-xs text-zinc-500">{{ descricao }}</p>
          </div>
        </div>
      </slot>
      <div v-if="$slots.acoes" class="flex flex-wrap items-center gap-2">
        <slot name="acoes" />
      </div>
    </header>

    <div :class="semPadding ? '' : 'px-6 py-5'">
      <slot />
    </div>

    <footer v-if="$slots.rodape" class="border-t border-zinc-100 bg-zinc-50 px-6 py-4">
      <slot name="rodape" />
    </footer>
  </section>
</template>
