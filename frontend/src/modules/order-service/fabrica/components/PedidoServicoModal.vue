<script setup lang="ts">
/**
 * @fileoverview Pedido de serviço à central de corte para um móvel terceirizado (F5).
 *
 * Nasce como RASCUNHO em Compras (tipo SERVIÇO). Enviar ao fornecedor, receber
 * (que gera a conta a pagar) e cancelar seguem pela tela de Pedidos de Compra.
 * A etapa "Separação e compra" só sai com o serviço recebido.
 */
import { computed, ref, watch } from 'vue';
import { useMutation, useQuery } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseMoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import { useToast } from '@/shared/composables/useToast';
import type { ApiError } from '@/shared/types/axios.types';
import { getErrorMessage } from '@/shared/utils/error.utils';
import { getFornecedoresQueVendem } from '@/modules/compras/shared/services/compras.service';

import { criarPedidoServico } from '../services/fabrica.service';
import type { MovelRead, PedidoServicoRead } from '../types/fabrica.types';

const props = defineProps<{ movel: MovelRead | null }>();
const emit = defineEmits<{ fechar: []; criado: [pedido: PedidoServicoRead] }>();

const toast = useToast();
const aberto = computed(() => !!props.movel);

const fornecedorId = ref<number | null>(null);
const valorReais = ref<number | undefined>(undefined);
const previsao = ref<string | null>(null);
const observacao = ref('');

watch(() => props.movel, (m) => {
  if (!m) return;
  fornecedorId.value = null;
  valorReais.value = m.custo_terceiro != null ? m.custo_terceiro / 100 : undefined;
  previsao.value = null;
  observacao.value = m.medidas ? `${m.nome} — ${m.medidas} mm` : m.nome;
});

const { data: fornecedores } = useQuery({
  queryKey: ['fabrica', 'fornecedores-servico'],
  queryFn: getFornecedoresQueVendem,
  enabled: aberto,
  staleTime: 60_000,
});

const valido = computed(() => !!fornecedorId.value && (valorReais.value ?? 0) > 0);

const criar = useMutation<PedidoServicoRead, AxiosError<ApiError>, void>({
  mutationFn: () =>
    criarPedidoServico(props.movel!.id, {
      fornecedor_id: fornecedorId.value as number,
      valor: Math.round((valorReais.value ?? 0) * 100),
      previsao_entrega: previsao.value || null,
      condicao_pagamento: null,
      observacao: observacao.value.trim() || null,
    }),
  onSuccess: (pedido) => {
    toast.success(`Pedido ${pedido.codigo} criado`, 'Envie à central pela tela de Pedidos de Compra.');
    emit('criado', pedido);
  },
  onError: (erro) => toast.error('Não foi possível criar o pedido', getErrorMessage(erro, 'Tente de novo.') as string),
});
</script>

<template>
  <BaseModal :is-open="aberto" :title="`Central de corte — ${movel?.nome ?? ''}`" size="sm" overlay @close="emit('fechar')">
    <div class="flex flex-col gap-3 text-sm">
      <label class="flex flex-col gap-1">
        <span class="text-xs font-medium text-zinc-600">Central de corte (fornecedor)</span>
        <select v-model.number="fornecedorId" class="min-h-10 px-2.5 border border-zinc-200 rounded-lg bg-white outline-none focus:border-brand-primary">
          <option :value="null" disabled>Escolha…</option>
          <option v-for="f in fornecedores" :key="f.id" :value="f.id">{{ f.nome_fantasia || f.nome }}</option>
        </select>
      </label>
      <BaseMoneyInput v-model="valorReais" label="Valor do serviço" />
      <label class="flex flex-col gap-1">
        <span class="text-xs font-medium text-zinc-600">Previsão de entrega</span>
        <input v-model="previsao" type="date" class="min-h-10 px-2.5 border border-zinc-200 rounded-lg outline-none focus:border-brand-primary" />
      </label>
      <label class="flex flex-col gap-1">
        <span class="text-xs font-medium text-zinc-600">O que vai para a central</span>
        <textarea v-model="observacao" rows="3" class="px-2.5 py-2 border border-zinc-200 rounded-lg outline-none focus:border-brand-primary" placeholder="Medidas, arquivo do plano de corte, cor da chapa…" />
      </label>
    </div>
    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <BaseButton variant="secondary" class="px-5" @click="emit('fechar')">Cancelar</BaseButton>
        <BaseButton class="px-5" :disabled="!valido" :is-loading="criar.isPending.value" @click="criar.mutate()">
          Criar pedido
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
