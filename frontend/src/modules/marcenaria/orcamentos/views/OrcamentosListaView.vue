<script setup lang="ts">
/**
 * @view OrcamentosListaView
 * @description Menu "Orçamentos" da marcenaria (Spec 06B §6.1, D48-D50):
 * chips com contagem, busca, vendedor, versões antigas e a tabela.
 *
 * O filtro escolhido fica na URL (`?status=ENVIADO&busca=alpha`): voltar do
 * editor devolve a mesma lista, na mesma página.
 */
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter, type LocationQueryRaw } from 'vue-router';
import { Plus } from 'lucide-vue-next';
import { refDebounced } from '@vueuse/core';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseTableContainer from '@/shared/components/commons/BaseTableContainer/BaseTableContainer.vue';
import PageReview from '@/shared/components/layout/PageReview/PageReview.vue';
import { useOsEmployeesGet } from '@/modules/order-service/ordens/composables/request/relationship/useOSRelationshipGet.queries';

import OrcamentosFiltros, { type ChipFiltro } from '../components/lista/OrcamentosFiltros.vue';
import OrcamentosTabela from '../components/lista/OrcamentosTabela.vue';
import { useExigeCapacidade } from '../composables/useExigeCapacidade';
import { useContagensQuery, useOrcamentosQuery } from '../composables/useOrcamentosQuery';
import { usePermissoesOrcamento } from '../composables/usePermissoesOrcamento';
import type { FiltrosLista } from '../services/orcamento.service';

// Sem a capacidade do segmento (outro segmento digitou o endereço): volta ao início (D3).
useExigeCapacidade('orcamento_tecnico');

const route = useRoute();
const router = useRouter();
const { podeVer, podeGerir, podeVerCustos } = usePermissoesOrcamento();

const POR_PAGINA = 20;
const CHIPS_VALIDOS: ChipFiltro[] = ['TODOS', 'RASCUNHO', 'ENVIADO', 'VENCE_3', 'VENCIDO', 'RECUSADO', 'APROVADO'];

// --- Estado dos filtros, lido da URL ao abrir ------------------------------
const texto = (valor: unknown) => (typeof valor === 'string' ? valor : '');
const chipDaUrl = (): ChipFiltro => {
  if (route.query.vence === '3') return 'VENCE_3';
  const status = texto(route.query.status) as ChipFiltro;
  return CHIPS_VALIDOS.includes(status) ? status : 'TODOS';
};

const chip = ref<ChipFiltro>(chipDaUrl());
const busca = ref(texto(route.query.busca));
const vendedorId = ref<number | null>(Number(route.query.vendedor) || null);
const versoesAntigas = ref(route.query.versoes === '1');
const pagina = ref(Number(route.query.pagina) || 1);

// A busca espera o usuário parar de digitar (não uma chamada por tecla).
const buscaEsperada = refDebounced(busca, 300);

/** Os filtros como a API recebe (06A §6.3). */
const filtros = computed<FiltrosLista>(() => ({
  status: chip.value !== 'TODOS' && chip.value !== 'VENCE_3' ? chip.value : null,
  vence_em_dias: chip.value === 'VENCE_3' ? 3 : null,
  busca: buscaEsperada.value.trim() || null,
  vendedor_id: vendedorId.value,
  incluir_versoes_antigas: versoesAntigas.value || undefined,
  page: pagina.value,
  limit: POR_PAGINA,
}));

// Filtro novo volta para a página 1 (na página 4 de um filtro novo, a lista pareceria vazia).
watch([chip, buscaEsperada, vendedorId, versoesAntigas], () => { pagina.value = 1; });

// Guarda os filtros na URL (replace: não enche o "voltar" do usuário de passos).
watch([chip, buscaEsperada, vendedorId, versoesAntigas, pagina], () => {
  const query: LocationQueryRaw = {};
  if (chip.value === 'VENCE_3') query.vence = '3';
  else if (chip.value !== 'TODOS') query.status = chip.value;
  if (buscaEsperada.value.trim()) query.busca = buscaEsperada.value.trim();
  if (vendedorId.value) query.vendedor = String(vendedorId.value);
  if (versoesAntigas.value) query.versoes = '1';
  if (pagina.value > 1) query.pagina = String(pagina.value);
  void router.replace({ query });
});

