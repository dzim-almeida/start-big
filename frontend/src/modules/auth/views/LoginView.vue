<script setup lang="ts">
/**
 * @view LoginView
 * @description Página de login/cadastro do sistema Start Big.
 * Apresenta um layout dividido com background decorativo à esquerda
 * e formulário de autenticação à direita.
 */

import { onMounted, ref } from 'vue';
import BaseInput from '@/shared/components/commons/BaseInput/BaseInput.vue';
import BaseButton from '@/shared/components/commons/BaseButton/BaseButton.vue';
import BaseCheckbox from '@/shared/components/commons/BaseCheckbox/BaseCheckbox.vue';
import BaseTab from '@/shared/components/commons/BaseTab/BaseTab.vue';
import BaseFooter from '@/shared/components/layout/BaseFooter.vue';

import { useLogin } from '../composables/useLogin';
import { useRegister } from '../composables/useRegister';
import type { AuthTab } from '../types/auth.types';

import backgroundImage from '@/assets/images/login/background.png';
import logoImage from '@/assets/images/login/start-logo.png';

const activeTab = ref<AuthTab>('entrar');

const authTabs = [
  { id: 'entrar', label: 'Entrar' },
  { id: 'cadastrar', label: 'Cadastrar' },
];

const {
  loginData,
  savedEmail,
  rememberMe,
  errors: loginErrors,
  apiError: loginApiError,
  isLoading: loginIsLoading,
  loginSubmit,
  submitCount: loginSubmitCount,
} = useLogin();

const {
  registerData,
  errors: registerErrors,
  apiError: registerApiError,
  isLoading: registerIsLoading,
  registerSubmit,
  submitCount: registerSubmitCount,
} = useRegister(activeTab);

onMounted(() => {
  if (savedEmail.value) {
    loginData.email = savedEmail.value;
  }
});
</script>

<template>
  <div class="h-screen flex overflow-hidden">
    <!-- Lado esquerdo - Background decorativo -->
    <div class="hidden lg:flex lg:w-full relative overflow-hidden select-none">
      <img
        :src="backgroundImage"
        alt="Background decorativo"
        class="absolute inset-0 w-full h-full object-cover"
      />
    </div>

    <!-- Lado direito - Login e Cadastro - Formulário -->
    <div
      class="w-full lg:w-5/10 flex flex-col items-center justify-between px-6 py-8 bg-white drop-shadow-xl shadow-brand-action overflow-y-scroll"
    >
      <div class="w-full max-w-xs flex flex-col items-center flex-1">
        <!-- Logo -->
        <div class="flex justify-center mb-8">
          <img :src="logoImage" alt="Start Big Logo" class="h-20 w-auto" />
        </div>

        <!-- Tabs Entrar/Cadastrar -->
        <div class="mb-8 mr-auto">
          <BaseTab v-model="activeTab" :tabs="authTabs" />
        </div>

        <!-- Formulário de Login -->
        <form v-if="activeTab === 'entrar'" @submit.prevent="loginSubmit" class="w-full space-y-1">
          <!-- Erro da API -->
          <div
            v-if="loginApiError"
            class="bg-red-50 border border-red-200 text-red-700 px-3 py-2 mb-4 rounded-lg text-xs"
          >
            {{ loginApiError }}
          </div>

          <div class="flex flex-col gap-5">
            <!-- Campo Email -->
            <BaseInput
              v-model="loginData.email"
              type="email"
              label="Email"
              placeholder="Digite seu email"
              :error="loginSubmitCount > 0 ? loginErrors.email : ''"
            />

            <!-- Campo Senha -->
            <BaseInput
              v-model="loginData.senha"
              type="password"
              label="Senha"
              placeholder="Digite sua senha"
              :error="loginSubmitCount > 0 ? loginErrors.senha : ''"
            />

            <!-- Lembre-se de mim -->
            <BaseCheckbox v-model="rememberMe" label="Lembre-se de mim" />

            <!-- Botão de Login -->
            <div class="pt-2">
              <BaseButton type="submit" size="md" :is-loading="loginIsLoading" class="w-full">
                Entrar
              </BaseButton>
            </div>
          </div>

          <!-- Link Esqueceu a senha -->
          <div class="text-center pt-1">
            <a href="#" class="text-xs text-brand-primary hover:underline"> Esqueceu a senha? </a>
          </div>
        </form>

        <!-- Formulário de Cadastro (placeholder) -->
        <form v-else @submit.prevent="registerSubmit" class="w-full space-y-1">
          <!-- Erro da API -->
          <div
            v-if="registerApiError"
            class="bg-red-50 border border-red-200 text-red-700 px-3 py-2 mb-4 rounded-lg text-xs"
          >
            {{ registerApiError }}
          </div>

          <div class="flex flex-col gap-5">
            <!-- Campo Nome de Usuário -->
            <BaseInput
              v-model="registerData.nome"
              type="text"
              label="Nome de Usuário"
              placeholder="Digite seu nome"
              :error="registerSubmitCount > 0 ? registerErrors.nome : ''"
            />

            <!-- Campo Email -->
            <BaseInput
              v-model="registerData.email"
              type="email"
              label="Email"
              placeholder="Digite seu email"
              :error="registerSubmitCount > 0 ? registerErrors.email : ''"
            />

            <!-- Campo Senha -->
            <BaseInput
              v-model="registerData.senha"
              type="password"
              label="Senha"
              placeholder="Digite sua senha"
              :error="registerErrors.senha"
            />

            <!-- Campo Confirme Senha -->
            <BaseInput
              v-model="registerData.confirmarSenha"
              type="password"
              label="Confirme sua senha"
              placeholder="Confirmar senha"
              :error="registerSubmitCount > 0 ? registerErrors.confirmarSenha : ''"
            />

            <!-- Botão de Cadastro -->
            <div class="pt-2">
              <BaseButton
                type="submit"
                size="md"
                :is-loading="registerIsLoading"
                class="w-full"
              >
                Cadastrar
              </BaseButton>
            </div>
          </div>
        </form>
      </div>

      <!-- Footer -->
      <footer class="mt-2">
        <BaseFooter />
      </footer>
    </div>
  </div>
</template>
