<script setup lang="ts">
import { Wrench } from 'lucide-vue-next';
import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import MoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import { useServicoForm } from '../../composables/useServicoForm';

interface Props {
  submitCount: number;
  disabled?: boolean;
}

defineProps<Props>();

const { descricao, valor, duracao_minutos, temDuracao, errors } = useServicoForm();
</script>

<template>
  <section>
    <!-- Section Header -->
    <div class="flex items-center gap-3 mb-6">
      <div
        class="w-10 h-10 bg-brand-primary-light rounded-xl flex items-center justify-center text-brand-primary"
      >
        <LucideIcon :icon="Wrench" />
      </div>
      <h3 class="text-lg font-semibold text-zinc-800">Dados do Serviço</h3>
    </div>

    <div class="grid grid-cols-12 gap-4">
      <div class="col-span-12" :class="temDuracao ? 'md:col-span-6' : 'md:col-span-8'">
        <BaseInput
          v-model="descricao"
          label="Descrição do serviço"
          placeholder="Ex: Troca de display"
          :error="submitCount > 0 ? errors.descricao : undefined"
          :disabled="disabled"
          required
        />
      </div>

      <div class="col-span-12" :class="temDuracao ? 'md:col-span-3' : 'md:col-span-4'">
        <MoneyInput
          v-model="valor"
          label="Valor base"
          :error="submitCount > 0 ? errors.valor : undefined"
          :disabled="disabled"
          required
        />
      </div>

      <!-- Lava-rápido: dá o "Pronto às…" do pátio e a duração do agendamento -->
      <div v-if="temDuracao" class="col-span-12 md:col-span-3">
        <BaseInput
          v-model="duracao_minutos"
          label="Duração (min)"
          placeholder="Ex: 40"
          inputmode="numeric"
          :error="submitCount > 0 ? errors.duracao_minutos : undefined"
          :disabled="disabled"
          data-testid="servico-duracao"
        />
      </div>
    </div>
  </section>
</template>
