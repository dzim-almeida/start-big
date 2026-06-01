<script setup lang="ts">
import { ref, watch } from 'vue';
import { User } from 'lucide-vue-next';
import { storeToRefs } from 'pinia';

import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import { useAuthStore } from '@/shared/stores/auth.store';
import { useAtualizarContaMutation } from '../composables/mutates/useAtualizarContaMutation';
import { useAlterarSenhaMutation } from '../composables/mutates/useAlterarSenhaMutation';
import { AtualizarContaSchema, AlterarSenhaSchema } from '../schemas/minhaConta.schema';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const authStore = useAuthStore();
const { userData } = storeToRefs(authStore);

// =============================================
// Dados da Conta
// =============================================

const nome = ref('');
const email = ref('');
const contaErrors = ref<Record<string, string>>({});

watch(
  userData,
  (user) => {
    if (user) {
      nome.value = user.nome;
      email.value = user.email;
    }
  },
  { immediate: true },
);

const { mutate: atualizarConta, isPending: isAtualizando } = useAtualizarContaMutation();

function salvarDados() {
  const resultado = AtualizarContaSchema.safeParse({ nome: nome.value, email: email.value });
  if (!resultado.success) {
    const erros: Record<string, string> = {};
    resultado.error.errors.forEach((e) => {
      if (e.path[0]) erros[String(e.path[0])] = e.message;
    });
    contaErrors.value = erros;
    return;
  }
  contaErrors.value = {};
  atualizarConta({ nome: nome.value, email: email.value });
}

// =============================================
// Alterar Senha
// =============================================

const senhaAtual = ref('');
const novaSenha = ref('');
const confirmarNovaSenha = ref('');
const senhaErrors = ref<Record<string, string>>({});

const { mutate: alterarSenha, isPending: isAlterando } = useAlterarSenhaMutation();

function salvarSenha() {
  const resultado = AlterarSenhaSchema.safeParse({
    senha_atual: senhaAtual.value,
    nova_senha: novaSenha.value,
    confirmar_nova_senha: confirmarNovaSenha.value,
  });
  if (!resultado.success) {
    const erros: Record<string, string> = {};
    resultado.error.errors.forEach((e) => {
      if (e.path[0]) erros[String(e.path[0])] = e.message;
    });
    senhaErrors.value = erros;
    return;
  }
  senhaErrors.value = {};
  alterarSenha(
    { senha_atual: senhaAtual.value, nova_senha: novaSenha.value },
    {
      onSuccess: () => {
        senhaAtual.value = '';
        novaSenha.value = '';
        confirmarNovaSenha.value = '';
      },
    },
  );
}
</script>

<template>
  <div class="h-full flex flex-col p-6 overflow-y-auto">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800">Minha Conta</h1>
      <p class="text-sm text-gray-500 mt-1">Gerencie seus dados de acesso ao sistema</p>
    </div>

    <div class="flex flex-col gap-6 max-w-lg">
      <!-- Foto de Perfil -->
      <div class="bg-white border border-zinc-200 rounded-xl p-5">
        <h2 class="text-sm font-semibold text-zinc-700 mb-4">Foto de Perfil</h2>
        <div class="flex items-center gap-4">
          <div class="w-16 h-16 bg-brand-primary rounded-xl flex items-end justify-center p-0.5 shrink-0">
            <img
              v-if="userData?.url_perfil"
              :src="`${API_BASE_URL}/${userData.url_perfil}`"
              alt="Foto de perfil"
              class="w-full h-full object-cover rounded-xl"
            />
            <User v-else :size="40" class="text-white" />
          </div>
          <div>
            <p class="text-sm font-semibold text-zinc-800">{{ userData?.nome }}</p>
            <p class="text-xs text-zinc-400 mt-0.5">{{ userData?.cargo?.nome }}</p>
          </div>
        </div>
      </div>

      <!-- Dados da Conta -->
      <div class="bg-white border border-zinc-200 rounded-xl p-5">
        <h2 class="text-sm font-semibold text-zinc-700 mb-4">Dados da Conta</h2>
        <div class="flex flex-col gap-3">
          <BaseInput
            v-model="nome"
            label="Nome"
            placeholder="Seu nome completo"
            :error="contaErrors.nome"
          />
          <BaseInput
            v-model="email"
            type="email"
            label="E-mail"
            placeholder="seu@email.com"
            :error="contaErrors.email"
          />
          <div class="flex justify-end mt-1">
            <BaseButton
              variant="primary"
              size="sm"
              :isLoading="isAtualizando"
              @click="salvarDados"
            >
              Salvar Dados
            </BaseButton>
          </div>
        </div>
      </div>

      <!-- Alterar Senha -->
      <div class="bg-white border border-zinc-200 rounded-xl p-5">
        <h2 class="text-sm font-semibold text-zinc-700 mb-4">Alterar Senha</h2>
        <div class="flex flex-col gap-3">
          <BaseInput
            v-model="senhaAtual"
            type="password"
            label="Senha Atual"
            placeholder="••••••••"
            :error="senhaErrors.senha_atual"
          />
          <BaseInput
            v-model="novaSenha"
            type="password"
            label="Nova Senha"
            placeholder="••••••••"
            :error="senhaErrors.nova_senha"
          />
          <BaseInput
            v-model="confirmarNovaSenha"
            type="password"
            label="Confirmar Nova Senha"
            placeholder="••••••••"
            :error="senhaErrors.confirmar_nova_senha"
          />
          <div class="flex justify-end mt-1">
            <BaseButton
              variant="primary"
              size="sm"
              :isLoading="isAlterando"
              @click="salvarSenha"
            >
              Alterar Senha
            </BaseButton>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
