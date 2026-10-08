<script setup lang="ts">
/**
 * @component ProductModal
 * @description Modal for creating/editing products with multi-section form and image upload
 */

import { defineAsyncComponent, ref, watch, onMounted, onUnmounted } from 'vue';
import { X } from 'lucide-vue-next';

import { useProductModal } from '../composables/useProductModal';
import { useProductFormProvider } from '../composables/useProductForm';
import { recursoDisponivel } from '@/shared/config/planos';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import DadosProdutoSection from './form/DadosProdutoSection.vue';
import DadosEstoqueSection from './form/DadosEstoqueSection.vue';
import DadosFiscaisSection from './form/DadosFiscaisSection.vue';
import EmbalagensSection from './form/EmbalagensSection.vue';
import RegrasPrecoSection from './form/RegrasPrecoSection.vue';
import { storeToRefs } from 'pinia';
import { useConfiguracoesStore } from '@/shared/stores/configuracoes.store';
import { useAcessoCompras } from '@/modules/compras/shared/composables/useAcessoCompras';
import { useSegmento } from '@/shared/composables/useSegmento';

const nfeDisponivel = recursoDisponivel('nfe');

// Fornecedores do produto: módulo Compras (contratável). Carregado sob demanda
// para que o código do módulo nem chegue a quem não o tem.
const { podeVer: comprasDisponivel } = useAcessoCompras();
const FornecedoresProdutoSection = defineAsyncComponent(
  () => import('@/modules/compras/fornecedores-produto/components/FornecedoresProdutoSection.vue'),
);

// Insumo da fábrica (chapa em m², fita em metro): só na marcenaria. Sob
// demanda, como os fornecedores — os outros segmentos nem baixam o código.
const { isMarcenaria } = useSegmento();
const InsumoProdutoSection = defineAsyncComponent(
  () => import('@/modules/order-service/fabrica/components/InsumoProdutoSection.vue'),
);

// =============================================
// Modal State
// =============================================

const {
  isOpen,
  isCreateMode,
  isViewMode,
  modalTitle,
  closeModal,
  selectedProduct,
} = useProductModal();

// Embalagens (fardo/caixa) só aparecem com a chave ligada em Configurações:
// para quem não usa, o cadastro fica exatamente como sempre foi.
const { usarEmbalagens, regraFaixasQuantidade, regraLevePague } = storeToRefs(useConfiguracoesStore());

const { onSubmit, isPending, submitCount, apiError, fornecedor_id } = useProductFormProvider();

/** A aba Fornecedores trocou o principal: o formulário passa a mandar o novo. */
function aoTrocarPrincipal(fornecedorId: number) {
  fornecedor_id.value = String(fornecedorId);
}

// =============================================
// Event Handlers
// =============================================

/**
 * Handle ESC key to close modal
 */
function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && isOpen.value) {
    closeModal();
  }
}

/**
 * Handle backdrop click to close modal
 */
const gestoComecouNoFundo = ref(false);

function handleBackdropMousedown(event: MouseEvent) {
  gestoComecouNoFundo.value = (event.target as HTMLElement).classList.contains('modal-backdrop');
}

/**
 * Fecha ao clicar no fundo — mas só quando o clique COMEÇOU no fundo.
 *
 * Decidir pelo `click` fechava o modal no meio da edição: ao arrastar o mouse
 * para selecionar o texto de um campo e soltar fora dele, o navegador dispara o
 * `click` no ancestral comum entre onde apertou e onde soltou — o próprio
 * backdrop. Só acontecia com o mouse; com teclado nunca.
 */
function handleBackdropClick(event: MouseEvent) {
  const terminouNoFundo = (event.target as HTMLElement).classList.contains('modal-backdrop');
  if (gestoComecouNoFundo.value && terminouNoFundo) {
    closeModal();
  }
  gestoComecouNoFundo.value = false;
}

// =============================================
// Lifecycle
// =============================================

onMounted(() => {
  document.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown);
});

