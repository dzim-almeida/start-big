<script setup lang="ts">
import BaseFormModal from '@/shared/components/layout/FormModal/BaseFormModal.vue';
import { useProductModal } from '../composables/useProductModal';

const { isModalOpen, closeModal } = useProductModal();
</script>

<template>
    <BaseFormModal :is-open="isModalOpen" :modal-title="'Produto'" :is-pending="false" :is-view-mode="false" :is-create-mode="false" :on-submit="() => {}" :close-modal="closeModal">
        <template #body>
            <div class="">
                
            </div>
        </template>
    </BaseFormModal>
</template>