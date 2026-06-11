<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { Eye, EyeOff } from 'lucide-vue-next'
import { storeToRefs } from 'pinia'
import { useConfiguracoesStore } from '@/shared/stores/configuracoes.store'

const configStore = useConfiguracoesStore()
const {
  requerPinDescontoVenda,
  requerPinAlterarPreco,
  requerPinCancelarVenda,
  requerPinReabrirVenda,
  requerPinCancelarOS,
  requerPinReabrirOS,
  requerPinAcessarConfigSensivel,
  temPinConfigurado,
} = storeToRefs(configStore)

const showPin = ref(false)

const form = reactive({
  pin_gerente: '' as string,
  requer_pin_acessar_config_sensivel: requerPinAcessarConfigSensivel.value,
  requer_pin_desconto_venda: requerPinDescontoVenda.value,
  requer_pin_alterar_preco_venda: requerPinAlterarPreco.value,
  requer_pin_cancelar_venda: requerPinCancelarVenda.value,
  requer_pin_reabrir_venda: requerPinReabrirVenda.value,
  requer_pin_cancelar_os: requerPinCancelarOS.value,
  requer_pin_reabrir_os: requerPinReabrirOS.value,
})

watch(() => configStore.configSeguranca, () => {
  form.pin_gerente = ''
  form.requer_pin_acessar_config_sensivel = requerPinAcessarConfigSensivel.value
  form.requer_pin_desconto_venda = requerPinDescontoVenda.value
  form.requer_pin_alterar_preco_venda = requerPinAlterarPreco.value
  form.requer_pin_cancelar_venda = requerPinCancelarVenda.value
  form.requer_pin_reabrir_venda = requerPinReabrirVenda.value
  form.requer_pin_cancelar_os = requerPinCancelarOS.value
  form.requer_pin_reabrir_os = requerPinReabrirOS.value
})

defineExpose({
  get form() {
    return {
      ...(form.pin_gerente ? { pin_gerente: form.pin_gerente } : {}),
      requer_pin_acessar_config_sensivel: form.requer_pin_acessar_config_sensivel,
      requer_pin_desconto_venda: form.requer_pin_desconto_venda,
      requer_pin_alterar_preco_venda: form.requer_pin_alterar_preco_venda,
      requer_pin_cancelar_venda: form.requer_pin_cancelar_venda,
      requer_pin_reabrir_venda: form.requer_pin_reabrir_venda,
      requer_pin_cancelar_os: form.requer_pin_cancelar_os,
      requer_pin_reabrir_os: form.requer_pin_reabrir_os,
    }
  },
})
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h3 class="text-base font-bold text-zinc-900">Segurança</h3>
      <p class="text-sm text-zinc-500 mt-0.5">Configure o PIN do gerente e defina quais ações exigem aprovação</p>
    </div>

    <!-- PIN do Gerente -->
    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">PIN do Gerente</p>

      <div class="py-3 border-b border-zinc-100">
        <div class="flex items-center justify-between mb-0.5">
          <label class="text-xs font-medium text-zinc-600">PIN de aprovação</label>
          <span v-if="temPinConfigurado" class="text-[10px] font-semibold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded-full">
            ✓ Configurado
          </span>
          <span v-else class="text-[10px] text-zinc-400 bg-zinc-100 px-1.5 py-0.5 rounded-full">
            Não configurado
          </span>
        </div>
        <p class="text-[11px] text-zinc-400 mt-0.5 mb-1.5">Deixe em branco para manter o PIN atual</p>
        <div class="relative">
          <input
            v-model="form.pin_gerente"
            :type="showPin ? 'text' : 'password'"
            placeholder="Novo PIN..."
            class="w-full border border-zinc-200 rounded-lg px-3 py-2.5 pr-10 bg-zinc-50 text-sm text-zinc-700 focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
          />
          <button
            type="button"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600"
            @click="showPin = !showPin"
          >
            <component :is="showPin ? EyeOff : Eye" :size="15" />
          </button>
        </div>
      </div>
    </div>

    <!-- Configurações -->
    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Configurações Gerais</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Proteger seções sensíveis</p>
          <p class="text-xs text-zinc-500 mt-0.5">Exige PIN para acessar Segurança, Financeiro e Regras de Vendas</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.requer_pin_acessar_config_sensivel ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.requer_pin_acessar_config_sensivel = !form.requer_pin_acessar_config_sensivel"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.requer_pin_acessar_config_sensivel ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>
    </div>

    <!-- Vendas -->
    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Vendas</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Desconto acima do limite</p>
          <p class="text-xs text-zinc-500 mt-0.5">Pede PIN quando o desconto ultrapassar o máximo configurado</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.requer_pin_desconto_venda ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.requer_pin_desconto_venda = !form.requer_pin_desconto_venda"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.requer_pin_desconto_venda ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Alterar preço de produto cadastrado</p>
          <p class="text-xs text-zinc-500 mt-0.5">OFF = bloqueado; ON = permite com PIN do gerente</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.requer_pin_alterar_preco_venda ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.requer_pin_alterar_preco_venda = !form.requer_pin_alterar_preco_venda"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.requer_pin_alterar_preco_venda ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Cancelar venda finalizada</p>
          <p class="text-xs text-zinc-500 mt-0.5">Exige PIN para cancelar uma venda já finalizada</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.requer_pin_cancelar_venda ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.requer_pin_cancelar_venda = !form.requer_pin_cancelar_venda"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.requer_pin_cancelar_venda ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Reabrir venda cancelada</p>
          <p class="text-xs text-zinc-500 mt-0.5">Exige PIN para reabrir uma venda cancelada</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.requer_pin_reabrir_venda ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.requer_pin_reabrir_venda = !form.requer_pin_reabrir_venda"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.requer_pin_reabrir_venda ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>
    </div>

    <!-- Ordens de Serviço -->
    <div class="flex flex-col">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3">Ordens de Serviço</p>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Cancelar OS</p>
          <p class="text-xs text-zinc-500 mt-0.5">Exige PIN para cancelar uma ordem de serviço</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.requer_pin_cancelar_os ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.requer_pin_cancelar_os = !form.requer_pin_cancelar_os"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.requer_pin_cancelar_os ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>

      <div class="flex items-center justify-between py-3 border-b border-zinc-100">
        <div>
          <p class="text-sm font-medium text-zinc-800">Reabrir OS finalizada ou cancelada</p>
          <p class="text-xs text-zinc-500 mt-0.5">Exige PIN para reabrir uma OS</p>
        </div>
        <button
          type="button"
          :class="['relative w-9 h-4.5 rounded-full transition-colors duration-200 cursor-pointer shrink-0', form.requer_pin_reabrir_os ? 'bg-brand-primary' : 'bg-zinc-200']"
          @click="form.requer_pin_reabrir_os = !form.requer_pin_reabrir_os"
        >
          <span :class="['absolute left-0 top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow transition-transform duration-200', form.requer_pin_reabrir_os ? 'translate-x-5' : 'translate-x-0.5']" />
        </button>
      </div>
    </div>
  </div>
</template>