// --- Dados ----------------------------------------------------------------
const { data: lista, isLoading, isError, refetch } = useOrcamentosQuery(filtros);
const { data: contagens } = useContagensQuery();

// Vendedores para o filtro. Sem permissão de funcionários (403), o filtro só some.
const { data: funcionarios } = useOsEmployeesGet();
const vendedores = computed(() =>
  ((funcionarios.value as unknown as { id: number; nome: string }[] | undefined) ?? [])
    .map((f) => ({ value: f.id, label: f.nome })),
);

/** Algum filtro ligado? Decide qual mensagem de lista vazia mostrar (D50). */
const temFiltro = computed(
  () => chip.value !== 'TODOS' || !!buscaEsperada.value.trim() || vendedorId.value != null || versoesAntigas.value,
);

function limparFiltros() {
  chip.value = 'TODOS';
  busca.value = '';
  vendedorId.value = null;
  versoesAntigas.value = false;
}

const abrir = (id: number) => router.push({ name: 'marcenaria-orcamento', params: { id } });
const novo = () => router.push({ name: 'marcenaria-orcamento-novo' });
</script>

<template>
  <!-- Sem permissão de ver (o menu já esconde o item; isto é para quem digitou o endereço). -->
  <div v-if="!podeVer" class="rounded-2xl border border-zinc-200 bg-white p-8 text-center text-sm text-zinc-500" data-testid="sem-permissao">
    Você não tem permissão para ver orçamentos.
  </div>

  <div v-else class="flex flex-col gap-6 md:gap-8">
    <div class="flex items-center justify-between gap-4">
      <PageReview title="Orçamentos" description="Propostas de móveis planejados, do rascunho à aprovação" />
      <BaseButton v-if="podeGerir" variant="primary" data-testid="novo-orcamento" @click="novo">
        <Plus :size="16" class="mr-1.5" /> Novo orçamento
      </BaseButton>
    </div>

    <BaseTableContainer
      :is-loading="isLoading"
      :is-error="isError"
      :is-empty="!lista?.items.length"
      :current-page="pagina"
      :total-pages="lista?.total_pages ?? 1"
      :total-items="lista?.total_items ?? 0"
      item-label="orçamento"
      item-label-plural="orçamentos"
      @update:current-page="pagina = $event"
    >
      <template #toolbar>
        <OrcamentosFiltros
          v-model:chip="chip"
          v-model:busca="busca"
          v-model:vendedor-id="vendedorId"
          v-model:versoes-antigas="versoesAntigas"
          :contagens="contagens"
          :vendedores="vendedores"
        />
      </template>

      <!-- Os dois vazios pedem ações diferentes (D50). -->
      <template #empty>
        <div class="flex flex-col items-center gap-3 py-12 text-center" data-testid="lista-vazia">
          <template v-if="temFiltro">
            <p class="text-sm text-zinc-500">Nenhum orçamento com estes filtros.</p>
            <BaseButton variant="secondary" size="sm" @click="limparFiltros">Limpar filtros</BaseButton>
          </template>
          <template v-else>
            <p class="text-sm text-zinc-500">Nenhum orçamento ainda.</p>
            <BaseButton v-if="podeGerir" variant="primary" size="sm" @click="novo">
              <Plus :size="14" class="mr-1" /> Novo orçamento
            </BaseButton>
          </template>
        </div>
      </template>

      <template #error>
        <div class="flex flex-col items-center gap-3 py-12 text-center">
          <p class="text-sm text-red-600">Não foi possível carregar os orçamentos.</p>
          <BaseButton variant="secondary" size="sm" @click="refetch()">Tentar de novo</BaseButton>
        </div>
      </template>

      <OrcamentosTabela :itens="lista?.items ?? []" :mostrar-margem="podeVerCustos" @abrir="abrir" />
    </BaseTableContainer>
  </div>
</template>
