<script setup lang="ts">
/**
 * @component LojaStep
 * @description Formulário de registro da loja + endereço (Passo 1).
 */

import { computed } from 'vue';

import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import { ArrowLeft, ArrowRight, Loader2, MapPin, Upload, X } from 'lucide-vue-next';

import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import SegmentSelect from '../ui/SegmentSelect.vue';
import SegmentIcons from '../icons/SegmentIcons.vue';

import { useLojaForm } from '../../composables/useLojaForm';
import { useSignIn } from '../../composables/useSignIn';
import { BUSINESS_SEGMENTS, getSegmentById, getSegmentTip } from '../../constants/segments';
import { ESTADOS_BRASILEIROS } from '@/shared/constants/locations.constants';

const {
  nomeLoja,
  segmento,
  celular,
  emailLoja,
  telefone,
  cep,
  logradouro,
  numero,
  complemento,
  bairro,
  cidade,
  estado,
  errors,
  cepIsLoading,
  onSubmit,
  submitCount,
} = useLojaForm();

const { previousStep, logoPreview, setLogoFile } = useSignIn();

const selectedSegment = computed(() => {
  const id = segmento.value;
  return id ? getSegmentById(id) : null;
});

const segmentTip = computed(() => {
  const id = segmento.value;
  return id ? getSegmentTip(id) : '';
});

function handleLogoUpload(event: Event): void {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (file) {
    setLogoFile(file);
  }
}

function removeLogo(): void {
  setLogoFile(null);
}
</script>

<template>
  <form @submit.prevent="onSubmit">
    <!-- Dica do segmento selecionado -->
    <div
      v-if="selectedSegment"
      class="p-3 mb-4 bg-blue-50 border border-blue-100 rounded-lg flex items-center gap-2"
    >
      <SegmentIcons :icon="selectedSegment.icon" :size="20" class="text-brand-primary mx-2 shrink-0" />
      <p class="text-xs text-brand-primary">{{ segmentTip }}</p>
    </div>

    <!-- Dados da Loja -->
    <h3 class="text-sm font-semibold text-brand-action mb-4">Dados da Loja</h3>

    <div class="grid grid-cols-2 gap-4 mb-6">
      <BaseInput
        v-model="nomeLoja"
        label="Nome da Loja"
        placeholder="Nome do seu negócio"
        required
        :error="submitCount > 0 ? errors.nomeLoja : ''"
      />
      <SegmentSelect
        v-model="segmento"
        label="Segmento"
        :options="BUSINESS_SEGMENTS"
        required
        :error="submitCount > 0 ? errors.segmento : ''"
      />
      <BaseInput
        v-model="celular"
        label="Celular"
        placeholder="(00) 0.0000-0000"
        mask="(##) #.####-####"
        required
        :error="submitCount > 0 ? errors.celular : ''"
      />
      <BaseInput
        v-model="emailLoja"
        type="email"
        label="E-mail da Loja"
        placeholder="contato@loja.com"
        required
        :error="submitCount > 0 ? errors.emailLoja : ''"
      />
      <BaseInput
        v-model="telefone"
        label="Telefone (opcional)"
        placeholder="(00) 0000-0000"
        mask="(##) ####-####"
        :error="submitCount > 0 ? errors.telefone : ''"
      />

      <!-- Logo Upload -->
      <div>
        <label class="block text-xs font-medium text-gray-700 mb-1.5">Logo (opcional)</label>
        <div v-if="!logoPreview" class="relative">
          <label
            class="flex items-center justify-center gap-2 px-3 py-2 border border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-brand-primary hover:bg-blue-50/50 transition-colors text-sm text-gray-500"
          >
            <LucideIcon :icon="Upload" size="sm" />
            <span>Selecionar imagem</span>
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp"
              class="hidden"
              @change="handleLogoUpload"
            />
          </label>
        </div>
        <div v-else class="flex items-center gap-3">
          <img
            :src="logoPreview"
            alt="Preview da logo"
            class="w-10 h-10 rounded-lg object-cover border border-gray-200"
          />
          <button
            type="button"
            class="text-red-500 hover:text-red-700 transition-colors"
            @click="removeLogo"
          >
            <LucideIcon :icon="X" size="md" />
          </button>
        </div>
      </div>
    </div>

    <!-- Endereço -->
    <h3 class="text-sm font-semibold text-brand-action mb-4 flex items-center gap-2">
      Endereço
    </h3>

    <div class="p-3 mb-4 bg-blue-50 border border-blue-100 rounded-lg">
      <p class="text-xs text-brand-primary">
        Digite o CEP e os campos serão preenchidos automaticamente.
      </p>
    </div>

    <div class="grid grid-cols-12 gap-4 mb-6">
      <div class="col-span-4">
        <BaseInput
          v-model="cep"
          label="CEP"
          placeholder="#####-###"
          mask="#####-###"
          required
          :error="submitCount > 0 ? errors.cep : ''"
        >
          <template v-if="cepIsLoading" #suffix>
            <LucideIcon :icon="Loader2" size="md" class="animate-spin text-brand-primary" />
          </template>
        </BaseInput>
      </div>
      <div class="col-span-6">
        <BaseInput
          v-model="logradouro"
          label="Logradouro"
          placeholder="Rua, Avenida..."
          required
          :error="submitCount > 0 ? errors.logradouro : ''"
        />
      </div>
      <div class="col-span-2">
        <BaseInput
          v-model="numero"
          label="Número"
          placeholder="Nº"
          :error="submitCount > 0 ? errors.numero : ''"
        />
      </div>
      <div class="col-span-4">
        <BaseInput
          v-model="complemento"
          label="Complemento"
          placeholder="Apto, Sala..."
          :error="submitCount > 0 ? errors.complemento : ''"
        />
      </div>
      <div class="col-span-4">
        <BaseInput
          v-model="bairro"
          label="Bairro"
          placeholder="Bairro"
          required
          :error="submitCount > 0 ? errors.bairro : ''"
        />
      </div>
      <div class="col-span-4">
        <BaseInput
          v-model="cidade"
          label="Cidade"
          placeholder="Cidade"
          required
          :error="submitCount > 0 ? errors.cidade : ''"
        />
      </div>
      <div class="col-span-4">
        <BaseSelect
          v-model="estado"
          label="Estado"
          placeholder="UF"
          :options="ESTADOS_BRASILEIROS"
          required
          :error="submitCount > 0 ? errors.estado : ''"
        />
      </div>
    </div>

    <!-- Botões -->
    <div class="flex gap-4 mt-6">
      <BaseButton
        type="button"
        variant="secondary"
        size="lg"
        class="flex-1"
        @click="previousStep"
      >
        <LucideIcon :icon="ArrowLeft" />
        Voltar
      </BaseButton>
      <BaseButton type="submit" size="lg" class="flex-1">
        Próximo
        <LucideIcon :icon="ArrowRight" />
      </BaseButton>
    </div>
  </form>
</template>
