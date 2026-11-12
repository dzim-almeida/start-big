<script setup lang="ts">
/**
 * @component SeletorLavadores
 * @description Escolha de 1 ou 2 lavadores em botões (comanda e pátio, Spec 10B).
 *
 * Botões e não lista suspensa (SPEC-00 U2): no balcão, um toque. O primeiro
 * escolhido é o responsável da OS quando a comanda a abre.
 */
import { computed } from 'vue';

import { useOsEmployeesGet } from '@/modules/order-service/ordens/composables/request/relationship/useOSRelationshipGet.queries';

/** "1 ou 2 por carro" (cliente); o backend aceita até 5. */
const MAXIMO = 2;

const ids = defineModel<number[]>({ default: () => [] });
const { data, isLoading } = useOsEmployeesGet();

const funcionarios = computed(() => {
  const lista = Array.isArray(data.value) ? (data.value as { id: number; nome: string }[]) : [];
  return [...lista].sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'));
});

function alternar(id: number) {
  if (ids.value.includes(id)) {
    ids.value = ids.value.filter((x) => x !== id);
  } else if (ids.value.length < MAXIMO) {
    ids.value = [...ids.value, id];
  } else {
    ids.value = [...ids.value.slice(1), id];            // troca o mais antigo
  }
}
</script>

<template>
  <div>
    <p v-if="isLoading" class="text-sm text-zinc-500">Carregando equipe…</p>
    <p v-else-if="!funcionarios.length" class="text-sm text-zinc-500">
      Nenhum funcionário cadastrado. Cadastre em Gestão de Equipe.
    </p>
    <div v-else class="flex flex-wrap gap-2">
      <button
        v-for="f in funcionarios"
        :key="f.id"
        type="button"
        class="rounded-full border px-3 py-1.5 text-sm font-medium transition-colors"
        :class="ids.includes(f.id)
          ? 'border-brand-primary bg-brand-primary text-white'
          : 'border-zinc-200 bg-white text-zinc-700 hover:border-brand-primary hover:text-brand-primary'"
        :aria-pressed="ids.includes(f.id)"
        @click="alternar(f.id)"
      >
        {{ f.nome }}
        <span v-if="ids.indexOf(f.id) === 0 && ids.length > 1" class="ml-1 text-[10px] opacity-80">1º</span>
      </button>
    </div>
    <p class="mt-2 text-xs text-zinc-400">Até {{ MAXIMO }} lavadores. Toque de novo para tirar.</p>
  </div>
</template>
