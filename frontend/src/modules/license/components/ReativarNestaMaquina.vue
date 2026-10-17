<script setup lang="ts">
/**
 * @component ReativarNestaMaquina
 * @description Reativa a licença num computador novo, com o login da conta StartBig.
 *
 * Existe para a troca de computador: o cliente copia o start_big.db para a
 * máquina nova e o sistema sobe em CLONAGEM_DETECTADA, porque a licença do
 * banco está cifrada com o HWID da máquina antiga. Sem isto a tela de erro não
 * tinha saída nenhuma além do suporte.
 *
 * Usa o mesmo `/auth/reconnect` do assistente de primeiro acesso: a nuvem
 * confere e-mail e senha e só então o backend troca a licença antiga pela desta
 * máquina. Os dados da loja não são tocados.
 */

import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useForm } from 'vee-validate';
import * as z from 'zod';
import { toTypedSchema } from '@vee-validate/zod';
import axios from 'axios';

import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { reconnectLicenca } from '@/modules/sign-in/services/sign-in.service';

const emit = defineEmits<{ cancelar: [] }>();

const router = useRouter();
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
    // Banco copiado já tem empresa e usuários: vai direto para o login. Se não
    // tiver (copiaram um banco vazio), o assistente de primeiro acesso cuida.
    router.replace({ name: result.inicializado ? 'auth.user' : 'sign-in' });
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      const detail = error.response.data?.detail;
      serverError.value = typeof detail === 'string'
        ? detail
        : detail?.mensagem || 'Não foi possível reativar. Confira o e-mail e a senha.';
    } else {
      serverError.value = 'Falha de comunicação com o servidor local.';
    }
  } finally {
    isLoading.value = false;
  }
});
</script>

<template>
  <form class="w-full" @submit.prevent="onSubmit">
    <p class="text-sm text-gray-600 mb-4">
      Use o e-mail e a senha da conta StartBig, os mesmos do primeiro acesso.
      A licença passa para este computador e os dados da loja continuam iguais.
    </p>

    <div
      v-if="serverError"
      class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm mb-4"
    >
      {{ serverError }}
    </div>

    <div class="grid grid-cols-1 gap-4 mb-4">
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
        placeholder="Senha da conta StartBig"
        :error="submitCount > 0 ? errors.senha : ''"
      />
    </div>

    <div class="flex gap-2">
      <BaseButton
        type="button"
        variant="secondary"
        class="flex-1"
        :disabled="isLoading"
        @click="emit('cancelar')"
      >
        Cancelar
      </BaseButton>
      <BaseButton type="submit" class="flex-1" :is-loading="isLoading">
        Reativar
      </BaseButton>
    </div>
  </form>
</template>
