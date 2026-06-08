<script setup lang="ts">
/**
 * @component AcessoStep
 * @description Formulário de dados de acesso ao sistema (Passo 3).
 * Coleta nome de exibição, email e senha para login.
 */

import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import { ArrowLeft, ArrowRight, Info } from 'lucide-vue-next';

import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import { useAcessoForm } from '../../composables/useAcessoForm';
import { useSignIn } from '../../composables/useSignIn';

const {
  nomeUsuario,
  email,
  senha,
  confirmarSenha,
  errors,
  onSubmit,
  submitCount,
} = useAcessoForm();

const { previousStep } = useSignIn();
</script>

<template>
  <form @submit.prevent="onSubmit">
    <!-- Dica -->
    <div class="p-3 mb-6 bg-blue-50 border border-blue-100 rounded-lg flex items-start gap-2">
      <LucideIcon :icon="Info" size="md" class="text-brand-primary mt-0.5 shrink-0" />
      <p class="text-xs text-brand-primary">
        Esses dados serão usados para fazer login no sistema. O nome de exibição
        será mostrado no menu e nas interações do sistema.
      </p>
    </div>

    <!-- Nome do Usuário -->
    <div class="grid grid-cols-1 gap-4 mb-6">
      <BaseInput
        v-model="nomeUsuario"
        label="Nome de Exibição"
        placeholder="Como você quer ser chamado no sistema"
        required
        :error="submitCount > 0 ? errors.nomeUsuario : ''"
      />
    </div>

    <!-- Dados de Login -->
    <h3 class="text-sm font-semibold text-brand-action mb-4">Credenciais de Login</h3>

    <div class="grid grid-cols-1 gap-4 mb-6">
      <BaseInput
        v-model="email"
        type="email"
        label="E-mail de Acesso"
        placeholder="seu@email.com"
        required
        :error="submitCount > 0 ? errors.email : ''"
      />
      <div class="grid grid-cols-2 gap-4">
        <BaseInput
          v-model="senha"
          type="password"
          label="Senha"
          placeholder="Mínimo 8 caracteres"
          required
          :error="submitCount > 0 ? errors.senha : ''"
        />
        <BaseInput
          v-model="confirmarSenha"
          type="password"
          label="Confirmar Senha"
          placeholder="Repita a senha"
          required
          :error="submitCount > 0 ? errors.confirmarSenha : ''"
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
