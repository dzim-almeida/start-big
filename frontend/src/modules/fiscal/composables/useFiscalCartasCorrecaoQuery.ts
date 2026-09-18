import { computed, type MaybeRefOrGetter, toValue } from 'vue';
import { useQuery } from '@tanstack/vue-query';

import { fiscalService } from '../services/fiscal.service';
import { fiscalKeys, FISCAL_STALE_TIME } from '../constants/fiscal.constants';
import type { DocumentoFiscalRead } from '../types/fiscal.types';

/** Só NF-e autorizada pode ter carta; para o resto nem vale a requisição. */
export function podeTerCartaCorrecao(
  documento: Pick<DocumentoFiscalRead, 'tipo_documento' | 'status'> | null | undefined,
): boolean {
  return documento?.tipo_documento === 'NFE' && documento.status === 'AUTORIZADA';
}

export function useFiscalCartasCorrecaoQuery(
  documento: MaybeRefOrGetter<DocumentoFiscalRead | null | undefined>,
) {
  const id = computed(() => toValue(documento)?.id ?? 0);
  const habilitada = computed(() => podeTerCartaCorrecao(toValue(documento)));

  return useQuery({
    queryKey: computed(() => fiscalKeys.cartasCorrecao(id.value)),
    queryFn: () => fiscalService.listarCartasCorrecao(id.value),
    enabled: habilitada,
    staleTime: FISCAL_STALE_TIME,
  });
}
