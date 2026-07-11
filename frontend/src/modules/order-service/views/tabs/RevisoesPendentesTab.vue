<script setup lang="ts">
import { ref } from 'vue';
import { CalendarClock, Gauge, Car, Loader2, ChevronRight } from 'lucide-vue-next';

import { useRevisoesPendentes } from '../../ordens/composables/request/useRevisao.queries';
import type { RevisaoPendente } from '../../ordens/services/revisao.service';
import OSKmHistoryModal from '../../ordens/components/OSKmHistoryModal.vue';

const { data: revisoes, isLoading } = useRevisoesPendentes(ref(true));

// Modal de histórico de KM do veículo selecionado.
const isKmModalOpen = ref(false);
const selectedObjetoId = ref<number | null>(null);
const selectedLabel = ref('');

function abrirHistorico(r: RevisaoPendente) {
  selectedObjetoId.value = r.objeto_id;
  selectedLabel.value = `${r.marca} ${r.modelo} (${r.numero_serie})`;
  isKmModalOpen.value = true;
}

function formatarData(d: string | null): string {
  return d ? new Date(d).toLocaleDateString('pt-BR') : '—';
}

function formatarKm(km: number | null): string {
  return km != null ? `${km.toLocaleString('pt-BR')} km` : '—';
}
</script>

<template>
  <div class="space-y-4 animate-fadeIn">
    <div class="flex items-center gap-3 border-b border-slate-200 pb-3">
      <div class="bg-brand-primary-light p-2 rounded-lg text-brand-primary">
        <CalendarClock :size="20" />
      </div>
      <div>
        <h5 class="text-sm font-bold text-slate-700">Revisões Pendentes</h5>
        <p class="text-xs text-slate-500">Veículos com revisão vencida por data e/ou quilometragem</p>
      </div>
    </div>

    <div v-if="isLoading" class="flex items-center justify-center py-16 text-slate-400">
      <Loader2 :size="22" class="animate-spin" />
    </div>

    <div
      v-else-if="!revisoes || revisoes.length === 0"
      class="flex flex-col items-center justify-center py-16 text-slate-400 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50/50"
    >
      <div class="w-14 h-14 bg-slate-100 rounded-full flex items-center justify-center mb-3">
        <CalendarClock :size="28" stroke-width="1.5" class="text-slate-300" />
      </div>
      <p class="text-sm font-semibold text-slate-500">Nenhuma revisão pendente</p>
      <p class="text-xs text-slate-400 mt-1">Os veículos com revisão agendada aparecerão aqui quando vencerem.</p>
    </div>

    <div v-else class="space-y-2">
      <button
        v-for="r in revisoes"
        :key="r.objeto_id"
        type="button"
        class="w-full flex items-center justify-between gap-3 p-3 bg-white border border-slate-200 rounded-lg hover:border-brand-primary/20 transition-colors text-left group"
        @click="abrirHistorico(r)"
      >
        <div class="flex items-center gap-3 overflow-hidden">
          <div class="w-10 h-10 rounded-lg flex items-center justify-center shrink-0 bg-brand-primary-light text-brand-primary">
            <Car :size="18" />
          </div>
          <div class="min-w-0">
            <p class="text-sm font-bold text-slate-700 truncate">
              {{ r.marca }} {{ r.modelo }}
              <span class="text-slate-400 font-medium">· {{ r.numero_serie }}</span>
            </p>
            <div class="flex items-center gap-2 mt-0.5">
              <span
                class="text-[10px] font-bold px-1.5 py-0.5 rounded-full shrink-0"
                :class="r.motivo === 'km' ? 'bg-amber-50 text-amber-600' : 'bg-red-50 text-red-600'"
              >
                {{ r.motivo === 'km' ? 'Venceu por KM' : 'Venceu por data' }}
              </span>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-6 shrink-0">
          <div class="text-right hidden sm:block">
            <p class="text-[11px] text-slate-400 font-medium uppercase flex items-center gap-1 justify-end">
              <CalendarClock :size="11" /> Data
            </p>
            <p class="text-sm font-bold text-slate-600">{{ formatarData(r.proxima_revisao_data) }}</p>
          </div>
          <div class="text-right hidden sm:block">
            <p class="text-[11px] text-slate-400 font-medium uppercase flex items-center gap-1 justify-end">
              <Gauge :size="11" /> Alvo / Atual
            </p>
            <p class="text-sm font-bold text-slate-600">{{ formatarKm(r.proxima_revisao_km) }} / {{ formatarKm(r.km_atual) }}</p>
          </div>
          <ChevronRight :size="18" class="text-slate-300 group-hover:text-brand-primary transition-colors" />
        </div>
      </button>
    </div>

    <OSKmHistoryModal
      :is-open="isKmModalOpen"
      :objeto-id="selectedObjetoId"
      :veiculo-label="selectedLabel"
      @close="isKmModalOpen = false"
    />
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
