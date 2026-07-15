<script setup lang="ts">
/**
 * @component ReconnectStep
 * @description Formulário para reconectar uma licença existente na StartBig.
 */

import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useForm } from 'vee-validate';
import * as z from 'zod';
import { toTypedSchema } from '@vee-validate/zod';
import axios from 'axios';

import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import { ArrowLeft, ArrowRight, Info, AlertCircle } from 'lucide-vue-next';

import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import { useSignIn } from '../../composables/useSignIn';
import { reconnectLicenca } from '../../services/sign-in.service';

const router = useRouter();
const { signInMode, updateAcessoData, goToStep } = useSignIn();

const isLoading = ref(false);
const serverError = ref<string | null>(null);

const schema = z.object({
  email: z.string().email('Digite um e-mail válido'),
  senha: z.string().min(8, 'A senha deve ter no mínimo 8 caracteres'),
});

const { handleSubmit, errors, defineField, submitCount } = useForm({
  validationSchema: toTypedSchema(schema),
});

const [email] = defineField('email');
const [senha] = defineField('senha');

const onSubmit = handleSubmit(async (values) => {
  isLoading.value = true;
  serverError.value = null;

  try {
    const result = await reconnectLicenca(values.email, values.senha);
    
    if (result.inicializado) {
      // Sistema já possui Empresa/Master
      router.push({ name: 'auth.user' });
    } else {
      // Licença vinculada, mas o banco de dados está vazio (nova instalação)
      // Passar credenciais para o step de configuração da Empresa
      updateAcessoData({
        email: values.email,
        senha: values.senha,
        confirmarSenha: values.senha,
      });
      signInMode.value = 'autocadastro';
      goToStep(1); // Vai direto para SegmentoStep, pulando a apresentação
    }
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      const detail = error.response.data?.detail;
      serverError.value = typeof detail === 'string' 
        ? detail 
        : detail?.mensagem || 'Erro ao tentar reconectar a licença. Verifique suas credenciais.';
    } else {
      serverError.value = 'Falha de comunicação com o servidor local.';
    }
  } finally {
    isLoading.value = false;
  }
});

function goBack() {
  signInMode.value = 'choice';
}
</script>

<template>
  <form @submit.prevent="onSubmit">
    <!-- Título -->
    <div class="mb-8">
      <h2 class="text-2xl font-bold text-brand-action">Reconectar Licença</h2>
      <p class="text-gray-500 mt-2">
        Insira suas credenciais da StartBig ERP para vincular esta máquina à sua licença existente.
      </p>
    </div>

    <!-- Dica -->
    <div class="p-3 mb-6 bg-blue-50 border border-blue-100 rounded-lg flex items-start gap-2">
      <LucideIcon :icon="Info" size="md" class="text-brand-primary mt-0.5 shrink-0" />
      <p class="text-xs text-brand-primary">
        Utilize o e-mail e a senha cadastrados no primeiro acesso ao sistema StartBig ERP.
      </p>
    </div>

    <!-- Erro do Servidor -->
    <div v-if="serverError" class="p-3 mb-6 bg-red-50 border border-red-100 rounded-lg flex items-start gap-2">
      <LucideIcon :icon="AlertCircle" size="md" class="text-red-600 mt-0.5 shrink-0" />
      <p class="text-sm text-red-700 font-medium">
        {{ serverError }}
      </p>
    </div>

    <!-- Dados de Login -->
    <div class="grid grid-cols-1 gap-4 mb-6">
      <BaseInput
        v-model="email"
        type="email"
        label="E-mail"
        placeholder="seu@email.com"
        :error="submitCount > 0 ? errors.email : ''"
      />
      <BaseInput
        v-model="senha"
        type="password"
        label="Senha"
        placeholder="Senha da licença"
        :error="submitCount > 0 ? errors.senha : ''"
      />
    </div>

    <!-- Botões -->
    <div class="flex gap-4 mt-6">
      <BaseButton
        type="button"
        variant="secondary"
        size="lg"
        class="flex-1"
        :disabled="isLoading"
        @click="goBack"
      >
        <LucideIcon :icon="ArrowLeft" />
        Voltar
      </BaseButton>
      <BaseButton type="submit" size="lg" class="flex-1" :is-loading="isLoading">
        Conectar
        <LucideIcon :icon="ArrowRight" v-if="!isLoading" />
      </BaseButton>
    </div>
  </form>
</template>
