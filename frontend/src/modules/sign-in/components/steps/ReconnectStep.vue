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

import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import { ArrowLeft, ArrowRight, Info, AlertCircle } from 'lucide-vue-next';

import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import { useSignIn } from '../../composables/useSignIn';
import { reconnectLicenca, reenviarLink } from '../../services/sign-in.service';
import { lerErroDaLicenca, mensagemDoCodigo } from '@/shared/services/licenca.service';

const router = useRouter();
const { signInMode, updateAcessoData, dadosRelogin, signInData } = useSignIn();

const isLoading = ref(false);
const serverError = ref<string | null>(null);
// Código do último erro: com AGUARDANDO_CONFIRMACAO_EMAIL a tela oferece
// "Reenviar link" (LIC-03 §6.5, quadro 3b).
const codigoErro = ref<string | undefined>(undefined);
const avisoReenvio = ref<string | null>(null);

const schema = z.object({
  email: z.string().email('Digite um e-mail válido'),
  senha: z.string().min(8, 'A senha deve ter no mínimo 8 caracteres'),
});

const { handleSubmit, errors, defineField, submitCount } = useForm({
  validationSchema: toTypedSchema(schema),
  // Quem vem do "Já confirmei, quero entrar" já chega com o e-mail preenchido
  initialValues: { email: signInData.acesso.email || undefined },
});

const [email] = defineField('email');
const [senha] = defineField('senha');

const onSubmit = handleSubmit(async (values) => {
  isLoading.value = true;
  serverError.value = null;
  codigoErro.value = undefined;
  avisoReenvio.value = null;

  try {
    const result = await reconnectLicenca(values.email, values.senha);
    
    if (result.inicializado) {
      // Sistema já possui Empresa/Master
      router.push({ name: 'auth.user' });
    } else {
      // Licença vinculada, mas o banco está vazio (computador novo ou banco perdido).
      // Guarda as credenciais para o setup e o que a nuvem mandou (LIC-03).
      updateAcessoData({
        email: values.email,
        senha: values.senha,
        confirmarSenha: values.senha,
      });
      dadosRelogin.backup = result.backup ?? null;
      dadosRelogin.titular = result.titular ?? null;
      // "Sua licença foi encontrada": com backup, restaurar; sem, preencher (§6.2)
      signInMode.value = 'escolha-restauracao';
    }
  } catch (error) {
    // Mensagem fixa por código, nunca o texto técnico do servidor (D-16)
    const { codigo } = lerErroDaLicenca(error);
    codigoErro.value = codigo;
    serverError.value = codigo
      ? mensagemDoCodigo(codigo)
      : 'O serviço do StartBig neste computador não respondeu. Aguarde alguns segundos e tente de novo.';
  } finally {
    isLoading.value = false;
  }
});

/** "Reenviar link" do quadro 3b: o backend sempre aceita. */
async function reenviar(): Promise<void> {
  try {
    await reenviarLink(email.value ?? '');
    avisoReenvio.value = 'Se este e-mail tiver conta, enviamos um novo link.';
  } catch (e) {
    avisoReenvio.value = mensagemDoCodigo(lerErroDaLicenca(e).codigo);
  }
}

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
      <div class="flex flex-col gap-2 flex-1">
        <p class="text-sm text-red-700 font-medium">
          {{ serverError }}
        </p>
        <!-- Conta esperando a confirmação do e-mail: oferece um link novo (quadro 3b) -->
        <div v-if="codigoErro === 'AGUARDANDO_CONFIRMACAO_EMAIL'" class="flex items-center gap-3">
          <button
            type="button"
            class="min-h-9 px-3 py-1 border border-brand-primary rounded-md bg-white text-brand-primary text-xs font-semibold cursor-pointer"
            @click="reenviar"
          >Reenviar link</button>
          <span class="text-xs text-gray-500">{{ avisoReenvio ?? 'O link novo substitui o anterior.' }}</span>
        </div>
      </div>
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
