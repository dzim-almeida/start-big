import { computed, type Ref } from 'vue';
import { useQuery } from '@tanstack/vue-query';

import { fiscalService } from '../services/fiscal.service';
import { fiscalKeys } from '../constants/fiscal.constants';
import type { NfseRota } from '../types/fiscal.types';

/** O que vale sem resposta: a Nacional, como o backend (`nfse/rota.py`). */
const PADRAO: NfseRota = {
  rota: 'NACIONAL', cidade: null, obrigatorios: {}, exige_login: false, confirmada: false, regime: 'mei',
};

/**
 * Por onde sai a NFS-e e o que a nota pede, para a tela mostrar só os campos
 * que importam (docs/nfse-melhorias-plano.md, M1).
 *
 * Nunca trava a tela: sem módulo, sem rede ou sem plataforma, devolve a
 * Nacional — e aí a tela mostra o que a NFS-e Nacional pede.
 */
export function useNfseRota(habilitado: Ref<boolean> | boolean = true) {
  const { data } = useQuery({
    queryKey: fiscalKeys.nfseRota(),
    queryFn: () => fiscalService.obterRotaNfse(),
    staleTime: 10 * 60 * 1000,
    retry: false,
    enabled: computed(() => (typeof habilitado === 'boolean' ? habilitado : habilitado.value)),
  });

  const rota = computed<NfseRota>(() => data.value ?? PADRAO);
  const municipal = computed(() => rota.value.rota === 'MUNICIPAL');
  /** A cidade exige o campo (só na rota municipal). */
  const exige = (campo: string) => municipal.value && rota.value.obrigatorios?.[campo] === true;

  return { rota, municipal, exige };
}
