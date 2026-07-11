<script setup lang="ts">
import { computed } from 'vue';
import { Smartphone, Car } from 'lucide-vue-next';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import type { SelectOption } from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import type { ObjetoHistorico } from '@/modules/customers/types/clientes.types';
import { OS_EQUIP_TYPE_OPTIONS } from '../../constants/ordemServico.constants';
import { useSegmento } from '@/shared/composables/useSegmento';
import { useObjetoLabels } from '../../composables/useObjetoLabels';

interface ObjetoForm {
  objeto: string;
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
  modelValue: ObjetoForm;
  objetosHistorico?: ObjetoHistorico[];
  selectedHistorico?: string;
  isLocked?: boolean;
  isCreateMode?: boolean;
  errors?: Record<string, string | undefined>;
}

const props = withDefaults(defineProps<Props>(), {
  objetosHistorico: () => [],
  selectedHistorico: '',
  isLocked: false,
  errors: () => ({}),
});

// Segmento define rótulos e quais campos aparecem. O usuário nunca vê "objeto":
// oficina → "Veículo/Placa" (sem IMEI/senha); informática → "Equipamento/Nº Série".
const { isOficinaMecanica } = useSegmento();
const { labelSingular, labelIdentificador } = useObjetoLabels();

function fieldError(field: string): string | undefined {
  return props.errors?.[`objeto.${field}`] ?? props.errors?.[field];
}

const emit = defineEmits<{
  'update:modelValue': [value: ObjetoForm];
  'update:selectedHistorico': [value: string];
  applyHistorico: [];
}>();

const historicoOptions = computed<SelectOption[]>(() => [
  { value: '', label: 'Usar anterior...' },
  ...props.objetosHistorico.map((objeto, idx) => ({
    value: String(idx),
    label: `${objeto.objeto}${objeto.numero_serie ? ` (S/N: ${objeto.numero_serie})` : ''}`,
  })),
]);

const tipoEquipamentoOptions: SelectOption[] = [
  { value: '', label: '-- Selecione --' },
  ...OS_EQUIP_TYPE_OPTIONS.map(o => ({ value: o.value, label: o.label })),
];

function updateField<K extends keyof ObjetoForm>(field: K, value: ObjetoForm[K]) {
  emit('update:modelValue', { ...props.modelValue, [field]: value });
}

function handleHistoricoSelectChange(value: string) {
  emit('update:selectedHistorico', value);
  if (value) {
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
            <component :is="isOficinaMecanica ? Car : Smartphone" :size="14" />
            Dados do {{ labelSingular }}
          </div>
          <div v-if="objetosHistorico.length > 0 && !isLocked && isCreateMode" class="flex items-center gap-2">
            <BaseSelect
              :model-value="selectedHistorico"
              :options="historicoOptions"
              class="max-w-37.5"
              @update:model-value="handleHistoricoSelectChange($event as string)"
            />
          </div>
        </h5>

        <!-- Tipo de equipamento: apenas segmentos de TI (oficina não usa) -->
        <BaseSelect
          v-if="!isOficinaMecanica"
          :model-value="modelValue.objeto || ''"
          label="Tipo de Equipamento"
          :options="tipoEquipamentoOptions"
          required
          :error="fieldError('tipo_equipamento')"
          @update:model-value="updateField('objeto', $event as string)"
        />

        <div class="grid grid-cols-2 gap-3">
          <BaseInput :model-value="modelValue.marca" label="Marca" placeholder="Marca" required :error="fieldError('marca')" @update:model-value="updateField('marca', $event)" />
          <BaseInput :model-value="modelValue.modelo" label="Modelo" placeholder="Modelo" required :error="fieldError('modelo')" @update:model-value="updateField('modelo', $event)" />
        </div>

        <BaseInput
          :model-value="modelValue.numero_serie"
          :label="labelIdentificador"
          :placeholder="isOficinaMecanica ? 'ABC1D23' : 'Número de série'"
          required
          :error="fieldError('numero_serie')"
          @update:model-value="updateField('numero_serie', $event)"
        />
      </div>

      <div class="space-y-4">
        <h5 class="flex items-center gap-2 text-xs font-bold text-slate-500 uppercase border-b border-slate-100 pb-2">
          {{ isOficinaMecanica ? 'Detalhes' : 'Detalhes & Segurança' }}
        </h5>

        <div class="grid grid-cols-2 gap-3">
          <!-- IMEI: apenas segmentos de TI -->
          <BaseInput v-if="!isOficinaMecanica" :model-value="modelValue.imei" label="IMEI" placeholder="IMEI (opcional)" :error="fieldError('imei')" @update:model-value="updateField('imei', $event)" />
          <BaseInput :model-value="modelValue.cor" label="Cor" placeholder="Ex: Preto" @update:model-value="updateField('cor', $event)" />
        </div>

        <!-- Senha e acessórios: apenas segmentos de TI -->
        <template v-if="!isOficinaMecanica">
          <BaseInput :model-value="modelValue.senha_aparelho" label="Senha / Padrão" placeholder="Senha de desbloqueio" @update:model-value="updateField('senha_aparelho', $event)" />
          <BaseInput :model-value="modelValue.acessorios" label="Acessórios (Deixados)" placeholder="Ex: Carregador, Capa..." @update:model-value="updateField('acessorios', $event)" />
        </template>
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
          :error="fieldError('defeito_relatado')"
          @update:model-value="updateField('defeito_relatado', $event as string)"
        />
      </div>

      <!-- Condições físicas de entrada: apenas segmentos de TI (oficina usa a vistoria) -->
      <div v-if="!isOficinaMecanica">
        <label class="block text-xs font-bold text-slate-600 mb-1 uppercase">
          Condições Físicas (Entrada)
        </label>
        <BaseInput
          :model-value="modelValue.condicoes_aparelho"
          placeholder="Riscos, trincas ou danos prévios..."
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
