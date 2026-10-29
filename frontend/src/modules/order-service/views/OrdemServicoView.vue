<script setup lang="ts">
import { ref, computed, defineAsyncComponent, onMounted } from 'vue';
import { Plus } from 'lucide-vue-next';

import { TAB_OPTIONS } from '../ordens/constants/ordemServico.constants';

import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';
import BaseTab2 from '@/shared/components/ui/BaseTab2/BaseTab2.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import OrdensServicoTab from './tabs/OrdensServicoTab.vue';
import ServicosTab from './tabs/ServicosTab.vue';
import RevisoesPendentesTab from './tabs/RevisoesPendentesTab.vue';
// Marcenaria: abas "Produção" (Spec 12B D15) e "Terceirizados" (11B D10). Sob
// demanda — os outros segmentos nem baixam.
const QuadroProducaoTab = defineAsyncComponent(
  () => import('@/modules/marcenaria/producao/components/QuadroProducaoTab.vue'),
);
// Marcenaria (Spec 13B D15): aba "Instalações" — quem instala onde, por dia.
const InstalacoesTab = defineAsyncComponent(
  () => import('@/modules/marcenaria/entrega/components/InstalacoesTab.vue'),
);
const TerceirizadosTab = defineAsyncComponent(
  () => import('@/modules/marcenaria/terceirizados/components/TerceirizadosTab.vue'),
);
// Marcenaria: aba "Orçamentos" — a lista que antes era um item próprio do menu (12/10/2026).
const OrcamentosTab = defineAsyncComponent(
  () => import('@/modules/marcenaria/orcamentos/views/OrcamentosListaView.vue'),
);

import { useServicoModal } from '../servicos/composables/useServicoModal';
import { useOSCreateFlow } from '../ordens/composables/useOSCreateFlow';
import { useCapacidades } from '../shared/segmento/useCapacidades';
import { useTiposDeTrabalho } from '../shared/segmento/useTiposDeTrabalho';
import { mostrarBotaoAdicionar, mostrarBotaoNovoOrcamento } from '../shared/segmento/botoesCriacaoOS';
import { usePermissoesOrcamento } from '@/modules/marcenaria/orcamentos/composables/usePermissoesOrcamento';
import { useRoute, useRouter } from 'vue-router';
import { getUniqueOS } from '../ordens/services/orderServiceGet.service';

const { openCreateModal } = useServicoModal();
const { openNovaOS, openExistingOS } = useOSCreateFlow();
const { temRevisoes, temOrcamentoTecnico } = useCapacidades();
// O segmento deixa abrir OS à mão? Na marcenaria, não: a OS nasce do orçamento (Spec 03B).
const { podeCriarOSManual } = useTiposDeTrabalho();

const router = useRouter();
const route = useRoute();
const { podeVer: podeVerOrcamentos, podeGerir: podeGerirOrcamentos } = usePermissoesOrcamento();

// Link de outra tela (aba NFS-e, detalhe da nota): `?os=OS-2026-000158` abre a
// OS. Não achou: fica a lista, como sem o parâmetro.
onMounted(async () => {
  const numero = typeof route.query.os === 'string' ? route.query.os : null;
  if (!numero) return;
  try {
    openExistingOS(await getUniqueOS(numero));
  } catch {
    // OS inexistente ou sem permissão: a lista normal.
  }
});

// Abas extras por capacidade, na ordem: Revisões (oficina, pós-venda), Produção
// (marcenaria, Spec 12B D15: o quadro que a fábrica abre de manhã), Instalações
// (13B D15) e Terceirizados (11B D10). Sem nenhuma, a lista é a de sempre.
//
// Marcenaria (12/10/2026): "Orçamentos" vem primeiro — é por ele que a loja
// fecha o serviço — e o "Cadastro de Serviços" some.
const tabOptions = computed(() => [
  ...(temOrcamentoTecnico.value && podeVerOrcamentos.value ? [{ id: 'orcamentos', label: 'Orçamentos' }] : []),
  ...(temOrcamentoTecnico.value ? TAB_OPTIONS.filter((aba) => aba.id !== 'servicos') : TAB_OPTIONS),
  ...(temRevisoes.value ? [{ id: 'revisoes', label: 'Revisões' }] : []),
  ...(temOrcamentoTecnico.value
    ? [
      { id: 'producao', label: 'Produção' },
      { id: 'instalacoes', label: 'Instalações' },
      { id: 'terceirizados', label: 'Terceirizados' },
    ]
    : []),
]);

// A aba aberta vem da URL (`?aba=orcamentos`): é como o "voltar" do editor de
// orçamento devolve o usuário à lista. Aba ausente, ou que o segmento não tem:
// a primeira da lista ("Ordens de Serviço" nos outros segmentos, como sempre).
const abaPedida = ref<string | null>(typeof route.query.aba === 'string' ? route.query.aba : null);
const activeTab = computed<string>({
  get: () => {
    const ids = tabOptions.value.map((aba) => aba.id);
    return abaPedida.value && ids.includes(abaPedida.value) ? abaPedida.value : ids[0];
  },
  set: (aba) => {
    abaPedida.value = aba;
    void router.replace({ query: { aba } });
  },
});

const pageTitle = computed(() => {
  if (activeTab.value === 'revisoes') return 'Revisões Pendentes';
  if (activeTab.value === 'producao') return 'Produção';
  if (activeTab.value === 'instalacoes') return 'Instalações';
  if (activeTab.value === 'terceirizados') return 'Terceirizados';
  if (activeTab.value === 'orcamentos') return 'Orçamentos';
  return activeTab.value === 'ordens' ? 'Ordens de Serviço' : 'Cadastro de Serviços';
});

const pageDescription = computed(() => {
  if (activeTab.value === 'revisoes') return 'Veículos com revisão vencida por data e/ou KM.';
  if (activeTab.value === 'producao') return 'As OS em produção, com o progresso e a próxima etapa, na ordem da entrega.';
  if (activeTab.value === 'instalacoes') return 'Quem instala onde, por dia.';
  if (activeTab.value === 'terceirizados') return 'Móveis pedidos às centrais parceiras e ainda não conferidos.';
  if (activeTab.value === 'orcamentos') return 'Acompanhe cada proposta, do rascunho até virar Ordem de Serviço.';
  return activeTab.value === 'ordens'
    ? 'Gerencie as ordens de serviço da sua organização.'
    : 'Gerencie o catálogo de serviços da sua organização.';
});

/** Botão do topo: "Nova OS" só onde dá para criar à mão; "Novo Serviço" sempre (Spec 03B, D3/D5). */
const exibirBotaoAdicionar = computed(() => mostrarBotaoAdicionar(activeTab.value, podeCriarOSManual.value));

/** Marcenaria: no lugar de "Nova OS", "Novo orçamento" (a OS nasce dele; Spec 06B, D4). */
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

      <!-- Abas à esquerda e o botão de criar à direita (André, remodelação item 1). -->
      <div class="flex w-full flex-wrap items-center justify-between gap-5">
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

    <OrcamentosTab v-if="activeTab === 'orcamentos'" embutida />
    <OrdensServicoTab v-else-if="activeTab === 'ordens'" />
    <RevisoesPendentesTab v-else-if="activeTab === 'revisoes'" />
    <QuadroProducaoTab v-else-if="activeTab === 'producao'" />
    <InstalacoesTab v-else-if="activeTab === 'instalacoes'" />
    <TerceirizadosTab v-else-if="activeTab === 'terceirizados'" />
    <ServicosTab v-else />
  </div>
</template>
