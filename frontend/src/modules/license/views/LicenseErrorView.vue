<script setup lang="ts">
/**
 * @view LicenseErrorView
 * @description Tela de bloqueio exibida quando a licença é inválida.
 * Mostra título contextual baseado no código de erro e permite tentar novamente.
 */

import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseFooter from '@/shared/components/layout/BaseFooter.vue';
import { verificarLicenca } from '@/shared/services/licenca.service';

import logoImage from '@/shared/assets/images/login/start-logo.png';

const props = defineProps<{
  codigo: string;
  mensagem: string;
}>();

const router = useRouter();
const isRetrying = ref(false);
const retryError = ref('');

const titulo = computed(() => {
  switch (props.codigo) {
    case 'CLONAGEM_DETECTADA':
      return 'Licença Inválida';
    case 'REQUISITA_CONEXAO_INTERNET':
      return 'Conexão com Internet Necessária';
    case 'LICENCA_EXPIRADA':
      return 'Licença Expirada';
    case 'LICENCA_NAO_ENCONTRADA':
      return 'Licença Não Encontrada';
    case 'LICENCA_RECUSADA':
      return 'Licença Recusada';
    case 'LICENCA_BLOQUEADA':
      return 'Licença Bloqueada';
    default:
      return 'Erro de Licença';
  }
});

const icone = computed(() => {
  switch (props.codigo) {
    case 'CLONAGEM_DETECTADA':
      return '🔒';
    case 'REQUISITA_CONEXAO_INTERNET':
      return '🌐';
    case 'LICENCA_EXPIRADA':
      return '⏰';
    case 'LICENCA_NAO_ENCONTRADA':
      return '🔍';
    case 'LICENCA_BLOQUEADA':
      return '🚫';
    default:
      return '⚠️';
  }
});

async function tentarNovamente() {
  isRetrying.value = true;
  retryError.value = '';

  try {
    await verificarLicenca();
    // Licença válida — redirecionar para login
    router.push({ name: 'auth.user' });
  } catch {
    retryError.value = 'A verificação falhou novamente. Verifique sua conexão e tente mais tarde.';
  } finally {
    isRetrying.value = false;
  }
}
</script>

<template>
  <div class="h-screen flex flex-col items-center justify-between bg-white px-6 py-8">
    <div class="flex flex-col items-center flex-1 justify-center max-w-md w-full">
      <!-- Logo -->
      <div class="flex justify-center mb-6">
        <img :src="logoImage" alt="Start Big Logo" class="h-16 w-auto" />
      </div>

      <!-- Ícone e Título -->
      <div class="text-center mb-6">
        <span class="text-5xl mb-4 block">{{ icone }}</span>
        <h1 class="text-2xl font-bold text-gray-800 mb-2">{{ titulo }}</h1>
      </div>

      <!-- Mensagem de Erro -->
      <div
        class="w-full bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm text-center mb-6"
      >
        {{ mensagem || 'Ocorreu um erro na verificação da licença.' }}
      </div>

      <!-- Erro do retry -->
      <div
        v-if="retryError"
        class="w-full bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded-lg text-sm text-center mb-4"
      >
        {{ retryError }}
      </div>

      <!-- Botão Tentar Novamente -->
      <BaseButton
        type="button"
        class="w-full"
        :disabled="isRetrying"
        @click="tentarNovamente"
      >
        {{ isRetrying ? 'Verificando...' : 'Tentar Novamente' }}
      </BaseButton>

      <!-- Orientação -->
      <p class="text-xs text-gray-400 text-center mt-4">
        Se o problema persistir, entre em contato com o suporte técnico.
      </p>
    </div>

    <BaseFooter />
  </div>
</template>
