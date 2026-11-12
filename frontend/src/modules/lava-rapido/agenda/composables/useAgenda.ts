import { computed, toValue, type MaybeRefOrGetter } from 'vue';
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';

import { useCapacidades } from '@/modules/order-service/shared/segmento/useCapacidades';
import { useToast } from '@/shared/composables/useToast';
import type { ApiError } from '@/shared/types/axios.types';
import { getErrorMessage } from '@/shared/utils/error.utils';

import type { AgendamentoEntrada, SituacaoAgenda } from '../../shared/schemas/agenda.schema';
import {
  atualizarAgendamento,
  criarAgendamento,
  excluirAgendamento,
  getAgendamentos,
} from '../../shared/services/agenda.service';

export const AGENDA_KEY = 'lava-rapido-agenda';

/** Data local "AAAA-MM-DD". */
export function diaISO(data: Date): string {
  const p = (n: number) => String(n).padStart(2, '0');
  return `${data.getFullYear()}-${p(data.getMonth() + 1)}-${p(data.getDate())}`;
}

/** Os 7 dias (segunda a domingo) da semana de `dia`. */
export function diasDaSemana(dia: Date): Date[] {
  const base = new Date(dia.getFullYear(), dia.getMonth(), dia.getDate());
  const deslocamento = (base.getDay() + 6) % 7;            // segunda = 0
  base.setDate(base.getDate() - deslocamento);
  return Array.from({ length: 7 }, (_, i) => new Date(base.getFullYear(), base.getMonth(), base.getDate() + i));
}

/** Instante UTC do backend (sem "Z") → Date. */
export function instanteDoBackend(isoUtc: string): Date {
  return new Date(/[zZ]|[+-]\d{2}:?\d{2}$/.test(isoUtc) ? isoUtc : `${isoUtc}Z`);
}

/** Agendamentos da semana do dia escolhido (uma query para a faixa e o dia). */
export function useAgendaSemana(dia: MaybeRefOrGetter<Date>) {
  const { tem } = useCapacidades();
  const semana = computed(() => diasDaSemana(toValue(dia)));
  const inicio = computed(() => diaISO(semana.value[0]));
  const fim = computed(() => diaISO(semana.value[6]));
  return useQuery({
    queryKey: computed(() => [AGENDA_KEY, inicio.value, fim.value]),
    queryFn: () => getAgendamentos(inicio.value, fim.value),
    enabled: () => tem('agenda_servicos'),
    refetchInterval: 60_000,
  });
}

export function useAgendaMutations() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const recarregar = () => queryClient.invalidateQueries({ queryKey: [AGENDA_KEY] });
  const avisar = (padrao: string) => (erro: AxiosError<ApiError>) => toast.error(getErrorMessage(erro, padrao));

  const criar = useMutation({
    mutationFn: criarAgendamento,
    onSuccess: () => { toast.success('Agendado.'); recarregar(); },
    onError: avisar('Não foi possível agendar.'),
  });
  const atualizar = useMutation({
    mutationFn: ({ id, dados }: { id: number; dados: Partial<AgendamentoEntrada> & { situacao?: SituacaoAgenda; numero_os?: string } }) =>
      atualizarAgendamento(id, dados),
    onSuccess: recarregar,
    onError: avisar('Não foi possível salvar o agendamento.'),
  });
  const excluir = useMutation({
    mutationFn: excluirAgendamento,
    onSuccess: recarregar,
    onError: avisar('Não foi possível excluir.'),
  });

  return { criar, atualizar, excluir, recarregar };
}
