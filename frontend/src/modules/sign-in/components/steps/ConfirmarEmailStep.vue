<script setup lang="ts">
/**
 * @component ConfirmarEmailStep
 * @description "Confirme o seu e-mail" (LIC-03 §6.5, quadro 3a).
 *
 * O cadastro novo foi aceito, mas a licença só nasce depois que o dono confirma
 * o e-mail (D-24). Nada foi gravado neste computador. Depois de confirmar, ele
 * entra pelo re-login, que traz a chave de ativação (D-23).
 */

import { ref } from 'vue';
import { Mail } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { lerErroDaLicenca, mensagemDoCodigo } from '@/shared/services/licenca.service';

import { useSignIn } from '../../composables/useSignIn';
import { reenviarLink } from '../../services/sign-in.service';

const { emailConfirmacao, signInMode, updateAcessoData } = useSignIn();

const reenviando = ref(false);
const aviso = ref<string | null>(null);

/** "Já confirmei, quero entrar": vai para o re-login com o e-mail já preenchido. */
function irParaOLogin(): void {
  updateAcessoData({ email: emailConfirmacao.value });
  signInMode.value = 'reconnect';
}

/** "Reenviar link": o backend sempre aceita (não revela se o e-mail tem conta). */
async function reenviar(): Promise<void> {
  reenviando.value = true;
  try {
    await reenviarLink(emailConfirmacao.value);
    aviso.value = 'Se este e-mail tiver conta, enviamos um novo link.';
  } catch (e) {
    aviso.value = mensagemDoCodigo(lerErroDaLicenca(e).codigo); // ex.: sem internet
  } finally {
    reenviando.value = false;
  }
}
</script>

<template>
  <div class="flex flex-col items-center gap-4">
    <div class="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center">
      <Mail :size="24" class="text-brand-primary" aria-hidden="true" />
    </div>
    <div class="flex flex-col items-center gap-1.5 text-center">
      <h2 class="text-2xl font-bold text-zinc-900">Confirme o seu e-mail</h2>
      <p class="text-sm text-zinc-600 leading-relaxed">
        Enviamos as instruções para <strong class="font-semibold text-zinc-800">{{ emailConfirmacao }}</strong>.
        Se este e-mail já tiver conta, enviamos as instruções para entrar.
      </p>
    </div>

    <div class="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-3.5 text-sm text-zinc-700">
      <p class="font-semibold mb-2">Próximos passos</p>
      <ol class="list-decimal pl-5 flex flex-col gap-1.5">
        <li>Abra o e-mail da StartBig (confira também a caixa de spam).</li>
        <li>Clique no link de confirmação. Ele vale por 24 horas.</li>
        <li>Volte aqui e entre com o seu e-mail e senha.</li>
      </ol>
    </div>

    <BaseButton type="button" class="w-full mt-1" @click="irParaOLogin">Já confirmei, quero entrar</BaseButton>

    <p class="text-sm text-zinc-500 text-center">
      Não recebeu?
      <button
        type="button"
        class="font-semibold text-brand-primary hover:underline cursor-pointer disabled:opacity-50"
        :disabled="reenviando"
        @click="reenviar"
      >Reenviar link</button>
    </p>
    <p v-if="aviso" class="text-xs text-zinc-600 text-center" role="status">{{ aviso }}</p>
  </div>
</template>
