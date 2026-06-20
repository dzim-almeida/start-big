<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { Eye, EyeOff, ShieldCheck, ShieldOff } from 'lucide-vue-next'

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue'
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue'
import { useToast } from '@/shared/composables/useToast'
import { PinGerenteSchema } from '../schemas/configuracoes.schema'
import { updateConfiguracoesSeguranca, verificarPinSeguranca } from '../services/configuracoes.service'
import type { ConfiguracaoSegurancaRead } from '../schemas/configuracoes.schema'

export type ModoPinGerente = 'definir' | 'alterar' | 'remover'

const props = defineProps<{ isOpen: boolean; modo: ModoPinGerente }>()
const emit = defineEmits<{ close: []; sucesso: [config: ConfiguracaoSegurancaRead] }>()

const toast = useToast()

const pinAtual = ref('')
const pinNovo = ref('')
const pinConfirmacao = ref('')
const erros = reactive({ atual: '', novo: '', confirmacao: '' })
const show = reactive({ atual: false, novo: false, confirmacao: false })
const isLoading = ref(false)

const titulo = computed(() => {
  if (props.modo === 'definir') return 'Definir PIN do Gerente'
  if (props.modo === 'alterar') return 'Alterar PIN do Gerente'
  return 'Remover PIN do Gerente'
})

const pedePinAtual = computed(() => props.modo !== 'definir')
const pedePinNovo = computed(() => props.modo !== 'remover')

function limpar() {
  pinAtual.value = ''
  pinNovo.value = ''
  pinConfirmacao.value = ''
  erros.atual = ''
  erros.novo = ''
  erros.confirmacao = ''
  show.atual = false
  show.novo = false
  show.confirmacao = false
}

watch(() => props.isOpen, (aberto) => {
  if (aberto) limpar()
})

// Limpa o erro assim que o usuário volta a digitar
watch(pinAtual, () => { erros.atual = '' })
watch(pinNovo, () => { erros.novo = '' })
watch(pinConfirmacao, () => { erros.confirmacao = '' })

function validar(): boolean {
  erros.atual = ''
  erros.novo = ''
  erros.confirmacao = ''

  if (pedePinAtual.value && !pinAtual.value) {
    erros.atual = 'Informe o PIN atual'
  }
  if (pedePinNovo.value) {
    const parsed = PinGerenteSchema.safeParse(pinNovo.value)
    if (!parsed.success) erros.novo = parsed.error.issues[0].message
    if (pinConfirmacao.value !== pinNovo.value) erros.confirmacao = 'Os PINs não coincidem'
  }
  return !erros.atual && !erros.novo && !erros.confirmacao
}

