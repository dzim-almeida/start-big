import { computed } from 'vue';

import { useSegmento } from '@/shared/composables/useSegmento';
import { useOSFieldDefinition } from './useOSFieldDefinition.queries';
import type { SegmentCapability } from './segmentDefinition.type';

/**
 * Capacidades do segmento — o que ele FAZ, dirigido pelo contrato do backend
 * (GET /ordens-servico/definicao-campos → definicao.capacidades).
 *
 * Existe para a UI parar de perguntar "quem é o cliente?" (`isOficinaMecanica`)
 * e passar a perguntar "o que este segmento faz?". A diferença é o custo do
 * próximo segmento: com `if segmento`, ligar a vistoria em `oficina_moto` exige
 * caçar e editar cada `v-if` do módulo; com capacidades, é uma linha no registry
 * (`app/core/segmentos.py`) e o frontend obedece sozinho.
 *
 * Nenhuma destas capacidades é exclusiva de oficina: aprovação de orçamento e
 * garantia servem qualquer negócio de serviço. Hoje só a oficina as declara
 * porque foi para ela que foram construídas.
 */

/**
 * Fallback usado ENQUANTO o contrato não chegou (a query é assíncrona e a
 * primeira abertura do formulário acontece antes da resposta).
 *
 * Sem isto a aba de Vistoria sumiria e apareceria com um pisca. É o mesmo
 * padrão de `useObjetoLabels`, e pela mesma razão: não piscar a UI errada.
 *
 * Repare que o `if segmento` não sumiu do projeto — ele foi CENTRALIZADO aqui,
 * em um lugar, como fallback de carregamento. Os componentes não o conhecem
 * mais. Quando o contrato chega, ele manda; este mapa nunca decide sozinho.
 */
const FALLBACK_POR_SEGMENTO: Record<string, SegmentCapability[]> = {
  oficina_mecanica: ['vistoria', 'revisoes', 'aprovacao_itens', 'garantia_itens'],
  assistencia_tecnica: [],
};

export function useCapacidades() {
  const { data, isPending } = useOSFieldDefinition();
  const { segmento } = useSegmento();

  const capacidades = computed<SegmentCapability[]>(() => {
    // Contrato ainda carregando: usa o fallback para não piscar.
    if (isPending.value) return FALLBACK_POR_SEGMENTO[segmento.value ?? ''] ?? [];
    // Contrato é a fonte da verdade. Segmento sem definição = nenhuma capacidade
    // (fluxo genérico de OS), que é o padrão seguro para um segmento novo.
    return data.value?.definicao?.capacidades ?? [];
  });

  /** True se o segmento declara a capacidade. */
  function tem(capacidade: SegmentCapability): boolean {
    return capacidades.value.includes(capacidade);
  }

  return {
    capacidades,
    tem,
    temVistoria: computed(() => tem('vistoria')),
    temRevisoes: computed(() => tem('revisoes')),
    temAprovacaoItens: computed(() => tem('aprovacao_itens')),
    temGarantiaItens: computed(() => tem('garantia_itens')),
  };
}
