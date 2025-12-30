<script setup lang="ts">
/**
 * @view VerifyEmailView
 * @description Página de verificação de email.
 * Exibe mensagem de confirmação após cadastro.
 */

import backgroundImage from '@/assets/images/login/background.png';
import logoImage from '@/assets/images/login/start-logo.png';
</script>

<template>
  <div class="h-screen flex overflow-hidden">
    <!-- Lado esquerdo - Background decorativo -->
    <div class="hidden lg:flex lg:w-full relative overflow-hidden">
      <img
        :src="backgroundImage"
        alt="Background decorativo"
        class="absolute inset-0 w-full h-full object-cover"
      />
    </div>

    <!-- Lado direito - Conteúdo -->
    <div
      class="w-full lg:w-5/10 flex flex-col items-center justify-center px-6 py-8 bg-white drop-shadow-xl shadow-brand-action"
    >
      <div class="w-full max-w-sm text-center">
        <!-- Logo -->
        <div class="flex justify-center mb-8">
          <img :src="logoImage" alt="Start Big Logo" class="h-20 w-auto" />
        </div>

        <!-- Ícone de email -->
        <div class="w-20 h-20 mx-auto mb-6 bg-blue-100 rounded-full flex items-center justify-center">
          <svg class="w-10 h-10 text-brand-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
          </svg>
        </div>

        <!-- Mensagem -->
        <h1 class="text-2xl font-bold text-brand-action mb-3">
          Verifique seu e-mail
        </h1>

        <p class="text-gray-500 text-sm mb-6">
          Enviamos um link de verificação para o seu e-mail.
          Por favor, verifique sua caixa de entrada e clique no link para ativar sua conta.
        </p>

        <!-- Link de voltar -->
        <router-link
          to="/"
          class="text-brand-primary hover:underline text-sm font-medium"
        >
          Voltar para o login
        </router-link>
      </div>
    </div>
  </div>
</template>