async function salvar(): Promise<void> {
  if (!validar()) return
  isLoading.value = true
  try {
    if (pedePinAtual.value) {
      try {
        await verificarPinSeguranca(pinAtual.value)
      } catch (error: any) {
        if (error?.response?.data?.detail === 'PIN_GERENTE_INVALIDO') {
          erros.atual = 'PIN atual incorreto'
          return
        }
        throw error
      }
    }

    // PIN vazio = remover; preenchido = definir/alterar
    const config = await updateConfiguracoesSeguranca({
      pin_gerente: props.modo === 'remover' ? '' : pinNovo.value,
    })

    if (props.modo === 'definir') toast.success('PIN do gerente definido com sucesso!')
    if (props.modo === 'alterar') toast.success('PIN do gerente atualizado com sucesso!')
    if (props.modo === 'remover') toast.success('PIN do gerente removido.')

    emit('sucesso', config)
    emit('close')
  } catch {
    toast.error('Erro ao salvar o PIN. Tente novamente.')
  } finally {
    isLoading.value = false
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') salvar()
  if (e.key === 'Escape') emit('close')
}
</script>

<template>
  <BaseModal :is-open="isOpen" :title="titulo" size="sm" overlay @close="emit('close')">
    <div class="flex flex-col gap-4" @keydown="handleKeydown">
      <div
        :class="[
          'flex items-start gap-3 p-3 border rounded-xl',
          modo === 'remover' ? 'bg-red-50 border-red-100 text-red-700' : 'bg-blue-50 border-blue-100 text-blue-700',
        ]"
      >
        <component :is="modo === 'remover' ? ShieldOff : ShieldCheck" :size="18" class="shrink-0 mt-0.5" />
        <p class="text-sm leading-snug">
          <template v-if="modo === 'remover'">
            Sem o PIN, as ações de aprovação e as seções protegidas deixam de exigir autorização do gerente.
          </template>
          <template v-else>
            O PIN será exigido nas ações de aprovação e nas seções protegidas configuradas. Use de 4 a 6 dígitos numéricos.
          </template>
        </p>
      </div>

      <div v-if="pedePinAtual">
        <label class="text-xs font-medium text-zinc-600">PIN atual</label>
        <div class="relative mt-1.5">
          <input
            v-model="pinAtual"
            :type="show.atual ? 'text' : 'password'"
            placeholder="Digite o PIN atual..."
            inputmode="numeric"
            maxlength="6"
            autocomplete="current-password"
            :class="[
              'w-full border rounded-lg px-3 py-2.5 pr-10 bg-zinc-50 text-sm text-zinc-700 focus:outline-none focus:ring-2',
              erros.atual ? 'border-red-300 focus:ring-red-200' : 'border-zinc-200 focus:ring-brand-primary/30',
            ]"
          />
          <button
            type="button"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600"
            @click="show.atual = !show.atual"
          >
            <component :is="show.atual ? EyeOff : Eye" :size="15" />
          </button>
        </div>
        <p v-if="erros.atual" class="text-xs text-red-500 mt-1">{{ erros.atual }}</p>
      </div>

      <div v-if="pedePinNovo">
        <label class="text-xs font-medium text-zinc-600">Novo PIN</label>
        <div class="relative mt-1.5">
          <input
            v-model="pinNovo"
            :type="show.novo ? 'text' : 'password'"
            placeholder="Digite o novo PIN..."
            inputmode="numeric"
            maxlength="6"
            autocomplete="new-password"
            :class="[
              'w-full border rounded-lg px-3 py-2.5 pr-10 bg-zinc-50 text-sm text-zinc-700 focus:outline-none focus:ring-2',
              erros.novo ? 'border-red-300 focus:ring-red-200' : 'border-zinc-200 focus:ring-brand-primary/30',
            ]"
          />
          <button
            type="button"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600"
            @click="show.novo = !show.novo"
          >
            <component :is="show.novo ? EyeOff : Eye" :size="15" />
          </button>
        </div>
        <p v-if="erros.novo" class="text-xs text-red-500 mt-1">{{ erros.novo }}</p>
      </div>

      <div v-if="pedePinNovo">
        <label class="text-xs font-medium text-zinc-600">Confirmar novo PIN</label>
        <div class="relative mt-1.5">
          <input
            v-model="pinConfirmacao"
            :type="show.confirmacao ? 'text' : 'password'"
            placeholder="Digite o PIN novamente..."
            inputmode="numeric"
            maxlength="6"
            autocomplete="new-password"
            :class="[
              'w-full border rounded-lg px-3 py-2.5 pr-10 bg-zinc-50 text-sm text-zinc-700 focus:outline-none focus:ring-2',
              erros.confirmacao ? 'border-red-300 focus:ring-red-200' : 'border-zinc-200 focus:ring-brand-primary/30',
            ]"
          />
          <button
            type="button"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600"
            @click="show.confirmacao = !show.confirmacao"
          >
            <component :is="show.confirmacao ? EyeOff : Eye" :size="15" />
          </button>
        </div>
        <p v-if="erros.confirmacao" class="text-xs text-red-500 mt-1">{{ erros.confirmacao }}</p>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2 w-full">
        <BaseButton variant="ghost" size="sm" :disabled="isLoading" @click="emit('close')">
          Cancelar
        </BaseButton>
        <BaseButton
          variant="primary"
          size="sm"
          :class="modo === 'remover' ? 'bg-red-500 hover:bg-red-600 border-red-500 text-white' : ''"
          :is-loading="isLoading"
          @click="salvar"
        >
          {{ modo === 'remover' ? 'Remover PIN' : 'Salvar PIN' }}
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
