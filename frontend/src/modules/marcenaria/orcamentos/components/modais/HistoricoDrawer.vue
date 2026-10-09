<script setup lang="ts">
/**
 * @component HistoricoDrawer
 * @description Gaveta lateral com os eventos de todas as versões (Spec 06B
 * D43; 06A D25): a frase, quem e quando ("há 2 h", com a data completa ao
 * passar o mouse).
 */
import { computed, toRef } from 'vue';
import { X } from 'lucide-vue-next';

import { formatDataHora, tempoDecorrido } from '@/shared/utils/date.utils';

import { useHistoricoQuery } from '../../composables/useOrcamentoQuery';

const props = defineProps<{ id: number | null; aberto: boolean }>();
const emit = defineEmits<{ fechar: [] }>();

// Só busca quando a gaveta abre.
const { data: eventos, isLoading, isError } = useHistoricoQuery(computed(() => props.id), toRef(props, 'aberto'));

/** "há 2 h" / "agora". */
function quando(data: string): string {
  const tempo = tempoDecorrido(data);
  return tempo === 'agora' ? 'agora' : `há ${tempo}`;
}
</script>

<template>
  <Teleport to="body">
    <div v-if="aberto" class="fixed inset-0 z-40 flex justify-end bg-black/20" @click.self="emit('fechar')" @keydown.esc="emit('fechar')">
      <aside class="flex h-full w-full max-w-md flex-col bg-white shadow-xl" role="dialog" aria-modal="true" aria-labelledby="titulo-historico">
        <header class="flex items-center justify-between border-b border-zinc-100 px-5 py-4">
          <h2 id="titulo-historico" class="text-base font-bold text-zinc-800">Histórico</h2>
          <button type="button" class="rounded-md p-1.5 text-zinc-400 hover:bg-zinc-100 cursor-pointer" aria-label="Fechar histórico" @click="emit('fechar')">
            <X :size="18" />
          </button>
        </header>

        <div class="flex-1 overflow-y-auto px-5 py-4">
          <p v-if="isLoading" class="text-sm text-zinc-400">Carregando…</p>
          <p v-else-if="isError" class="text-sm text-red-600">Não foi possível carregar o histórico.</p>
          <ol v-else class="flex flex-col gap-4">
            <li v-for="evento in eventos ?? []" :key="evento.id" class="border-l-2 border-zinc-200 pl-3">
              <p class="text-sm text-zinc-800">{{ evento.descricao }}</p>
              <p class="mt-0.5 text-[11px] text-zinc-400">
                {{ evento.usuario_nome }} ·
                <time :datetime="evento.ocorrido_em" :title="formatDataHora(evento.ocorrido_em)">{{ quando(evento.ocorrido_em) }}</time>
              </p>
            </li>
          </ol>
        </div>
      </aside>
    </div>
  </Teleport>
</template>
