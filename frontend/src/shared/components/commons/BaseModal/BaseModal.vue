<script lang="ts">
// Contador global de modais abertos para gerenciar overflow do body
let openModalCount = 0;
</script>

<script setup lang="ts">
import { watch, onUnmounted } from 'vue';
import { X } from 'lucide-vue-next';

interface Props {
  isOpen: boolean;
  title: string;
  subtitle?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl';
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
});

const emit = defineEmits<{
  close: [];
}>();

const sizeClasses = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
  '2xl': 'max-w-6xl',
  '3xl': 'max-w-7xl',
  '4xl': 'max-w-[90rem]',
};

function handleClose() {
  emit('close');
}

// Gerenciar overflow do body com contador global (suporte a modais aninhados)
let wasOpen = false;

watch(
  () => props.isOpen,
  (isOpen) => {
    if (isOpen && !wasOpen) {
      openModalCount++;
      document.body.style.overflow = 'hidden';
      wasOpen = true;
    } else if (!isOpen && wasOpen) {
      openModalCount = Math.max(0, openModalCount - 1);
      if (openModalCount === 0) {
        document.body.style.overflow = '';
      }
      wasOpen = false;
    }
  }
);

onUnmounted(() => {
  if (wasOpen) {
    openModalCount = Math.max(0, openModalCount - 1);
    if (openModalCount === 0) {
      document.body.style.overflow = '';
    }
    wasOpen = false;
  }
});
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        <!-- Backdrop - clique aqui fecha o modal -->
        <div
          class="absolute inset-0 bg-black/50 backdrop-blur-sm"
          @click="handleClose"
        />

        <!-- Modal Content -->
        <div
          :class="[
            'relative w-full bg-white rounded-2xl shadow-2xl transform transition-all z-10 flex flex-col max-h-[95vh]',
            sizeClasses[size],
          ]"
          @click.stop
        >
          <!-- Header -->
          <div v-if="$slots.header" class="shrink-0">
             <slot name="header" :close="handleClose" />
          </div>
          <div v-else class="flex items-start justify-between p-6 border-b border-zinc-100 shrink-0">
            <div>
              <h2 class="text-lg font-bold text-zinc-900">{{ title }}</h2>
              <p v-if="subtitle" class="text-sm text-zinc-500 mt-0.5">{{ subtitle }}</p>
            </div>
            <button
              type="button"
              class="p-2 -m-2 text-zinc-400 hover:text-red-500 hover:bg-zinc-100 rounded-lg transition-colors cursor-pointer"
              @click="handleClose"
            >
              <X :size="20" />
            </button>
          </div>

          <!-- Body -->
          <div class="p-6 overflow-y-auto flex-initial min-h-0">
            <slot />
          </div>

          <!-- Footer -->
          <div v-if="$slots.footer" class="p-6 border-t border-zinc-100 bg-zinc-50 rounded-b-2xl shrink-0">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-active > div:last-child,
.modal-leave-active > div:last-child {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from > div:last-child,
.modal-leave-to > div:last-child {
  transform: scale(0.95);
  opacity: 0;
}
</style>
