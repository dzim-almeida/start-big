<script setup lang="ts">
/**
 * @component CertificadoSection
 * @description Seção de certificado digital do formulário de empresa
 * Refatorado para usar inject pattern
 */

import { ref, computed } from 'vue';
import { Shield, Upload, Key, CheckCircle, AlertCircle } from 'lucide-vue-next';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { SECTION_LABELS, UPLOAD_CONFIG } from '../../constants/empresa.constants';
import { useEmpresaForm } from '../../composables/useEmpresaFormProvider';
import type { FiscalSettings } from '../../types/empresa.types';

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
  fiscal_settings,
  certificado_senha,
  windowsCertificates,
  isUploadingCert,
  isLoadingCertificates,
  handleCertUpload,
  refetchWindowsCerts,
} = useEmpresaForm();

// =============================================
// Refs
// =============================================

const certInput = ref<HTMLInputElement | null>(null);

// =============================================
// Computed
// =============================================

const tipoCertificado = computed({
  get: () => fiscal_settings.value.tipo_certificado || 'ARQUIVO',
  set: (value) => updateFiscalSetting('tipo_certificado', value),
});

const isArquivo = computed(() => tipoCertificado.value === 'ARQUIVO');

const hasCertificadoPath = computed(() => Boolean(fiscal_settings.value.certificado_digital_path));

const certificadoValidade = computed(() => {
  if (!fiscal_settings.value.certificado_validade) return null;
  return new Date(fiscal_settings.value.certificado_validade).toLocaleDateString('pt-BR');
});

// =============================================
// Methods
// =============================================

function updateFiscalSetting<K extends keyof FiscalSettings>(field: K, value: FiscalSettings[K]) {
  fiscal_settings.value = { ...fiscal_settings.value, [field]: value };
}

function onCertFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files[0]) {
    const file = input.files[0];
    const extension = file.name.toLowerCase();

    // Validar extensão
    const isValid = UPLOAD_CONFIG.certificado.extensions.some(ext => extension.endsWith(ext));
    if (!isValid) {
      return;
    }

    handleCertUpload(file, certificado_senha.value);
    input.value = '';
  }
}
</script>

