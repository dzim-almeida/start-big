<script setup lang="ts">
/**
 * @component SeletorLavadores
 * @description Quem vai lavar: "Lavador" e "2º lavador (opcional)", em
 * seletores do padrão da casa (comanda e pátio, Spec 10B).
 *
 * "1 ou 2 por carro" (cliente, 12/11/2026). O modelo é a lista de ids na
 * ordem: [lavador, 2º lavador]. O 2º só aparece depois do 1º.
 */
import { computed } from 'vue';

import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import type { SelectOption } from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import { useOsEmployeesGet } from '@/modules/order-service/ordens/composables/request/relationship/useOSRelationshipGet.queries';

const ids = defineModel<number[]>({ default: () => [] });
const { data, isLoading } = useOsEmployeesGet();

const funcionarios = computed(() => {
  const lista = Array.isArray(data.value) ? (data.value as { id: number; nome: string }[]) : [];
  return [...lista].sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'));
});

const NENHUM: SelectOption = { value: '', label: '— Ninguém —' };

const opcoes1 = computed<SelectOption[]>(() => [
  NENHUM,
  ...funcionarios.value.map((f) => ({ value: String(f.id), label: f.nome })),
]);
/** O 2º não repete o 1º. */
const opcoes2 = computed<SelectOption[]>(() => [
  NENHUM,
  ...funcionarios.value.filter((f) => f.id !== ids.value[0]).map((f) => ({ value: String(f.id), label: f.nome })),
]);

const primeiro = computed<string>({
  get: () => (ids.value[0] ? String(ids.value[0]) : ''),
  set: (v) => {
    const id = Number(v) || null;
    // Sem o 1º, o 2º sobe; o 2º igual ao novo 1º sai.
    const segundo = ids.value[1] && ids.value[1] !== id ? ids.value[1] : null;
    ids.value = id ? [id, ...(segundo ? [segundo] : [])] : (segundo ? [segundo] : []);
  },
});
const segundo = computed<string>({
  get: () => (ids.value[1] ? String(ids.value[1]) : ''),
  set: (v) => {
    const id = Number(v) || null;
    ids.value = ids.value[0] ? [ids.value[0], ...(id ? [id] : [])] : [];
  },
});
</script>

<template>
  <div>
    <p v-if="!isLoading && !funcionarios.length" class="text-sm text-zinc-500">
      Nenhum funcionário cadastrado. Cadastre em Gestão de Equipe.
    </p>
    <div v-else class="grid grid-cols-1 gap-3 sm:grid-cols-2">
      <BaseSelect v-model="primeiro" label="Lavador" :options="opcoes1" placeholder="Escolha" />
      <BaseSelect
        v-model="segundo"
        label="2º lavador (opcional)"
        :options="opcoes2"
        placeholder="Escolha"
        :disabled="!ids[0]"
      />
    </div>
  </div>
</template>
