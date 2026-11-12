<script setup lang="ts">
/**
 * @component SeletorDivisaoComissao
 * @description "Quando a lavagem tiver mais de um lavador" — Dividir ou
 * Inteira (lava-rápido, SPEC-00 O7c e Spec 10B).
 *
 * Usado no cargo (sem "Herdar": vazio vale Dividir) e no funcionário (com
 * "Herdar do cargo", a cascata de sempre). Quem decide é o dono.
 */
import { computed } from 'vue';

type Divisao = 'dividir' | 'inteira';

const props = defineProps<{
  /** No funcionário: mostra "Herdar do cargo" (null). */
  permitirHerdar?: boolean;
  disabled?: boolean;
}>();

const modelo = defineModel<Divisao | null | undefined>();

const opcoes = computed(() => [
  ...(props.permitirHerdar
    ? [{ id: null, titulo: 'Herdar do cargo', ajuda: 'Usa a regra do cargo' }]
    : []),
  { id: 'dividir' as const, titulo: 'Dividir', ajuda: 'Cada um recebe sobre a sua parte (R$ 100 ÷ 2)' },
  { id: 'inteira' as const, titulo: 'Inteira', ajuda: 'Cada um recebe sobre o valor todo' },
]);

/** Sem "Herdar", vazio é Dividir (o padrão do backend). */
const atual = computed<Divisao | null>(() => modelo.value ?? (props.permitirHerdar ? null : 'dividir'));
</script>

<template>
  <div>
    <label class="mb-1.5 block text-xs font-medium text-zinc-600">Quando a lavagem tiver mais de um lavador</label>
    <div class="grid gap-2" :class="permitirHerdar ? 'grid-cols-3' : 'grid-cols-2'">
      <button
        v-for="o in opcoes"
        :key="String(o.id)"
        type="button"
        :disabled="disabled"
        class="rounded-xl border px-3 py-2.5 text-left transition disabled:opacity-60"
        :class="atual === o.id
          ? 'border-brand-primary bg-brand-primary-light ring-1 ring-brand-primary'
          : 'border-zinc-200 bg-white hover:border-zinc-300'"
        @click="modelo = o.id"
      >
        <span class="block text-xs font-semibold text-zinc-800">{{ o.titulo }}</span>
        <span class="mt-0.5 block text-[11px] leading-tight text-zinc-500">{{ o.ajuda }}</span>
      </button>
    </div>
  </div>
</template>
