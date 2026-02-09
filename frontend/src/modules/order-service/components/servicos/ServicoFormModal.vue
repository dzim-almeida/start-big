<script setup lang="ts">
import { watch, onMounted, onUnmounted } from 'vue';
import { X } from 'lucide-vue-next';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { useServicoModal } from '../../composables/useServicoModal';
import { useServicoFormProvider } from '../../composables/useServicoForm';
import ServicoDadosSection from './form/ServicoDadosSection.vue';

const { isOpen, isCreateMode, isViewMode, modalTitle, closeModal } = useServicoModal();
const { onSubmit, isPending, apiError } = useServicoFormProvider();

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && isOpen.value) {
    closeModal();
  }
}

function handleBackdropClick(event: MouseEvent) {
  if ((event.target as HTMLElement).classList.contains('modal-backdrop')) {
    closeModal();
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown);
});

watch(isOpen, (open) => {
  document.body.style.overflow = open ? 'hidden' : '';
});
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition ease-out duration-300"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition ease-in duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen"
        class="modal-backdrop fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
        @click="handleBackdropClick"
      >
        <Transition
          enter-active-class="transition ease-out duration-300"
          enter-from-class="opacity-0 scale-95 translate-y-4"
          enter-to-class="opacity-100 scale-100 translate-y-0"
          leave-active-class="transition ease-in duration-200"
          leave-from-class="opacity-100 scale-100 translate-y-0"
          leave-to-class="opacity-0 scale-95 translate-y-4"
        >
          <div
            v-if="isOpen"
            class="bg-white rounded-2xl shadow-2xl w-full max-w-xl max-h-[90vh] overflow-hidden flex flex-col mx-4"
          >
            <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-200">
              <h2 class="text-xl font-bold text-zinc-800">
                {{ modalTitle }}
              </h2>
              <button
                type="button"
                class="p-2 text-zinc-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
                @click="closeModal"
              >
                <X :size="20" />
              </button>
            </div>

            <div class="flex-1 overflow-y-auto px-6 py-6">
              <div
                v-if="apiError"
                class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm"
              >
                {{ apiError }}
              </div>

              <form id="servico-form" @submit.prevent="onSubmit" class="space-y-6">
                <ServicoDadosSection :disabled="isViewMode" />
              </form>
            </div>

            <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-zinc-200 bg-zinc-50">
              <BaseButton
                type="button"
                variant="secondary"
                @click="closeModal"
              >
                {{ isViewMode ? 'Fechar' : 'Cancelar' }}
              </BaseButton>
              <BaseButton
                v-if="!isViewMode"
                type="submit"
                variant="primary"
                :is-loading="isPending"
                @click="onSubmit"
              >
                {{ isCreateMode ? 'Cadastrar Serviço' : 'Salvar Alterações' }}
              </BaseButton>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
