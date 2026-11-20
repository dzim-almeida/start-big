<script setup lang="ts">
/**
 * @component EscolhaRestauracaoStep
 * @description "Sua licença foi encontrada" — a tela logo depois do re-login
 * com o banco vazio (LIC-03 §6.2, quadros 1a e 1b dos mockups aprovados).
 *
 * Regra (D-22): COM backup na nuvem, a tela só oferece restaurar; SEM backup,
 * só oferece preencher os dados da empresa (o setup, já com os dados da nuvem).
 */

import { computed, ref } from 'vue';
import { CloudCheck, Info, ShieldCheck, Check } from 'lucide-vue-next';

import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { lerErroDaLicenca, mensagemDoCodigo } from '@/shared/services/licenca.service';

import { useSignIn } from '../../composables/useSignIn';
import { restaurarBackupDaNuvem } from '../../services/sign-in.service';

const { dadosRelogin, signInData, signInMode, restauracaoPreparada, aplicarTitular, goToStep } = useSignIn();

/** Há backup na nuvem? (a mesma regra do backend: um ciclo com full confirmado) */
const temBackup = computed(() => dadosRelogin.backup !== null);

/** "17/11/2026" a partir do ciclo ISO "2026-11-17" (sem fuso: é só uma data). */
const semana = computed(() => {
  const ciclo = dadosRelogin.backup?.ciclo ?? '';
  const [ano, mes, dia] = ciclo.split('-');
  return ano && mes && dia ? `${dia}/${mes}/${ano}` : ciclo;
});

/** "18/11/2026, 19:40" do último envio, quando a nuvem informa. */
const ultimoEnvio = computed(() => {
  const quando = dadosRelogin.backup?.ultimo_envio;
  if (!quando) return null;
  const data = new Date(quando);
  if (Number.isNaN(data.getTime())) return null;
  return data.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
});

// O e-mail vem do re-login e fica travado; a senha é pedida de novo (D-07).
const senha = ref('');
const enviando = ref(false);
const erro = ref<string | null>(null);

/** Restaurar: o backend confere a senha na nuvem, baixa o backup e prepara para o próximo boot. */
async function restaurar(): Promise<void> {
  if (!senha.value) {
    erro.value = 'Digite a senha da conta StartBig.';
    return;
  }
  enviando.value = true;
  erro.value = null;
  try {
    const resposta = await restaurarBackupDaNuvem(
      signInData.acesso.email,
      senha.value,
      dadosRelogin.backup?.ciclo,
    );
    restauracaoPreparada.value = { ciclo: resposta.ciclo, mensagem: resposta.mensagem };
    signInMode.value = 'restauracao-preparada';
  } catch (e) {
    // Nunca o texto técnico do servidor: só a frase fixa do código (D-16)
    erro.value = mensagemDoCodigo(lerErroDaLicenca(e).codigo);
  } finally {
    enviando.value = false;
  }
}

/** Sem backup: o setup abre com os dados que a conta já tem na nuvem. */
function preencherDados(): void {
  if (dadosRelogin.titular) aplicarTitular(dadosRelogin.titular);
  signInMode.value = 'autocadastro';
  goToStep(1); // pula a apresentação, como o re-login já fazia
}
</script>

<template>
  <div class="flex flex-col items-center gap-4">
    <!-- Ícone e título -->
    <div class="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center">
      <ShieldCheck :size="24" class="text-brand-primary" aria-hidden="true" />
    </div>
    <div class="flex flex-col items-center gap-1.5 text-center">
      <h2 class="text-2xl font-bold text-zinc-900">Sua licença foi encontrada</h2>
      <p class="text-sm text-zinc-600 leading-relaxed">
        Se você já usava o sistema neste computador ou em outro, é possível recuperar os dados do último
        backup da nuvem.
      </p>
    </div>

    <!-- ===== Com backup (quadro 1a): só restaurar ===== -->
    <template v-if="temBackup">
      <div class="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-3 flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center shrink-0">
          <CloudCheck :size="16" class="text-emerald-600" aria-hidden="true" />
        </div>
        <div class="flex flex-col gap-0.5">
          <p class="text-sm font-medium text-zinc-800">Backup encontrado na nuvem</p>
          <p class="text-xs text-zinc-500">
            Semana de {{ semana }}<template v-if="ultimoEnvio"> · último envio em {{ ultimoEnvio }}</template>
          </p>
        </div>
      </div>

      <!-- Erro com a mensagem fixa do código -->
      <p v-if="erro" class="w-full p-3 bg-red-50 border border-red-100 rounded-lg text-sm text-red-700 font-medium">
        {{ erro }}
      </p>

      <form class="w-full flex flex-col gap-3" @submit.prevent="restaurar">
        <BaseInput
          :model-value="signInData.acesso.email"
          type="email"
          label="E-mail da conta StartBig"
          disabled
        />
        <BaseInput
          v-model="senha"
          type="password"
          label="Confirme a senha da conta"
          placeholder="Senha da conta StartBig"
        />
        <BaseButton type="submit" class="w-full mt-1" :is-loading="enviando">
          Restaurar backup da nuvem
        </BaseButton>
      </form>
    </template>

    <!-- ===== Sem backup (quadro 1b): só preencher ===== -->
    <template v-else>
      <div class="w-full bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 flex items-start gap-2.5">
        <Info :size="18" class="text-amber-700 shrink-0 mt-0.5" aria-hidden="true" />
        <p class="text-sm text-amber-800 leading-relaxed">
          Não há backup na nuvem para esta licença. Confira os dados da empresa, que vêm da sua conta na
          StartBig.
        </p>
      </div>
      <ul class="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-3.5 flex flex-col gap-2 text-sm text-zinc-700">
        <li class="flex gap-2 items-start">
          <Check :size="16" class="text-emerald-600 shrink-0 mt-0.5" aria-hidden="true" />
          O nome, o CPF ou CNPJ e o endereço já vêm preenchidos.
        </li>
        <li class="flex gap-2 items-start">
          <Check :size="16" class="text-emerald-600 shrink-0 mt-0.5" aria-hidden="true" />
          Você só confere e completa o que faltar.
        </li>
      </ul>
      <BaseButton type="button" class="w-full mt-1" @click="preencherDados">
        Preencher os dados da empresa
      </BaseButton>
    </template>
  </div>
</template>
