import { ref } from 'vue';
import { useImpressaoStore } from '@/shared/stores/impressao.store';
import { useCompanyPrintInfo } from '@/shared/utils/print.utils';
import { DOTS } from '@/shared/services/escpos';
import { carregarLogoRaster } from '@/shared/services/escposImagem';
import { useObjetoLabels } from '@/modules/order-service/shared/segmento/useObjetoLabels';
import { useTextosImpressaoOS } from '@/modules/order-service/shared/segmento/textosImpressaoOS';
import { useAtributosImpressaoOS } from '@/modules/order-service/shared/segmento/useAtributosImpressaoOS';
import { useConfiguracoesStore } from '@/shared/stores/configuracoes.store';
import { osToEscPos } from '../../components/osToEscPos';
import type { OrderServiceReadDataType } from '../../schemas/orderServiceQuery.schema';

/**
 * Monta os bytes do cupom térmico (ESC/POS) de uma OS com TUDO que o
 * segmento declara: rótulos, termos jurídicos, prazo de abandono da loja,
 * atributos extras do objeto e rótulos da situação.
 *
 * Existe porque havia dois montadores: o do formulário (`useOSPrintFlow`)
 * passava tudo isso, e o da tabela (`OrdensServicoTab`) passava só bobina,
 * empresa, logo e o rótulo do objeto — então o mesmo botão "Cupom" imprimia
 * os termos da assistência técnica numa oficina ou numa serigrafia, conforme a
 * tela de onde o operador clicou. Um montador só, e os dois botões saem iguais.
 *
 * Os termos variam com o tipo de trabalho da OS (camisa × sacola, planejados ×
 * reforma), por isso a OS a imprimir entra num ref que o `useTextosImpressaoOS`
 * observa — o computed resolve na leitura, logo depois do set.
 */
export function useCupomOS() {
  const impressaoStore = useImpressaoStore();
  const { companyInfo } = useCompanyPrintInfo();
  const { labelSingular, definicao } = useObjetoLabels();
  const { atributos } = useAtributosImpressaoOS();
  const configuracoesStore = useConfiguracoesStore();

  const osAtual = ref<OrderServiceReadDataType | null>(null);
  const { textos, identificadorCupom } = useTextosImpressaoOS(
    () => (osAtual.value?.dados_adicionais as Record<string, unknown> | undefined)
      ?.tipo_trabalho as string | undefined,
  );

  async function montarCupom(
    os: OrderServiceReadDataType,
    tipo: 'ENTRADA' | 'SAIDA' | 'CANCELAMENTO',
  ): Promise<Uint8Array> {
    osAtual.value = os;
    const bobina = impressaoStore.config.bobina;
    const logoRaster = await carregarLogoRaster(companyInfo.value.logo, DOTS[bobina]);
    return osToEscPos(os, tipo, {
      bobina,
      empresa: companyInfo.value,
      logoRaster,
      rotuloObjeto: labelSingular.value,
      rotuloIdentificador: identificadorCupom.value,
      textos: textos.value.cupom,
      prazoAbandonoDias: configuracoesStore.prazoAbandonoDias,
      atributos: atributos(os.objeto?.dados_adicionais, os.dados_adicionais),
      rotulosSituacao: definicao.value?.rotulos_situacao,
    });
  }

  return { montarCupom };
}
