<script setup lang="ts">
/**
 * @component EditarEtapasModal
 * @description As etapas de UM móvel da OS (Spec 12B D8; 12A D3, D4).
 *
 * Usa o mesmo editor de listas de Configurações › Marcenaria: incluir,
 * renomear, remover e reordenar, com as mesmas regras (1 a 20 etapas, até 60
 * caracteres, sem repetir). Etapa CONCLUÍDA não pode ser removida nem
 * renomeada (o que foi feito não some do histórico): o motivo vai no `title`.
 *
 * A identidade (`id`) de cada etapa anda com ela no editor: assim o backend
 * sabe qual foi renomeada ou movida, e as novas chegam sem `id`.
 */
import { computed, ref, watch } from 'vue';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import ListaTextosEditavel from '@/shared/components/ui/ListaTextosEditavel/ListaTextosEditavel.vue';
import { errosDosItens } from '@/shared/components/ui/ListaTextosEditavel/errosDosItens';

import type { MovelProducao } from '../schemas/producao.schema';
import { etapasEmOrdem } from '../utils/producao';

/** Os mesmos limites da configuração (12A D4 = 04A §6.4). */
const MAX_ETAPAS = 20;
const MAX_CARACTERES = 60;

const props = defineProps<{ isOpen: boolean; movel: MovelProducao | null; gravando: boolean }>();
const emit = defineEmits<{ close: []; salvar: [etapas: { id: number | null; nome: string }[]] }>();

const nomes = ref<string[]>([]);
const ids = ref<(number | null)[]>([]);

// Abriu: a lista atual do móvel, na ordem dele.
watch(() => props.isOpen, (aberto) => {
  if (!aberto || !props.movel) return;
  const atuais = etapasEmOrdem(props.movel);
  nomes.value = atuais.map((e) => e.nome);
  ids.value = atuais.map((e) => e.id);
}, { immediate: true });

/** As concluídas (pelo id: a trava anda com a etapa quando ela sobe ou desce). */
const concluidas = computed(() =>
  new Set((props.movel?.etapas ?? []).filter((e) => e.status === 'CONCLUIDA').map((e) => e.id)));
const travados = computed(() => ids.value.map((id) => id !== null && concluidas.value.has(id)));

const temErro = computed(() => errosDosItens(nomes.value, MAX_CARACTERES).some(Boolean));

function salvar() {
  if (temErro.value || props.gravando) return;
  emit('salvar', nomes.value.map((nome, i) => ({ id: ids.value[i] ?? null, nome: nome.trim() })));
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="Editar etapas" :subtitle="movel?.nome" size="md" overlay @close="emit('close')">
    <ListaTextosEditavel
      v-model="nomes"
      v-model:ids="ids"
      :travados="travados"
      motivo-travado="Etapa concluída: reabra antes de remover ou renomear."
      :max-itens="MAX_ETAPAS"
      :max-caracteres="MAX_CARACTERES"
      rotulo-item="etapa"
    />
    <p class="mt-3 text-xs text-zinc-500">Vale só para este móvel. As etapas padrão ficam em Configurações › Marcenaria.</p>
    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
        <BaseButton :disabled="temErro" :is-loading="gravando" data-testid="salvar-etapas" @click="salvar">Salvar etapas</BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