<template>
  <section class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
    <!-- Header -->
    <h3
      class="text-sm font-bold text-gray-900 uppercase tracking-wider mb-6 pb-2 border-b border-gray-50 flex items-center gap-2"
    >
      <Shield :size="18" class="text-gray-400" />
      {{ SECTION_LABELS.certificado }}
    </h3>

    <div class="space-y-6">
      <!-- Tipo de Certificado -->
      <div class="flex gap-6">
        <label class="flex items-center gap-2 cursor-pointer">
          <input
            v-model="tipoCertificado"
            type="radio"
            value="ARQUIVO"
            :disabled="disabled"
            class="radio radio-primary radio-sm"
          />
          <span class="text-sm font-medium text-gray-700">Arquivo (A1)</span>
        </label>
        <label class="flex items-center gap-2 cursor-pointer">
          <input
            v-model="tipoCertificado"
            type="radio"
            value="WINDOWS"
            :disabled="disabled"
            class="radio radio-primary radio-sm"
          />
          <span class="text-sm font-medium text-gray-700">Instalado no Windows (A1 ou A3)</span>
        </label>
      </div>

      <!-- OPÇÃO 1: ARQUIVO A1 -->
      <div v-if="isArquivo" class="space-y-6 animate-in fade-in zoom-in duration-300">
        <!-- Status Banner -->
        <div
          v-if="hasCertificadoPath"
          class="flex items-center gap-3 p-4 bg-green-50 border border-green-100 rounded-lg text-green-800"
        >
          <CheckCircle class="text-green-600" :size="24" />
          <div>
            <p class="font-bold text-sm">Certificado Enviado</p>
            <p v-if="certificadoValidade" class="text-xs text-green-700 mt-0.5">
              Válido até: {{ certificadoValidade }}
            </p>
            <p v-else class="text-xs text-green-700 mt-0.5">
              Arquivo armazenado no servidor.
            </p>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
          <!-- Upload -->
          <div class="space-y-2">
            <label class="text-sm font-medium text-gray-700">Arquivo (.pfx / .p12)</label>
            <div class="relative">
              <input
                ref="certInput"
                type="file"
                :accept="UPLOAD_CONFIG.certificado.accept"
                :disabled="isUploadingCert || disabled"
                class="hidden"
                @change="onCertFileChange"
              />
              <button
                type="button"
                :disabled="isUploadingCert || disabled"
                class="flex items-center justify-center gap-2 w-full px-4 py-2.5 bg-gray-50 border border-dashed border-gray-300 rounded-lg text-sm text-gray-600 cursor-pointer hover:bg-gray-100 hover:border-gray-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                @click="certInput?.click()"
              >
                <span v-if="isUploadingCert" class="loading loading-spinner loading-sm"></span>
                <Upload v-else :size="16" />
                {{ isUploadingCert ? 'Enviando...' : 'Selecionar Arquivo' }}
              </button>
            </div>
            <p class="text-xs text-gray-500">
              Selecione o arquivo do certificado digital modelo A1.
            </p>
          </div>

          <!-- Senha do Certificado -->
          <div class="space-y-2">
            <label class="text-sm font-medium text-gray-700">Senha do Certificado</label>
            <div class="relative">
              <div
                class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400"
              >
                <Key :size="18" />
              </div>
              <input
                v-model="certificado_senha"
                type="password"
                placeholder="••••••••"
                :disabled="disabled"
                class="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg focus:bg-white focus:ring-2 focus:ring-brand-primary-light focus:border-brand-primary outline-none transition-all text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              />
            </div>
            <p class="text-xs text-gray-500">A senha é necessária para emitir notas.</p>
          </div>
        </div>
      </div>

      <!-- OPÇÃO 2: WINDOWS KEYSTORE -->
      <div v-else class="space-y-6 animate-in fade-in zoom-in duration-300">
        <!-- Info Banner -->
        <div
          class="bg-brand-primary-light border border-brand-primary/20 p-4 rounded-lg flex items-start gap-3"
        >
          <AlertCircle class="text-brand-primary shrink-0 mt-0.5" :size="20" />
          <div class="space-y-1">
            <p class="text-sm text-brand-primary font-bold">Certificado A3 ou Integrado</p>
            <p class="text-xs text-brand-primary">
              Esta opção utiliza os certificados instalados no Windows (Token, Cartão ou Arquivo
              instalado). O Backend deve estar rodando na mesma máquina onde o certificado está
              conectado.
            </p>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 items-end">
          <!-- Select de Certificados -->
          <div class="space-y-2">
            <label class="text-sm font-medium text-gray-700">Selecione o Certificado</label>
            <select
              :value="fiscal_settings.certificado_thumbprint"
              :disabled="disabled"
              class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg focus:bg-white focus:ring-2 focus:ring-brand-primary-light focus:border-brand-primary outline-none transition-all text-sm text-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
              @change="updateFiscalSetting('certificado_thumbprint', ($event.target as HTMLSelectElement).value)"
            >
              <option value="" disabled>Selecione...</option>
              <option
                v-for="cert in windowsCertificates"
                :key="cert.thumbprint"
                :value="cert.thumbprint"
              >
                {{ cert.friendly_name }} ({{ cert.issuer.substring(0, 20) }}...)
              </option>
            </select>
            <p
              v-if="fiscal_settings.certificado_thumbprint"
              class="text-xs text-gray-500"
            >
              Thumbprint: {{ fiscal_settings.certificado_thumbprint }}
            </p>
          </div>

          <!-- Botão Carregar Lista -->
          <BaseButton
            type="button"
            variant="secondary"
            :loading="isLoadingCertificates"
            :disabled="disabled"
            class="w-full justify-center md:w-auto"
            @click="refetchWindowsCerts"
          >
            <Upload :size="16" class="mr-2" />
            Carregar Lista de Certificados
          </BaseButton>
        </div>
      </div>
    </div>
  </section>
</template>
