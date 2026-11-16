import { ref } from 'vue';

import { useCupomOS } from '@/modules/order-service/ordens/composables/modal/useCupomOS';
import type { OrderServiceReadDataType } from '@/modules/order-service/ordens/schemas/orderServiceQuery.schema';
import { getUniqueOS } from '@/modules/order-service/ordens/services/orderServiceGet.service';
import { useImpressao } from '@/shared/composables/useImpressao';
import { usePerfilComprovante } from '@/shared/composables/usePerfilComprovante';
import { useToast } from '@/shared/composables/useToast';
import { useImpressaoStore } from '@/shared/stores/impressao.store';
import { aguardarImagensDaImpressao, imprimirComPagina } from '@/shared/utils/print.utils';

/**
 * "Entrar e imprimir" da comanda (14/11/2026): imprime a via de ENTRADA da
 * lavagem que acabou de abrir.
 *
 * A regra é a MESMA da lista de OS (`OrdensServicoTab.imprimirComRegra`) e do
 * formulário (`useOSPrintFlow.imprimir`): formato Cupom + térmica configurada
 * → cupom ESC/POS direto; formato A4, sem térmica ou falha → via A4 com o
 * diálogo do sistema, no papel escolhido pela empresa para a entrada.
 *
 * Quem usa monta o `OSPrintTemplate` com `osParaImprimir` (ver EntradaLavagem).
 */
export function useImprimirEntrada() {
  const osParaImprimir = ref<OrderServiceReadDataType | null>(null);

  const impressao = useImpressao();
  const impressaoStore = useImpressaoStore();
  const { opcoesPaginaDe } = usePerfilComprovante();
  const { montarCupom } = useCupomOS();
  const toast = useToast();

  async function imprimirEntrada(numeroOs: string): Promise<void> {
    let os: OrderServiceReadDataType;
    try {
      os = await getUniqueOS(numeroOs);
    } catch {
      toast.error(`Lavagem aberta (${numeroOs}), mas não foi possível preparar a impressão. Imprima pela lista.`);
      return;
    }

    if (impressaoStore.config.formato_os === 'cupom' && impressao.podeImprimirDireto.value) {
      if (await impressao.imprimirCupom(await montarCupom(os, 'ENTRADA'))) return;
    }

    osParaImprimir.value = os;
    setTimeout(async () => {
      await aguardarImagensDaImpressao();
      imprimirComPagina('A4', opcoesPaginaDe('os_entrada'));
      setTimeout(() => { osParaImprimir.value = null; }, 500);
    }, 100);
  }

  return { osParaImprimir, imprimirEntrada };
}
