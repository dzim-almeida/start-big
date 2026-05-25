<script setup lang="ts">
/**
 * @component IdentificationSection
 * @description Seção de identificação da empresa (logo, razão social, CNPJ, etc.)
 * Refatorado para usar inject pattern
 */

import { ref, computed } from 'vue';
import { Building2, Upload, Image as ImageIcon } from 'lucide-vue-next';
import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import { SECTION_LABELS } from '../../constants/empresa.constants';
import { useEmpresaForm } from '../../composables/useEmpresaFormProvider';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// =============================================
// Props
// =============================================

interface Props {
  disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
});

// =============================================
// Inject Context
// =============================================

const {
  razao_social,
  nome_fantasia,
  documento,
  cnae_principal,
  url_logo,
  handleLogoUpload,
  isUploadingLogo,
  errors,
  submitCount,
} = useEmpresaForm();

// =============================================
// Refs
// =============================================

const logoInput = ref<HTMLInputElement | null>(null);

// =============================================
// Computed
// =============================================

const logoUrl = computed(() => {
  const path = url_logo.value;
  if (!path) return '';
  if (path.startsWith('http')) return path;
  const cleanPath = path.replace(/^static\//, '');
  return `http://localhost:8000/static/${cleanPath}`;
});

// =============================================
// Methods
// =============================================

function triggerLogoUpload() {
  logoInput.value?.click();
}

function onLogoFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files[0]) {
    const file = input.files[0];
    handleLogoUpload(file);
    input.value = '';
  }
}
</script>

<template>
  <section class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
    <div class="flex items-center gap-3 mb-6">
      <div
        class="w-10 h-10 bg-brand-primary-light rounded-xl flex items-center justify-center text-brand-primary"
      >
        <LucideIcon :icon="Building2"/>
      </div>
      <h3 class="text-lg font-semibold text-zinc-800">{{ SECTION_LABELS.identificacao }}</h3>
    </div>
    <!-- Header -->

    <div class="space-y-6">
      <!-- Logo Upload -->
      <div
        class="flex items-center gap-6 p-4 bg-gray-50 rounded-lg border border-gray-100 mb-6"
      >
        <div class="relative shrink-0">
          <div
            class="w-24 h-24 rounded-lg bg-white border border-gray-200 flex items-center justify-center overflow-hidden shadow-sm group"
          >
            <img
              v-if="logoUrl"
              :src="logoUrl"
              alt="Logo Empresa"
              class="w-full h-full object-contain p-1"
            />
            <div v-else class="text-gray-300">
              <ImageIcon :size="32" stroke-width="1.5" />
            </div>
            <div
              class="absolute rounded-lg inset-0 bg-black/40 hidden group-hover:flex items-center justify-center transition-all cursor-pointer"
              @click="triggerLogoUpload"
            >
              <Upload :size="20" class="text-white" />
            </div>
          </div>
        </div>
        <div class="flex-1">
          <h4 class="font-medium text-gray-800 text-sm mb-1">Logomarca</h4>
          <p class="text-xs text-gray-500 mb-3">
            Exibida em orçamentos, pedidos e no cabeçalho do sistema. Recomendado:
            200x200px (PNG ou JPG).
          </p>
          <div class="flex items-center gap-3">
            <input
              ref="logoInput"
              type="file"
              accept="image/png, image/jpeg, image/jpg"
              class="hidden"
              :disabled="isUploadingLogo || disabled"
              @change="onLogoFileChange"
            />
            <label
              class="px-4 py-2 bg-white border border-gray-300 rounded-lg text-xs font-bold text-gray-700 hover:bg-gray-50 cursor-pointer shadow-sm transition-all flex items-center gap-2"
              @click="triggerLogoUpload"
            >
              <span v-if="isUploadingLogo" class="loading loading-spinner loading-xs"></span>
              <Upload v-else :size="14" />
              {{ isUploadingLogo ? 'Enviando...' : 'Alterar Logo' }}
            </label>
          </div>
        </div>
      </div>

      <!-- Razão Social / Nome Fantasia -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <BaseInput
          v-model="razao_social"
          label="Razão Social"
          type="text"
          required
          :disabled="disabled"
          :error="submitCount > 0 ? errors.razao_social : ''"
        />
        <BaseInput
          v-model="nome_fantasia"
          label="Nome Fantasia"
          type="text"
          :disabled="disabled"
          :error="submitCount > 0 ? errors.nome_fantasia : ''"
        />
      </div>

      <!-- CNPJ / CNAE -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <BaseInput
          v-model="documento"
          label="CNPJ"
          mask="##.###.###/####-##"
          placeholder="00.000.000/0000-00"
          :required="true"
          :disabled="disabled"
          :error="submitCount > 0 ? errors.documento : ''"
        />
        <BaseInput
          v-model="cnae_principal"
          label="CNAE Principal"
          type="text"
          :disabled="disabled"
          :error="submitCount > 0 ? errors.cnae_principal : ''"
        />
      </div>
    </div>
  </section>
</template>
