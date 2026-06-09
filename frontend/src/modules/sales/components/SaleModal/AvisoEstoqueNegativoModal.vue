<script setup lang="ts">
import { computed } from 'vue'
import { AlertTriangle } from 'lucide-vue-next'
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue'

const props = defineProps<{
  isOpen: boolean
  nomeProduto: string
  estoqueAtual: number
  quantidadeDesejada: number
}>()

const emit = defineEmits<{
  (e: 'confirmar'): void;
  (e: 'cancelar'): void;
}>()

const estoqueApos = computed(() => props.estoqueAtual - props.quantidadeDesejada)

function handleConfirmar() { emit('confirmar') }
function handleCancelar() { emit('cancelar') }
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-9999 flex items-center justify-center bg-black/40 backdrop-blur-[2px] px-4"
        @click.self="handleCancelar"
      >
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 flex flex-col gap-5">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center shrink-0">
              <AlertTriangle :size="20" class="text-amber-600" />
            </div>
            <div>
              <h3 class="text-sm font-bold text-zinc-900">Estoque Insuficiente</h3>
              <p class="text-xs text-zinc-500 mt-0.5">Este produto ficará com estoque negativo</p>
            </div>
          </div>

          <div class="bg-amber-50 border border-amber-100 rounded-xl p-4 flex flex-col gap-2">
            <p class="text-sm font-semibold text-zinc-800 truncate">{{ nomeProduto }}</p>
            <div class="flex items-center justify-between text-xs text-zinc-600">
              <span>Estoque atual</span>
              <span class="font-semibold">{{ estoqueAtual }} unidade(s)</span>
            </div>
            <div class="flex items-center justify-between text-xs text-zinc-600">
              <span>Quantidade vendida</span>
              <span class="font-semibold">{{ quantidadeDesejada }} unidade(s)</span>
            </div>
            <div class="border-t border-amber-200 my-1" />
            <div class="flex items-center justify-between text-xs font-bold">
              <span class="text-zinc-700">Estoque após venda</span>
              <span :class="estoqueApos < 0 ? 'text-red-600' : 'text-zinc-700'">
                {{ estoqueApos }} unidade(s)
              </span>
            </div>
          </div>

          <p class="text-xs text-zinc-500 leading-relaxed">
            A configuração da empresa permite vender com estoque negativo. Você pode continuar ou cancelar e ajustar a quantidade.
          </p>

          <div class="flex gap-2 justify-end">
            <BaseButton variant="ghost" size="sm" @click="handleCancelar">
              Cancelar
            </BaseButton>
            <BaseButton variant="danger" size="sm" @click="handleConfirmar">
              Vender mesmo assim
            </BaseButton>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
