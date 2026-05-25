<script setup lang="ts">
import { computed } from 'vue';

import { User2, Building2, House, Phone, UserX, RefreshCw } from 'lucide-vue-next';

import BaseInfoCard from '@/shared/components/layout/StatsCard/BaseInfoCard.vue';

import type { CustomerSimpleRead } from '../../schemas/customers.schema';

const props = defineProps<{
  customer: CustomerSimpleRead[number] | undefined | null;
  readonly?: boolean;
}>();

const emit = defineEmits<{
  changeCliente: [];
}>();

const address = computed(() => {
  if (!props.customer?.endereco) return 'Endereço não informado';

  const address = props.customer.endereco[0];
  return `${address.logradouro}, ${address.numero}${address.complemento ? `, ${address.complemento}` : ''} - ${address.bairro}, ${address.cidade}/${address.estado}`;
});
</script>
<template>
  <BaseInfoCard :icon="customer?.tipo === 'PF' ? User2 : Building2" title="DADOS DO CLIENTE">
    <template #header>
      <div class="flex items-center justify-end" v-if="!readonly">
        <button
          type="button"
          class="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-semibold text-brand-primary hover:bg-brand-primary/10 rounded-md transition-colors cursor-pointer"
          @click="emit('changeCliente')"
        >
          <RefreshCw :size="12" />
          Trocar
        </button>
      </div>
    </template>
    <div v-if="customer" class="px-4 py-3 flex flex-col gap-2">
      <div>
        <h2 class="font-poppins font-bold text-xs text-zinc-600 uppercase">Cliente</h2>
        <p class="font-poppins text-sm">
          {{ customer?.tipo === 'PF' ? customer?.nome : customer?.razao_social }}
        </p>
      </div>
      <div>
        <h2 class="font-poppins font-bold text-xs text-zinc-600 uppercase">Documento</h2>
        <p class="font-poppins text-sm">
          {{ customer?.tipo === 'PF' ? customer?.cpf : customer?.cnpj }}
        </p>
      </div>
      <div class="flex flex-col gap-2">
        <h2 class="font-poppins font-bold text-xs text-zinc-600 uppercase">Contato</h2>
        <div class="flex gap-2 items-center">
          <House :size="15" />
          <p class="font-poppins text-xs">{{ address }}</p>
        </div>
        <div class="flex gap-2 items-center">
          <Phone :size="15" />
          <p class="font-poppins text-xs">{{ customer?.telefone || 'Contato não informado' }}</p>
        </div>
      </div>
    </div>
    <div v-else class="min-h-40 flex flex-col items-center justify-center gap-2">
      <UserX :size="30" class="text-zinc-600" />
      <p class="text-sm text-muted-foreground text-zinc-500">
        Nenhum cliente selecionado.
      </p>
    </div>
  </BaseInfoCard>
</template>
