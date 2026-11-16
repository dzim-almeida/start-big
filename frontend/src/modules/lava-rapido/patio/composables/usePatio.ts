import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import { useCapacidades } from '@/modules/order-service/shared/segmento/useCapacidades';
import { useToast } from '@/shared/composables/useToast';
import type { ApiError } from '@/shared/types/axios.types';
import { getErrorMessage } from '@/shared/utils/error.utils';

import { avancarNoPatio, definirLavadores, getPatio, voltarNoPatio } from '../../shared/services/patio.service';

export const PATIO_KEY = 'lava-rapido-patio';

/**
 * O pátio do dia (Spec 04B). Recarrega sozinho a cada 15 s: num lava-rápido
 * com dois computadores, o carro que o outro balcão abriu aparece aqui sem
 * ninguém apertar F5.
 */
export function usePatioQuery() {
  const { tem } = useCapacidades();
  return useQuery({
    queryKey: [PATIO_KEY],
    queryFn: getPatio,
    enabled: () => tem('operacao_patio'),
    refetchInterval: 15_000,
    refetchOnWindowFocus: true,
  });
}

/** Avançar, voltar e trocar lavadores; recarrega o pátio no fim. */
export function usePatioMutations() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const recarregar = () => queryClient.invalidateQueries({ queryKey: [PATIO_KEY] });
  const avisar = (padrao: string) => (erro: AxiosError<ApiError>) => toast.error(getErrorMessage(erro, padrao));

  const avancar = useMutation({
    mutationFn: avancarNoPatio,
    onSuccess: recarregar,
    onError: avisar('Não foi possível avançar o veículo.'),
  });
  const voltar = useMutation({
    mutationFn: voltarNoPatio,
    onSuccess: recarregar,
    onError: avisar('Não foi possível voltar o veículo.'),
  });
  const trocarLavadores = useMutation({
    mutationFn: ({ numeroOs, ids }: { numeroOs: string; ids: number[] }) => definirLavadores(numeroOs, ids),
    onSuccess: () => {
      toast.success('Lavadores atualizados.');
      recarregar();
    },
    onError: avisar('Não foi possível trocar os lavadores.'),
  });

  return { avancar, voltar, trocarLavadores, recarregar };
}
