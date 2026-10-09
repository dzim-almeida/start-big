<script setup lang="ts">
import { ref, computed, defineAsyncComponent } from 'vue';
import { Plus } from 'lucide-vue-next';

import { TAB_OPTIONS } from '../ordens/constants/ordemServico.constants';

import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';
import BaseTab2 from '@/shared/components/ui/BaseTab2/BaseTab2.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import OrdensServicoTab from './tabs/OrdensServicoTab.vue';
import ServicosTab from './tabs/ServicosTab.vue';
import RevisoesPendentesTab from './tabs/RevisoesPendentesTab.vue';
// Marcenaria (Spec 11B D10): aba "Terceirizados". Sob demanda — os outros segmentos nem baixam.
const TerceirizadosTab = defineAsyncComponent(
  () => import('@/modules/marcenaria/terceirizados/components/TerceirizadosTab.vue'),
);

import { useServicoModal } from '../servicos/composables/useServicoModal';
import { useOSCreateFlow } from '../ordens/composables/useOSCreateFlow';
import { useCapacidades } from '../shared/segmento/useCapacidades';
import { useTiposDeTrabalho } from '../shared/segmento/useTiposDeTrabalho';
import { mostrarBotaoAdicionar, mostrarBotaoNovoOrcamento } from '../shared/segmento/botoesCriacaoOS';
import { usePermissoesOrcamento } from '@/modules/marcenaria/orcamentos/composables/usePermissoesOrcamento';
import { useRouter } from 'vue-router';

const { openCreateModal } = useServicoModal();
const { openNovaOS } = useOSCreateFlow();
const { temRevisoes, temOrcamentoTecnico } = useCapacidades();
// O segmento deixa abrir OS à mão? Na marcenaria, não: a OS nasce do orçamento (Spec 03B).
const { podeCriarOSManual } = useTiposDeTrabalho();

const activeTab = ref('ordens');

// Abas extras por capacidade, na ordem: Revisões (oficina, pós-venda) e
// Terceirizados (marcenaria, Spec 11B D10). Sem nenhuma, a lista é a de sempre.
const tabOptions = computed(() => [
  ...TAB_OPTIONS,
  ...(temRevisoes.value ? [{ id: 'revisoes', label: 'Revisões' }] : []),
  ...(temOrcamentoTecnico.value ? [{ id: 'terceirizados', label: 'Terceirizados' }] : []),
]);

const pageTitle = computed(() => {
  if (activeTab.value === 'revisoes') return 'Revisões Pendentes';
  if (activeTab.value === 'terceirizados') return 'Terceirizados';
  return activeTab.value === 'ordens' ? 'Ordens de Serviço' : 'Cadastro de Serviços';
});

const pageDescription = computed(() => {
  if (activeTab.value === 'revisoes') return 'Veículos com revisão vencida por data e/ou KM.';
  if (activeTab.value === 'terceirizados') return 'Móveis pedidos às centrais parceiras e ainda não conferidos.';
  return activeTab.value === 'ordens'
    ? 'Gerencie as ordens de serviço da sua organização.'
    : 'Gerencie o catálogo de serviços da sua organização.';
});

/** Botão do topo: "Nova OS" só onde dá para criar à mão; "Novo Serviço" sempre (Spec 03B, D3/D5). */
const exibirBotaoAdicionar = computed(() => mostrarBotaoAdicionar(activeTab.value, podeCriarOSManual.value));

/** Marcenaria: no lugar de "Nova OS", "Novo orçamento" (a OS nasce dele; Spec 06B, D4). */
const router = useRouter();
const { podeGerir: podeGerirOrcamentos } = usePermissoesOrcamento();
const exibirNovoOrcamento = computed(() =>
  mostrarBotaoNovoOrcamento(activeTab.value, podeCriarOSManual.value, temOrcamentoTecnico.value && podeGerirOrcamentos.value),
);
const novoOrcamento = () => router.push({ name: 'marcenaria-orcamento-novo' });

function handleAddClick() {
  if (activeTab.value === 'ordens') {
    openNovaOS();
  } else {
    openCreateModal();
  }
}
</script>

<template>
  <div class="p-4 md:p-6 lg:p-8 space-y-6 md:space-y-8">
    <div class="flex flex-col flex-wrap sm:flex-row sm:justify-between sm:items-end gap-4">
      <PageReview
        :title="pageTitle"
        :description="pageDescription"
      />

      <div class="flex gap-5">
        <BaseTab2 :options="tabOptions" v-model="activeTab" />
        <BaseButton
          v-if="exibirBotaoAdicionar"
          variant="primary"
          size="md"
          type="button"
          class="flex gap-1"
          @click="handleAddClick"
        >
          <Plus :size="20" />
          {{ activeTab === 'ordens' ? 'Nova OS' : 'Novo Serviço' }}
        </BaseButton>
        <BaseButton
          v-else-if="exibirNovoOrcamento"
          variant="primary"
          size="md"
          type="button"
          class="flex gap-1"
          data-testid="novo-orcamento-os"
          @click="novoOrcamento"
        >
          <Plus :size="20" />
          Novo orçamento
        </BaseButton>
      </div>
    </div>

    <OrdensServicoTab v-if="activeTab === 'ordens'" />
    <RevisoesPendentesTab v-else-if="activeTab === 'revisoes'" />
    <TerceirizadosTab v-else-if="activeTab === 'terceirizados'" />
    <ServicosTab v-else />
  </div>
</template>
