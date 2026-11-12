<script setup lang="ts">
/**
 * @component EntradaLavagem
 * @description A busca de cliente/placa da OS + a comanda, montadas uma vez
 * na tela de Serviços do lava-rápido (Spec 03B). Quem abre é o
 * `useEntradaLavagem` (botão do topo, pátio, agenda).
 */
import OSClienteSearchModal from '@/modules/order-service/ordens/components/OSClienteSearchModal.vue';

import { useEntradaLavagem } from '../composables/useEntradaLavagem';
import ComandaModal from './ComandaModal.vue';

const e = useEntradaLavagem();
</script>

<template>
  <OSClienteSearchModal
    :is-open="e.buscaAberta.value"
    @close="e.fecharBusca"
    @select-cliente="e.clienteEscolhido"
    @select-objeto="e.veiculoEscolhido"
  />
  <ComandaModal
    :is-open="e.comandaAberta.value"
    :cliente="e.cliente.value"
    :objeto="e.objeto.value"
    :agendamento="e.agendamento.value"
    @close="e.fecharComanda"
    @criada="e.lavagemCriada"
  />
</template>
