<script setup lang="ts">
/**
 * @view TransferirLicencaView
 * @description Transfere a licença para este computador — a troca de servidor.
 *
 * Aparece quando o banco foi copiado de outro computador: a ativação gravada
 * nele é cifrada com o HWID da máquina antiga e não vale aqui. Chega-se a
 * esta tela por QUALQUER porta que descubra isso — a checagem de licença do
 * router, o login e a tela de erro de licença. Até 19/10/2026 só a última
 * tinha saída, e o cliente que descobria pelo login ficava preso.
 *
 * Quem autoriza é a conta StartBig (e-mail + senha), conferida na nuvem. Os
 * dados da loja não são tocados.
 */

import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useForm } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import * as z from 'zod';
import axios from 'axios';
import { openUrl } from '@tauri-apps/plugin-opener';
import { ArrowRightLeft, CheckCircle2, ShieldCheck } from 'lucide-vue-next';

import AppLogo from '@/shared/components/AppLogo.vue';
import BaseFooter from '@/shared/components/layout/BaseFooter.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { useLicencaStore } from '@/shared/stores/licenca.store';
import { LINKS } from '@/shared/config/links';
import { transferirLicenca, type TransferenciaResultado } from '../services/transferencia.service';

const router = useRouter();
const isLoading = ref(false);
const serverError = ref<string | null>(null);
const resultado = ref<TransferenciaResultado | null>(null);

const schema = z.object({
  email: z.string().email('Digite um e-mail válido'),
  senha: z.string().min(1, 'Digite a senha da conta StartBig'),
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
    resultado.value = await transferirLicenca(values.email, values.senha);
    useLicencaStore().limpar();
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      const detail = error.response.data?.detail;
      serverError.value = typeof detail === 'string'
        ? detail
        : detail?.mensagem || 'Não foi possível transferir a licença. Tente de novo.';
    } else {
      serverError.value = 'O serviço do StartBig neste computador não respondeu. Aguarde alguns segundos e tente de novo.';
    }
  } finally {
    isLoading.value = false;
  }
});

function continuar() {
  // Banco copiado já tem empresa e usuários: vai direto para o login. Se não
  // tiver (copiaram um banco vazio), o assistente de primeiro acesso cuida.
  router.replace({ name: resultado.value?.inicializado ? 'auth.user' : 'sign-in' });
}

function voltar() {
  router.replace({ name: 'auth.user' });
}
</script>

<template>
  <div class="h-screen flex flex-col items-center justify-between bg-white px-6 py-8 overflow-y-auto">
    <div class="flex flex-col items-center flex-1 justify-center max-w-md w-full">
      <div class="flex justify-center mb-6">
        <AppLogo class="h-16 w-auto" />
      </div>

      <!-- Concluído -->
      <template v-if="resultado">
        <CheckCircle2 :size="48" class="text-emerald-500 mb-4" />
        <h1 class="text-2xl font-bold text-zinc-800 mb-2 text-center">Licença transferida</h1>
        <p class="text-sm text-zinc-600 text-center mb-6">
          Este computador agora é o dono da licença. Os dados da loja continuam exatamente como estavam.
        </p>

        <div class="w-full bg-zinc-50 border border-zinc-200 rounded-xl p-4 text-sm text-zinc-700 mb-6">
          <p class="font-semibold mb-2">Próximos passos</p>
          <ol class="list-decimal pl-5 space-y-1.5">
            <li>Entre com o seu usuário do sistema, como sempre.</li>
            <li>
              Nos caixas, se não conectarem sozinhos, abra
              <strong>Configurações › Rede e Conexão</strong> e busque o servidor novo.
            </li>
            <li>No computador antigo, não abra mais o StartBig como servidor.</li>
          </ol>
        </div>

        <BaseButton type="button" class="w-full" @click="continuar">
          Entrar no sistema
        </BaseButton>
      </template>

      <!-- Formulário -->
      <template v-else>
        <div class="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center mb-4">
          <ArrowRightLeft :size="24" class="text-blue-600" />
        </div>
        <h1 class="text-2xl font-bold text-zinc-800 mb-2 text-center">
          Transferir a licença para este computador
        </h1>
        <p class="text-sm text-zinc-600 text-center mb-6">
          Os dados deste sistema vieram de outro computador, onde a licença está ativada.
          Entre com a sua conta StartBig para passar a licença para cá.
        </p>

        <ul class="w-full bg-zinc-50 border border-zinc-200 rounded-xl p-4 text-sm text-zinc-700 space-y-2 mb-6">
          <li class="flex gap-2">
            <ShieldCheck :size="16" class="text-emerald-600 shrink-0 mt-0.5" />
            Vendas, clientes, estoque e usuários continuam como estão.
          </li>
          <li class="flex gap-2">
            <ShieldCheck :size="16" class="text-emerald-600 shrink-0 mt-0.5" />
            O computador antigo deixa de usar a licença.
          </li>
          <li class="flex gap-2">
            <ShieldCheck :size="16" class="text-emerald-600 shrink-0 mt-0.5" />
            Por segurança, o e-mail da conta recebe um aviso da troca.
          </li>
        </ul>

        <form class="w-full" @submit.prevent="onSubmit">
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
              label="E-mail da conta StartBig"
              placeholder="seu@email.com"
              :error="submitCount > 0 ? errors.email : ''"
            />
            <BaseInput
              v-model="senha"
              type="password"
              label="Senha da conta StartBig"
              placeholder="A mesma do primeiro acesso"
              :error="submitCount > 0 ? errors.senha : ''"
            />
          </div>

          <BaseButton type="submit" class="w-full mb-2" :is-loading="isLoading">
            Transferir para este computador
          </BaseButton>
          <BaseButton type="button" variant="ghost" class="w-full" :disabled="isLoading" @click="voltar">
            Voltar
          </BaseButton>
        </form>

        <p class="text-xs text-zinc-500 text-center mt-4">
          Não é a conta do sistema (usuário do caixa): é a conta StartBig, usada na instalação.
        </p>
      </template>

      <button
        type="button"
        class="text-xs text-zinc-400 hover:text-zinc-600 underline text-center mt-4 cursor-pointer"
        @click="openUrl(LINKS.whatsapp)"
      >
        Precisa de ajuda? Falar com o suporte
      </button>
    </div>

    <BaseFooter />
  </div>
</template>
