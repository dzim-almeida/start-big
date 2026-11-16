/**
 * @fileoverview Guarda das telas de orçamento (Spec 06B D3).
 *
 * O guard do router não enxerga o TanStack Query (o QueryClient não é
 * exportado), então a guarda fica no componente: quando o contrato do
 * segmento CHEGA sem a capacidade, volta para o início. Enquanto carrega,
 * nada acontece (a marcenaria já declara a capacidade no fallback, 04B D2).
 *
 * O backend já responde 404 nesse caso (06A D26); isto só evita uma tela
 * quebrada para quem digitar o endereço.
 */
import { computed, watch } from 'vue';
import { useRouter } from 'vue-router';

import { useCapacidades } from '@/modules/order-service/shared/segmento/useCapacidades';
import { useOSFieldDefinition } from '@/modules/order-service/shared/segmento/useOSFieldDefinition.queries';
import type { SegmentCapability } from '@/modules/order-service/shared/segmento/segmentDefinition.type';

export function useExigeCapacidade(capacidade: SegmentCapability) {
  const router = useRouter();
  const { tem } = useCapacidades();
  const { isPending } = useOSFieldDefinition();      // mesma query do menu: não faz chamada nova

  /** True quando a tela pode aparecer (contrato carregando conta como "sim"). */
  const liberado = computed(() => isPending.value || tem(capacidade));

  // `immediate`: confere já ao abrir, não só quando algo mudar.
  watch(liberado, (pode) => {
    if (!pode) void router.replace({ name: 'home' });
  }, { immediate: true });

  return { liberado };
}
