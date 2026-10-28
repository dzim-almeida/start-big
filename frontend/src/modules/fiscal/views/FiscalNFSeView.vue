<script setup lang="ts">
/**
 * Aba NFS-e do Centro Fiscal (backend-fastapi/docs/nfse-plano.md, F3).
 *
 * Só com o módulo NFSE (a rota exige). Hoje: NFS-e Nacional da mão de obra de
 * uma OS. A rota municipal (cidades que não usam o padrão nacional para todas
 * as empresas) entra cidade por cidade.
 */
import { ref } from 'vue';
import { FolderArchive, Send } from 'lucide-vue-next';

import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';
import FranquiaFiscalCard from '../components/shared/FranquiaFiscalCard.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import NfseDocumentosTable from '../components/nfse/NfseDocumentosTable.vue';
import NfseEmitirModal from '../components/nfse/NfseEmitirModal.vue';
import FiscalExportarXmlModal from '../components/listagem/FiscalExportarXmlModal.vue';

const showEmitirModal = ref(false);
const showExportarXmlModal = ref(false);
</script>

<template>
  <div class="flex flex-col gap-6 flex-1 min-h-0">
    <div class="flex flex-col flex-wrap sm:flex-row sm:justify-between sm:items-end gap-4">
      <PageReview title="NFS-e" description="Notas Fiscais de Serviço (padrão nacional)" />

      <div class="flex items-center gap-2">
        <FranquiaFiscalCard />
        <BaseButton type="button" variant="ghost" class="text-sm" @click="showExportarXmlModal = true">
          <FolderArchive :size="16" class="mr-1.5" />
          XMLs do período
        </BaseButton>
        <BaseButton type="button" variant="primary" class="text-sm" @click="showEmitirModal = true">
          <Send :size="16" class="mr-1.5" />
          Emitir NFS-e
        </BaseButton>
      </div>
    </div>

    <NfseDocumentosTable />

    <NfseEmitirModal :is-open="showEmitirModal" @close="showEmitirModal = false" />
    <FiscalExportarXmlModal :is-open="showExportarXmlModal" tipo-inicial="NFSE" @close="showExportarXmlModal = false" />
  </div>
</template>
