<script setup lang="ts">
import { Smartphone } from 'lucide-vue-next';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';
import type { EquipamentoHistorico } from '@/modules/customers/types/clientes.types';

interface EquipamentoForm {
  equipamento: string;
  marca: string;
  modelo: string;
  numero_serie: string;
  imei: string;
  cor: string;
  senha_aparelho: string;
  acessorios: string;
  defeito_relatado: string;
  condicoes_aparelho: string;
}

interface Props {
  modelValue: EquipamentoForm;
  equipamentosHistorico?: EquipamentoHistorico[];
  selectedHistorico?: string;
  isLocked?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  equipamentosHistorico: () => [],
  selectedHistorico: '',
  isLocked: false,
});

const emit = defineEmits<{
  'update:modelValue': [value: EquipamentoForm];
  'update:selectedHistorico': [value: string];
  applyHistorico: [];
}>();

function updateField<K extends keyof EquipamentoForm>(field: K, value: EquipamentoForm[K]) {
  emit('update:modelValue', { ...props.modelValue, [field]: value });
}

function handleHistoricoChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  emit('update:selectedHistorico', target.value);
  if (target.value) {
    emit('applyHistorico');
  }
}
</script>

<template>
  <div class="space-y-5 animate-fadeIn">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="space-y-4">
        <h5 class="flex items-center justify-between text-xs font-bold text-slate-500 uppercase border-b border-slate-100 pb-2">
          <div class="flex items-center gap-2">
            <Smartphone :size="14" />
            Dados do Aparelho
          </div>
          <div v-if="equipamentosHistorico.length > 0 && !isLocked" class="flex items-center gap-2">
            <select
              :value="selectedHistorico"
              class="text-[10px] bg-brand-primary-light text-brand-primary border border-brand-primary-light rounded px-2 py-0.5 focus:outline-none focus:ring-1 focus:ring-brand-primary/30 max-w-37.5 truncate"
              @change="handleHistoricoChange"
            >
              <option value="">Usar anterior...</option>
              <option v-for="(equip, idx) in equipamentosHistorico" :key="idx" :value="idx">
                {{ equip.equipamento }} {{ equip.numero_serie ? `(S/N: ${equip.numero_serie})` : '' }}
              </option>
            </select>
          </div>
        </h5>

        <BaseInput
          :model-value="modelValue.equipamento"
          label="Equipamento *"
          placeholder="Ex: iPhone 14, Notebook Dell..."
          required
          @update:model-value="updateField('equipamento', $event)"
        />

        <div class="grid grid-cols-2 gap-3">
          <BaseInput :model-value="modelValue.marca" label="Marca" placeholder="Marca" @update:model-value="updateField('marca', $event)" />
          <BaseInput :model-value="modelValue.modelo" label="Modelo" placeholder="Modelo" @update:model-value="updateField('modelo', $event)" />
        </div>

        <BaseInput :model-value="modelValue.numero_serie" label="N° Serie" placeholder="Serial Number" @update:model-value="updateField('numero_serie', $event)" />
      </div>

      <div class="space-y-4">
        <h5 class="flex items-center gap-2 text-xs font-bold text-slate-500 uppercase border-b border-slate-100 pb-2">
          Detalhes & Seguranca
        </h5>

        <div class="grid grid-cols-2 gap-3">
          <BaseInput :model-value="modelValue.imei" label="IMEI" placeholder="IMEI" @update:model-value="updateField('imei', $event)" />
          <BaseInput :model-value="modelValue.cor" label="Cor" placeholder="Ex: Preto" @update:model-value="updateField('cor', $event)" />
        </div>

        <BaseInput :model-value="modelValue.senha_aparelho" label="Senha / Padrao" placeholder="Senha de desbloqueio" @update:model-value="updateField('senha_aparelho', $event)" />
        <BaseInput :model-value="modelValue.acessorios" label="Acessorios (Deixados)" placeholder="Ex: Carregador, Capa..." @update:model-value="updateField('acessorios', $event)" />
      </div>
    </div>

    <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-4">
      <div>
        <BaseTextarea
          :model-value="modelValue.defeito_relatado"
          label="Defeito Relatado"
          :rows="3"
          placeholder="Descreva o problema principal relatado pelo cliente..."
          required
          @update:model-value="updateField('defeito_relatado', $event as string)"
        />
      </div>

      <div>
        <label class="block text-xs font-bold text-slate-600 mb-1 uppercase">
          Condicoes Fisicas (Entrada)
        </label>
        <BaseInput
          :model-value="modelValue.condicoes_aparelho"
          placeholder="Riscos, trincas ou danos previos..."
          @update:model-value="updateField('condicoes_aparelho', $event)"
        />
      </div>
    </div>
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
