<script setup lang="ts">
/**
 * @component EntradaLavagem
 * @description A busca de cliente/placa da OS + a comanda, montadas uma vez
 * na tela de Serviços do lava-rápido (Spec 03B). Quem abre é o
 * `useEntradaLavagem` (botão do topo, pátio, agenda).
 *
 * Também hospeda a via de entrada do "Entrar e imprimir": a comanda fecha ao
 * salvar, e a via precisa de um lugar que continue montado.
 */
import OSClienteSearchModal from '@/modules/order-service/ordens/components/OSClienteSearchModal.vue';
import OSPrintTemplate from '@/modules/order-service/ordens/components/OSPrintTemplate.vue';

import { useEntradaLavagem } from '../composables/useEntradaLavagem';
import { useImprimirEntrada } from '../composables/useImprimirEntrada';
import ComandaModal from './ComandaModal.vue';

const e = useEntradaLavagem();
const { osParaImprimir, imprimirEntrada } = useImprimirEntrada();

function criada(numeroOs: string, imprimir = false) {
  e.lavagemCriada(numeroOs);
  if (imprimir) void imprimirEntrada(numeroOs);
}
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
    @criada="criada"
  />
  <OSPrintTemplate v-if="osParaImprimir" :ordem-servico="osParaImprimir" type="ENTRADA" />
</template>
