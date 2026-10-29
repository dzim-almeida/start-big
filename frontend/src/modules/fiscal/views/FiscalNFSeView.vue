<script setup lang="ts">
/**
 * Aba NFS-e do Centro Fiscal (backend-fastapi/docs/nfse-plano.md, F3).
 *
 * Só com o módulo NFSE (a rota exige). A rota (Nacional ou prefeitura) quem
 * decide é a plataforma (G6). Cards por status e "Saúde Fiscal" iguais aos da
 * aba NF-e (docs/nfse-melhorias-plano.md, M4).
 */
import { ref } from 'vue';
import { FilePlus, FolderArchive, Send, Settings } from 'lucide-vue-next';

import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';
import FranquiaFiscalCard from '../components/shared/FranquiaFiscalCard.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import NfseDocumentosTable from '../components/nfse/NfseDocumentosTable.vue';
import NfseEmitirModal from '../components/nfse/NfseEmitirModal.vue';
import FiscalExportarXmlModal from '../components/listagem/FiscalExportarXmlModal.vue';
import NfseConfiguracaoModal from '../components/nfse/NfseConfiguracaoModal.vue';
import NfseAvulsaModal from '../components/nfse/NfseAvulsaModal.vue';
import NfseSaudeCard from '../components/nfse/NfseSaudeCard.vue';
import FiscalStats from '../components/listagem/FiscalStats.vue';
import { useNfseResumoQuery } from '../composables/useNfse';
import type { DocumentoFiscalStatus } from '../types/fiscal.types';

const showEmitirModal = ref(false);
const showExportarXmlModal = ref(false);
const showConfiguracaoModal = ref(false);
const showAvulsaModal = ref(false);
const statusFiltro = ref<DocumentoFiscalStatus | null>(null);

const { data: resumo, isLoading: isResumoLoading } = useNfseResumoQuery();
</script>

<template>
  <div class="flex flex-col gap-6 flex-1 min-h-0">
    <div class="flex flex-col flex-wrap sm:flex-row sm:justify-between sm:items-end gap-4">
      <PageReview title="NFS-e" description="Notas Fiscais de Serviço" />

      <div class="flex items-center gap-2">
        <FranquiaFiscalCard />
        <NfseSaudeCard />
        <BaseButton type="button" variant="ghost" class="text-sm" @click="showConfiguracaoModal = true">
          <Settings :size="16" class="mr-1.5" />
          Configuração
        </BaseButton>
        <BaseButton type="button" variant="ghost" class="text-sm" @click="showExportarXmlModal = true">
          <FolderArchive :size="16" class="mr-1.5" />
          XMLs do período
        </BaseButton>
        <BaseButton type="button" variant="secondary" class="text-sm" @click="showAvulsaModal = true">
          <FilePlus :size="16" class="mr-1.5" />
          NFS-e avulsa
        </BaseButton>
        <BaseButton type="button" variant="primary" class="text-sm" @click="showEmitirModal = true">
          <Send :size="16" class="mr-1.5" />
          Emitir NFS-e
        </BaseButton>
      </div>
    </div>

    <FiscalStats
      :resumo="resumo"
      :is-loading="isResumoLoading"
      :active-status="statusFiltro"
      @filter-status="statusFiltro = $event"
    />

    <NfseDocumentosTable :status-filtro="statusFiltro" />

    <NfseEmitirModal :is-open="showEmitirModal" @close="showEmitirModal = false" />
    <FiscalExportarXmlModal :is-open="showExportarXmlModal" tipo-inicial="NFSE" @close="showExportarXmlModal = false" />
    <NfseConfiguracaoModal :is-open="showConfiguracaoModal" @close="showConfiguracaoModal = false" />
    <NfseAvulsaModal :is-open="showAvulsaModal" @close="showAvulsaModal = false" />
  </div>
</template>