// Prevent body scroll when modal is open
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
        @mousedown="handleBackdropMousedown"
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
            class="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col mx-4"
          >
            <!-- Header -->
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

            <!-- Body (scrollable) -->
            <div class="flex-1 overflow-y-auto px-6 py-6">
              <!-- API Error Alert -->
              <div
                v-if="apiError"
                class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm"
              >
                {{ apiError }}
              </div>

              <form id="product-form" @submit.prevent="onSubmit" class="space-y-8">
                <DadosProdutoSection
                  :submit-count="submitCount"
                  :disabled="isViewMode"
                />

                <!-- Divider -->
                <div class="relative">
                  <div class="absolute inset-0 flex items-center">
                    <div class="w-full border-t border-zinc-200"></div>
                  </div>
                  <div class="relative flex justify-center">
                    <span
                      class="px-4 bg-white text-xs font-medium text-zinc-500 uppercase tracking-wider"
                    >
                      Dados de Estoque
                    </span>
                  </div>
                </div>

                <!-- Stock & Pricing Data -->
                <DadosEstoqueSection
                  :submit-count="submitCount"
                  :disabled="isViewMode"
                  :is-create-mode="isCreateMode"
                />

                <!-- Dados Fiscais — visível apenas para licenças com módulo fiscal ativo -->
                <template v-if="nfeDisponivel">
                  <!-- Divider -->
                  <div class="relative">
                    <div class="absolute inset-0 flex items-center">
                      <div class="w-full border-t border-zinc-200"></div>
                    </div>
                    <div class="relative flex justify-center">
                      <span
                        class="px-4 bg-white text-xs font-medium text-zinc-500 uppercase tracking-wider"
                      >
                        Dados Fiscais
                      </span>
                    </div>
                  </div>

                  <DadosFiscaisSection
                    :submit-count="submitCount"
                    :disabled="isViewMode"
                  />
                </template>
              </form>

              <!--
                Fora do <form> de propósito: tem o próprio "Salvar" (rota
                separada), e Enter num campo daqui não pode salvar o produto.
              -->
              <template v-if="usarEmbalagens">
                <div class="relative mt-8 mb-6">
                  <div class="absolute inset-0 flex items-center">
                    <div class="w-full border-t border-zinc-200"></div>
                  </div>
                  <div class="relative flex justify-center">
                    <span class="px-4 bg-white text-xs font-medium text-zinc-500 uppercase tracking-wider">
                      Embalagens (fardo, caixa)
                    </span>
                  </div>
                </div>
                <EmbalagensSection
                  :produto="isCreateMode ? null : selectedProduct"
                  :disabled="isViewMode"
                />
              </template>

              <!-- Fornecedores do produto (módulo Compras): só com o módulo na
                   licença e a linha "Compras" no cargo. Fora do <form> pelo
                   mesmo motivo das embalagens: tem o próprio "Salvar". -->
              <template v-if="comprasDisponivel">
                <div class="relative mt-8 mb-6">
                  <div class="absolute inset-0 flex items-center">
                    <div class="w-full border-t border-zinc-200"></div>
                  </div>
                  <div class="relative flex justify-center">
                    <span class="px-4 bg-white text-xs font-medium text-zinc-500 uppercase tracking-wider">
                      Fornecedores (compras)
                    </span>
                  </div>
                </div>
                <FornecedoresProdutoSection
                  :produto="isCreateMode ? null : selectedProduct"
                  :disabled="isViewMode"
                  @principal-alterado="aoTrocarPrincipal"
                />
              </template>

              <!-- Insumo da fábrica (marcenaria): como o orçamento por móvel
                   consome o produto. Fora do <form>, "Salvar" próprio. -->
              <template v-if="isMarcenaria">
                <div class="relative mt-8 mb-6">
                  <div class="absolute inset-0 flex items-center">
                    <div class="w-full border-t border-zinc-200"></div>
                  </div>
                  <div class="relative flex justify-center">
                    <span class="px-4 bg-white text-xs font-medium text-zinc-500 uppercase tracking-wider">
                      Insumo da fábrica
                    </span>
                  </div>
                </div>
                <InsumoProdutoSection
                  :produto="isCreateMode ? null : selectedProduct"
                  :disabled="isViewMode"
                />
              </template>

              <!-- Regras de preço por quantidade (R2/R3, §6.1): só com a chave
                   de alguma delas ligada em Regras de Vendas. Mesmo motivo de
                   ficar fora do <form> que as embalagens. -->
              <template v-if="regraFaixasQuantidade || regraLevePague">
                <div class="relative mt-8 mb-6">
                  <div class="absolute inset-0 flex items-center">
                    <div class="w-full border-t border-zinc-200"></div>
                  </div>
                  <div class="relative flex justify-center">
                    <span class="px-4 bg-white text-xs font-medium text-zinc-500 uppercase tracking-wider">
                      Preço por quantidade
                    </span>
                  </div>
                </div>
                <RegrasPrecoSection
                  :produto="isCreateMode ? null : selectedProduct"
                  :disabled="isViewMode"
                />
              </template>
            </div>

            <!-- Footer -->
            <div
              class="flex items-center justify-end gap-3 px-6 py-4 border-t border-zinc-200 bg-zinc-50"
            >
              <BaseButton type="button" variant="secondary" @click="closeModal">
                {{ isViewMode ? 'Fechar' : 'Cancelar' }}
              </BaseButton>
              <BaseButton
                v-if="!isViewMode"
                type="submit"
                variant="primary"
                :is-loading="isPending"
                @click="onSubmit"
              >
                {{ isCreateMode ? 'Cadastrar Produto' : 'Salvar Alterações' }}
              </BaseButton>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
