import { computed } from 'vue';

import { useSegmento } from '@/shared/composables/useSegmento';
import { useOSFieldDefinition } from './request/useOSFieldDefinition.queries';

/**
 * Rótulos dinâmicos do "objeto de serviço" por segmento, dirigidos pelo contrato
 * do backend (GET /ordens-servico/definicao-campos).
 *
 * O usuário nunca vê a palavra interna "objeto": em oficina vê "Veículo/Placa",
 * em informática vê "Equipamento/Nº de Série". Novos segmentos passam a exibir
 * seus próprios rótulos sem alterar o frontend — basta o backend definir.
 *
 * Enquanto o contrato carrega (ou para segmentos sem definição dedicada), usa
 * um fallback por segmento para não piscar rótulo errado.
 */
export function useObjetoLabels() {
  const { data } = useOSFieldDefinition();
  const { isOficinaMecanica } = useSegmento();

  const definicao = computed(() => data.value?.definicao ?? null);

  const labelSingular = computed(
    () => definicao.value?.rotulo_objeto_singular
      ?? (isOficinaMecanica.value ? 'Veículo' : 'Equipamento'),
  );

  const labelPlural = computed(
    () => definicao.value?.rotulo_objeto_plural
      ?? (isOficinaMecanica.value ? 'Veículos' : 'Equipamentos'),
  );

  const labelIdentificador = computed(
    () => definicao.value?.identificador?.label
      ?? (isOficinaMecanica.value ? 'Placa' : 'Nº de Série'),
  );

  /** Regex de validação do identificador (ex: placa), quando o segmento define. */
  const identificadorRegex = computed(() => definicao.value?.identificador?.regex ?? null);

  return {
    definicao,
    labelSingular,
    labelPlural,
    labelIdentificador,
    identificadorRegex,
  };
}
