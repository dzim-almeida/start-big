<script setup lang="ts">
/**
 * @component PositionModal
 * @description Modal for creating/editing cargos with permission matrix
 */

import { computed, onMounted, onUnmounted, watch } from 'vue';
import { Check, X, XCircle } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';

import { usePositionModal } from '../composables/usePositionModal';
import { usePositionFormProvider } from '../composables/usePositionForm';
import { useDeletePositionMutation } from '../composables/usePositionsQuery';
import {
  PERMISSION_KEYS,
  PERMISSION_MATRIX,
  getAccessLevel,
  getPermissionStats,
} from '../constants/positions.constants';

const {
  isOpen,
  isCreateMode,
  isViewMode,
  modalTitle,
  closeModal,
  selectedPosition,
} = usePositionModal();

const {
  nome,
  permissoes,
  errors,
  submitCount,
  apiError,
  isPending,
  setPermission,
  setAllPermissions,
  onSubmit,
} = usePositionFormProvider();

const deleteMutation = useDeletePositionMutation();

const totalPermissions = computed(() => PERMISSION_KEYS.length);
const permissionStats = computed(() => getPermissionStats(permissoes.value));
const enabledPermissions = computed(() => permissionStats.value.enabled);
const accessLevel = computed(() => getAccessLevel(permissoes.value));

const isAllSelected = computed(
  () => enabledPermissions.value === totalPermissions.value && totalPermissions.value > 0,
);

function togglePermission(key: string) {
  if (isViewMode.value) return;
  const currentValue = !!permissoes.value?.[key];
  setPermission(key, !currentValue);
}

function toggleAllPermissions() {
  if (isViewMode.value) return;
  setAllPermissions(!isAllSelected.value);
}

