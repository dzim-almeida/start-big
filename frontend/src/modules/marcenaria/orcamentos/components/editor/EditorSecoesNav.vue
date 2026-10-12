<script setup lang="ts">
/**
 * @component EditorSecoesNav
 * @description As seções do editor de orçamento no cabeçalho (redesign
 * 10/2026): um clique rola até a seção, e a seção que está na tela fica
 * marcada enquanto o usuário rola.
 *
 * As seções são os `id` que os blocos do editor já têm (`secao-cliente`…).
 * Sem IntersectionObserver (testes em jsdom), só o clique funciona.
 */
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';

export interface SecaoEditor { id: string; rotulo: string; contagem?: number }

const props = defineProps<{ secoes: SecaoEditor[] }>();

const ativa = ref(props.secoes[0]?.id ?? '');
let observador: IntersectionObserver | null = null;

function ir(id: string) {
  ativa.value = id;
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/** Observa as seções: a mais alta que cruza a faixa do topo é a ativa. */
function observar() {
  observador?.disconnect();
  if (typeof IntersectionObserver === 'undefined') return;
  observador = new IntersectionObserver(
    (entradas) => {
      const visivel = entradas
        .filter((e) => e.isIntersecting)
        .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
      if (visivel) ativa.value = visivel.target.id;
    },
    // A faixa fica logo abaixo do cabeçalho fixo; o resto da tela não conta.
    { rootMargin: '-160px 0px -55% 0px' },
  );
  for (const secao of props.secoes) {
    const el = document.getElementById(secao.id);
    if (el) observador.observe(el);
  }
}

onMounted(observar);
// As seções aparecem depois que o orçamento carrega.
watch(() => props.secoes.map((s) => s.id).join(), () => setTimeout(observar), { flush: 'post' });
onBeforeUnmount(() => observador?.disconnect());
</script>

<template>
  <nav class="flex gap-6 overflow-x-auto" aria-label="Seções do orçamento">
    <button
      v-for="secao in secoes"
      :key="secao.id"
      type="button"
      :aria-current="ativa === secao.id ? 'true' : undefined"
      :class="[
        'flex shrink-0 items-center gap-2 border-b-2 pb-2.5 pt-2 text-sm whitespace-nowrap transition-colors cursor-pointer',
        ativa === secao.id
          ? 'border-brand-primary font-semibold text-brand-primary'
          : 'border-transparent font-medium text-zinc-500 hover:text-zinc-900',
      ]"
      :data-testid="`ir-${secao.id}`"
      @click="ir(secao.id)"
    >
      {{ secao.rotulo }}
      <span
        v-if="secao.contagem"
        :class="['rounded-full px-1.5 text-xs font-semibold tabular-nums', ativa === secao.id ? 'bg-brand-primary-light text-brand-primary' : 'bg-zinc-100 text-zinc-600']"
      >
        {{ secao.contagem }}
      </span>
    </button>
  </nav>
</template>
