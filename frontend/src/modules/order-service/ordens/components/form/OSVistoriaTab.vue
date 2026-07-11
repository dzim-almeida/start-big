<script setup lang="ts">
import { computed } from 'vue';
import { ClipboardCheck, Check } from 'lucide-vue-next';

import { useOSFieldDefinition } from '../../composables/request/useOSFieldDefinition.queries';

interface Props {
  /** dados_adicionais da OS (guarda acessorios + vistoria). */
  osDados?: Record<string, unknown>;
  isLocked?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  osDados: () => ({}),
  isLocked: false,
});

const emit = defineEmits<{
  'update:osDados': [value: Record<string, unknown>];
}>();

// A vistoria é dirigida pelo contrato do backend (/definicao-campos): acessórios
// e grupos de inspeção vêm de lá, então novos segmentos/checklists não mexem aqui.
const { data } = useOSFieldDefinition();
const definicao = computed(() => data.value?.definicao ?? null);
const acessorios = computed<string[]>(() => definicao.value?.acessorios ?? []);
const grupos = computed(() => definicao.value?.vistoria ?? []);

const ESTADOS: { value: string; label: string; selected: string }[] = [
  { value: 'OK', label: 'OK', selected: 'bg-emerald-500 text-white border-emerald-500' },
  { value: 'N_OK', label: 'N/OK', selected: 'bg-amber-500 text-white border-amber-500' },
  { value: 'REPARAR', label: 'Reparar', selected: 'bg-red-500 text-white border-red-500' },
];

const acessoriosSel = computed<Record<string, boolean>>(
  () => (props.osDados.acessorios as Record<string, boolean>) ?? {},
);
const vistoriaSel = computed<Record<string, string>>(
  () => (props.osDados.vistoria as Record<string, string>) ?? {},
);

/** Converte o slug do backend (ex: chave_de_roda) em rótulo (Chave de roda). */
function rotulo(slug: string): string {
  const s = slug.replace(/_/g, ' ');
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/** Chave estável do item na vistoria (evita colisão de "percepcoes_de_uso" entre grupos). */
function chaveItem(grupoIdx: number, item: string): string {
  return `${grupoIdx}_${item}`;
}

function toggleAcessorio(key: string) {
  if (props.isLocked) return;
  const acessoriosNovos = { ...acessoriosSel.value, [key]: !acessoriosSel.value[key] };
  emit('update:osDados', { ...props.osDados, acessorios: acessoriosNovos });
}

function setVistoria(grupoIdx: number, item: string, estado: string) {
  if (props.isLocked) return;
  const key = chaveItem(grupoIdx, item);
  const atual = vistoriaSel.value[key];
  // Clicar no estado já selecionado limpa (toggle).
  const vistoriaNova = { ...vistoriaSel.value, [key]: atual === estado ? '' : estado };
  emit('update:osDados', { ...props.osDados, vistoria: vistoriaNova });
}
</script>

<template>
  <div class="space-y-5 animate-fadeIn">
    <div class="flex items-center gap-3 border-b border-slate-200 pb-3">
      <div class="bg-brand-primary-light p-2 rounded-lg text-brand-primary">
        <ClipboardCheck :size="20" />
      </div>
      <div>
        <h5 class="text-sm font-bold text-slate-700">Vistoria de Entrada</h5>
        <p class="text-xs text-slate-500">Acessórios e checklist de inspeção do veículo</p>
      </div>
    </div>

    <div
      v-if="!definicao"
      class="flex flex-col items-center justify-center py-12 text-slate-400 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50/50"
    >
      <div class="w-14 h-14 bg-slate-100 rounded-full flex items-center justify-center mb-3">
        <ClipboardCheck :size="28" stroke-width="1.5" class="text-slate-300" />
      </div>
      <p class="text-sm font-semibold text-slate-500">Vistoria não disponível</p>
      <p class="text-xs text-slate-400 mt-1">Este segmento não possui checklist de vistoria.</p>
    </div>

    <fieldset v-else :disabled="isLocked" class="contents">
      <!-- Acessórios presentes -->
      <div v-if="acessorios.length" class="space-y-3">
        <h6 class="text-xs font-bold text-slate-500 uppercase">Acessórios presentes</h6>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
          <button
            v-for="ac in acessorios"
            :key="ac"
            type="button"
            class="flex items-center gap-2 p-2.5 rounded-lg border text-sm text-left transition-colors"
            :class="acessoriosSel[ac]
              ? 'bg-brand-primary-light border-brand-primary/30 text-brand-primary font-semibold'
              : 'bg-white border-slate-200 text-slate-600 hover:border-brand-primary/20'"
            @click="toggleAcessorio(ac)"
          >
            <span
              class="w-4 h-4 rounded flex items-center justify-center shrink-0 border"
              :class="acessoriosSel[ac] ? 'bg-brand-primary border-brand-primary text-white' : 'border-slate-300'"
            >
              <Check v-if="acessoriosSel[ac]" :size="12" />
            </span>
            {{ rotulo(ac) }}
          </button>
        </div>
      </div>

      <!-- Grupos de inspeção (OK / N-OK / Reparar) -->
      <div v-for="(grupo, gi) in grupos" :key="grupo.titulo" class="space-y-2">
        <h6 class="text-xs font-bold text-slate-500 uppercase">{{ grupo.titulo }}</h6>
        <div class="space-y-2">
          <div
            v-for="item in grupo.itens"
            :key="item"
            class="flex items-center justify-between gap-3 p-3 bg-white border border-slate-200 rounded-lg"
          >
            <p class="text-sm text-slate-700 truncate">{{ rotulo(item) }}</p>
            <div class="flex items-center gap-1 shrink-0">
              <button
                v-for="estado in ESTADOS"
                :key="estado.value"
                type="button"
                class="px-2.5 py-1 text-xs font-bold rounded-md border transition-colors"
                :class="vistoriaSel[chaveItem(gi, item)] === estado.value
                  ? estado.selected
                  : 'bg-slate-50 border-slate-200 text-slate-400 hover:text-slate-600'"
                @click="setVistoria(gi, item, estado.value)"
              >
                {{ estado.label }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </fieldset>
  </div>
</template>

<style scoped>
.animate-fadeIn {
  animation: fadeIn 0.3s ease-in-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