function handleDelete() {
  if (!selectedPosition.value) return;
  const confirmed = window.confirm(
    `Tem certeza que deseja excluir o cargo "${selectedPosition.value.nome}"?`,
  );
  if (!confirmed) return;

  deleteMutation.mutate(selectedPosition.value.id, {
    onSuccess: () => {
      closeModal();
    },
  });
}

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
            class="flex w-full max-w-6xl max-h-[90vh] flex-col overflow-hidden rounded-2xl bg-white shadow-2xl mx-4"
          >
            <div class="flex items-center justify-between border-b border-zinc-200 px-6 py-4">
              <div>
                <h2 class="text-xl font-bold text-zinc-800">{{ modalTitle }}</h2>
              </div>
              <button
                type="button"
                class="rounded-lg p-2 text-zinc-400 transition-colors hover:bg-red-50 hover:text-red-600 cursor-pointer"
                @click="closeModal"
              >
                <X :size="20" />
              </button>
            </div>

            <div class="flex-1 overflow-y-auto px-6 py-6">
              <div
                v-if="apiError"
                class="mb-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"
              >
                {{ apiError }}
              </div>

              <form id="position-form" class="grid grid-cols-1 gap-6 lg:grid-cols-[320px_1fr]" @submit.prevent="onSubmit">
                <div class="space-y-6">
                  <div class="rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm">
                    <h3 class="text-sm font-semibold text-zinc-800">Informacoes Gerais</h3>
                    <p class="mt-1 text-xs text-zinc-400">
                      Defina o nome do cargo e o escopo principal.
                    </p>
                    <div class="mt-5">
                      <BaseInput
                        v-model="nome"
                        label="Nome do cargo"
                        placeholder="Ex: Gerente de Vendas"
                        :required="true"
                        :error="submitCount > 0 ? errors.nome : ''"
                        :disabled="isViewMode"
                      />
                    </div>
                    <div class="mt-4 rounded-xl border border-dashed border-zinc-200 bg-zinc-50 p-3">
                      <p class="text-[10px] font-semibold uppercase text-zinc-400">Resumo</p>
                      <div class="mt-2 text-xs text-zinc-600">
                        {{ enabledPermissions }} de {{ totalPermissions }} permissoes habilitadas
                      </div>
                    </div>
                  </div>

                  <div
                    class="rounded-2xl bg-linear-to-br p-5 text-white shadow-lg"
                    :class="accessLevel.gradient"
                  >
                    <div class="flex items-center justify-between">
                      <div class="text-sm font-semibold">Nivel de Acesso</div>
                      <span class="rounded-full bg-white/20 px-3 py-1 text-[10px] font-semibold uppercase tracking-widest">
                        {{ accessLevel.badge }}
                      </span>
                    </div>
                    <h4 class="mt-3 text-xl font-bold">{{ accessLevel.label }}</h4>
                    <p class="mt-2 text-sm text-white/80">
                      {{ accessLevel.description }}
                    </p>
                    <div class="mt-4 text-xs text-white/70">
                      Cobertura geral: {{ enabledPermissions }} / {{ totalPermissions }}
                    </div>
                  </div>
                </div>

                <div class="rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm">
                  <div class="flex items-center justify-between">
                    <div>
                      <h3 class="text-sm font-semibold text-zinc-800">Matriz de Permissoes</h3>
                      <p class="mt-1 text-xs text-zinc-400">
                        Defina o que este cargo pode visualizar, editar e excluir.
                      </p>
                    </div>
                    <button
                      type="button"
                      class="text-xs font-semibold text-brand-primary hover:text-brand-primary/80"
                      @click="toggleAllPermissions"
                    >
                      {{ isAllSelected ? 'Desmarcar tudo' : 'Marcar tudo' }}
                    </button>
                  </div>

                  <div class="mt-6 overflow-hidden rounded-xl border border-zinc-100">
                    <div class="grid grid-cols-[1fr_88px_88px_88px] items-center bg-zinc-50 px-4 py-3 text-[10px] font-semibold uppercase tracking-widest text-zinc-400">
                      <span>Modulo</span>
                      <span class="text-center">Visualizar</span>
                      <span class="text-center">Editar/Criar</span>
                      <span class="text-center">Excluir</span>
                    </div>

                    <div
                      v-for="item in PERMISSION_MATRIX"
                      :key="item.id"
                      class="grid grid-cols-[1fr_88px_88px_88px] items-center border-t border-zinc-100 px-4 py-3"
                    >
                      <div class="flex items-center gap-3">
                        <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-zinc-50 text-zinc-600">
                          <component :is="item.icon" :size="18" />
                        </div>
                        <div>
                          <p class="text-sm font-semibold text-zinc-800">{{ item.label }}</p>
                          <p class="text-xs text-zinc-400">{{ item.description }}</p>
                        </div>
                      </div>

                      <div class="flex items-center justify-center">
                        <button
                          type="button"
                          :disabled="isViewMode"
                          :class="[
                            'flex h-9 w-9 items-center justify-center rounded-full border transition-all',
                            permissoes?.[item.viewKey]
                              ? 'border-emerald-200 bg-emerald-50 text-emerald-600'
                              : 'border-zinc-200 bg-zinc-50 text-zinc-400',
                            isViewMode ? 'cursor-not-allowed opacity-60' : 'hover:border-emerald-300',
                          ]"
                          @click="togglePermission(item.viewKey)"
                        >
                          <Check v-if="permissoes?.[item.viewKey]" :size="16" />
                          <XCircle v-else :size="16" />
                        </button>
                      </div>

                      <div class="flex items-center justify-center">
                        <button
                          type="button"
                          :disabled="isViewMode"
                          :class="[
                            'flex h-9 w-9 items-center justify-center rounded-full border transition-all',
                            permissoes?.[item.manageKey]
                              ? 'border-emerald-200 bg-emerald-50 text-emerald-600'
                              : 'border-zinc-200 bg-zinc-50 text-zinc-400',
                            isViewMode ? 'cursor-not-allowed opacity-60' : 'hover:border-emerald-300',
                          ]"
                          @click="togglePermission(item.manageKey)"
                        >
                          <Check v-if="permissoes?.[item.manageKey]" :size="16" />
                          <XCircle v-else :size="16" />
                        </button>
                      </div>

                      <div class="flex items-center justify-center">
                        <button
                          type="button"
                          :disabled="isViewMode"
                          :class="[
                            'flex h-9 w-9 items-center justify-center rounded-full border transition-all',
                            permissoes?.[item.deleteKey]
                              ? 'border-emerald-200 bg-emerald-50 text-emerald-600'
                              : 'border-zinc-200 bg-zinc-50 text-zinc-400',
                            isViewMode ? 'cursor-not-allowed opacity-60' : 'hover:border-emerald-300',
                          ]"
                          @click="togglePermission(item.deleteKey)"
                        >
                          <Check v-if="permissoes?.[item.deleteKey]" :size="16" />
                          <XCircle v-else :size="16" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </form>
            </div>

            <div class="flex flex-col gap-3 border-t border-zinc-200 bg-zinc-50 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <BaseButton
                  v-if="!isCreateMode && !isViewMode"
                  type="button"
                  variant="danger"
                  :disabled="deleteMutation.isPending.value"
                  @click="handleDelete"
                >
                  Excluir Cargo
                </BaseButton>
              </div>
              <div class="flex items-center justify-end gap-3">
                <BaseButton
                  type="button"
                  variant="secondary"
                  @click="closeModal"
                >
                  {{ isViewMode ? 'Fechar' : 'Descartar Alteracoes' }}
                </BaseButton>
                <BaseButton
                  v-if="!isViewMode"
                  type="submit"
                  variant="primary"
                  :is-loading="isPending"
                  @click="onSubmit"
                >
                  {{ isCreateMode ? 'Salvar Cargo' : 'Atualizar Cargo' }}
                </BaseButton>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
