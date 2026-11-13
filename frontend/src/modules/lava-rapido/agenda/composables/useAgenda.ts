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

/** A grade do mês de `dia`: 6 semanas (42 dias) de segunda a domingo. */
export function diasDoMes(dia: Date): Date[] {
  const primeiro = new Date(dia.getFullYear(), dia.getMonth(), 1);
  const inicio = diasDaSemana(primeiro)[0];
  return Array.from({ length: 42 }, (_, i) => new Date(inicio.getFullYear(), inicio.getMonth(), inicio.getDate() + i));
}

/** Instante UTC do backend (sem "Z") → Date. */
export function instanteDoBackend(isoUtc: string): Date {
  return new Date(/[zZ]|[+-]\d{2}:?\d{2}$/.test(isoUtc) ? isoUtc : `${isoUtc}Z`);
}

/** Agendamentos da semana do dia escolhido. */
export function useAgendaSemana(dia: MaybeRefOrGetter<Date>) {
  const semana = computed(() => diasDaSemana(toValue(dia)));
  return useAgendaPeriodo(() => semana.value[0], () => semana.value[6]);
}

/** Agendamentos da grade do mês de `dia` (o calendário da aba). */
export function useAgendaMes(dia: MaybeRefOrGetter<Date>) {
  const grade = computed(() => diasDoMes(toValue(dia)));
  return useAgendaPeriodo(() => grade.value[0], () => grade.value[41]);
}

function useAgendaPeriodo(de: () => Date, ate: () => Date) {
  const { tem } = useCapacidades();
  const inicio = computed(() => diaISO(de()));
  const fim = computed(() => diaISO(ate()));
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
