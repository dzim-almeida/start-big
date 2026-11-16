import { ref } from 'vue';

import type { CustomerUnionReadSchemaDataType } from '@/modules/order-service/ordens/schemas/relationship/customer/customer.schema';
import type { ObjetoBuscaItemDataType } from '@/modules/order-service/ordens/schemas/relationship/objetoBusca.schema';
import { getCustomerByIdForOS } from '@/modules/order-service/ordens/services/relationship/osRelationshipGet.service';
import { useToast } from '@/shared/composables/useToast';

import type { Agendamento } from '../../shared/schemas/agenda.schema';

/**
 * Entrada de uma lavagem no PADRÃO DA OS (Spec 03B, revisão de 12/11):
 * primeiro o cliente — pela busca de sempre, que acha também pela placa —,
 * depois a comanda já com ele (e com o veículo, se veio pela placa).
 *
 * Estado de MÓDULO, como o `useOSCreateFlow`: o botão do topo, o pátio e a
 * agenda abrem a mesma entrada, montada uma vez só (`EntradaLavagem.vue`).
 */
const buscaAberta = ref(false);
const comandaAberta = ref(false);
const cliente = ref<CustomerUnionReadSchemaDataType | null>(null);
const objeto = ref<ObjetoBuscaItemDataType | null>(null);
const agendamento = ref<Agendamento | null>(null);
/** Quem abriu quer saber da OS criada (a agenda marca o "Chegou"). */
let aoCriar: ((numeroOs: string) => void) | null = null;

export function useEntradaLavagem() {
  const toast = useToast();

  /** "Nova entrada": começa pela busca de cliente, como a "Nova OS". */
  function abrirNovaEntrada() {
    // Fecha antes: se a tela foi trocada com a comanda aberta, o "aberta"
    // ficava preso e a próxima entrada não aplicava o cliente (bug de 12/11).
    comandaAberta.value = false;
    cliente.value = null;
    objeto.value = null;
    agendamento.value = null;
    aoCriar = null;
    buscaAberta.value = true;
  }

  /**
   * O cliente agendado chegou. Com cadastro, a comanda abre direto; sem, a
   * busca vem antes (para achar ou cadastrar) e a comanda abre em seguida.
   */
  async function chegouAgendado(a: Agendamento, depois: (numeroOs: string) => void) {
    comandaAberta.value = false;
    buscaAberta.value = false;
    agendamento.value = a;
    objeto.value = null;
    aoCriar = depois;
    cliente.value = null;
    if (a.cliente_id) {
      try {
        cliente.value = await getCustomerByIdForOS(a.cliente_id);
        comandaAberta.value = true;
        return;
      } catch {
        // cadastro sumiu: escolhe pela busca
      }
    }
    buscaAberta.value = true;
  }

  function clienteEscolhido(c: CustomerUnionReadSchemaDataType) {
    cliente.value = c;
    buscaAberta.value = false;
    comandaAberta.value = true;
  }

  /** Achou o veículo pela placa: o dono vem junto. */
  async function veiculoEscolhido(o: ObjetoBuscaItemDataType) {
    try {
      cliente.value = await getCustomerByIdForOS(o.cliente_id);
    } catch {
      toast.error('Não foi possível carregar o dono do veículo.');
      return;
    }
    objeto.value = o;
    buscaAberta.value = false;
    comandaAberta.value = true;
  }

  function fecharBusca() {
    buscaAberta.value = false;
  }

  function fecharComanda() {
    comandaAberta.value = false;
    agendamento.value = null;
  }

  function lavagemCriada(numeroOs: string) {
    aoCriar?.(numeroOs);
    aoCriar = null;
  }

  return {
    buscaAberta, comandaAberta, cliente, objeto, agendamento,
    abrirNovaEntrada, chegouAgendado, clienteEscolhido, veiculoEscolhido,
    fecharBusca, fecharComanda, lavagemCriada,
  };
}
