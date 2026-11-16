<script setup lang="ts">
/**
 * @section LicencaComputador
 * @description Configurações › Licença deste Computador. Mostra a licença
 *   ativada neste servidor e conduz a troca de servidor no padrão de mercado:
 *   desativar aqui (libera a vaga na nuvem) e ativar no computador novo com a
 *   conta StartBig. Só leitura + uma ação — não participa do "Salvar" do modal.
 *
 *   Só aparece no SERVIDOR e para o master (ver ConfiguracoesModal): num caixa,
 *   "desativar" desligaria a licença da loja inteira — o backend recusa mesmo
 *   assim (SOMENTE_NO_SERVIDOR), mas o botão nem deve existir ali.
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useQuery } from '@tanstack/vue-query'
import axios from 'axios'
import { KeyRound, PowerOff } from 'lucide-vue-next'

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue'
import BaseConfirmModal from '@/shared/components/commons/BaseConfirmModal/BaseConfirmModal.vue'
import { useToast } from '@/shared/composables/useToast'
import { useAuthStore } from '@/shared/stores/auth.store'
import {
  obterLicencaEstaMaquina,
  desativarEstaMaquina,
} from '@/modules/license/services/transferencia.service'

const router = useRouter()
const toast = useToast()
const authStore = useAuthStore()

const { data: licenca, isLoading } = useQuery({
  queryKey: ['licenca-esta-maquina'],
  queryFn: obterLicencaEstaMaquina,
  staleTime: 60_000,
})

const confirmando = ref(false)
const desativando = ref(false)

function formatarData(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('pt-BR')
}

async function desativar() {
  desativando.value = true
  try {
    await desativarEstaMaquina()
    confirmando.value = false
    toast.success('Licença desativada neste computador. Já pode ativá-la no computador novo.')
    // Sem licença, este computador volta ao assistente de primeiro acesso.
    authStore.logoutUser()
    router.replace({ name: 'sign-in' })
  } catch (error) {
    const detail = axios.isAxiosError(error) ? error.response?.data?.detail : null
    toast.error(detail?.mensagem || 'Não foi possível desativar a licença. Nada foi alterado.')
  } finally {
    desativando.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h3 class="text-base font-bold text-zinc-900">Licença deste Computador</h3>
      <p class="text-sm text-zinc-500 mt-0.5">
        A licença da loja e como trocar o servidor de computador
      </p>
    </div>

    <!-- Situação -->
    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Licença</p>

      <div v-if="isLoading" class="bg-zinc-50 rounded-xl p-4 text-xs text-zinc-500">Carregando…</div>
      <div v-else-if="licenca" class="bg-zinc-50 rounded-xl p-4 flex flex-col gap-2.5">
        <div class="flex items-center justify-between">
          <span class="text-xs text-zinc-500">Situação</span>
          <span
            :class="[
              'text-xs font-semibold',
              licenca.ativada_nesta_maquina ? 'text-emerald-600' : 'text-amber-600',
            ]"
          >
            {{ licenca.ativada_nesta_maquina ? 'Ativada neste computador' : 'Ativada em outro computador' }}
          </span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-xs text-zinc-500">Computadores em uso</span>
          <span class="text-xs font-semibold text-zinc-700">
            {{ licenca.computadores_conectados }} de {{ licenca.limite_computadores }}
          </span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-xs text-zinc-500">Vencimento</span>
          <span class="text-xs font-semibold text-zinc-700">{{ formatarData(licenca.data_vencimento) }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-xs text-zinc-500">Última sincronização</span>
          <span class="text-xs font-semibold text-zinc-700">{{ formatarData(licenca.ultima_sincronizacao) }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-xs text-zinc-500">Código para o suporte</span>
          <span class="text-xs font-mono text-zinc-600">{{ licenca.licenca_id }} · {{ licenca.computador }}</span>
        </div>
      </div>
    </div>

    <!-- Passo a passo -->
    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Trocar o servidor de computador</p>

      <ol class="bg-white border border-zinc-200 rounded-xl p-4 text-xs text-zinc-700 list-decimal pl-8 space-y-1.5">
        <li>Faça um backup em <strong>Backup dos Dados</strong> e guarde uma cópia num pendrive.</li>
        <li>Clique em <strong>Desativar licença neste computador</strong>, abaixo. Isso libera a vaga.</li>
        <li>Feche o StartBig neste computador e em todos os caixas.</li>
        <li>No computador novo: instale o StartBig, escolha <strong>Servidor</strong> e restaure o backup (ou copie o banco de dados).</li>
        <li>Quando o sistema pedir, entre com a <strong>conta StartBig</strong>: a licença passa para lá.</li>
        <li>Nos caixas: <strong>Rede e Conexão</strong> › buscar o servidor novo.</li>
      </ol>

      <div class="bg-blue-50 border border-blue-100 rounded-xl p-3 text-xs text-blue-800 flex gap-2">
        <KeyRound :size="14" class="shrink-0 mt-0.5" />
        <span>
          Computador antigo quebrou ou não liga? Pule o passo 2: no computador novo, entrar com a conta
          StartBig já transfere a licença, e o e-mail da conta recebe um aviso.
        </span>
      </div>
    </div>

    <!-- Ação -->
    <div v-if="licenca?.ativada_nesta_maquina" class="border border-red-100 rounded-xl p-4 flex items-center justify-between gap-4">
      <div>
        <p class="text-sm font-semibold text-zinc-800">Desativar licença neste computador</p>
        <p class="text-xs text-zinc-500 mt-0.5">
          Este computador deixa de ser o servidor da loja. Os dados ficam guardados aqui.
        </p>
      </div>
      <BaseButton variant="danger" size="sm" @click="confirmando = true">
        <PowerOff :size="14" class="mr-1.5" />
        Desativar
      </BaseButton>
    </div>

    <BaseConfirmModal
      :is-open="confirmando"
      title="Desativar a licença neste computador?"
      description="O sistema vai parar de funcionar <strong>neste computador e em todos os caixas</strong> até a licença ser ativada no computador novo. Os dados não são apagados. Se for engano, basta entrar de novo com a conta StartBig."
      confirm-label="Desativar"
      is-danger
      overlay
      :is-loading="desativando"
      @confirm="desativar"
      @close="confirmando = false"
    />
  </div>
</template>
