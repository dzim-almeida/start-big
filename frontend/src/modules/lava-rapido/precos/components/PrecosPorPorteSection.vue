<script setup lang="ts">
/**
 * @component PrecosPorPorteSection
 * @description Grade "porte → preço e duração" no cadastro de serviço
 * (lava-rápido, Spec 02B).
 *
 * Só é montada no segmento com `preco_por_porte` (quem decide é o
 * `ServicoFormModal`). Um serviço ("Lavagem completa") tem um preço por porte;
 * porte sem preço usa o **valor base** do serviço, que continua no campo de
 * sempre. A duração alimenta a previsão de entrega da comanda.
 *
 * A grade vai para o servidor no salvar do serviço, pelo gancho `aoSalvar` do
 * formulário: num serviço novo ainda não existe id antes disso.
 */
import { computed, onBeforeUnmount, ref, watch, watchEffect } from 'vue';
import { Car } from 'lucide-vue-next';

import LucideIcon from '@/shared/components/icons/LucideIcon.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import MoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import { useServicoForm } from '@/modules/order-service/servicos/composables/useServicoForm';
import { useServicoModal } from '@/modules/order-service/servicos/composables/useServicoModal';
import { useTiposDeTrabalho } from '@/modules/order-service/shared/segmento/useTiposDeTrabalho';

import { usePortesQuery } from '../../shared/composables/usePortes';
import { usePrecosPorPorteForm } from '../composables/usePrecosPorPorteForm';

defineProps<{ disabled?: boolean }>();

const { selectedServico } = useServicoModal();
const { aoSalvar, valor: valorBase } = useServicoForm();
const { opcoes: tiposDeVeiculo } = useTiposDeTrabalho();
const { ativosDoTipo, isLoading: carregandoPortes } = usePortesQuery();

const { linhas, garantirLinhas, salvar } = usePrecosPorPorteForm(() => selectedServico.value?.id ?? null);

// Grava junto com o serviço; desfaz o registro quando o modal desmonta.
const desfazer = aoSalvar(salvar);
onBeforeUnmount(desfazer);

/** Tipo de veículo aberto na grade (abas: Carro, Moto, Caminhão...). */
const tipoAtivo = ref<string>('');
watch(
  tiposDeVeiculo,
  (opcoes) => {
    if (!tipoAtivo.value && opcoes.length) tipoAtivo.value = opcoes[0].value;
  },
  { immediate: true },
);

const portesDoTipo = computed(() => ativosDoTipo(tipoAtivo.value));
// Toda linha visível existe antes do render (também depois de recarregar a grade).
watchEffect(() => garantirLinhas(portesDoTipo.value.map((p) => p.id)));

/** Texto do valor base, mostrado no lugar do preço vazio. */
const textoBase = computed(() =>
  (Number(valorBase.value) || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }),
);
</script>

<template>
  <section>
    <div class="mb-2 flex items-center gap-3">
      <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-primary-light text-brand-primary">
        <LucideIcon :icon="Car" />
      </div>
      <div>
        <h3 class="text-lg font-semibold text-zinc-800">Preço por porte</h3>
        <p class="text-xs text-zinc-500">
          Deixe em branco para usar o valor base ({{ textoBase }}). A duração calcula a hora em que o veículo fica pronto.
        </p>
      </div>
    </div>

    <!-- Tipo de veículo: botões, como na comanda -->
    <div class="mb-4 mt-4 flex flex-wrap gap-2" role="tablist">
      <button
        v-for="tipo in tiposDeVeiculo"
        :key="tipo.value"
        type="button"
        role="tab"
        :aria-selected="tipoAtivo === tipo.value"
        class="rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors"
        :class="tipoAtivo === tipo.value
          ? 'border-brand-primary bg-brand-primary text-white'
          : 'border-zinc-200 bg-white text-zinc-600 hover:border-brand-primary hover:text-brand-primary'"
        @click="tipoAtivo = tipo.value"
      >
        {{ tipo.label }}
      </button>
    </div>

    <p v-if="carregandoPortes" class="text-sm text-zinc-500">Carregando portes…</p>
    <p v-else-if="!portesDoTipo.length" class="text-sm text-zinc-500">
      Nenhum porte ativo neste tipo. Cadastre em Configurações › Lava-Rápido.
    </p>

    <ul v-else class="divide-y divide-zinc-100 rounded-2xl border border-zinc-100 bg-white">
      <li v-for="porte in portesDoTipo" :key="porte.id" class="grid grid-cols-12 items-end gap-3 px-4 py-3">
        <template v-if="linhas[porte.id]">
          <p class="col-span-12 pb-2 text-sm font-medium text-zinc-700 md:col-span-4">{{ porte.nome }}</p>
          <div class="col-span-7 md:col-span-5">
            <MoneyInput
              v-model="linhas[porte.id].valor"
              :label="`Preço (${porte.nome})`"
              :disabled="disabled"
            />
          </div>
          <div class="col-span-5 md:col-span-3">
            <BaseInput
              v-model="linhas[porte.id].duracao"
              label="Duração (min)"
              type="text"
              inputmode="numeric"
              placeholder="Ex: 40"
              :disabled="disabled"
            />
          </div>
        </template>
      </li>
    </ul>
  </section>
</template>
